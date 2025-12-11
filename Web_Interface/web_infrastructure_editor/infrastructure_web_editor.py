import os
import json
from json import JSONDecodeError
from flask import Flask, render_template, request, jsonify, send_file, Blueprint, Response, stream_with_context, send_from_directory
import sys, os, glob
import subprocess
import time

try:
    from serial.tools import list_ports
except Exception:
    list_ports = None



app = Flask(__name__)

UPLOAD_FOLDER = os.path.abspath(".")
DEFAULT_FILE  = "default.json"
CONFIG_FILE   = "config.json"
MAPPING_FILE  = "function_to_coil_mapping.json"

def _stream_journal(unit: str, lines: int, priority: str | None, grep: str | None):
    """
    Stream journalctl output as Server-Sent Events (SSE).
    Equivalent of: journalctl -u <unit> -n <lines> -f -o cat [-p <priority>]
    """
    cmd = ["journalctl", "--unit", unit, "--no-pager", "-f", "-n", str(lines), "-o", "cat"]
    if priority:
        cmd.extend(["-p", priority])  # debug | info | warning | err | crit | alert | emerg

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    last_heartbeat = time.time()

    def cleanup():
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
            except Exception:
                pass

    try:
        if proc.stdout is None:
            yield "event: error\ndata: Failed to open journalctl\n\n"
            cleanup()
            return

        for raw in proc.stdout:
            line = raw.rstrip("\n")
            if grep and grep not in line:
                # skip
                pass
            else:
                yield f"data: {line}\n\n"

            # keep-alive heartbeat every ~15s
            now = time.time()
            if now - last_heartbeat > 15:
                last_heartbeat = now
                yield f": ping {int(now)}\n\n"  # SSE comment line
        rc = proc.poll()
        yield f"event: done\ndata: journalctl exited with code {rc}\n\n"
    finally:
        cleanup()

@app.route("/logs")
def logs_index():
    unit = request.args.get("unit", os.environ.get("DEFAULT_UNIT", "interlocking.service"))
    lines = int(request.args.get("lines", 200))
    return render_template("logs.html", unit=unit, lines=lines)

@app.route("/logs/stream")
def logs_stream():
    unit = request.args.get("unit", os.environ.get("DEFAULT_UNIT", "interlocking.service"))
    lines = int(request.args.get("lines", 200))
    priority = request.args.get("priority")  # e.g. info, warning, err
    grep = request.args.get("grep")
    generator = stream_with_context(_stream_journal(unit, lines, priority, grep))
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }
    return Response(generator, headers=headers)

def _list_serial_ports():
    # 1) Prefer pyserial for robust cross-platform listing
    if list_ports:
        try:
            ports = [p.device for p in list_ports.comports()]
            if ports:
                return ports
        except Exception:
            pass

    # 2) Fallbacks if pyserial isn't available / returns nothing
    if os.name == "nt":
        # Windows – probe common COM range
        return [f"COM{i}" for i in range(1, 257)]
    else:
        # Linux / macOS – glob common device patterns
        patterns = [
            "/dev/ttyUSB*", "/dev/ttyACM*", "/dev/ttyS*",
            "/dev/tty.*",   "/dev/cu.*"
        ]
        found = []
        for pat in patterns:
            found.extend(glob.glob(pat))
        # de-dupe and sort for stability
        return sorted(set(found))

@app.get("/api/ports")
def api_ports():
    return jsonify({"ports": _list_serial_ports()})

def load_json_file(path):
    """Safely load JSON, returning {} on missing/invalid."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except JSONDecodeError:
        print(f"Warning: {path} contains invalid JSON. Using empty dict.")
        return {}
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return {}

def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# Optional / future
coil_mapping = load_json_file(os.path.join(UPLOAD_FOLDER, MAPPING_FILE))

def empty_layout():
    return {
        "AxleCounters": {},
        "TrackCircuits" :{},
        "Signals": {},
        "Points": {},
        "Sections": {},
        "Plungers": {},
        "Routes": {},
        "Triggers": {}
    }

def default_config():
    # sensible defaults if config.json missing
    return {
        "axle_tolerance": 4,
        "layoutDB": DEFAULT_FILE,
        "network_ports": {"network_1": "", "network_2": ""},
        "logging_level": 20,
        "mqtt_broker_address": "127.0.0.1",
        "point_interlock_timeout": 5
    }

@app.route("/infra_editor")
def infra_editor():
    # Do NOT auto-load a layout file unless explicitly asked
    filename = request.args.get("file")  # None if not provided
    if filename:
        data = load_json_file(os.path.join(UPLOAD_FOLDER, filename)) or empty_layout()
        # ensure keys exist
        for k in empty_layout().keys():
            data.setdefault(k, {})
    else:
        data = empty_layout()

    # Always load config.json by default (for the Config tab / network lists)
    cfg_path = os.path.join(UPLOAD_FOLDER, CONFIG_FILE)
    cfg = load_json_file(cfg_path) or default_config()

    # Show all JSON files for the picker
    server_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(".json")]

    tabs = ["AxleCounters","TrackCircuits","Signals","Points","Plungers","Sections","Routes","Triggers"]

    return render_template(
        "editor.html",
        data=data,
        tabs=tabs,
        server_files=server_files,
        current_file=filename or "",
        config=cfg
    )

@app.route("/")
def index():
    # Do NOT auto-load a layout file unless explicitly asked
    filename = request.args.get("file")  # None if not provided
    if filename:
        data = load_json_file(os.path.join(UPLOAD_FOLDER, filename)) or empty_layout()
        # ensure keys exist
        for k in empty_layout().keys():
            data.setdefault(k, {})
    else:
        data = empty_layout()

    # Always load config.json by default (for the Config tab / network lists)
    cfg_path = os.path.join(UPLOAD_FOLDER, CONFIG_FILE)
    cfg = load_json_file(cfg_path) or default_config()

    # Show all JSON files for the picker
    server_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(".json")]

    tabs = ["AxleCounters","TrackCircuits","Signals","Points","Plungers","Sections","Routes","Triggers"]

    return render_template(
        "editor.html",
        data=data,
        tabs=tabs,
        server_files=server_files,
        current_file=filename or "",
        config=cfg
    )


@app.route("/diagnostics")
def diagnostics():
    return render_template("non-graphic.html")

@app.route("/graphic")
def graphic():
    return render_template("graphic.html")

@app.route("/non-graphic")
def non_graphic():
    return render_template("non-graphic.html")

@app.route("/mqtt")
def mqtt_page():
    return render_template("mqtt.html", title="MQTT Errors")

# return whichever json file is specified by layoutDB in config.json
@app.route("/layout-json")
def layout_json():
    cfg = load_json_file(os.path.join(UPLOAD_FOLDER, CONFIG_FILE)) or {}
    layout_file = cfg.get("layoutDB", DEFAULT_FILE)

    return send_from_directory(UPLOAD_FOLDER, layout_file)

# Route to serve the JSON file
@app.route("/routes-data")
def routes_data():
    json_path = os.path.join(app.root_path, "routes.json")
    with open(json_path) as f:
        data = json.load(f)
    return jsonify(data)

@app.route("/api/save", methods=["POST"])
def save_json():
    payload  = request.get_json() or {}
    filename = request.args.get("filename", DEFAULT_FILE)
    save_json_file(os.path.join(UPLOAD_FOLDER, filename), payload)
    return jsonify({"status":"saved","filename":filename})

@app.route("/api/load", methods=["GET"])
def load_json():
    filename = request.args.get("filename", DEFAULT_FILE)
    data     = load_json_file(os.path.join(UPLOAD_FOLDER, filename)) or empty_layout()
    return jsonify(data)

@app.route("/api/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"error":"no file provided"}), 400
    dest = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(dest)
    return jsonify({"status":"uploaded","filename":file.filename})

@app.route("/api/download", methods=["GET"])
def download():
    filename = request.args.get("filename", DEFAULT_FILE)
    path     = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        return jsonify({"error":"not found"}), 404
    return send_file(path, as_attachment=True)

# ---- Config.json API ----

@app.route("/api/config", methods=["GET"])
def get_config():
    cfg = load_json_file(os.path.join(UPLOAD_FOLDER, CONFIG_FILE)) or default_config()
    return jsonify(cfg)

@app.route("/api/config", methods=["POST"])
def save_config():
    cfg = request.get_json() or {}
    # minimal guard rails
    cfg.setdefault("network_ports", {})
    save_json_file(os.path.join(UPLOAD_FOLDER, CONFIG_FILE), cfg)
    return jsonify(cfg)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
