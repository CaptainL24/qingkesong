# PawPause Health Bridge

PawPause is the desktop entry point for the worker-pet prototype. External services own Feishu calendar checks, keyboard/mouse activity, camera capture, and banwei analysis. PawPause only consumes local JSONL events and turns them into pet states, bubbles, and the neck-exercise entry point.

## Event File

Default paths:

- macOS/Linux: `~/.local/share/pawpause/health-events.jsonl`
- macOS app-style fallback: `~/Library/Application Support/PawPause/health-events.jsonl`
- Windows fallback: `%APPDATA%/PawPause/health-events.jsonl`

Override path:

```sh
PAWPAUSE_HEALTH_EVENTS=/absolute/path/to/health-events.jsonl
```

## Event Schema

```json
{
  "id": "stable-event-id",
  "type": "meeting_start",
  "timestampMs": 1780110000000,
  "payload": {
    "banweiLevel": "low",
    "banweiScore": 72,
    "message": "班味有点上来了，活动一下颈椎吧。",
    "suggestedAction": "none"
  }
}
```

Supported `type` values:

- `meeting_start`: shrink the pet into a compact floating ball. Events received during meetings are silently ignored except `meeting_end`.
- `meeting_end`: restore the normal Dodong pet state.
- `work_active`: mark the user as actively working. No bubble is shown.
- `analyzing`: briefly show the analysis state.
- `banwei_result`: show a gentle low/medium/high banwei reminder. It does not open the exercise game.
- `neck_guide`: show the neck-stretch guide state and an action button that opens the exercise game.
- `exercise_done`: show a completion response and return to the default state.

Supported `payload` fields:

- `banweiLevel`: `low`, `medium`, or `high`.
- `banweiScore`: optional numeric score used only in reminder copy.
- `message`: optional user-facing bubble copy.
- `suggestedAction`: `none` or `exercise`. In v1, only `neck_guide` creates an exercise action.

## Quick Test

```sh
mkdir -p ~/.local/share/pawpause
printf '%s\n' '{"id":"demo-meeting-start","type":"meeting_start"}' >> ~/.local/share/pawpause/health-events.jsonl
printf '%s\n' '{"id":"demo-meeting-end","type":"meeting_end"}' >> ~/.local/share/pawpause/health-events.jsonl
printf '%s\n' '{"id":"demo-work","type":"work_active"}' >> ~/.local/share/pawpause/health-events.jsonl
printf '%s\n' '{"id":"demo-banwei","type":"banwei_result","payload":{"banweiLevel":"medium","banweiScore":72}}' >> ~/.local/share/pawpause/health-events.jsonl
printf '%s\n' '{"id":"demo-neck","type":"neck_guide","payload":{"message":"复检还是有班味，多栋开始带你活动颈椎了。","suggestedAction":"exercise"}}' >> ~/.local/share/pawpause/health-events.jsonl
```

The pet should react within a few seconds. Clicking the pet or the `neck_guide` bubble action opens the neck exercise window.

## Agent Integration (zyj_part)

When using the bundled Python agent (`zyj_part/orchestrator.py`), events are emitted in this order per capture:

1. `analyzing` — always first (`run_with_analyzing`)
2. Then one of:
   - `banwei_result` — first check of the day, or banwei level escalated after cooldown
   - `neck_guide` — recheck with `banwei_heavy: true` (not the first check)
   - _(no event)_ — `noop` when cooldown active or `exercise_done_today` in agent memory

Agent-side daily memory lives at `~/.local/share/pawpause/agent-memory.json` (override with `PAWPAUSE_AGENT_MEMORY`). See [zyj_part/README.md](../../../../zyj_part/README.md) for decision rules.

Recommended integration test (pet must be running):

```sh
cd zyj_part && source .venv/bin/activate && python test_orchestrator.py
```

## Pet-Side State Notes

- Events are tail-read every 5 seconds; duplicate `id` values are ignored.
- During `meeting_start`, all events except `meeting_end` are dropped.
- After temporary states (`analyzing`, `banwei_result`, etc.), the pet returns to `idle`, `working`, or `meetingCompact` depending on internal flags.
- Completing the neck exercise game updates `exerciseSessions` and `exerciseTotalScore` in the pet app; hover the pet to see today's totals.
- External `exercise_done` events are supported but the pet also shows completion feedback when the game finishes locally via IPC.
