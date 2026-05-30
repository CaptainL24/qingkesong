"""Append health events for wx_part PawPause worker pet (health-events.jsonl)."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

DEFAULT_EVENTS_PATH = Path.home() / ".local" / "share" / "pawpause" / "health-events.jsonl"

EMOTION_TO_BANWEI_LEVEL = {
    "轻松": "low",
    "一般": "medium",
    "疲惫": "high",
}


def events_path() -> Path:
    override = os.getenv("PAWPAUSE_HEALTH_EVENTS", "").strip()
    if override:
        return Path(override).expanduser()
    return DEFAULT_EVENTS_PATH


def append_event(
    event_type: str,
    payload: dict[str, Any] | None = None,
    *,
    event_id: str | None = None,
    timestamp_ms: int | None = None,
) -> dict[str, Any]:
    path = events_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    event: dict[str, Any] = {
        "id": event_id or f"zyj-{event_type}-{uuid.uuid4().hex[:12]}",
        "type": event_type,
        "timestampMs": timestamp_ms if timestamp_ms is not None else int(time.time() * 1000),
    }
    if payload:
        event["payload"] = payload

    line = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")

    print(f"[health_bridge] wrote {event_type} -> {path}", flush=True)
    return event


def emit_analyzing(message: str = "多栋看一眼班味浓度。") -> dict[str, Any]:
    return append_event("analyzing", {"message": message})


def emit_banwei_result(
    emotion_label: str,
    *,
    banwei_heavy: bool = False,
    reason: str = "",
) -> dict[str, Any]:
    level = EMOTION_TO_BANWEI_LEVEL.get(emotion_label, "medium")
    if banwei_heavy and level == "low":
        level = "medium"

    if level == "high":
        message = "班味有点上来了，先伸个懒腰压一压。"
    elif level == "medium":
        message = "班味慢慢上来了，记得活动一下。"
    else:
        message = "状态还不错，继续保持。"

    if reason:
        message = f"{message}（{reason}）"

    return append_event(
        "banwei_result",
        {
            "banweiLevel": level,
            "message": message,
            "suggestedAction": "none",
        },
    )


def emit_neck_guide(
    emotion_label: str = "疲惫",
    *,
    reason: str = "",
) -> dict[str, Any]:
    message = f"检测到你当前状态偏 {emotion_label}，班味有点重，要来一段颈椎操吗？"
    if reason:
        message = f"{message}（{reason}）"

    return append_event(
        "neck_guide",
        {
            "message": message,
            "suggestedAction": "exercise",
        },
    )


def notify_analysis_result(result: dict[str, Any]) -> dict[str, Any]:
    """Map camera_ai analysis to wx_part health events."""
    mood = str(result.get("emotion_label", "一般"))
    heavy = bool(result.get("banwei_heavy", False))
    reason = str(result.get("reason", "")).strip()

    if heavy:
        return emit_neck_guide(mood, reason=reason)
    return emit_banwei_result(mood, banwei_heavy=False, reason=reason)
