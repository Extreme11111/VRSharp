# UE交接：预设手指权重

分支 cloud/authored-finger-pose；UVRSharpHandPose新增UseFingerWeights、ThumbWeight、IndexWeight、GraspWeight。默认不开启，旧姿态仅对齐手掌且继续动态接触。开启时抓取选择到该HandPose后，三个0..1权重作为本次抓取的固定目标，沿原动画平滑生效；该模式明确暂停指尖动态接触修正，释放后恢复。配置在抓取开始采样，抓住期间编辑不会实时更新；扳机动态混合未实现。

UE5.7/UnrealSharp0.1完整生成Glue并编译。在/VRSharp/Maps/VRSharpDemo副本，给可抓Actor使用现有HandPose组件和Grabbable.GrabPoses名称映射；保留现有命名匹配规则。设置UseFingerWeights=true、权重(.2,.7,1)，抓取时观察三通道保持，碰撞接触不覆盖。释放后应张开；换抓无预设/未开启对象应恢复原动态接触。两手分别测试，检查默认旧资产和保存重开序列化。越界值被钳制，非有限值转0。

关联源码 Script/ManagedVRSharp/Core/VRSharpHandPose.cs、VRSharpHand.cs、VRSharpMathHelper.cs。数学测试仅覆盖归一化，不证明实际姿态、蓝图、碰撞或视觉正确。完整UE编译、PIE、头显均未执行；不自动合并。该模式需要作者有意选择，不与动态接触同时争夺手指目标。

- 2026-11-03：新增UseTriggerBlend与TriggerIndexWeight；在UseFingerWeights开启的抓握姿势中，SetGrabTrigger(value)把食指从基础IndexWeight混合至TriggerIndexWeight，0/1为端点、范围外钳制，非有限样本返回false并保持旧目标。释放后禁用；拇指/三指保持预设。该增量取代“扳机混合未实现”的历史描述。UE侧需将XR轴或PC滑条接入并在扳机松开时提交0，不自动修改旧TriggerAction。验收0/.5/1、反向端点、释放后拒绝、异常值保持、重新抓取回基础姿态。两个独立数学检查及新增混合边界检查在01e005c通过；完整UE/Glue编译、PIE和头显仍待验证，未合并。


- 2026-11-04 特殊姿势动画链路：HandPose新增AnimationKey和DisableLeftHand/DisableRightHand（默认允许）；名称候选同时经过手别筛选。成功登记抓取后手保存GetActiveGrabPose、触发C# GrabPoseEntered(hand,pose)；Release清空状态/归零扳机并触发GrabPoseExited。旧抓放事件保留。SetGrabTrigger现在对任何有效活动姿势提供0..1 GetGrabPoseTrigger；启用UseTriggerBlend时额外驱动原食指目标，未启用时可只驱动专用动画。

本地动画接线：手的AnimBP使用Get Owning Actor→Cast AVRSharpHand，Event Blueprint Update Animation读取GetActiveGrabPose，IsValid后读取AnimationKey；无有效姿势则空字符串并回默认动画。新增专用Grab状态：条件AnimationKey等于例如ToolGrip，进入/退出用0.1秒过渡。Hold内将同Skeleton的ToolIdleGrip/ToolPressedGrip两个Sequence Player接Blend(float)，Alpha取GetGrabPoseTrigger；或用1D BlendSpace，轴0..1。最终与默认手动画按HasActivePose选择；只需静态姿势时Sequence Player保持对应帧。专用动画图自行决定是否使用Thumb/Index/GraspWeight，避免同时由两套图覆盖同骨骼。

Actor上分别放置Pose_Left/Pose_Right，设相同AnimationKey、不同掌心变换和相应禁止手别；Grabbable.GrabPoses的名称映射保留已有匹配方式。C#订阅GrabPoseEntered/Exited可启动/停止自定义动画逻辑，结束播放时仍以GetActiveGrabPose状态为准，EndPlay退订，失效姿势引用先IsValid。

验收：两手选中各自抓点；成功进入一次；持续抓握读取同姿势和0/.5/1扳机；释放退出并清状态；再次抓不同姿势不沿用旧动画；禁用对应手的姿势不参与选择。手别无匹配时回默认抓取。完整UE编译、动画资产/图、PIE、头显及这些生命周期用例尚未执行。PR8需顺序同步最新PR6再使用这些新增查询。当前不是宣称完整特殊动画系统已实测完成。
