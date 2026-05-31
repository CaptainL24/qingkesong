import health_bridge
import memory
import orchestrator


def _seed_after_first_check() -> None:
    """模拟已完成首次班味提醒，下一轮复检且班味重时走颈椎引导。"""
    state = memory.load()
    memory.record_banwei_reminder(state, "high")
    memory.save(state)


if __name__ == "__main__":
    memory.reset()
    _seed_after_first_check()
    result = orchestrator.run_with_analyzing({
        "emotion_label": "疲惫",
        "banwei_heavy": True,
        "reason": "",
    })
    event = result.get("event")
    print(f"tool={result['tool']} reason={result['decision_reason']}", flush=True)
    if event:
        print(f"已写入事件: {event['type']} (id={event['id']})", flush=True)
    else:
        print("本轮未写入桌宠事件 (noop)", flush=True)
    print(f"events: {health_bridge.events_path()}", flush=True)
    print(f"memory: {memory.memory_path()}", flush=True)
