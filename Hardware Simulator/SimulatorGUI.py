"""Hardware Simulator with tkinter control panel."""
import asyncio
import logging
import os
import queue
import re
import sys
import threading
import tkinter as tk
from tkinter import ttk

import jsons
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
from pymodbus.server import StartAsyncSerialServer

PORT = "COM6"
BAUD = 19200
JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "WDSME.json")

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.WARN)

with open(JSON_PATH) as f:
    layout = jsons.loads(f.read())


def _natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


def _sorted(section):
    return sorted(layout[section].items(), key=lambda x: _natural_key(x[0]))


# ── Modbus context ─────────────────────────────────────────────────────────────

def _make_slave():
    return ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [False] * 2000),
        co=ModbusSequentialDataBlock(0, [False] * 2000),
        hr=ModbusSequentialDataBlock(0, [0] * 100),
        ir=ModbusSequentialDataBlock(0, [0] * 100),
    )


def build_context():
    slaves = {}

    def _add(items):
        for item in items.values():
            addr = item["address"]
            if addr not in slaves:
                slaves[addr] = _make_slave()

    _add(layout["Signals"])
    _add(layout["Points"])
    _add(layout.get("AxleCounters", {}))
    _add(layout["TrackCircuits"])
    _add(layout["Plungers"])
    return ModbusServerContext(slaves=slaves, single=False)


context = build_context()


# ── Colour maps ────────────────────────────────────────────────────────────────

ASPECT_COLOR = {
    "CLEAR":   "#1a9e3f",
    "CAUTION": "#e8a000",
    "DANGER":  "#cc2222",
    "UNKNOWN": "#666666",
    "ERROR":   "#aa00cc",
}
TC_COLOR  = {True: "#cc2222", False: "#1a9e3f"}
PTS_COLOR = {"NORMAL": "#1070cc", "REVERSE": "#dd6600", "UNKNOWN": "#666666", "ERROR": "#aa00cc"}


# ── GUI ────────────────────────────────────────────────────────────────────────

class SimulatorGUI:
    def __init__(self, root: tk.Tk, ctx: ModbusServerContext):
        self.root = root
        self.ctx = ctx
        self._queue: queue.Queue = queue.Queue()

        # Previous coil states per point for timed-mode change detection
        self._pts_prev_coils: dict = {}
        # Pending after-IDs for timed mode
        self._pts_timed_id: dict = {}

        # TC stepper state
        self._stepper_after_id = None
        self._stepper_seq: list = []
        self._stepper_idx: int = 0

        root.title("Hardware Simulator")
        root.resizable(True, True)

        wrap = ttk.Frame(root, padding=8)
        wrap.grid(sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self._build_ac(wrap, row=0)
        self._build_tc(wrap, row=1)
        self._build_tc_stepper(wrap, row=2)
        self._build_plungers(wrap, row=3)
        self._build_signals(wrap, row=4)
        self._build_points(wrap, row=5)
        self._build_status(wrap, row=6)

        self._refresh()

    # ── Section builders ───────────────────────────────────────────────────────

    def _build_ac(self, parent, row):
        frame = ttk.LabelFrame(parent, text="Axle Counters", padding=6)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 4))

        self._ac: dict = {}
        PER_ROW = 5
        STRIDE = 7  # columns per AC entry

        for i, (name, data) in enumerate(_sorted("AxleCounters")):
            r, c = divmod(i, PER_ROW)
            base = c * STRIDE

            ttk.Label(frame, text=name, anchor="e", width=4).grid(
                row=r, column=base, padx=(8, 4), pady=3)

            up_var = tk.IntVar(value=0)
            down_var = tk.IntVar(value=0)

            tk.Button(
                frame, text="↑ Up", width=5,
                bg="#1a4a8a", fg="white", activebackground="#2a6acc",
                command=lambda n=name: self._on_ac(n, "up"),
            ).grid(row=r, column=base + 1, padx=2, pady=3)

            tk.Label(frame, textvariable=up_var, width=4,
                     relief="sunken", anchor="center", bg="#f0f0f0").grid(
                row=r, column=base + 2, padx=(0, 4), pady=3)

            tk.Button(
                frame, text="↓ Dn", width=5,
                bg="#8a2a1a", fg="white", activebackground="#cc4433",
                command=lambda n=name: self._on_ac(n, "down"),
            ).grid(row=r, column=base + 3, padx=2, pady=3)

            tk.Label(frame, textvariable=down_var, width=4,
                     relief="sunken", anchor="center", bg="#f0f0f0").grid(
                row=r, column=base + 4, padx=(0, 4), pady=3)

            tk.Button(
                frame, text="Rst", width=3,
                bg="#555555", fg="white", activebackground="#777777",
                command=lambda n=name: self._on_ac_reset(n),
            ).grid(row=r, column=base + 5, padx=(0, 14), pady=3)

            self._ac[name] = {"data": data, "up_var": up_var, "down_var": down_var}

    def _build_tc(self, parent, row):
        frame = ttk.LabelFrame(parent, text="Track Circuits", padding=6)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 4))

        self._tc: dict = {}
        PER_ROW = 5
        for i, (name, data) in enumerate(_sorted("TrackCircuits")):
            r, c = divmod(i, PER_ROW)
            col = c * 3

            ttk.Label(frame, text=name, anchor="e", width=4).grid(
                row=r, column=col, padx=(8, 2), pady=3)

            ind = tk.Label(frame, width=2, bg=TC_COLOR[False], relief="groove")
            ind.grid(row=r, column=col + 1, padx=2, pady=3)

            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(frame, text="Occupied", variable=var,
                                  command=lambda n=name: self._on_tc(n))
            chk.grid(row=r, column=col + 2, padx=(2, 14), pady=3, sticky="w")

            self._tc[name] = {"var": var, "ind": ind, "data": data}

    def _build_tc_stepper(self, parent, row):
        frame = ttk.LabelFrame(parent, text="TC Stepper", padding=6)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 4))

        ttk.Label(frame, text="Sequence:").grid(row=0, column=0, padx=(0, 4), pady=4, sticky="e")
        self._stepper_seq_var = tk.StringVar(value="G,A,B,C,D,S")
        ttk.Entry(frame, textvariable=self._stepper_seq_var, width=24).grid(
            row=0, column=1, padx=(0, 12), pady=4, sticky="w")

        ttk.Label(frame, text="Interval (s):").grid(row=0, column=2, padx=(0, 4), pady=4, sticky="e")
        self._stepper_interval_var = tk.IntVar(value=5)
        ttk.Spinbox(frame, textvariable=self._stepper_interval_var,
                    from_=1, to=300, width=5).grid(
            row=0, column=3, padx=(0, 12), pady=4, sticky="w")

        self._stepper_start_btn = tk.Button(
            frame, text="Start", width=6,
            bg="#1a8000", fg="white", activebackground="#2ab000",
            command=self._stepper_start)
        self._stepper_start_btn.grid(row=0, column=4, padx=4, pady=4)

        self._stepper_stop_btn = tk.Button(
            frame, text="Stop", width=6,
            bg="#880000", fg="white", activebackground="#aa2222",
            command=self._stepper_stop, state="disabled")
        self._stepper_stop_btn.grid(row=0, column=5, padx=4, pady=4)

        tk.Button(
            frame, text="Reset", width=6,
            bg="#555555", fg="white", activebackground="#777777",
            command=self._stepper_reset,
        ).grid(row=0, column=6, padx=4, pady=4)

        ttk.Label(frame, text="Current TC:").grid(row=0, column=7, padx=(16, 4), pady=4, sticky="e")
        self._stepper_cur_var = tk.StringVar(value="—")
        self._stepper_cur_lbl = tk.Label(
            frame, textvariable=self._stepper_cur_var,
            width=7, bg="#555555", fg="white", relief="groove")
        self._stepper_cur_lbl.grid(row=0, column=8, padx=(0, 8), pady=4)

    def _build_plungers(self, parent, row):
        frame = ttk.LabelFrame(parent, text="Plungers", padding=6)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 4))

        self._pl: dict = {}
        PER_ROW = 6
        for i, (name, data) in enumerate(_sorted("Plungers")):
            r, c = divmod(i, PER_ROW)
            col = c * 4
            ttk.Label(frame, text=name, anchor="e").grid(
                row=r, column=col, padx=(8, 4), pady=4)
            ttk.Label(frame, text=data.get("description", ""),
                      foreground="#888888").grid(row=r, column=col + 1, padx=(0, 8))

            ind = tk.Label(frame, width=2, bg="#555555", relief="groove")
            ind.grid(row=r, column=col + 2, padx=4, pady=4)

            btn = tk.Button(frame, text="PRESS", width=6,
                            bg="#444444", fg="white",
                            activebackground="#777777", relief="raised", bd=2)
            btn.grid(row=r, column=col + 3, padx=(0, 14), pady=4)
            btn.bind("<ButtonPress-1>",   lambda e, n=name: self._on_plunger(n, True))
            btn.bind("<ButtonRelease-1>", lambda e, n=name: self._on_plunger(n, False))

            self._pl[name] = {"btn": btn, "ind": ind, "data": data}

    def _build_signals(self, parent, row):
        frame = ttk.LabelFrame(parent, text="Signals (read-only)", padding=6)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 4))

        self._sig: dict = {}
        PER_ROW = 6
        for i, (name, data) in enumerate(_sorted("Signals")):
            r, c = divmod(i, PER_ROW)
            col = c * 2
            ttk.Label(frame, text=f"Sig {name}", anchor="e", width=7).grid(
                row=r, column=col, padx=(8, 2), pady=3)
            lbl = tk.Label(frame, text="DANGER", width=8,
                           bg=ASPECT_COLOR["DANGER"], fg="white", relief="groove")
            lbl.grid(row=r, column=col + 1, padx=(2, 14), pady=3)
            self._sig[name] = {"lbl": lbl, "data": data}

    def _build_points(self, parent, row):
        frame = ttk.LabelFrame(parent, text="Points", padding=6)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 4))

        # Column headers
        headers = ["Point", "Direction", "Det Mode", "Delay (s)", "Set Det (manual)", "", "Det Feedback"]
        for col, text in enumerate(headers):
            ttk.Label(frame, text=text, foreground="#888888", font=("", 8)).grid(
                row=0, column=col, padx=4, pady=(0, 2), sticky="w")

        self._pts: dict = {}
        for i, (name, data) in enumerate(_sorted("Points")):
            r = i + 1

            ttk.Label(frame, text=f"Pts {name}", anchor="e", width=8).grid(
                row=r, column=0, padx=(8, 4), pady=4, sticky="e")

            dir_lbl = tk.Label(frame, text="UNKNOWN", width=9,
                               bg=PTS_COLOR["UNKNOWN"], fg="white", relief="groove")
            dir_lbl.grid(row=r, column=1, padx=(0, 8), pady=4)

            mode_var = tk.StringVar(value="auto")
            mode_cb = ttk.Combobox(frame, textvariable=mode_var,
                                   values=["auto", "manual", "timed"],
                                   width=7, state="readonly")
            mode_cb.grid(row=r, column=2, padx=(0, 8), pady=4)

            delay_var = tk.IntVar(value=3)
            delay_spin = ttk.Spinbox(frame, textvariable=delay_var,
                                     from_=1, to=120, width=6, state="disabled")
            delay_spin.grid(row=r, column=3, padx=(0, 8), pady=4)

            det_var = tk.StringVar(value="UNKNOWN")
            det_cb = ttk.Combobox(frame, textvariable=det_var,
                                  values=["NORMAL", "REVERSE", "UNKNOWN"],
                                  width=9, state="disabled")
            det_cb.grid(row=r, column=4, padx=(0, 4), pady=4)

            apply_btn = ttk.Button(frame, text="Apply", state="disabled",
                                   command=lambda n=name: self._apply_pts_det(n))
            apply_btn.grid(row=r, column=5, padx=(0, 8), pady=4)

            det_ind = tk.Label(frame, text="UNKNOWN", width=9,
                               bg=PTS_COLOR["UNKNOWN"], fg="white", relief="groove")
            det_ind.grid(row=r, column=6, padx=(0, 14), pady=4)

            self._pts[name] = {
                "lbl": dir_lbl, "data": data,
                "mode": mode_var, "delay": delay_var, "det": det_var,
                "det_ind": det_ind, "delay_spin": delay_spin,
                "det_cb": det_cb, "apply_btn": apply_btn,
            }
            self._pts_prev_coils[name] = (None, None)
            mode_var.trace_add("write", lambda *_, n=name: self._on_pts_mode_change(n))

    def _build_status(self, parent, row):
        self._status_var = tk.StringVar(value="Starting Modbus server…")
        ttk.Label(parent, textvariable=self._status_var,
                  relief="sunken", anchor="w", padding=(4, 2)).grid(
            row=row, column=0, sticky="ew", pady=(4, 0))

    # ── Actions ────────────────────────────────────────────────────────────────

    def _slave(self, address):
        try:
            return self.ctx[address]
        except Exception:
            return None

    # -- Axle counters --

    def _on_ac(self, name: str, direction: str):
        w = self._ac[name]
        data = w["data"]
        sl = self._slave(data["address"])
        if not sl:
            return
        if direction == "up":
            reg = data.get("upcount_reg", 13)
            coil = data.get("normal_coil")
        else:
            reg = data.get("downcount_reg", 14)
            coil = data.get("reverse_coil")
        current = sl.getValues(3, reg, 1)[0]
        sl.setValues(3, reg, [current + 1])
        # Pulse the detection coil momentarily to simulate axle detection
        if coil is not None:
            sl.setValues(1, coil, [True])
            sl.setValues(2, coil, [True])
            self.root.after(300, lambda addr=data["address"], c=coil: self._clear_ac_coil(addr, c))

    def _clear_ac_coil(self, address, coil):
        sl = self._slave(address)
        if sl:
            sl.setValues(1, coil, [False])
            sl.setValues(2, coil, [False])

    def _on_ac_reset(self, name: str):
        w = self._ac[name]
        data = w["data"]
        sl = self._slave(data["address"])
        if not sl:
            return
        sl.setValues(3, data.get("upcount_reg", 13), [0])
        sl.setValues(3, data.get("downcount_reg", 14), [0])

    # -- Track circuits --

    def _on_tc(self, name):
        w = self._tc[name]
        occupied = w["var"].get()
        data = w["data"]
        sl = self._slave(data["address"])
        if sl:
            for reg in data["registers"].get("self-latching", []):
                sl.setValues(1, reg, [occupied])
                sl.setValues(2, reg, [occupied])
        w["ind"].config(bg=TC_COLOR[occupied])

    # -- Plungers --

    def _on_plunger(self, name, pressed: bool):
        w = self._pl[name]
        data = w["data"]
        sl = self._slave(data["address"])
        if sl:
            reg = data["register"]
            sl.setValues(1, reg, [pressed])
            sl.setValues(2, reg, [pressed])
        w["ind"].config(bg="#ff4444" if pressed else "#555555")
        w["btn"].config(relief="sunken" if pressed else "raised")

    # -- Points detection mode --

    def _on_pts_mode_change(self, name: str):
        w = self._pts[name]
        mode = w["mode"].get()
        is_timed = mode == "timed"
        is_manual = mode == "manual"
        w["delay_spin"].config(state="normal" if is_timed else "disabled")
        w["det_cb"].config(state="readonly" if is_manual else "disabled")
        w["apply_btn"].config(state="normal" if is_manual else "disabled")
        # Cancel any pending timed mirror
        if name in self._pts_timed_id:
            self.root.after_cancel(self._pts_timed_id.pop(name))
        # When switching back to auto, mirror immediately
        if mode == "auto":
            self._mirror_pts_now(name)

    def _apply_pts_det(self, name: str):
        """Write manual detection state to discrete inputs."""
        w = self._pts[name]
        data = w["data"]
        sl = self._slave(data["address"])
        if not sl:
            return
        det = w["det"].get()
        n_coil = data.get("normal_coil")
        r_coil = data.get("reverse_coil")
        if n_coil is not None:
            sl.setValues(2, n_coil, [det == "NORMAL"])
        if r_coil is not None:
            sl.setValues(2, r_coil, [det == "REVERSE"])

    def _mirror_pts_now(self, name: str):
        """Copy output coil state to discrete inputs for a single point."""
        data = self._pts[name]["data"]
        sl = self._slave(data["address"])
        if not sl:
            return
        for key in ("normal_coil", "reverse_coil"):
            reg = data.get(key)
            if reg is not None:
                sl.setValues(2, reg, sl.getValues(1, reg, 1))

    # -- TC Stepper --

    def _stepper_start(self):
        seq_str = self._stepper_seq_var.get().strip()
        self._stepper_seq = [s.strip() for s in seq_str.split(",") if s.strip()]
        if not self._stepper_seq:
            return
        self._stepper_idx = 0
        self._stepper_start_btn.config(state="disabled")
        self._stepper_stop_btn.config(state="normal")
        self._stepper_step()

    def _stepper_stop(self):
        if self._stepper_after_id:
            self.root.after_cancel(self._stepper_after_id)
            self._stepper_after_id = None
        self._stepper_clear_all()
        self._stepper_cur_var.set("—")
        self._stepper_cur_lbl.config(bg="#555555")
        self._stepper_start_btn.config(state="normal")
        self._stepper_stop_btn.config(state="disabled")

    def _stepper_reset(self):
        self._stepper_stop()
        self._stepper_idx = 0

    def _stepper_clear_all(self):
        for tc_name in self._stepper_seq:
            if tc_name in self._tc:
                self._tc[tc_name]["var"].set(False)
                self._on_tc(tc_name)

    def _stepper_step(self):
        # Clear the previously active TC
        if self._stepper_idx > 0:
            prev = self._stepper_seq[self._stepper_idx - 1]
            if prev in self._tc:
                self._tc[prev]["var"].set(False)
                self._on_tc(prev)

        if self._stepper_idx >= len(self._stepper_seq):
            self._stepper_cur_var.set("Done")
            self._stepper_cur_lbl.config(bg="#1a8000")
            self._stepper_start_btn.config(state="normal")
            self._stepper_stop_btn.config(state="disabled")
            return

        cur = self._stepper_seq[self._stepper_idx]
        self._stepper_cur_var.set(cur)
        self._stepper_cur_lbl.config(bg="#cc2222")

        if cur in self._tc:
            self._tc[cur]["var"].set(True)
            self._on_tc(cur)

        self._stepper_idx += 1
        interval_ms = self._stepper_interval_var.get() * 1000
        self._stepper_after_id = self.root.after(interval_ms, self._stepper_step)

    # ── Refresh loop ───────────────────────────────────────────────────────────

    def _coil(self, slave, reg) -> bool:
        if reg is None or reg is False:
            return False
        try:
            return bool(slave.getValues(1, int(reg), 1)[0])
        except Exception:
            return False

    def _di(self, slave, reg) -> bool:
        if reg is None or reg is False:
            return False
        try:
            return bool(slave.getValues(2, int(reg), 1)[0])
        except Exception:
            return False

    def _get_aspect(self, data) -> str:
        sl = self._slave(data["address"])
        if not sl:
            return "ERROR"
        try:
            if self._coil(sl, data.get("clearreg")):
                return "CLEAR"
            if self._coil(sl, data.get("doublecautionreg")) or self._coil(sl, data.get("cautionreg")):
                return "CAUTION"
            return "DANGER"
        except Exception:
            return "ERROR"

    def _get_pts_dir(self, data) -> str:
        """Direction commanded by output coils."""
        sl = self._slave(data["address"])
        if not sl:
            return "ERROR"
        try:
            n = self._coil(sl, data.get("normal_coil"))
            r = self._coil(sl, data.get("reverse_coil"))
            if n and not r:
                return "NORMAL"
            if r and not n:
                return "REVERSE"
            if n and r:
                return "ERROR"
            return "UNKNOWN"
        except Exception:
            return "ERROR"

    def _get_pts_det(self, data) -> str:
        """Detection reported by discrete inputs."""
        sl = self._slave(data["address"])
        if not sl:
            return "ERROR"
        try:
            n = self._di(sl, data.get("normal_coil"))
            r = self._di(sl, data.get("reverse_coil"))
            if n and not r:
                return "NORMAL"
            if r and not n:
                return "REVERSE"
            if n and r:
                return "ERROR"
            return "UNKNOWN"
        except Exception:
            return "ERROR"

    def _refresh(self):
        while True:
            try:
                kind, val = self._queue.get_nowait()
                if kind == "status":
                    self._status_var.set(val)
            except queue.Empty:
                break

        # Axle counter count displays (kept in sync with actual HR values)
        for name, w in self._ac.items():
            data = w["data"]
            sl = self._slave(data["address"])
            if sl:
                up_reg = data.get("upcount_reg", 13)
                dn_reg = data.get("downcount_reg", 14)
                w["up_var"].set(sl.getValues(3, up_reg, 1)[0])
                w["down_var"].set(sl.getValues(3, dn_reg, 1)[0])

        # Signals
        for w in self._sig.values():
            asp = self._get_aspect(w["data"])
            w["lbl"].config(text=asp, bg=ASPECT_COLOR.get(asp, "#666666"))

        # Points
        for name, w in self._pts.items():
            data = w["data"]
            mode = w["mode"].get()
            sl = self._slave(data["address"])

            if sl and mode in ("auto", "timed"):
                n_coil = data.get("normal_coil")
                r_coil = data.get("reverse_coil")
                n_val = bool(sl.getValues(1, n_coil, 1)[0]) if n_coil is not None else False
                r_val = bool(sl.getValues(1, r_coil, 1)[0]) if r_coil is not None else False
                prev = self._pts_prev_coils.get(name, (None, None))

                if mode == "auto":
                    self._mirror_pts_now(name)
                elif (n_val, r_val) != prev:
                    # Coils changed: (re)schedule delayed mirror
                    if name in self._pts_timed_id:
                        self.root.after_cancel(self._pts_timed_id[name])
                    delay_ms = w["delay"].get() * 1000
                    self._pts_timed_id[name] = self.root.after(
                        delay_ms, lambda n=name: self._mirror_pts_now(n))

                self._pts_prev_coils[name] = (n_val, r_val)

            # Direction (coil) indicator
            pos = self._get_pts_dir(data)
            w["lbl"].config(text=pos, bg=PTS_COLOR.get(pos, "#666666"))

            # Detection (DI) indicator
            det = self._get_pts_det(data)
            w["det_ind"].config(text=det, bg=PTS_COLOR.get(det, "#666666"))

        self.root.after(500, self._refresh)

    def post_status(self, msg: str):
        self._queue.put(("status", msg))


# ── Asyncio server ─────────────────────────────────────────────────────────────

async def _server(port, ctx, gui):
    # Restart loop — serial_asyncio on Windows (ProactorEventLoop) silently stops
    # delivering callbacks after ~60s; SelectorEventLoop fixes the root cause but
    # we also restart on any exception as a safety net.
    while True:
        try:
            gui.post_status(f"Modbus server running on {port} @ {BAUD} baud")
            await StartAsyncSerialServer(context=ctx, port=port, baudrate=BAUD)
        except Exception as exc:
            gui.post_status(f"Server error (restarting in 2 s): {exc}")
            log.error("Modbus server error: %s", exc)
        else:
            gui.post_status("Server stopped — restarting in 2 s…")
        await asyncio.sleep(2)


def _thread_main(loop, port, ctx, gui):
    asyncio.set_event_loop(loop)
    # _mirror_points removed — auto mirroring is now handled in the GUI refresh loop
    loop.run_until_complete(_server(port, ctx, gui))


if __name__ == "__main__":
    root = tk.Tk()
    gui = SimulatorGUI(root, context)

    # serial_asyncio requires SelectorEventLoop on Windows —
    # the default ProactorEventLoop (Python 3.8+) silently breaks serial I/O
    # after ~60 s with virtual COM ports (Com0Com).
    if sys.platform == "win32":
        loop = asyncio.SelectorEventLoop()
    else:
        loop = asyncio.new_event_loop()

    t = threading.Thread(target=_thread_main, args=(loop, PORT, context, gui), daemon=True)
    t.start()

    root.mainloop()
