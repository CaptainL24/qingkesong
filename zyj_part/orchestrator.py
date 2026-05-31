"""Rule-based agent orchestrator: memory + tool selection."""

from __future__ import annotations

from typing import Any

import memory
import tools
from health_bridge import EMOTION_TO_BANWEI_LEVEL

REMINDER_COOLDOWN_SECONDS = 30 * 60


def _analysis_fields(analysis: dict[str, Any]) -> tuple[str, bool, str, str]:
    mood = str(analysis.get("emotion_label", "一般"))
    heavy = bool(analysis.get("banwei_heavy", False))
    reason = str(analysis.get("reason", "")).strip()
    level = EMOTION_TO_BANWEI_LEVEL.get(mood, "medium")
    return mood, heavy, reason, level


def decide_tool(state: dict[str, Any], analysis: dict[str, Any]) -> tuple[str, str]:
    mood, heavy, _reason, level = _analysis_fields(analysis)

    if state.get("exercise_done_today"):
        return "noop", "exercise_done_today"

    if int(state.get("banwei_check_count", 0)) == 0:
        return "emit_banwei_result", "first_check_gentle_reminder"

    if heavy:
        return "emit_neck_guide", "recheck_banwei_heavy"

    last_level = state.get("last_banwei_level")
    if last_level and memory.level_rank(level) > memory.level_rank(str(last_level)):
        if memory.can_remind_again(state, REMINDER_COOLDOWN_SECONDS):
            return "emit_banwei_result", "level_escalated"
        return "noop", "cooldown_after_escalation"

    if memory.can_remind_again(state, REMINDER_COOLDOWN_SECONDS):
        return "noop", "no_action_needed"

    return "noop", "cooldown"


def handle_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    state = memory.load()
    memory.record_analysis(state)

    mood, heavy, reason, level = _analysis_fields(analysis)
    tool_name, decision_reason = decide_tool(state, analysis)

    print(
        f"[orchestrator] tool={tool_name} reason={decision_reason} "
        f"mood={mood} heavy={heavy} level={level} checks={state.get('banwei_check_count', 0)}",
        flush=True,
    )

    event = None
    if tool_name == "emit_banwei_result":
        event = tools.run_tool(
            "emit_banwei_result",
            emotion_label=mood,
            banwei_heavy=False,
            reason=reason,
        )
        memory.record_banwei_reminder(state, level)
    elif tool_name == "emit_neck_guide":
        event = tools.run_tool(
            "emit_neck_guide",
            emotion_label=mood,
            reason=reason,
        )
        memory.record_neck_guide(state)
        state["last_banwei_level"] = level
    elif tool_name != "noop":
        event = tools.run_tool(tool_name, emotion_label=mood, reason=reason)

    memory.save(state)

    return {
        "tool": tool_name,
        "decision_reason": decision_reason,
        "event": event,
        "memory": state,
    }


def run_with_analyzing(analysis: dict[str, Any]) -> dict[str, Any]:
    tools.run_tool("emit_analyzing")
    return handle_analysis(analysis)
