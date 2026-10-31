# 手指接触回弹（2026-10-23）

修改 VRSharpHand 和 VRSharpMathHelper：抓握时逐帧检测已抓物体的碰撞表面，使用 GetClosestPointOnCollision 获取指尖检测球心到表面的真实距离。小于 0.8R 时按深入程度逐步减小闭合权重；0.8R..R 时保持当前权重；大于 R 时继续累积闭合。目标权重限制 0..1，按 deltaSeconds 积分；碰撞体内部距离为零。拇指、食指分别反馈，中指/无名指/小指共用 GraspWeight，采用三者最深接触。

抓握姿势 Lerp 从旧的约 6/s 提高到 24/s，改成 1-exp(-speed*dt) 的指数混合，防止低帧率时插值系数直接饱和。空手原有响应保留约18/s。脱离表面会重新闭合，不再永久锁死在首次接触姿势。未配置的骨骼不检测；复杂碰撞不支持最近点查询时仍按重叠保持浅接触，避免使用无效接触点产生错误回弹。

验证：C# 编译、热重载成功。直接链接生产数学助手的闭环模型在30/60/90/120Hz、初始张开与闭合状态下均稳定于接触带，末秒持续振荡为零。MCP PIE 左右手实际抓取后调用生产 Tick，使用真实 thumb_socket 与 UE 碰撞距离，0.4R 接触使闭合权重从约1下降到0.7046；0.9R 接触保持；移开后恢复到0.9996。测试为控制表面相对指尖运动，在 PIE 中临时解绑手的物理附着并保留抓取状态；不是完整骨骼动画/头显视觉验证。

报告 Saved/Tests/FingerFeedback-20261023.json；运行检查 Tools/FingerContactChecks 与 Tools/test_finger_feedback.py。临时对象已清理，无需重启。源码备份 Saved/RepairBackup/FingerContact-20261023。
