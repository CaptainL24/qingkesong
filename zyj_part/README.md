*脚本*

browser_photo_backup.py大概是一个比较全的流程，其它的代码主要是把这个脚本拆开了方便测试

browser_photo.py可以实现浏览器调起（但没有实现桌宠的动画/交互）&拍照&检测

camera_ai.py可以实现接ai判断“班味重不重”

ui_flow.py是后续调起recommendation.py（进入小游戏界面）

test_ui_flow.py是为了测试方便单独

*网页*

网页在templates文件夹下面，index.html是初始界面（调摄像头），test是转移到小游戏的中间界面，game是游戏们