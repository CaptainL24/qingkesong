"""Agent tools: wrap health_bridge actions."""

from __future__ import annotations

from typing import Any

import health_bridge

TOOL_NAMES = (
    "emit_analyzing",
    "emit_banwei_result",
    "emit_neck_guide",
    "noop",
)


def run_tool(name: str, **kwargs: Any) -> dict[str, Any] | None:
    if name == "noop":
        print("[tools] noop", flush=True)
        return None

    if name == "emit_analyzing":
        return health_bridge.emit_analyzing(kwargs.get("message", "多栋看一眼班味浓度。"))

    if name == "emit_banwei_result":
        return health_bridge.emit_banwei_result(
            kwargs.get("emotion_label", "一般"),
            banwei_heavy=bool(kwargs.get("banwei_heavy", False)),
            reason=str(kwargs.get("reason", "")),
        )

    if name == "emit_neck_guide":
        return health_bridge.emit_neck_guide(
            kwargs.get("emotion_label", "疲惫"),
            reason=str(kwargs.get("reason", "")),
        )

    raise ValueError(f"unknown tool: {name}")
