import health_bridge


if __name__ == "__main__":
    health_bridge.emit_analyzing()
    event = health_bridge.notify_analysis_result({
        "emotion_label": "疲惫",
        "banwei_heavy": True,
        "reason": "手动测试 JSONL 对接",
    })
    print(f"已写入事件: {event['type']} (id={event['id']})", flush=True)
    print(f"文件路径: {health_bridge.events_path()}", flush=True)
