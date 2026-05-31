# 比格多栋打工人防久坐桌宠 MVP

这是基于 PawPause 改造的内部原型版桌宠，用于承接外部健康事件（班味分析 Agent、飞书日历等），并在桌面上用「比格多栋」风格小狗做低打扰提醒。

完整说明（状态机、统计、Agent 协作、测试命令）见项目内文档：

**[PawPause-dodong-worker-pet-merge-20260531/README_WORKER_PET.md](PawPause-dodong-worker-pet-merge-20260531/README_WORKER_PET.md)**

## 快速启动

```sh
cd PawPause-dodong-worker-pet-merge-20260531
corepack pnpm install
corepack pnpm dev
```

或与 zyj_part 一起在仓库根目录：

```sh
./start.sh
```

## 核心能力摘要

- 消费 `~/.local/share/pawpause/health-events.jsonl`，切换比格多栋状态（idle / 会议球 / 陪工 / 分析 / 班味 / 颈椎引导 / 完成）。
- 第一次班味温和提醒，复检班味重时引导颈椎操；点击桌宠或气泡打开 `game1_v2.html`。
- 悬停显示今日颈椎操次数与活力值；双击打开现场演示面板。
- zyj_part Agent 负责决策写哪些事件，详见 [../zyj_part/README.md](../zyj_part/README.md).
