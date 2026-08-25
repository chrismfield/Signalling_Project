import os
import json
import shutil
from json import JSONDecodeError
from xml.etree import ElementTree
from flask import Flask, render_template, request, jsonify, send_file, Blueprint, Response, stream_with_context, send_from_directory
from werkzeug.utils import secure_filename
import sys, os, glob
import subprocess
import time

try:
    from serial.tools import list_ports
except Exception:
    list_ports = None



app = Flask(__name__)

# Cap any upload (layout JSON or track diagram) at 32 MB.
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

UPLOAD_FOLDER = os.path.abspath(".")
DEFAULT_FILE  = "default.json"
CONFIG_FILE   = "config.json"
MAPPING_FILE  = "function_to_coil_mapping.json"
SVG_FOLDER    = os.path.join(UPLOAD_FOLDER, "static", "images")
DEFAULT_SVG   = "WDSME Scheme_C.svg"
SVG_FILE      = "static/images/WDSME Scheme_C.svg"   # legacy constant, kept for compatibility

DEFAULT_BAUDRATE = 19200
# config.json values that must end up as ints, whatever the browser posted.
CONFIG_INT_FIELDS = ("axle_tolerance", "logging_level", "point_interlock_timeout", "baudrate")

# Per-entity keys the editor never shows and must never destroy. These are
# written by the diagram-authoring side, not the editor, so a round trip
# through the Add/Edit forms has to put them back.
PRESERVED_ENTITY_KEYS = ("coords",)

def get_layout_file():
    """Get the layout file from config.json, fallback to DEFAULT_FILE."""
    cfg = load_json_file(os.path.join(UPLOAD_FOLDER, CONFIG_FILE)) or {}
    return cfg.get("layoutDB", DEFAULT_FILE)

def get_svg_file():
    """Get the current track diagram filename from config.json, fallback to DEFAULT_SVG.

    Only ever a bare filename inside SVG_FOLDER - basename() stops a hand-edited
    config.json from reaching outside that directory.
    """
    cfg = load_json_file(os.path.join(UPLOAD_FOLDER, CONFIG_FILE)) or {}
    name = str(cfg.get("layoutSVG") or "").strip()
    return os.path.basename(name) or DEFAULT_SVG

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
        "baudrate": DEFAULT_BAUDRATE,
        "layoutDB": DEFAULT_FILE,
        "layoutSVG": DEFAULT_SVG,
        "network_ports": {"network_1": "", "network_2": ""},
        "logging_level": 20,
        "mqtt_broker_address": "127.0.0.1",
        "point_interlock_timeout": 5
    }

def coerce_config(cfg):
    """Force the numeric config fields to ints, leaving anything odd alone."""
    for key in CONFIG_INT_FIELDS:
        if cfg.get(key) not in (None, ""):
            try:
                cfg[key] = int(cfg[key])
            except (TypeError, ValueError):
                pass
    return cfg

def merge_config(incoming):
    """Overlay a posted config on top of what is already on disk.

    The editor only knows about the fields it renders, so writing its payload
    straight out would silently drop anything hand-added to config.json.
    Merging means an older browser tab can't wipe a setting it never saw.
    """
    cfg = load_json_file(os.path.join(UPLOAD_FOLDER, CONFIG_FILE)) or default_config()
    cfg.update(incoming or {})
    cfg.setdefault("network_ports", {})
    cfg.setdefault("baudrate", DEFAULT_BAUDRATE)
    return coerce_config(cfg)

def merge_preserved_fields(incoming, existing):
    """Put back the hidden per-entity keys (coords) the editor doesn't round-trip.

    Walks every entity type / ref in the posted layout and, where the record
    on disk carries a preserved key that the payload has dropped, restores it.
    Returns (payload, number_of_keys_restored).
    """
    restored = 0
    if not isinstance(incoming, dict) or not isinstance(existing, dict):
        return incoming, restored
    for entity_type, records in incoming.items():
        old_records = existing.get(entity_type)
        if not isinstance(records, dict) or not isinstance(old_records, dict):
            continue
        for ref, record in records.items():
            old = old_records.get(ref)
            if not isinstance(record, dict) or not isinstance(old, dict):
                continue
            for key in PRESERVED_ENTITY_KEYS:
                if key not in record and key in old:
                    record[key] = old[key]
                    restored += 1
    return incoming, restored

@app.route("/editor")
def editor():
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

@app.route("/SVG")
def svg():
    return render_template("SVG.html")

@app.route("/mqtt")
def mqtt_page():
    return render_template("mqtt.html", title="MQTT Errors")

# return whichever json file is specified by layoutDB in config.json
@app.route("/layout-json")
def layout_json():
    cfg = load_json_file(os.path.join(UPLOAD_FOLDER, CONFIG_FILE)) or {}
    layout_file = cfg.get("layoutDB", DEFAULT_FILE)

    return send_from_directory(UPLOAD_FOLDER, layout_file)

# Unchanged contract: returns the *path* of the current diagram as plain text,
# but now reads layoutSVG from config.json instead of the hard-coded constant.
@app.route("/layout-svg")
def layout_svg():
    return "static/images/" + get_svg_file()

# ---- Track diagram (SVG) API ----

@app.get("/api/svg")
def api_svg():
    """Serve a track diagram. Defaults to the one named by layoutSVG in config.json.

    ?filename=<name> serves a specific file (used by the editor's preview).
    """
    name = os.path.basename(request.args.get("filename") or get_svg_file())
    path = os.path.join(SVG_FOLDER, name)
    if not name.lower().endswith(".svg") or not os.path.exists(path):
        return jsonify({"error": "SVG not found", "filename": name}), 404
    resp = send_from_directory(SVG_FOLDER, name, mimetype="image/svg+xml")
    # The diagram changes when someone uploads a new one, so don't let it stick.
    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.get("/api/svg/list")
def api_svg_list():
    """List the .svg files available in static/images and say which one is current."""
    os.makedirs(SVG_FOLDER, exist_ok=True)
    files = sorted(f for f in os.listdir(SVG_FOLDER) if f.lower().endswith(".svg"))
    return jsonify({"files": files, "current": get_svg_file()})

@app.post("/api/svg/upload")
def api_svg_upload():
    """Upload a track diagram into static/images.

    Validates that the payload really is an SVG before it lands on disk, keeps a
    .bak of anything it replaces, and (unless ?setCurrent=0) points config.json's
    layoutSVG at the new file.
    """
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "no file provided"}), 400

    name = secure_filename(file.filename)   # spaces become underscores, no path separators
    if not name.lower().endswith(".svg"):
        return jsonify({"error": "file must have a .svg extension"}), 400

    data = file.read()
    if not data:
        return jsonify({"error": "file is empty"}), 400
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as e:
        return jsonify({"error": f"not valid XML: {e}"}), 400
    # ElementTree reports namespaced tags as "{http://www.w3.org/2000/svg}svg"
    if not root.tag.rsplit("}", 1)[-1].lower() == "svg":
        return jsonify({"error": "root element is not <svg>"}), 400

    os.makedirs(SVG_FOLDER, exist_ok=True)
    dest = os.path.join(SVG_FOLDER, name)
    replaced = os.path.exists(dest)
    if replaced:
        shutil.copy2(dest, dest + ".bak")
    with open(dest, "wb") as f:
        f.write(data)

    set_current = request.args.get("setCurrent", "1").lower() not in ("0", "false", "no")
    if set_current:
        cfg_path = os.path.join(UPLOAD_FOLDER, CONFIG_FILE)
        cfg = load_json_file(cfg_path) or default_config()
        cfg["layoutSVG"] = name
        save_json_file(cfg_path, cfg)

    return jsonify({
        "status": "uploaded",
        "filename": name,
        "bytes": len(data),
        "replaced": replaced,
        "current": set_current,
    })

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
    # basename() so a crafted ?filename= can't write outside UPLOAD_FOLDER
    filename = os.path.basename(request.args.get("filename") or get_layout_file())
    path     = os.path.join(UPLOAD_FOLDER, filename)

    restored = 0
    if filename == CONFIG_FILE:
        # The editor posts config.json here as well as to /api/config, so both
        # doors need the same merge or baudrate would come and go.
        payload = merge_config(payload)
    else:
        payload, restored = merge_preserved_fields(payload, load_json_file(path))

    if os.path.exists(path):
        shutil.copy2(path, path + ".bak")
    save_json_file(path, payload)
    return jsonify({"status":"saved","filename":filename,"preserved":restored})

@app.route("/api/load", methods=["GET"])
def load_json():
    filename = os.path.basename(request.args.get("filename") or get_layout_file())
    if filename == CONFIG_FILE:
        cfg = load_json_file(os.path.join(UPLOAD_FOLDER, CONFIG_FILE)) or default_config()
        cfg.setdefault("baudrate", DEFAULT_BAUDRATE)
        return jsonify(coerce_config(cfg))
    data = load_json_file(os.path.join(UPLOAD_FOLDER, filename)) or empty_layout()
    return jsonify(data)

@app.route("/api/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error":"no file provided"}), 400
    # file.filename is client-supplied: "../../etc/foo.json" would otherwise escape UPLOAD_FOLDER
    name = secure_filename(file.filename)
    if not name.lower().endswith(".json"):
        return jsonify({"error":"file must have a .json extension"}), 400
    dest = os.path.join(UPLOAD_FOLDER, name)
    file.save(dest)
    return jsonify({"status":"uploaded","filename":name})

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
    # An older config.json predates the baudrate setting; report the default
    # rather than leaving the editor with a blank field.
    cfg.setdefault("baudrate", DEFAULT_BAUDRATE)
    return jsonify(coerce_config(cfg))

@app.route("/api/config", methods=["POST"])
def save_config():
    cfg_path = os.path.join(UPLOAD_FOLDER, CONFIG_FILE)
    cfg = merge_config(request.get_json() or {})
    if os.path.exists(cfg_path):
        shutil.copy2(cfg_path, cfg_path + ".bak")
    save_json_file(cfg_path, cfg)
    return jsonify(cfg)

@app.post('/api/reboot')
def api_reboot():
    subprocess.Popen(['sudo', 'reboot'])
    return jsonify({'status':'ok'})

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8000)
