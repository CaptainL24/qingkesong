# zyj_part — 班味感知与 Agent 决策链路

Python 侧负责：键盘活跃检测 → 浏览器拍照 → AI 班味分析 → **规则 Agent 决策** → 写入桌宠 JSONL 事件流。

桌宠 UI 在 `wx_part`，两端通过本地文件解耦，不直接 HTTP 通信。

## 模块一览

| 文件 | 职责 |
|------|------|
| `browser_photo.py` | **主入口**：Flask `:5001`，自动开浏览器调摄像头，接 orchestrator |
| `camera_ai.py` | 键盘监听（pynput）+ StepFun 视觉 API，输出 `emotion_label` / `banwei_heavy` |
| `orchestrator.py` | **规则 Agent**：读 memory → 选 tool → 写事件 |
| `memory.py` | 当日 Agent 状态持久化（检测次数、冷却、是否已做操等） |
| `tools.py` | 工具层，封装 `health_bridge` 的 emit 动作 |
| `health_bridge.py` | 追加 JSONL 到 `health-events.jsonl` |
| `test_orchestrator.py` | 跳过摄像头，跑完整 Agent 决策用例（推荐联调） |
| `test_ui_flow.py` | 单次手动触发 orchestrator（快速冒烟） |
| `ui_flow.py` | 旧 Tkinter 弹窗流程（已废弃，现走 JSONL） |
| `browser_photo_backup.py` | 早期完整流程备份 |
| `templates/` | 浏览器页：`index.html` 调摄像头并轮询 `/signal` |

## 端到端数据流

```text
键盘活跃 (camera_ai)
    → 前端轮询 GET /signal，capture=true 时拍照
    → POST /upload（base64 图片）
    → camera_ai.check_image()（StepFun 视觉 API）
    → orchestrator.run_with_analyzing()
        1. tools.emit_analyzing  → JSONL type=analyzing
        2. decide_tool + 写 banwei_result / neck_guide / noop
    → health_bridge.append_event()
    → ~/.local/share/pawpause/health-events.jsonl
    → wx_part 桌宠消费并切换状态
```

## Agent 决策逻辑（orchestrator）

AI 分析结果字段：

| 字段 | 说明 |
|------|------|
| `emotion_label` | `轻松` / `一般` / `疲惫` |
| `banwei_heavy` | 班味是否很重（bool） |
| `reason` | AI 判断理由（会拼进桌宠文案） |

情绪 → 班味档位映射（`health_bridge.EMOTION_TO_BANWEI_LEVEL`）：

| emotion_label | banweiLevel |
|---------------|-------------|
| 轻松 | low |
| 一般 | medium |
| 疲惫 | high |

`decide_tool()` 规则（按优先级）：

1. **今日已完成颈椎操**（`memory.exercise_done_today`）→ `noop`
2. **第一次检测**（`banwei_check_count == 0`）→ `emit_banwei_result`（温和提醒，不引导游戏）
3. **复检且 `banwei_heavy == true`** → `emit_neck_guide`（引导颈椎操）
4. **班味档位升高**（如 medium → high）且冷却结束 → `emit_banwei_result`
5. 其它情况 → `noop`（默认 **30 分钟**冷却，`REMINDER_COOLDOWN_SECONDS`）

可用工具（`tools.py`）：

| tool | 写入事件 | 桌宠效果 |
|------|----------|----------|
| `emit_analyzing` | `analyzing` | 短暂「分析中」状态 |
| `emit_banwei_result` | `banwei_result` | 低/中/高班味提醒 |
| `emit_neck_guide` | `neck_guide` | 颈椎引导 + 可开小游戏 |
| `noop` | 无 | 静默 |

## Agent 记忆（memory）

默认路径：

```text
~/.local/share/pawpause/agent-memory.json
```

环境变量覆盖：

```bash
export PAWPAUSE_AGENT_MEMORY=/absolute/path/to/agent-memory.json
```

当日状态字段（跨天自动清零）：

| 字段 | 说明 |
|------|------|
| `date` | 当天日期 `YYYY-MM-DD` |
| `analysis_count` | 累计 AI 分析次数 |
| `banwei_check_count` | 已发出班味/引导类提醒次数 |
| `last_banwei_level` | 上次提醒档位 `low` / `medium` / `high` |
| `last_reminder_at` | 上次提醒 Unix 时间戳（冷却用） |
| `neck_guide_count` | 颈椎引导次数 |
| `exercise_done_today` | 今日是否已完成颈椎操（为 true 后 Agent 静默） |

> 说明：`exercise_done_today` 目前由 Agent 侧 memory 维护，桌宠完成小游戏后会更新 **wx 侧** 的 `exerciseSessions` / `exerciseTotalScore`，但尚未自动回写 Agent memory。联调时可手动 `memory.mark_exercise_done()`，或跑 `test_orchestrator.py` Case 3。

## 本地事件流（health_bridge）

默认路径（与 wx_part 共用）：

```text
~/.local/share/pawpause/health-events.jsonl
```

```bash
export PAWPAUSE_HEALTH_EVENTS=/absolute/path/to/health-events.jsonl
```

事件格式示例：

```json
{
  "id": "zyj-banwei_result-abc123",
  "type": "banwei_result",
  "timestampMs": 1780110000000,
  "payload": {
    "banweiLevel": "medium",
    "message": "班味慢慢上来了，记得活动一下。（眼神略倦）",
    "suggestedAction": "none"
  }
}
```

## 运行方式

### 1. 完整链路（摄像头 + 键盘 + Agent）

需先启动桌宠（`wx_part` 或 `./start.sh`），再：

```bash
cd zyj_part
source .venv/bin/activate
export STEP_API_KEY="你的密钥"
python browser_photo.py
```

浏览器会自动打开 `http://127.0.0.1:5001`，授权摄像头后等待键盘活跃触发拍照。

### 2. Agent 决策联调（推荐，跳过摄像头）

桌宠需在运行中。会依次写入 analyzing → banwei_result → neck_guide 等事件：

```bash
python test_orchestrator.py
```

用例覆盖：首次温和提醒 → 复检班味重引导 → 做完操后静默 → 重置后再测。

### 3. 单次冒烟

```bash
python test_ui_flow.py
```

重置 memory 后模拟一次「疲惫 + 班味重」分析，验证 JSONL 写入。

### 4. 环境变量

```bash
export STEP_API_KEY="..."                          # StepFun API（必填）
export STEP_MODEL=step-3.7-flash                   # 可选，默认 step-3.7-flash
export STEP_BASE_URL=https://api.stepfun.com/v1    # 可选
export PAWPAUSE_HEALTH_EVENTS=...                  # JSONL 路径
export PAWPAUSE_AGENT_MEMORY=...                   # Agent memory 路径
```

## 网页模板

`templates/index.html`：打开摄像头，每 5 秒轮询 `GET /signal`；后端 `capture=true` 时拍照并 `POST /upload`。

`templates/game1.html` / `game2.html`：早期小游戏页；正式颈椎操在 wx_part 的 `game1_v2.html`。
