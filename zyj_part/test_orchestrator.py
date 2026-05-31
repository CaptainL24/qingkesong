"""Test agent orchestrator without camera. Requires wx desk pet running for UI feedback."""

from __future__ import annotations

import health_bridge
import memory
import orchestrator


def run_case(label: str, analysis: dict) -> None:
    print(f"\n=== {label} ===", flush=True)
    result = orchestrator.run_with_analyzing(analysis)
    event = result.get("event")
    event_type = event.get("type") if event else None
    print(
        f"tool={result['tool']} reason={result['decision_reason']} event={event_type}",
        flush=True,
    )
    print(f"memory={result['memory']}", flush=True)


if __name__ == "__main__":
    memory.reset()
    print(f"memory file: {memory.memory_path()}", flush=True)
    print(f"events file: {health_bridge.events_path()}", flush=True)
    print("\n请确保桌宠已在运行 (./start.sh 或 pnpm dev)。", flush=True)

    run_case(
        "Case 1: 第一次检测（应 banwei_result）",
        {"emotion_label": "一般", "banwei_heavy": False, "reason": "测试-首次"},
    )
    run_case(
        "Case 2: 第二次且班味重（应 neck_guide）",
        {"emotion_label": "疲惫", "banwei_heavy": True, "reason": "测试-复检重"},
    )

    state = memory.load()
    memory.mark_exercise_done(state)
    memory.save(state)
    run_case(
        "Case 3: 已完成颈椎操后（应 noop）",
        {"emotion_label": "疲惫", "banwei_heavy": True, "reason": "测试-应静默"},
    )

    memory.reset()
    run_case(
        "Case 4: 重置后第一次 heavy 仍只温和提醒（应 banwei_result）",
        {"emotion_label": "疲惫", "banwei_heavy": True, "reason": "测试-首次heavy"},
    )

    print("\n完成。桌宠应依次出现：班味提醒 → 颈椎引导 → 静默 →（重置后）再次班味提醒。", flush=True)
