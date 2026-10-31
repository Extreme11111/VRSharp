# 颈部偏移与头身碰撞（2026-10-23）

Player 新增两个 DefaultComponent，均挂在 Camera 下：

- Neck：局部位置默认 (-5, 0, -12) cm。蓝图组件面板可直接调节。身体水平跟随 Neck.WorldLocation，保留原来的水平投影、碰撞扫掠和 VROrigin 实际位移补偿。
- HeadCollision：球半径默认 15 cm，跟随 Camera，不独立模拟物理。BeginPlay 复制 BodyCapsule 的碰撞预设、ObjectType、CollisionEnabled 和所有通道响应。子组件不参与根组件移动扫掠，因此额外执行头部球体轨迹扫掠，命中时修正追踪原点。

CapsuleAdditionalHeight / CapsuleSubHeight 的名称、序列化和配置值均保留。前者继续控制头顶余量：球心在 Camera 局部 Z 的位置为 AdditionalHeight - 球半径（默认正好为零）。后者继续控制脚底相对追踪原点的升高差。速度的身高映射继续使用 Camera.RelativeLocation.Z + AdditionalHeight。

身体底部保持不变，改变半高时中心移动相同距离；VROrigin 使用新的半高做相反方向补偿。胶囊顶部半球与头部球体采用球心距离求切线，而不是简单减去半径：顶部 = 头球中心高度 - sqrt((身体半径 + 头球半径)^2 - 水平距离^2) + 身体半径。高度基于 VROrigin 局部空间计算。极端蹲伏受 UE 胶囊半高不得小于半径的限制；若人为把 Neck 移到两半径之和以外，头身已水平分离，无法维持相切。

验证：C# 编译通过，热重载成功；MCP PIE 调用实际 Player Tick，验证站立、俯仰 ±60 度、转向、蹲伏、SubHeight=12、AdditionalHeight=25。五组测试脚底和相机位移误差小于 0.00001 cm，头身切线误差小于 0.00001 cm。另用临时横梁验证头球从 X=10000 向 10080 移动时停在 X=10030（梁前表面 10045，头球半径 15）。临时测试物体已清理。

报告：Saved/Tests/Neck-Geometry-20261023.json。测试脚本：Tools/test_neck_geometry.py。未进行头显实机测试；HMD 渲染阶段的 late update 不在游戏线程扫掠测试范围内。

本轮之前的台阶移动修复尚未完成完整通行测试，本报告不代表该项已经验证完成。
