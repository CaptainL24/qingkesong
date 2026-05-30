from collections import deque
from flask import Flask, request, render_template, jsonify
from PIL import Image, UnidentifiedImageError
import base64
import io
import json
import os
import subprocess
import sys
import threading
import time
import webbrowser

from openai import OpenAI

try:
    from pynput import keyboard
except ImportError:
    keyboard = None

app = Flask(__name__)

AI_API_KEY = os.getenv("STEP_API_KEY", "")
AI_MODEL = os.getenv("STEP_MODEL", "step-3.7-flash")
AI_BASE_URL = os.getenv("STEP_BASE_URL", "https://api.stepfun.com/v1")

# =========================
# 弹窗
# =========================
def run_recommendation_script():
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recommendation.py")
    if not os.path.exists(script_path):
        print(f"recommendation script not found: {script_path}", flush=True)
        return
    subprocess.Popen([sys.executable, script_path])


def show_message(result: dict | None = None):
    result = result or {}
    mood = result.get("emotion_label", "一般")
    heavy = result.get("banwei_heavy", False)

    if heavy:
        title = "班味提醒"
        message = f"检测到你当前状态偏 {mood}，班味有点重，建议休息一下。"
        confirm_text = "确认后打开小游戏"
    else:
        title = "状态良好"
        message = f"检测到你当前状态偏 {mood}，看起来还不错，继续保持。"
        confirm_text = "确认"

    script = f'''
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

recommendation_script = os.environ.get("RECOMMENDATION_SCRIPT", "")

root = tk.Tk()
root.title({title!r})
root.geometry("420x220")
root.resizable(False, False)
root.attributes("-topmost", True)
root.configure(bg="#f7f9ff")

frame = ttk.Frame(root, padding=16)
frame.pack(fill="both", expand=True)

msg = ttk.Label(frame, text={message!r}, wraplength=360, justify="left")
msg.pack(anchor="w")

btns = ttk.Frame(frame)
btns.pack(side="bottom", fill="x", pady=(20, 0))


def on_ok():
    root.destroy()
    if {heavy!r} and recommendation_script:
        subprocess.Popen([sys.executable, recommendation_script])

ok_btn = ttk.Button(btns, text={confirm_text!r}, command=on_ok)
ok_btn.pack(side="right", padx=(8, 0))

cancel_btn = ttk.Button(btns, text="取消", command=root.destroy)
cancel_btn.pack(side="right")

root.mainloop()
'''
    env = os.environ.copy()
    env["RECOMMENDATION_SCRIPT"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recommendation.py")
    subprocess.Popen([sys.executable, "-c", script], env=env)


# =========================
# 判断逻辑
# =========================

def _image_to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image = image.convert("RGB")
    image.save(buffer, format="JPEG", quality=90)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def analyze_image_with_ai(image: Image.Image) -> dict:
    if not AI_API_KEY:
        raise RuntimeError("STEP_API_KEY is not set")

    client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)

    prompt = (
        "请分析图片中人物的工作状态，并输出严格 JSON。"
        "你只需要判断人物当前情绪/状态，不需要考虑环境是否为办公室，因为背景一定是工作场景。"
        "需要识别两个字段：emotion_label 和 banwei_heavy。"
        "emotion_label 只能是以下分类之一：轻松、一般、疲惫。"
        "判断规则："
        "1. 如果人物明显放松、精神状态好、眼神有神、姿态自然轻快，归类为‘轻松’。"
        "2. 如果人物状态中性、没有明显疲劳或放松特征，归类为‘一般’。"
        "3. 如果人物呈现持续工作后的状态，即使表情平静自然、没有明显痛苦或皱眉，"
        "但眼神略带倦意、精神发沉、动作/姿态显得消耗感较强、像久坐久盯屏幕后状态，"
        "也应归类为‘疲惫’。"
        "banwei_heavy 为布尔值，表示班味是否很重；如果人物呈现明显的打工感、倦怠感、机械感、被工作消耗的感觉，则为 true。"
        "同时给出 reason 简短说明，reason 要尽量直接说明你为什么判断为该标签，重点描述表情、眼神、姿态和疲劳感。"
        "只输出 JSON，不要输出多余文本。"
    )

    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": _image_to_data_url(image)}},
                ],
            }
        ],
    )
    content = response.choices[0].message.content or ""
    print("AI raw content:", repr(content), flush=True)
    content = content.strip()
    if content.startswith("```"):
        content = content.removeprefix("```json").removeprefix("```").strip()
        if content.endswith("```"):
            content = content[:-3].strip()
    result = json.loads(content)

    emotion_label = result.get("emotion_label", "一般")
    if emotion_label not in {"轻松", "一般", "疲惫"}:
        emotion_label = "一般"
    
    return {
        "emotion_label": emotion_label,
        "banwei_heavy": bool(result.get("banwei_heavy", False)),
        "emotion_label_candidates": result.get("emotion_label_candidates", ["轻松", "一般", "疲惫"]),
        "reason": result.get("reason", ""),
        "raw": result,
    }


def check_image(image: Image.Image):
    try:
        return analyze_image_with_ai(image)
    except Exception as exc:
        print(f"AI analysis failed: {exc}", flush=True)
        return {
            "emotion_label": "一般",
            "banwei_heavy": False,
            "emotion_label_candidates": ["轻松", "一般", "疲惫"],
            "reason": f"fallback due to error: {exc}",
            "raw": {},
        }


# 30 次滑动窗口，测试时按 1 秒采样 1 次
keyboard_history = deque(maxlen=30)
capture_requested = False
capture_lock = threading.Lock()
last_keyboard_event = 0.0


# =========================
# 键盘使用判断（还要加上飞书cli）
# =========================
def on_key_press(_key):
    global last_keyboard_event
    last_keyboard_event = time.time()


def start_keyboard_listener():
    if keyboard is None:
        print("pynput not installed; keyboard detection disabled", flush=True)
        return None

    listener = keyboard.Listener(on_press=on_key_press)
    listener.daemon = True
    listener.start()
    return listener


def is_keyboard_used_in_last_second() -> bool:
    return (time.time() - last_keyboard_event) <= 1.0  ##测试用


def should_capture_from_history() -> bool:
    # print(keyboard_history, flush=True)
    return sum(keyboard_history) > 5  ##测试用


# =========================
# Python 定时判断
# =========================
def judge_should_capture():
    global capture_requested
    while True:
        used = is_keyboard_used_in_last_second()
        with capture_lock:
            keyboard_history.append(used)
            if len(keyboard_history) == keyboard_history.maxlen:
                capture_requested = should_capture_from_history()
                print("used =", used, "history =", list(keyboard_history), "capture =", capture_requested, flush=True)
                keyboard_history.clear()
            else:
                # print("used =", used, "history =", list(keyboard_history), "capture =", capture_requested, flush=True)
                1
        time.sleep(1)


# =========================
# 前端轮询信号
# =========================
@app.route("/signal", methods=["GET"])
def signal():
    global capture_requested
    with capture_lock:
        should_capture = capture_requested
        capture_requested = False
    return jsonify({"capture": should_capture})


# =========================
# 接收前端图片
# =========================
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

    analysis = check_image(image)
    # image.save("./src/debug_upload.png")
    show_message(analysis)

    return jsonify({"ok": True})


# =========================
# 页面
# =========================
@app.route("/")
def index():
    return render_template("index.html")


# =========================
# 启动
# =========================
def open_browser():
    webbrowser.open("http://127.0.0.1:5001")


if __name__ == "__main__":
    start_keyboard_listener()
    print("start_keyboard_listener")
    threading.Thread(target=judge_should_capture, daemon=True).start()
    print(1111, flush=True)
    open_browser()
    print(2222, flush=True)
    app.run(debug=True, use_reloader=False, port=5001)  ## 可能需要把5001改成5000，魏姐的电脑5000一直被占用（）