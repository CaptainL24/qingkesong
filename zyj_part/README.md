*脚本*

browser_photo_backup.py大概是一个比较全的流程，其它的代码主要是把这个脚本拆开了方便测试

browser_photo.py可以实现浏览器调起、拍照、AI 检测，并通过 `health_bridge.py` 把事件写入桌宠 JSONL

camera_ai.py可以实现接ai判断“班味重不重”

health_bridge.py负责把事件追加到 `~/.local/share/pawpause/health-events.jsonl`，供 wx_part 桌宠消费

ui_flow.py是旧的 Tkinter 弹窗 + recommendation.py 流程（browser_photo 已改走 JSONL）

test_ui_flow.py手动写入一条 `neck_guide` 事件，方便不测摄像头时验证桌宠对接

*网页*

网页在templates文件夹下面，index.html是初始界面（调摄像头），test是转移到小游戏的中间界面，game是游戏们


## Run the code

### 1.从头开始create browser, browser调用摄像头，自动调用camera_ai.py监控键盘
```bash
python browser_photo.py
```

### 2.跳过摄像头，直接测试 JSONL → 桌宠对接（需 wx_part 桌宠已在跑）
```bash
python test_ui_flow.py
```

### 3.环境变量（可选）
```bash
# 与 wx_part 共用，覆盖 JSONL 路径
export PAWPAUSE_HEALTH_EVENTS=/absolute/path/to/health-events.jsonl
```
