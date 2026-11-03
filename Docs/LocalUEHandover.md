# UE交接：预设手指权重

分支 cloud/authored-finger-pose；UVRSharpHandPose新增UseFingerWeights、ThumbWeight、IndexWeight、GraspWeight。默认不开启，旧姿态仅对齐手掌且继续动态接触。开启时抓取选择到该HandPose后，三个0..1权重作为本次抓取的固定目标，沿原动画平滑生效；该模式明确暂停指尖动态接触修正，释放后恢复。配置在抓取开始采样，抓住期间编辑不会实时更新；扳机动态混合未实现。

UE5.7/UnrealSharp0.1完整生成Glue并编译。在/VRSharp/Maps/VRSharpDemo副本，给可抓Actor使用现有HandPose组件和Grabbable.GrabPoses名称映射；保留现有命名匹配规则。设置UseFingerWeights=true、权重(.2,.7,1)，抓取时观察三通道保持，碰撞接触不覆盖。释放后应张开；换抓无预设/未开启对象应恢复原动态接触。两手分别测试，检查默认旧资产和保存重开序列化。越界值被钳制，非有限值转0。

关联源码 Script/ManagedVRSharp/Core/VRSharpHandPose.cs、VRSharpHand.cs、VRSharpMathHelper.cs。数学测试仅覆盖归一化，不证明实际姿态、蓝图、碰撞或视觉正确。完整UE编译、PIE、头显均未执行；不自动合并。该模式需要作者有意选择，不与动态接触同时争夺手指目标。

- 2026-11-03：新增UseTriggerBlend与TriggerIndexWeight；在UseFingerWeights开启的抓握姿势中，SetGrabTrigger(value)把食指从基础IndexWeight混合至TriggerIndexWeight，0/1为端点、范围外钳制，非有限样本返回false并保持旧目标。释放后禁用；拇指/三指保持预设。该增量取代“扳机混合未实现”的历史描述。UE侧需将XR轴或PC滑条接入并在扳机松开时提交0，不自动修改旧TriggerAction。验收0/.5/1、反向端点、释放后拒绝、异常值保持、重新抓取回基础姿态。两个独立数学检查及新增混合边界检查在01e005c通过；完整UE/Glue编译、PIE和头显仍待验证，未合并。


# 非VR桌面交互测试Pawn
新增 AVRSharpDesktopTestPawn，分支cloud/desktop-test-pawn基于PR #6（必须先组合该姿势功能，不是独立main补丁）。C#实现自由飞行、鼠标视角、双手追踪目标、活动手切换、局部抓取/放下及抓握扳机；无HMD/XR查询或会话需求。自由飞行不模拟物理玩家通行，不用于台阶验收；完整桌面地图仍待以下UE接线。

1. UE5.7/UnrealSharp0.1编译并生成Glue；新建BP_DesktopTestPawn继承该类。Camera关闭Lock to HMD；LeftTarget相对坐标(45,-20,-15)，RightTarget(45,20,-15)，按现有手掌轴调旋转。
2. 在VRSharpDemo地图副本放置现有左右手蓝图实例，配置完整HandMesh/GrabSphere/Palm/物理参数，赋给Pawn.LeftHand/RightHand；Pawn AutoPossess Player0，GameMode不再生成VRSharpPlayer，避免两个驱动器同时驱动手。Pawn只调用InitializeHand，不绑定VR动作。
3. 创建IMC_DesktopTest和EnhancedInputActions：Move三轴W/S、A/D、E/Q，Triggered调用SetMoveInput，Completed/Canceled提交(0,0,0)；Look鼠标XY乘灵敏度调用Look（每次鼠标增量，不乘dt）；Tab切换SelectLeftHand。
4. HandMove三轴以I/K、L/J、U/O驱动SetHandMoveInput，Completed/Canceled归零。左鼠标Started调用GrabActiveHand、Completed/Canceled调用ReleaseActiveHand；右鼠标或滚轮模拟0..1调用SetTrigger，松开必须提交0。切换手时旧手保持已抓状态，仅旧扳机归零。
5. PlayerController BeginPlay添加IMC；输入模式GameOnly并捕获鼠标。失去焦点/暂停/移除映射时调用ResetDesktopInput；退出地图前左右手Release，清理外部手实例。当前未自动处理UnPossess/EndPlay。
6. 用带UseFingerWeights/UseTriggerBlend的对象验证抓取、放下、食指基础/按压姿势、切手后另一手继续保持。远物体不能吸取；两手同时持物及分别放下；无XR运行普通PIE；比较30/60/120Hz。目标位姿在相机局部空间，手自由移动不带碰撞限制，实际物体碰撞由原物理手负责。

待验证：完整UE编译、Pawn tick启用与摄像机视点、蓝图属性、全部输入接线、实际抓放和姿势。数学检查不编译DesktopPawn。MoveSpeed/HandSpeed当前为C#属性，蓝图需修改时通过C#子类设置，后续可改为反射配置。无原生资产修改。
