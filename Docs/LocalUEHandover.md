# UE交接：预设手指权重

分支 cloud/authored-finger-pose；UVRSharpHandPose新增UseFingerWeights、ThumbWeight、IndexWeight、GraspWeight。默认不开启，旧姿态仅对齐手掌且继续动态接触。开启时抓取选择到该HandPose后，三个0..1权重作为本次抓取的固定目标，沿原动画平滑生效；该模式明确暂停指尖动态接触修正，释放后恢复。配置在抓取开始采样，抓住期间编辑不会实时更新；扳机动态混合未实现。

UE5.7/UnrealSharp0.1完整生成Glue并编译。在/VRSharp/Maps/VRSharpDemo副本，给可抓Actor使用现有HandPose组件和Grabbable.GrabPoses名称映射；保留现有命名匹配规则。设置UseFingerWeights=true、权重(.2,.7,1)，抓取时观察三通道保持，碰撞接触不覆盖。释放后应张开；换抓无预设/未开启对象应恢复原动态接触。两手分别测试，检查默认旧资产和保存重开序列化。越界值被钳制，非有限值转0。

关联源码 Script/ManagedVRSharp/Core/VRSharpHandPose.cs、VRSharpHand.cs、VRSharpMathHelper.cs。数学测试仅覆盖归一化，不证明实际姿态、蓝图、碰撞或视觉正确。完整UE编译、PIE、头显均未执行；不自动合并。该模式需要作者有意选择，不与动态接触同时争夺手指目标。

- 2026-11-03：新增UseTriggerBlend与TriggerIndexWeight；在UseFingerWeights开启的抓握姿势中，SetGrabTrigger(value)把食指从基础IndexWeight混合至TriggerIndexWeight，0/1为端点、范围外钳制，非有限样本返回false并保持旧目标。释放后禁用；拇指/三指保持预设。该增量取代“扳机混合未实现”的历史描述。UE侧需将XR轴或PC滑条接入并在扳机松开时提交0，不自动修改旧TriggerAction。验收0/.5/1、反向端点、释放后拒绝、异常值保持、重新抓取回基础姿态。两个独立数学检查及新增混合边界检查在01e005c通过；完整UE/Glue编译、PIE和头显仍待验证，未合并。
