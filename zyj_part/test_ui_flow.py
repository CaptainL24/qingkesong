import health_bridge
import memory
import orchestrator


if __name__ == "__main__":
    memory.reset()
    result = orchestrator.run_with_analyzing({
        "emotion_label": "疲惫",
        "banwei_heavy": True,
        "reason": "手动测试 JSONL 对接",
    })
    event = result.get("event")
    print(f"tool={result['tool']} reason={result['decision_reason']}", flush=True)
    if event:
        print(f"已写入事件: {event['type']} (id={event['id']})", flush=True)
    else:
        print("本轮未写入桌宠事件 (noop)", flush=True)
    print(f"events: {health_bridge.events_path()}", flush=True)
    print(f"memory: {memory.memory_path()}", flush=True)
