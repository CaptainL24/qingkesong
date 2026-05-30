from flask import Flask, request, render_template, jsonify
from PIL import Image, UnidentifiedImageError
import base64
import io
import threading
import webbrowser

import camera_ai
import health_bridge

app = Flask(__name__)


def process_captured_image(image: Image.Image) -> dict:
    health_bridge.emit_analyzing()
    analysis = camera_ai.check_image(image)
    event = health_bridge.notify_analysis_result(analysis)
    print(f"[browser_photo] analysis={analysis.get('emotion_label')} heavy={analysis.get('banwei_heavy')}", flush=True)
    return {"analysis": analysis, "event": event}


@app.route("/signal", methods=["GET"])
def signal():
    with camera_ai.capture_lock:
        should_capture = camera_ai.capture_requested
        camera_ai.capture_requested = False
    return jsonify({"capture": should_capture})


@app.route("/upload", methods=["POST"])
def upload():
    payload = request.get_json(silent=True) or {}
    data = payload.get("image")
    if not data:
        return jsonify({"ok": False, "error": "missing image"}), 400

    try:
        if "," in data:
            data = data.split(",", 1)[1]
        img_bytes = base64.b64decode(data)
        image = Image.open(io.BytesIO(img_bytes))
        image.load()
    except (ValueError, UnidentifiedImageError, IndexError, base64.binascii.Error) as e:
        return jsonify({"ok": False, "error": f"invalid image: {e}"}), 400

    result = process_captured_image(image)
    return jsonify({"ok": True, **result})


@app.route("/")
def index():
    return render_template("index.html")


def open_browser():
    webbrowser.open("http://127.0.0.1:5001")


if __name__ == "__main__":
    camera_ai.start_keyboard_listener()
    threading.Thread(target=camera_ai.judge_should_capture, daemon=True).start()
    open_browser()
    app.run(debug=True, use_reloader=False, port=5001)
