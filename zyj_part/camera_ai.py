from collections import deque
import base64
import io
import json
import os
import threading
import time
from typing import Any

from PIL import Image
from openai import OpenAI

try:
    from pynput import keyboard
except ImportError:  # pragma: no cover
    keyboard = None

AI_API_KEY = os.getenv("STEP_API_KEY", "")
AI_MODEL = os.getenv("STEP_MODEL", "step-3.7-flash")
AI_BASE_URL = os.getenv("STEP_BASE_URL", "https://api.stepfun.com/v1")

keyboard_history = deque(maxlen=30)
capture_requested = False
capture_lock = threading.Lock()
last_keyboard_event = 0.0


def _image_to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image = image.convert("RGB")
    image.save(buffer, format="JPEG", quality=90)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def analyze_image_with_ai(image: Image.Image) -> dict[str, Any]:
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


def check_image(image: Image.Image) -> dict[str, Any]:
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
    return (time.time() - last_keyboard_event) <= 1.0


def should_capture_from_history() -> bool:
    return sum(keyboard_history) > 5


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
        time.sleep(1)
