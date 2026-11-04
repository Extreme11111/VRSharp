# 组合测试版本（2026-11-04）

cloud/desktop-test-pawn 现同时包含桌面输入/双手抓放、特殊姿势动画查询与生命周期、Grabbable事件和状态API。下方保留各功能详细步骤；统一从本分支生成Glue并编译。桌面测试Actor订阅物体Grabbed/Released，记录Hand、Component、IsGrabbed与当前姿势，执行左右手抓取→扳机→切手→松键→ReleaseAll的组合验收。PR3/4及其他未同步分支不在此组合中。UE编译、PIE、动画资产验证仍待执行。

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

- 2026-11-04 桌面输入链路：Pawn新增六个可编辑动作引用DesktopMove/DesktopLook/DesktopHandMove/DesktopGrip/DesktopSwitchHand/DesktopTrigger；C# BindDesktopInput在EnhancedInputComponent可用后自动绑定一次，动作未全部赋值时不做部分绑定，重复调用同组件不重复注册。Move/Look/HandMove/Trigger使用Axis3D（Trigger取X、Look取XY），Grip/Switch使用Bool。Completed/Canceled显式归零移动/手移动/扳机并释放活动手。请在BP详情赋六个动作、PlayerController添加IMC，移除旧的手动动作事件→Pawn方法接线以免重复执行；不用再逐个蓝图连接事件。映射方向与前述键位一致，鼠标灵敏度放在输入Modifier。失焦/取消映射仍调用ResetDesktopInput。UE验收需测试开始/持续/Completed/Canceled、迟到的InputComponent、重复Bind调用、不完整配置、切换手与左右手抓放。数学检查不能证明绑定签名、source-generator或引擎事件路由，完整UE编译/PIE仍待执行。

- 2026-11-04 桌面抓握输入所有权：Grip Started成功时保存响应手和被抓对象，Completed/Canceled释放该次输入对应的手/对象，不随当前活动手切换；失败按下不登记，重复开始/结束幂等，已换抓其他对象时不误放。ResetDesktopInput也终止该次输入抓握（更新此前仅清轴值的说明）。显式ReleaseActiveHand仍作用于当前活动手。UE验收：左手按下→Tab切右手→松键仅放左手；右手已持物时不能被失败点击或旧按键释放；失焦Reset释放输入持有者、保留其他独立抓握。新增生产方法子集回归使用手/物体替身，不含UE事件路由/原生生命周期；完整UE编译、PIE仍待执行。

- 2026-11-04 特殊姿势动画链路：HandPose新增AnimationKey和DisableLeftHand/DisableRightHand（默认允许）；名称候选同时经过手别筛选。成功登记抓取后手保存GetActiveGrabPose、触发C# GrabPoseEntered(hand,pose)；Release清空状态/归零扳机并触发GrabPoseExited。旧抓放事件保留。SetGrabTrigger现在对任何有效活动姿势提供0..1 GetGrabPoseTrigger；启用UseTriggerBlend时额外驱动原食指目标，未启用时可只驱动专用动画。

本地动画接线：手的AnimBP使用Get Owning Actor→Cast AVRSharpHand，Event Blueprint Update Animation读取GetActiveGrabPose，IsValid后读取AnimationKey；无有效姿势则空字符串并回默认动画。新增专用Grab状态：条件AnimationKey等于例如ToolGrip，进入/退出用0.1秒过渡。Hold内将同Skeleton的ToolIdleGrip/ToolPressedGrip两个Sequence Player接Blend(float)，Alpha取GetGrabPoseTrigger；或用1D BlendSpace，轴0..1。最终与默认手动画按HasActivePose选择；只需静态姿势时Sequence Player保持对应帧。专用动画图自行决定是否使用Thumb/Index/GraspWeight，避免同时由两套图覆盖同骨骼。

Actor上分别放置Pose_Left/Pose_Right，设相同AnimationKey、不同掌心变换和相应禁止手别；Grabbable.GrabPoses的名称映射保留已有匹配方式。C#订阅GrabPoseEntered/Exited可启动/停止自定义动画逻辑，结束播放时仍以GetActiveGrabPose状态为准，EndPlay退订，失效姿势引用先IsValid。

验收：两手选中各自抓点；成功进入一次；持续抓握读取同姿势和0/.5/1扳机；释放退出并清状态；再次抓不同姿势不沿用旧动画；禁用对应手的姿势不参与选择。手别无匹配时回默认抓取。完整UE编译、动画资产/图、PIE、头显及这些生命周期用例尚未执行。PR8需顺序同步最新PR6再使用这些新增查询。当前不是宣称完整特殊动画系统已实测完成。

# 抓放事件与状态 API 交接

分支 cloud/grab-events-state；UVRSharpGrabbable新增只读IsGrabbed、GrabCount，GetIsGrabbed/GetGrabCount蓝图查询，IsHeldBy/GetHeldComponent/GetGrabbingHands（快照）；TryGrabWith/ReleaseFrom/ReleaseAll提供C#调用入口。TryGrabWith仍遵守手附近的局部抓取检测，不是远距离强制吸取。

C#使用示例：
```csharp
grabbable.Grabbed += HandleGrabbed;
grabbable.Released += HandleReleased;
// 在EndPlay对应 -=，不要用无法解除的临时lambda。
void HandleGrabbed(AVRSharpHand hand, UVRSharpGrabbable item, UPrimitiveComponent component)
{
    // 此时item.IsGrabbed为true，登记状态已更新。
}
void HandleReleased(AVRSharpHand hand, UVRSharpGrabbable item, UPrimitiveComponent component)
{
    // hand已从登记移除；双手只放开一只时item仍可IsGrabbed。
}
// if (grabbable.TryGrabWith(hand)) ...
// grabbable.ReleaseFrom(hand); grabbable.ReleaseAll();
```

新事件为C#事件，不是蓝图动态委托；旧OnBefore/OnAfter事件和签名保留。Grabbed在Attach成功并完成登记后触发；Released在Detach和LIFO重附着完成后触发。不是动画完成事件，早于手侧旧OnAfter事件。相同手/组件重复Attach不重复发送，未登记Detach不发送。订阅者可读状态；不要从事件同步递归修改同一次抓握，复杂变更排至下一帧。异常按普通C#事件传播，未实现异常隔离。生命周期销毁清理未完成，不承诺销毁自动发Released。

本地UE5.7/UnrealSharp0.1完整编译并生成Glue。使用/VRSharp/Maps/VRSharpDemo测试副本，添加C#监听器，记录手/物/组件和事件时的状态；分别测试单手抓放、双手依次释放、重复Attach/Detach、原生Attach失败、近距离TryGrabWith成功与远距离失败、ReleaseAll回调期间持有者列表变化。首次抓取仅1次Grabbed，单手释放仅1次Released，失败动作不发送成功事件。核对AttachToComponent返回值绑定。蓝图仅查询状态，若需可绑定蓝图事件需后续动态委托适配。

完整UE编译、PIE、头显和上述事件回归均待执行。独立数学检查不覆盖这些原生调用。非VR控制器与特殊动画逻辑是后续主线，不能因这些API存在就标完成。合并时须与PR #3/#4同文件改动协调，不能直接覆盖其逻辑。

# UE 本地交接：Grabbable 抓取准入

分支 cloud/grabbable-admission；类 UVRSharpGrabbable / AVRSharpHand，源码 Script/ManagedVRSharp/Core/。

新增四个 BlueprintReadWrite/EditAnywhere 布尔值：DisableGrabbing、DisableLeftHand、DisableRightHand、SingleHandOnly。默认 false，保留旧资产允许左右手共同抓取的行为。准入用于目标筛选、Grab入口、回调后及Attach入口。运行时更改配置仅限制后续抓取，不强制释放已抓手；原有释放流程保留。释放行为配置、姿势混合、PC/OpenXR为后续功能，未在本轮实现。

本地步骤：UE5.7/UnrealSharp0.1宿主生成Glue并完整编译。打开 /VRSharp/Maps/VRSharpDemo 的测试副本，使用现有左右手和简单碰撞可抓Actor。检查Grabbable详情面板与蓝图读写四项属性；保存重开确认序列化。无需增加辅助组件或改输入映射。

验收矩阵：全false保持旧行为；DisableGrabbing拒绝左右手高亮/抓取；仅DisableLeftHand时右手可抓；仅DisableRightHand时左手可抓；两手均禁用时均不可抓。SingleHandOnly开启后第一手可抓、第二手不可抓，释放第一手后第二手可抓；同手重复准入不应被误拒。已抓取期间禁用仍应可正常释放。OnBeforeGrab中切换禁用或占用状态后不得继续Attach。测试前向射线拒绝目标后可继续找到球内其他允许目标。

状态：完整UE编译、PIE、头显均待执行。独立数学测试不覆盖本轮新增准入逻辑；不得把它们的通过视作该功能运行验证。关联PR创建后见对应PR标题。

- 2026-11-03 follow-up: Grab now returns rejection to GrabWithHitResult/TryGrab instead of unconditional success. Revalidate grabbable and primitive between each before-grab callback; suppress successful completion if attachment did not register this hand. Runtime regression pending: disable/destroy target or primitive in either before-grab callback, expect false and no success callbacks; normal grab expects true. Full UE build/PIE/headset not run. Attempt to rerun standalone checks failed before process creation (exec-server: no such file or directory), so no new test pass is claimed. Previous PR CI was green, reviews/comments empty. Connector text write succeeded; this does not establish LFS upload authorization.

- 2026-11-03: Execution environment recovered by using an existing workspace path and a fresh isolated worktree. Both math suites and 192 admission policy cases passed against 9fd5774; these do not compile the Unreal hand callback code. Added CanGrab null/native-invalid hand rejection before reading IsLeft. This subsequent guard is source-reviewed only; UE runtime acceptance must call CanGrab with null and a destroyed hand and expect false without native access, then verify a valid hand still follows policy. UE build/PIE/headset remain pending. Local LFS fsck passed; upload authorization remains unproven. PR #4 CI green at inspection, no review feedback; no merge.

- 2026-11-04 手侧接口组：AVRSharpHand新增Grabbed/Released C#事件，签名同物体事件(hand,item,component)。Grabbable在实际Attach/Detach完成状态变更后先通知手、再通知物体；重复/失败动作仍不通知。GetCurrentGrabComponent提供蓝图/C#按手查询；弹簧与指尖反馈改为该查询，避免另一手先抓组件的共享缓存误用（覆盖PR3相同用途，不直接覆写旧分支）。C#可 hand.Grabbed += handler / hand.Released += handler，EndPlay配对退订；旧OnBefore/After API保留。不能在同步通知内递归抓放同一对象。UE组合验收：两手抓同Actor不同Primitive，事件回调读取手/物体状态应一致，分别驱动各自Primitive，释放一手不改变另一手查询，最后释放返回null。完整UE编译、PIE与原生组件生命周期仍待执行；隔离测试仅检查生产物体方法调用手通知桥接时的状态，不编译完整手类或实际物理。

- 2026-11-04 桌面六自由度操作：新增可选DesktopHandRotate Axis3D动作，X/Y/Z对应yaw/pitch/roll，SetHandRotateInput供C#/蓝图模拟，默认角速度90度/秒。Triggered持续输入，Completed/Canceled归零，切手和Reset清理旋转输入，非活动手保持自己的目标变换。旋转在相机局部空间以受限dt积分，混合轴归一化。UE侧在BindDesktopInput第一次成功前赋动作；可映射R/F、T/G、Y/H三组正负轴（Negate/Swizzle，与Axis3D移动相同做法），不赋值时保留旧控制。不自动改输入资产。验收每轴单独转动、组合转动、切手停止旧轴、失焦停止旋转、抓物旋转与专用抓点对齐、30/60/120Hz角速度对比。新增原生旋转路径尚未经过UE编译/PIE验证；现有独立测试不覆盖FRotator及实际手目标变换。已定义的自由飞行限制继续适用。

## PR #8 — 显式特殊抓点与选择规则（2026-11-04）
代码：Core/VRSharpHandPose.cs 的 TargetComponent / Priority；Core/VRSharpHand.cs 的 FindExplicitGrabPose。关联提交见 PR #8 本节所在提交。
在待抓Actor蓝图添加多个 VRSharpHandPose 场景组件，各自 TargetComponent 选择同Actor的目标 Primitive（例如 StaticMesh），移动/旋转抓点到手掌期望位置。为左右手分别勾选 DisableRightHand / DisableLeftHand。Priority 越大越优先；相同时按抓取前 Palm 世界位置选择最近点，完全同距按组件名序稳定选择。无有效显式候选时才使用既有 GrabPoses 名称映射；未赋 TargetComponent 的旧资源不变。非有限位置的候选被忽略。
每点继续配置 AnimationKey、UseFingerWeights、UseTriggerBlend 等既有字段；动画蓝图通过 GetActiveGrabPose 读取 AnimationKey，通过 GetGrabPoseTrigger 驱动既有专用动画状态，进入/保持/退出接线见前文。本轮没有制作动画资产。
本地验收：编译生成C#绑定并打开蓝图，确认组件引用可保存/重开；同一物体放两个同优先级抓点，用桌面双手目标分别靠近它们，抓取应各选近点；提高远点Priority应选远点；禁用该手后应跳过；两个Primitive的点不得串用；清空所有显式引用应恢复旧映射。放下、切手、重新抓取后姿势生命周期与事件仍应一致。
已验证仅生产选择方法抽取的托管测试（原生组件/向量为替身）及独立数学检查；完整UE编译、组件引用序列化、PIE、真实对齐和头显未验证，不代表完整特殊姿势系统已验收。

## PR #8 桌面锁存抓握（2026-11-04）
VRSharpDesktopTestPawn.cs新增DesktopToggleGrip和ToggleActiveGrip。创建Bool输入动作IA_DesktopToggleGrip，映射E键，在Pawn默认值赋给DesktopToggleGrip（首次绑定前）。Started切换当前手抓放；不绑定Completed，因此松键仍持物，可切到另一手抓取。旧按住Grip模式保留；同一次测试避免混用两种动作。切手后分别再次按E释放各手；抓取失败返回false，不产生持有状态。ResetDesktopInput只释放旧按住输入拥有的抓握，锁存抓握需显式ReleaseActiveHand释放。
验收：右手E抓取→松E→切左手→E抓取→两手保持→E只放左手→切右手E释放。空目标E返回false；再次接近物体可重试。独立数学和既有方法测试不能证明此新增输入路由；完整UE编译/PIE/头显未验证。

## PR #8 桌面目标复位（2026-11-05）
VRSharpDesktopTestPawn.ResetHandTargets保存BeginPlay时左右目标的相机局部位置/旋转，调用后恢复两手目标并清除平移/旋转轴。蓝图在桌面Pawn添加Home键Started→ResetHandTargets；无需XR。先设置LeftTarget/RightTarget的默认局部变换再开始游戏。未初始化或目标失效返回false。复位不放下物体、不清扳机，也不瞬移物理手；原跟随逻辑把手带向恢复后的目标，因此抓着物体时谨慎测试碰撞。
验收：平移/旋转双手后按Home，两目标应回初始变换；再次输入仍可移动；锁存持物保持。抽取方法测试仅验证可调用/缺目标拒绝，不覆盖原生变换赋值、跟随物理；完整UE编译/PIE/头显待验。

## PR #8 持物扳机业务事件（2026-11-05）
Core/VRSharpHand.cs新增C# GrabTriggerChanged(hand,item,primitive,value)，业务组件在BeginPlay订阅手、EndPlay退订。SetGrabTrigger现在适用于普通持物及特殊姿势；仅有效持物、有效组件、有限输入成功，归一到0..1，变化后更新状态/动画再通知，重复值不通知。Release在before-release回调前发送归零（原值非零时）；事件内不可递归抓放。GetGrabPoseTrigger兼容保留，普通物体同样可读。
例如处理器按item和primitive筛选自己的工具，value>=0.8开启工具，value<=0.2关闭；Released也必须作为业务停止兜底（物体销毁不保证扳机通知）。桌面DesktopTrigger沿用现有动作；OpenXR在既有Trigger输入回调调用SetGrabTrigger，Completed/Canceled传0。无需动画资产即可驱动业务事件；配置专用姿势时仍驱动现有动画混合。
本地验收：普通物体及特殊姿势分别按压/松开，事件上下文正确且重复相同值不重发；按住扳机放下先归零再Released；双手只通知输入对应手；空手不通知。生产方法托管抽取测试通过，原生类型为替身；完整UE编译、PIE、业务/动画实际接线与头显均未验证。

## PR #8 物体侧持物扳机事件（2026-11-05）
Core/VRSharpGrabbable.cs新增GrabTriggerChanged(hand,item,primitive,value)，对象业务C#组件直接在BeginPlay订阅自己的Grabbable，EndPlay退订，不必逐一查找左右手。手侧更新状态/动画后先通知手，再通知物体；物体通知会再次核对IsHeldBy/GetHeldComponent，手侧回调已改变持有关系时不向旧物体发送。回调中仍不要递归抓放。放下归零语义沿用上一节。
示例：grabbable.GrabTriggerChanged += OnToolTrigger；OnToolTrigger按primitive区分把手或按钮，记录每只手value；双手工具在Released时清除对应手记录，工具是否启动按产品逻辑决定。该事件为C#事件，不是已生成的Blueprint动态委托；蓝图业务需本地增加C#转发组件后接线。
验收：桌面和XR分别抓取同一工具，只有该工具收到变化；双手上下文各自正确；重复值不通知；正常放下归零；抓放后旧工具不再收到输入。托管手方法抽取测试验证桥接调用，未编译完整物体/手类；UE编译、PIE、实际工具示例资产及头显仍未验证。
