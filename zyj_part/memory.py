"""Persistent agent memory for banwei orchestration."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

DEFAULT_MEMORY_PATH = Path.home() / ".local" / "share" / "pawpause" / "agent-memory.json"

LEVEL_RANK = {"low": 0, "medium": 1, "high": 2}


def memory_path() -> Path:
    override = os.getenv("PAWPAUSE_AGENT_MEMORY", "").strip()
    if override:
        return Path(override).expanduser()
    return DEFAULT_MEMORY_PATH


def _today_key() -> str:
    return time.strftime("%Y-%m-%d", time.localtime())


def _empty_state() -> dict[str, Any]:
    return {
        "date": _today_key(),
        "analysis_count": 0,
        "banwei_check_count": 0,
        "last_banwei_level": None,
        "last_reminder_at": None,
        "neck_guide_count": 0,
        "exercise_done_today": False,
    }


def load() -> dict[str, Any]:
    path = memory_path()
    if not path.exists():
        return _empty_state()

    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_state()

    if state.get("date") != _today_key():
        return _empty_state()
    return {**_empty_state(), **state}


def save(state: dict[str, Any]) -> None:
    path = memory_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    state["date"] = _today_key()
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def reset() -> dict[str, Any]:
    state = _empty_state()
    save(state)
    return state


def level_rank(level: str | None) -> int:
    if not level:
        return -1
    return LEVEL_RANK.get(level, 1)


def record_analysis(state: dict[str, Any]) -> None:
    state["analysis_count"] = int(state.get("analysis_count", 0)) + 1


def record_banwei_reminder(state: dict[str, Any], level: str) -> None:
    state["banwei_check_count"] = int(state.get("banwei_check_count", 0)) + 1
    state["last_banwei_level"] = level
    state["last_reminder_at"] = int(time.time())


def record_neck_guide(state: dict[str, Any]) -> None:
    state["neck_guide_count"] = int(state.get("neck_guide_count", 0)) + 1
    state["banwei_check_count"] = int(state.get("banwei_check_count", 0)) + 1
    state["last_reminder_at"] = int(time.time())


def mark_exercise_done(state: dict[str, Any]) -> None:
    state["exercise_done_today"] = True


def can_remind_again(state: dict[str, Any], cooldown_seconds: int = 30 * 60) -> bool:
    last_at = state.get("last_reminder_at")
    if last_at is None:
        return True
    return int(time.time()) - int(last_at) >= cooldown_seconds
