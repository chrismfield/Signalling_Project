import os
import json
from json import JSONDecodeError
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

UPLOAD_FOLDER = os.path.abspath(".")
DEFAULT_FILE    = "default.json"
MAPPING_FILE    = "function_to_coil_mapping.json"

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
    """Write JSON out with UTF‑8 encoding."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# Preload coil mapping if needed in future
coil_mapping = load_json_file(os.path.join(UPLOAD_FOLDER, MAPPING_FILE))

@app.route("/")
def index():
    # 1) Which server‐file are we editing?
    filename = request.args.get("file", DEFAULT_FILE)
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # 2) Load it safely
    data = load_json_file(filepath)
    # Ensure all entity keys exist
    for key in ["AxleCounters","Signals","Points","Sections","Plungers","Routes","Triggers"]:
        data.setdefault(key, {})

    # 3) List all JSON files in the folder for “Load from server”
    server_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(".json")]

    # 4) Define the tabs in desired order
    tabs = ["AxleCounters","Signals","Points","Sections","Plungers","Routes","Triggers"]

    return render_template(
        "index.html",
        data=data,
        tabs=tabs,
        server_files=server_files,
        current_file=filename
    )

@app.route("/api/add_axlecounter", methods=["POST"])
def add_axlecounter():
    """Add or update one AxleCounter entry in default.json."""
    content = request.get_json() or {}
    ref     = content.get("ref","").strip()
    if not ref:
        return jsonify({"error":"ref required"}), 400

    # Load or init the JSON
    filepath = os.path.join(UPLOAD_FOLDER, DEFAULT_FILE)
    data     = load_json_file(filepath)
    data.setdefault("AxleCounters", {})

    # Build the new/updated axle‐counter record
    ac_entry = {
        "ref": ref,
        "description": content.get("description",""),
        "address": int(content.get("address",0)),
        "mode": int(content.get("mode",0)),
        "board_index": int(content.get("board_index",0)),
        "upcount_reg": 13,
        "downcount_reg": 14,
        "normal_coil": 22,
        "reverse_coil": 23,
        "network": content.get("network","network_1"),
        "comms_status":"", "upcount":0, "downcount":0,
        "sessionupcount":0, "sessiondowncount":0,
        "instances": {}, "slave": None
    }

    data["AxleCounters"][ref] = ac_entry
    save_json_file(filepath, data)
    return jsonify({"status":"ok","ref":ref})

@app.route("/api/save", methods=["POST"])
def save_json():
    """Save full payload (all tabs) to a chosen filename."""
    payload  = request.get_json() or {}
    filename = request.args.get("filename", DEFAULT_FILE)
    save_json_file(os.path.join(UPLOAD_FOLDER, filename), payload)
    return jsonify({"status":"saved","filename":filename})

@app.route("/api/load", methods=["GET"])
def load_json():
    """Return JSON file contents to browser (not used by UI directly)."""
    filename = request.args.get("filename", DEFAULT_FILE)
    data     = load_json_file(os.path.join(UPLOAD_FOLDER, filename))
    return jsonify(data)

@app.route("/api/upload", methods=["POST"])
def upload():
    """Accept a local file upload and save it server‐side."""
    file = request.files.get("file")
    if not file:
        return jsonify({"error":"no file provided"}), 400
    dest = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(dest)
    return jsonify({"status":"uploaded","filename":file.filename})

@app.route("/api/download", methods=["GET"])
def download():
    """Send a JSON file for download."""
    filename = request.args.get("filename", DEFAULT_FILE)
    path     = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        return jsonify({"error":"not found"}), 404
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
