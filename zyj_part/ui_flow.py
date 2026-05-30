import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk


def run_recommendation_script():
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recommendation.py")
    if not os.path.exists(script_path):
        print(f"recommendation script not found: {script_path}", flush=True)
        return
    subprocess.Popen([sys.executable, script_path])


def show_message(result: dict | None = None):
    result = result or {}
    mood = result.get("emotion_label", "一般")
    heavy = bool(result.get("banwei_heavy", False))

    if heavy:
        title = "班味提醒"
        message = f"检测到你当前状态偏 {mood}，班味有点重，建议休息一下。"
        confirm_text = "确认后打开小游戏"
    else:
        title = "状态良好"
        message = f"检测到你当前状态偏 {mood}，看起来还不错，继续保持。"
        confirm_text = "确认"

    root = tk.Tk()
    root.title(title)
    root.geometry("420x220")
    root.resizable(False, False)
    root.attributes("-topmost", True)
    root.configure(bg="#f7f9ff")

    frame = ttk.Frame(root, padding=16)
    frame.pack(fill="both", expand=True)

    msg = ttk.Label(frame, text=message, wraplength=360, justify="left")
    msg.pack(anchor="w")

    btns = ttk.Frame(frame)
    btns.pack(side="bottom", fill="x", pady=(20, 0))

    def on_ok():
        root.destroy()
        if heavy:
            run_recommendation_script()

    ok_btn = ttk.Button(btns, text=confirm_text, command=on_ok)
    ok_btn.pack(side="right", padx=(8, 0))

    cancel_btn = ttk.Button(btns, text="取消", command=root.destroy)
    cancel_btn.pack(side="right")

    root.mainloop()
