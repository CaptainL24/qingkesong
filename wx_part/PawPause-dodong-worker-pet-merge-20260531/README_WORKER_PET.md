# 比格多栋打工人防久坐桌宠 MVP

这是基于 PawPause 改造的内部原型版桌宠，用于承接外部健康事件（班味分析 Agent、飞书日历等），并在桌面上用「比格多栋」风格小狗做低打扰提醒。

![比格多栋状态预览](assets/dodong-states/preview-contact-sheet.png)

## 现在能做什么

- 默认显示小号比格多栋桌宠，约 70% 尺寸（`WORKER_PET_MODE`，`petScale = 0.7`）。
- 消费本地 JSONL 事件流，按类型切换宠物状态与气泡文案。
- 会议中缩成豆包式悬浮球，会议期间静默丢弃其它提醒。
- 第一次班味检测只弹温和提醒；复检班味仍重时进入颈椎引导。
- 点击桌宠或气泡按钮，打开颈椎小游戏（MediaPipe 八拍版 `game1_v2.html`）。
- 完成小游戏后展示反馈，并累计**今日颈椎操次数**与**活力值**。
- 鼠标悬停桌宠显示今日统计气泡（次数 / 活力）。
- 双击桌宠打开现场演示面板，可一键切换各状态（嘉宾演示用）。
- 不展示照片，只展示班味结论和建议。

## 运行方式

```sh
corepack pnpm install
corepack pnpm dev
```

Electron 桌宠会浮在桌面上。颈椎小游戏会在点击桌宠、气泡按钮或托盘菜单时打开；开发模式下也可直接访问：

```text
http://localhost:5173/game1_v2.html
```

生产构建检查：

```sh
corepack pnpm typecheck
corepack pnpm build
```

与 zyj_part 联调时，建议仓库根目录 `./start.sh` 一键启动两端。

## 本地事件流

桌宠不直接接飞书、键鼠或摄像头。外部链路（如 zyj_part Agent）只需要把 JSONL 事件追加到本地文件：

```text
~/.local/share/pawpause/health-events.jsonl
```

环境变量覆盖：

```sh
PAWPAUSE_HEALTH_EVENTS=/absolute/path/to/health-events.jsonl
```

主进程每 **5 秒** tail 增量行（`HEALTH_BRIDGE_CHECK_INTERVAL_MS`），按 `id` 去重，超过 10 分钟的事件丢弃。

### 事件格式

```json
{
  "id": "stable-event-id",
  "type": "banwei_result",
  "timestampMs": 1780110000000,
  "payload": {
    "banweiLevel": "medium",
    "banweiScore": 72,
    "message": "班味有点上来了，先伸个懒腰压一压。",
    "suggestedAction": "none"
  }
}
```

### 支持的 `type` 与桌宠行为

| type | 宠物状态 (`PetState`) | 行为 |
|------|----------------------|------|
| `meeting_start` | `meetingCompact` | 缩成悬浮球，静默 |
| `meeting_end` | `idle` / `working` | 恢复普通或陪工态 |
| `work_active` | `working` | 认真工作，不弹气泡 |
| `analyzing` | `analyzing` | 短暂「分析中」，自动回到上一基态 |
| `banwei_result` | `banweiLow` / `banweiMedium` / `banweiHigh` | 班味提醒，不强制开游戏 |
| `neck_guide` | `neckGuide` | 颈椎引导，气泡按钮可开小游戏 |
| `exercise_done` | `exerciseDone` | 完成反馈后回默认态 |

会议中（`meetingCompactActive`）除 `meeting_end` 外的事件一律丢弃。

### 状态恢复规则

内部维护两个持久标志：

- `meetingCompactActive`：会议悬浮球模式
- `workerActivityActive`：陪工模式（`work_active` 触发）

临时状态（分析中、班味、完成反馈等）结束后，`healthReturnState()` 决定回到：

- 会议中 → `meetingCompact`
- 陪工中 → `working`
- 否则 → `idle`

对应 PNG 素材见 `assets/dodong-states/transparent/` 与 `src/renderer/src/dodong-states/`。

## 桌宠侧状态维护

### 今日统计（electron-store）

小游戏完成时（`exercise:complete` IPC），更新：

| 字段 | 说明 |
|------|------|
| `stats.exerciseSessions` | 今日颈椎操局数 |
| `stats.exerciseTotalScore` | 今日累计活力值 |

设置页可查看历史；悬停桌宠时以绿色气泡展示（`PetView` → `.pet-hover-stats`）。

### 窗口尺寸

显示 speech bubble、悬停统计或演示面板时，主进程会扩展透明窗口高度（`needsExpandedPetWindow()`），避免气泡上半部分被裁切。

### Worker Pet 模式关闭的能力

`WORKER_PET_MODE = true` 时关闭：喝水提醒、专注模式、分心检测、自定义提醒、AI agent 监控等 PawPause 原版主动逻辑，桌宠仅响应外部 health 事件与用户交互。

## 与 zyj_part Agent 的协作

zyj_part 的 `orchestrator` 负责「何时提醒、提醒什么」；桌宠只负责展示。典型链路：

```text
首次检测 → analyzing + banwei_result（温和）
复检班味重 → analyzing + neck_guide（引导做操）
今日已做操 / 冷却中 → analyzing + noop（桌宠无新变化）
```

Agent 当日记忆在 `~/.local/share/pawpause/agent-memory.json`，详见 [zyj_part/README.md](../../zyj_part/README.md)。

## 快速测试

```sh
mkdir -p ~/.local/share/pawpause
```

会议悬浮球：

```sh
printf '%s\n' '{"id":"demo-meeting-start","type":"meeting_start"}' >> ~/.local/share/pawpause/health-events.jsonl
printf '%s\n' '{"id":"demo-meeting-end","type":"meeting_end"}' >> ~/.local/share/pawpause/health-events.jsonl
```

第一次班味提醒：

```sh
printf '%s\n' '{"id":"demo-banwei-medium","type":"banwei_result","payload":{"banweiLevel":"medium","banweiScore":72,"message":"班味有点上来了，先伸个懒腰压一压。"}}' >> ~/.local/share/pawpause/health-events.jsonl
```

颈椎引导：

```sh
printf '%s\n' '{"id":"demo-neck-guide","type":"neck_guide","payload":{"message":"多栋先动了，你随意，真的随意。","suggestedAction":"exercise"}}' >> ~/.local/share/pawpause/health-events.jsonl
```

注意：`id` 会去重，重复测试请换新 `id`。

**推荐**：在桌宠运行时用 zyj_part 的 `python test_orchestrator.py` 跑完整 Agent 用例。

### 现场演示（双击桌宠）

- **单击**桌宠：打开颈椎小游戏
- **双击**桌宠：展开状态演示面板
- **悬停**桌宠：今日颈椎操次数 / 活力值
- 面板按钮：直接触发对应状态，适合嘉宾快速展示

## 默认文案口吻

外部事件不传 `payload.message` 时，桌宠使用内置随机文案（含动态班味分数）。

低班味示例：`班味 28 分刚冒头，伸个懒腰还能救。`

中班味示例：`班味 67 分，工位封印开始生效了。`

高班味示例：`班味 91 分。你快和工位合体了。`

颈椎引导示例：`多栋先动了，你随意，真的随意。`

## 比格狗 UI 素材

透明底 PNG：

```text
assets/dodong-states/transparent/
```

含 `idle`、`meeting-compact`、`working`、`analyzing`、`banwei-low/medium/high`、`neck-guide`、`exercise-done`。

原始绿幕图：`assets/dodong-states/raw/`

Prompt 记录：`docs/DODONG_STATE_PROMPTS.md`

## 研发合并提示

- 主入口：Electron + React + Vite（`src/main/main.ts` + `src/renderer/`）。
- 默认宠物 `dodong`，强制小尺寸 `0.7`。
- Health bridge 逻辑在 `main.ts` 约 3520–3900 行；UI 在 `PetView.tsx`。
- PNG 状态图与 CSS 原型小狗并存，PNG 可作为后续 spritesheet 资产基础。
- 商用前需确认「比格多栋」IP 授权，或替换为原创形象。

## 相关文档

- 仓库总览：[../../README.md](../../README.md)
- Agent 决策：[../../zyj_part/README.md](../../zyj_part/README.md)
- Health Bridge 协议：[docs/HEALTH_BRIDGE.md](docs/HEALTH_BRIDGE.md)
