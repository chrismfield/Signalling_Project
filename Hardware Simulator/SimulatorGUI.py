"""Hardware Simulator with tkinter control panel."""
import asyncio
import logging
import os
import queue
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

        root.title("Hardware Simulator")
        root.resizable(True, True)

        wrap = ttk.Frame(root, padding=8)
        wrap.grid(sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self._build_tc(wrap, row=0)
        self._build_plungers(wrap, row=1)
        self._build_signals(wrap, row=2)
        self._build_points(wrap, row=3)
        self._build_status(wrap, row=4)

        self._refresh()

    # ── Section builders ───────────────────────────────────────────────────────

    def _build_tc(self, parent, row):
        frame = ttk.LabelFrame(parent, text="Track Circuits", padding=6)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 4))

        self._tc: dict = {}
        PER_ROW = 5
        for i, (name, data) in enumerate(layout["TrackCircuits"].items()):
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

    def _build_plungers(self, parent, row):
        frame = ttk.LabelFrame(parent, text="Plungers", padding=6)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 4))

        self._pl: dict = {}
        for i, (name, data) in enumerate(layout["Plungers"].items()):
            col = i * 4
            ttk.Label(frame, text=name, anchor="e").grid(
                row=0, column=col, padx=(8, 4), pady=4)
            ttk.Label(frame, text=data.get("description", ""),
                      foreground="#888888").grid(row=0, column=col + 1, padx=(0, 8))

            ind = tk.Label(frame, width=2, bg="#555555", relief="groove")
            ind.grid(row=0, column=col + 2, padx=4, pady=4)

            btn = tk.Button(frame, text="PRESS", width=6,
                            bg="#444444", fg="white",
                            activebackground="#777777", relief="raised", bd=2)
            btn.grid(row=0, column=col + 3, padx=(0, 14), pady=4)
            btn.bind("<ButtonPress-1>",   lambda e, n=name: self._on_plunger(n, True))
            btn.bind("<ButtonRelease-1>", lambda e, n=name: self._on_plunger(n, False))

            self._pl[name] = {"btn": btn, "ind": ind, "data": data}

    def _build_signals(self, parent, row):
        frame = ttk.LabelFrame(parent, text="Signals (read-only)", padding=6)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 4))

        self._sig: dict = {}
        PER_ROW = 6
        for i, (name, data) in enumerate(layout["Signals"].items()):
            r, c = divmod(i, PER_ROW)
            col = c * 2
            ttk.Label(frame, text=f"Sig {name}", anchor="e", width=7).grid(
                row=r, column=col, padx=(8, 2), pady=3)
            lbl = tk.Label(frame, text="DANGER", width=8,
                           bg=ASPECT_COLOR["DANGER"], fg="white", relief="groove")
            lbl.grid(row=r, column=col + 1, padx=(2, 14), pady=3)
            self._sig[name] = {"lbl": lbl, "data": data}

    def _build_points(self, parent, row):
        frame = ttk.LabelFrame(parent, text="Points (read-only)", padding=6)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 4))

        self._pts: dict = {}
        for i, (name, data) in enumerate(layout["Points"].items()):
            col = i * 2
            ttk.Label(frame, text=f"Pts {name}", anchor="e", width=8).grid(
                row=0, column=col, padx=(8, 2), pady=4)
            lbl = tk.Label(frame, text="UNKNOWN", width=8,
                           bg=PTS_COLOR["UNKNOWN"], fg="white", relief="groove")
            lbl.grid(row=0, column=col + 1, padx=(2, 14), pady=4)
            self._pts[name] = {"lbl": lbl, "data": data}

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

    def _on_tc(self, name):
        w = self._tc[name]
        occupied = w["var"].get()
        data = w["data"]
        sl = self._slave(data["address"])
        if sl:
            for reg in data["registers"].get("self-latching", []):
                sl.setValues(1, reg, [occupied])  # coils  (FC1)
                sl.setValues(2, reg, [occupied])  # discrete inputs (FC2)
        w["ind"].config(bg=TC_COLOR[occupied])

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

    # ── Refresh loop ───────────────────────────────────────────────────────────

    def _coil(self, slave, reg) -> bool:
        if reg is None or reg is False:
            return False
        try:
            return bool(slave.getValues(1, int(reg), 1)[0])
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

    def _get_pts(self, data) -> str:
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

    def _refresh(self):
        while True:
            try:
                kind, val = self._queue.get_nowait()
                if kind == "status":
                    self._status_var.set(val)
            except queue.Empty:
                break

        for w in self._sig.values():
            asp = self._get_aspect(w["data"])
            w["lbl"].config(text=asp, bg=ASPECT_COLOR.get(asp, "#666666"))

        for w in self._pts.values():
            pos = self._get_pts(w["data"])
            w["lbl"].config(text=pos, bg=PTS_COLOR.get(pos, "#666666"))

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


async def _mirror_points(ctx):
    """Copy coil state to discrete inputs for points feedback."""
    while True:
        try:
            for point in layout["Points"].values():
                sid = point["address"]
                coils = ctx[sid].getValues(1, 1, 2000)
                ctx[sid].setValues(2, 1, coils)
        except Exception as exc:
            log.error("Mirror error: %s", exc)
        await asyncio.sleep(1)


def _thread_main(loop, port, ctx, gui):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(asyncio.gather(
        _server(port, ctx, gui),
        _mirror_points(ctx),
    ))


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
