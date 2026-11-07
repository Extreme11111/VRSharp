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

## PR #8 特殊姿势动画淡入淡出（2026-11-05）
Core/VRSharpHandPose.cs新增EnterBlendSeconds/ExitBlendSeconds，秒，默认0兼容瞬切。Core/VRSharpHand.cs在成功抓取后启动视觉生命周期，Tick推进0..1权重；放下立即清理逻辑GetActiveGrabPose/触发旧退出事件，但GetAnimationGrabPose保留退出姿势到淡出完成，IsGrabPoseExiting区分退出。无效资源立即清理；淡出中抓新姿势立即换新姿势并从其进入权重开始，不是两套专用动画交叉混合。
本地AnimBP Event Blueprint Update Animation：读取手GetAnimationGrabPose并检查有效→缓存AnimationKey、GetGrabPoseBlendWeight、IsGrabPoseExiting；无效则权重0。AnimGraph以原有动态手指图为Base，按AnimationKey选择左右手匹配的专用Sequence Player或可复用姿势子图（如ToolGrip），通过Blend Poses by float的Alpha接上述权重；专用图内部用GetGrabPoseTrigger混合ToolGrip/ToolPress动画。不要用GetActiveGrabPose为空作为整个专用图的立即关闭条件，否则跳过淡出。退出期间扳机归零，逻辑Released仍即时发生，不延迟物理释放。
测试资产建议/VRSharp/Tests/Animations/ToolGrip_L、ToolGrip_R、ToolPress_L、ToolPress_R，须本地制作匹配手骨架；本轮未生成资产。抓点Enter=.15、Exit=.2。验收桌面抓取淡入→持续保持/扳机→放下淡出→恢复动态图；进入中放下、退出中抓另一物体、抓点销毁、左右手独立、30/60/120Hz。托管测试直接抽取生产进入/推进方法，原生有效性用替身；未验证完整UE编译、AnimBP节点/资产兼容、PIE、视觉质量与头显。
# UE交接：模拟手指输入

分支 cloud/manual-finger-input；AVRSharpHand.SetFingerInput(thumb,index,grasp) 位于 Script/ManagedVRSharp/Core/VRSharpHand.cs。三个轴为0..1；非有限样本保留前值；正在抓取时返回false并不覆盖接触反馈。此入口目前只支持空手，不代表已实现抓握期间扳机姿势混合或完整PC/OpenXR适配器。

UE5.7/UnrealSharp0.1宿主生成Glue并编译。在/VRSharp/Maps/VRSharpDemo测试副本，通过临时UMG三滑条或OpenXR轴值每帧调用每手SetFingerInput；使用该入口时不要同时驱动原Touched/Clicked动画回调，否则同帧后写入者覆盖前者。姿态跟随可使用现有UpdateTracking，抓放使用TryGrab/Release，输入映射需本地建立，未修改原资产。

验收：0/.5/1连续输入平滑驱动对应拇指/食指/三指；越界钳制；NaN/Infinity不污染目标；抓取时调用返回false且接触动画继续；释放后可重新驱动。左右手分别测试，保存蓝图重开确认节点可用。正常旧输入绑定应保持。UE编译、蓝图、PIE和头显均待执行；独立测试仅覆盖数值归一化。

- 2026-11-03 输入所有权更新（5db78bd）：成功SetFingerInput后，旧Touched/Clicked/Released动画回调不再覆盖外部目标；新增BlueprintCallable ClearFingerInput，在适配器断开、UI关闭或切换回旧输入时调用。空手清零目标；抓取中仅解除外部所有权，保留接触姿势。不主动释放物体，也不自动检测设备断开。此规则取代此前“同帧后写入者覆盖”的接线警告。待UE验收：外部输入后触发全部旧动画事件，目标应保持；Clear后空手张开且旧输入事件恢复；抓取中Clear不改变接触姿势；连续Clear幂等；左右手所有权独立。完整UE编译/PIE/头显与此状态切换路径未验证，数值测试不能替代。

## PR #8 + PR #5 桌面空手输入集成（2026-11-05）
合并manual-finger-input到desktop-test-pawn，保留事件、准入和动画淡出逻辑。Core/VRSharpDesktopTestPawn.cs新增可选DesktopFingers Axis3D，XYZ=thumb/index/grasp；SetEmptyHandInput可供UI直接调用。创建IA_DesktopFingers，Z/X/C分别映射X/Y/Z正轴，使用Swizzle将一维值移至相应轴；Triggered持续赋值，Completed/Canceled清零。首次BindDesktopInput成功前赋动作。原DesktopTrigger空手时同时控制食指，取两输入最大值；持物时沿用扳机业务/动画。无需XR。
切手清除旧手外部输入并清零模拟轴；ResetDesktopInput清理两手；抓握期间SetFingerInput拒绝覆盖接触/专用姿势。松开后下一Tick恢复当前桌面空手输入。空手外部输入会阻止旧VR空手回调覆盖，ClearFingerInput交还旧输入。验收：三轴单独/组合闭合、松键张开、按住手指轴抓取专用工具→扳机→放下恢复当前输入、切手不残留、失焦调用Reset、两手持物不受空手轴影响。
生产FingerInput/手方法隔离回归及数学检查用于验证托管逻辑；不覆盖完整Pawn、原生输入、骨骼动画和接触物理。UE编译、PIE、头显未验证。二进制资产未编辑。

## PR #8 OpenXR 与桌面持物扳机共用（2026-11-05）
`Script/ManagedVRSharp/Core/VRSharpHand.cs` 在现有 `InitializeInputEvents` 绑定手侧扳机。保留原 `TriggerAction` 的数字 Started→1。可在左右手蓝图分别配置 `AnalogTriggerAction`，替代数字输入。创建 Axis3D 的 `IA_TriggerAnalog_L` 和 `IA_TriggerAnalog_R`，在 VR Pawn 的 OpenXR Mapping Context 分别映射控制器左、右模拟 Trigger Axis 到 X，使用持续 Triggered 的轴配置。Completed 和 Canceled 清零。不要给两个手实例指派同一个 Action。桌面 Pawn 继续通过自己的输入绑定调用共用 `SetGrabTrigger`。若宿主此前按旧交接在蓝图手动转发同一个 XR 动作，应移除重复转发。
空手时轴驱动食指，外部 `SetFingerInput` 占用时优先。抓取后每帧使用最新样本，先按扳机再抓也会驱动专用姿势和物体事件。放下时工具归零，空手下一个 Tick 仍反映实际按压。多个输入事件在一次手 Tick 内合为最后一个样本。
本地先用 UE5.7/UnrealSharp0.1 生成 Glue 并编译，确认 `BindAction(..., out _)`、Axis3D Getter 和蓝图属性可用。桌面 PIE 回归扳机与抓放，然后在 VR Preview 测数字回退、左右手分别半按、先按再抓、按住释放、取消动作映射。预期相应手的 `GetGrabPoseTrigger`、专用动画和工具事件同步，另一手不受影响。托管测试覆盖路由、输入占用和取消归零，尚未验证 UE 编译、PIE 或头显。

## PR #8 道具原地松手配置（2026-11-05）
`Script/ManagedVRSharp/Core/VRSharpGrabbable.cs` 新增 `DropWithoutMomentum`。在道具蓝图的 Grabbable 组件开启，配合启用了 Simulate Physics 的单刚体 Static Mesh 和原有可抓碰撞设置。最后一只手解除焊接后，在 Released 通知前清零该手对应组件根刚体的线速度和角速度。重力和碰撞仍参与后续物理步。多组件道具仅处理最后释放的那个 Primitive。默认关闭，沿用宿主物理速度。无效组件或未模拟物理时跳过。
UE5.7/UnrealSharp0.1 先生成 Glue 并编译，确认 `SetPhysicsAngularVelocityInRadians` 绑定。复制两个相同道具到桌面测试地图，分别打开和关闭此选项。在移动和转动中松开，比较 Released 当帧速度，打开的应归零后自然下落。双手先放一只不清速，最终放开才清速。用桌面锁存抓握和 OpenXR 各走一遍。验证切换组件、无物理对象和对象销毁时的行为，检查托管测试使用的原生调用替身与 Chaos 实际脱焊结果。完整 UE 编译、PIE 和头显待验。

## PR #8 指定特殊抓点的测试入口（2026-11-05）
`Script/ManagedVRSharp/Core/VRSharpHand.cs` 的 `TryGrabAtPose(Grabbable, HandPose)` 和 `VRSharpDesktopTestPawn.cs` 的 `GrabActiveHandAtPose` 提供同一套抓点指定入口。将两个 HandPose 加到同一测试道具蓝图，分别设置同一或不同的 `TargetComponent`，设置明显不同的手掌姿势和 AnimationKey。仅接受与 Grabbable 同 Actor 的组件引用，并使用当前抓球、射线、碰撞查询及手别限制。指定失败返回 false。普通抓取仍按配置选择姿势。
在桌面地图放置道具，给测试 Widget 或关卡蓝图分别添加两个按钮，调用 `GrabActiveHandAtPose` 并打印返回值。成功后读取 `GetActiveGrabPose`，应等于传入组件，即使另一个抓点优先级更高。通过原 `ReleaseActiveHand` 放下，检查淡出与扳机恢复。切手后检查手别禁用。将指定碰撞体移出手的抓取范围，同时保留近处兄弟碰撞体，预期 false 且无成功抓取事件。通过 `TryGrabAtPose` 可用同一测试步骤验证 XR 手。
已用原生替身测试指定入口和接触过滤。完整 UE 编译、PIE、碰撞查询和头显待验。

## PR #8 桌面键鼠映射自动接入（2026-11-05）
在 `Script/ManagedVRSharp/Core/VRSharpDesktopTestPawn.cs` 对应桌面 Pawn 蓝图中，将此前创建的 `IMC_VRSharpDesktop` 指派给 `DesktopMappingContext`，`DesktopMappingPriority` 默认 0。宿主测试地图以 Auto Possess Player 0 或 GameMode Default Pawn Class 占用该 Pawn。Action 属性、左右手引用与相机目标照原交接配置。启用后可移除关卡蓝图中为本 Pawn 手动 AddMappingContext 的节点。留空继续使用宿主管理的输入映射。
Pawn Tick 检测本地 PlayerController 并向其 Enhanced Input 子系统添加映射。控制器丢失、配置更换或 EndPlay 时移除本 Pawn 添加的映射并清理桌面输入，按住型抓握随 ResetDesktopInput 清理，锁存型抓握保持原设计。若同一映射由宿主事先添加，Pawn 不更改其优先级且不移除。请为桌面 Pawn 使用专用映射，避免两个对象同时管理同一资产。优先级在添加时读取。
验收先生成 UE5.7/UnrealSharp0.1 Glue，核对 GetController、EndPlay、HasMappingContext 和 RemoveMappingContext 绑定。在无头显的普通 PIE 占用 Pawn，键鼠移动、左右手切换、抓放和扳机应可用。带着按住型抓握切换到另一个 Pawn，确认释放和轴归零，桌面映射消失且其他映射保持。重新占用并检查一键一次事件。预先由宿主添加同一映射后退出桌面 Pawn，应保留该映射。托管测试覆盖映射所有权和生命周期，完整 UE 编译、PIE、头显未验证。

## PR #8 桌面 Pawn 自动生成测试手（2026-11-05）
`Script/ManagedVRSharp/Core/VRSharpDesktopTestPawn.cs` 新增 `LeftHandClass`、`RightHandClass`。在桌面 Pawn 蓝图 Class Defaults 指派 VR Pawn 已使用的左右手蓝图类，配置 Camera 下的左右目标位置和旋转，然后按前节配置 DesktopMappingContext 与输入动作。关卡可不再放置手实例。有效的 `LeftHand`/`RightHand` 实例引用优先于类配置，允许一侧摆放、一侧自动生成。手类仍需具备原有物理体、Palm、GrabSphere、骨骼和 AnimBP 配置。
BeginPlay 在目标世界变换处生成缺少的手，初始化物理与手别，不接入 XR 输入。Pawn EndPlay 会先释放其生成的手所抓的有效道具，再销毁这些手。已有实例不由 Pawn 销毁。缺类、缺目标或生成失败会保留空手引用，另一侧仍可使用。
UE5.7/UnrealSharp0.1 先生成 Glue 并编译，检查 SpawnActor、DestroyActor 与 EndPlay 绑定。用无头显普通 PIE 启动桌面地图，确认两只手各生成一次、在对应目标附近、可用键鼠切手、抓取和扳机驱动专用姿势。保持锁存抓取后销毁桌面 Pawn，预期道具释放、生成手消失。再预放一侧手并填实例引用，预期该侧无重复生成且退出后保留。托管回归覆盖选择、生成失败和释放先于销毁，未验证 UE 编译、PIE、Chaos 或头显。

## PR #8 可抓道具的扳机开关（2026-11-05）
在 `Script/ManagedVRSharp/Core/VRSharpGrabbable.cs` 对应的 Grabbable 组件上设置 `TriggerPressThreshold=0.75`、`TriggerReleaseThreshold=0.55`。两个阈值之间保持各手原状态，避免模拟扳机在临界值来回抖动。默认按下阈值为 0，关闭开关功能。配置要求 `0 <= release < press <= 1`，无效配置在下一次有效扳机样本时清掉该手的激活。配置建议在抓取前完成。
工具 C# 类可用 `grabbable.TriggerActivationChanged += OnActivationChanged` 在 BeginPlay 订阅，并在 EndPlay 退订。回调签名为 `(AVRSharpHand hand, UVRSharpGrabbable item, UPrimitiveComponent primitive, bool active)`。可用 `active` 开关手电筒灯或电钻马达。蓝图可通过 `GetIsTriggerActive` 读取合并后的状态，或由 C# 工具类转发事件。第一个激活手触发开启，最后一个激活手松开扳机或放下时触发关闭。更新状态后发布开关事件，再转发原模拟输入事件。直接 Detach 也会清除该手的激活，先于 Released 通知。回调内不要递归抓放。
在桌面测试地图放一个带可抓碰撞的手电筒测试蓝图，沿用已有桌面扳机或 OpenXR 模拟动作。用蓝图滑条调用 `SetTrigger` 依次发送 0.8、0.65、0.55，预期开、保持、关各一次。双手抓同一物体时让两只手依次按住，先松或放下其中一只应保持，另一只放下后关闭。桌面切手会清空旧手扳机，双手同时按压需用 XR 或 C# 直接分别输入。确认空手、错误 Primitive 和未设置阈值的旧物体不触发开关。完整 UE 编译、蓝图接线、PIE 和头显待验证，托管回归使用原生替身。

## PR #8 桌面测试地图配置自检（2026-11-06）
`Script/ManagedVRSharp/Core/VRSharpDesktopTestPawn.cs` 提供 `GetDesktopSetupIssues` 和 `IsDesktopInputBound`。在桌面 Pawn 蓝图 BeginPlay 父类执行后调用前者，返回字符串非空时接 Print String 或调试 Widget。也可加一个检查按钮按需刷新，不必每帧调用。报告列出缺失或失效的相机、目标、手实例/类和必需 Action，并指出共享手/目标或重复 Action。手生成后会报告实际不可用的一侧。`IsDesktopInputBound` 可在占用后的下一帧或按钮上查询当前 Enhanced Input 组件绑定状态。
本地验收先编译 Glue。在无头显 PIE 中，故意清空 `DesktopGrip` 并将 `DesktopLook` 指向 `DesktopMove`，应同时报告缺失与重复。修复后运行，应得到空报告，键鼠映射生效后绑定查询为 true。再移除一侧手类和实例，应定位对应手。留空可选 `DesktopMappingContext` 时可由宿主管理，不报缺项。报告检查引用及绑定状态，映射内键位、Action 轴类型、手骨骼与碰撞需按前节另行验收。托管测试使用原生替身，完整 UE 编译、PIE、头显尚未验证。

## PR #8 整合 PR #2 的失效道具释放恢复（2026-11-06）
`Script/ManagedVRSharp/Core/VRSharpHand.cs` 的 `Release()` 在释放回调后重新校验 Grabbable。若已销毁或缺失，手以 KeepWorld 解除附着并清空持有状态，归零扳机和手指目标。失效的姿势跳过退出通知及淡出，仍有效的姿势走原淡出。旧的手侧 OnAfterRelease 继续触发，监听者访问旧对象前应检查有效性。无法通知已销毁对象的 Released。`VRSharpDesktopTestPawn.cs` 退出时调用相同恢复流程再销毁自建手。
无需新增资产配置。用已有桌面测试地图和一件特殊姿势道具，分别在手和 Grabbable 的 C# BeforeRelease 回调销毁该道具 Actor。放下后应无原生无效引用异常，IsGrabbing 为 false，姿势和扳机清空，手能接着抓另一件物体。再以普通释放确认事件、工具开关与淡出保持。持物时销毁桌面 Pawn，验证自建手退出清理。回归使用原生替身测试真实 Release 方法，UE 编译、PIE、Chaos 脱焊和头显仍待验。

## PR #8 道具仅允许专用抓点（2026-11-06）
在道具蓝图的 `VRSharpGrabbable` 开启 `RequireExplicitGrabPose`。同 Actor 添加 `VRSharpHandPose` 场景组件，将 `TargetComponent` 指向可抓取的碰撞 Primitive，并配置手别、优先级、对齐变换和 AnimationKey。接触候选只保留有匹配抓点的组件，抓取回调后再检查配置。此模式需要显式组件引用，旧 `GrabPoses` 名称表仅在此选项关闭时可回退。旧资产默认关闭。底层 `Attach` 仍是原来的焊接入口，游戏逻辑应调用 `TryGrab`、`TryGrabAtPose` 或 `TryGrabWith` 走完整验证。
本地用 UE5.7/UnrealSharp0.1 生成 Glue 并编译。在桌面和 VR 测试地图放置一件带两块可抓碰撞的工具，只给把手配置抓点，并禁用左手。右手靠近机身时预期无该工具高亮且抓取失败，靠近把手可抓取、播放专用动画并使用扳机。左手应失败。在同一抓球中放置另一个正常可抓物体，机身不应阻挡正常候选。取消限制后验证原抓法与名称映射可用。托管测试覆盖接触候选过滤和显式抓点选择。UE 编译、PIE、高亮、碰撞和头显待验。

## PR #8 桌面双手独立扳机（2026-11-06）
`Script/ManagedVRSharp/Core/VRSharpDesktopTestPawn.cs` 新增 `DesktopLeftTrigger`、`DesktopRightTrigger` 和 `SetHandTrigger(left,value)`。在 `IMC_VRSharpDesktop` 中分别创建两个不同的 Axis3D Action，键值进入 X 轴，例如 V/B 分别按压左右手，指派给 Pawn 对应属性。也可用测试 Widget 的两个滑条调用 SetHandTrigger。现有 DesktopTrigger 仍跟随当前手，与该手专用值取最大值。切手只清共享扳机，专用值保留。Completed/Canceled 清对应手，ResetDesktopInput 清两手，空手可观察各自食指。
先用 UE5.7/UnrealSharp0.1 编译 Glue。在无头显桌面地图用锁存抓握让两手各抓一件测试物，或共同抓允许双手的同一工具。给工具设置扳机开关和专用姿势，按住 V 和 B 后切手并松 V，预期左手扳机归零、右手值不变，双手工具保持开启。再松 B，预期关闭。测试失焦时调用 ResetDesktopInput 并验证两手都归零。托管测试运行生产路由方法，原生按键映射、完整 UE 编译、PIE、动画显示和头显仍待验证。

## PR #8 可抓手电筒验收道具（2026-11-06）
`Script/ManagedVRSharp/Demo/VRSharpFlashlight.cs` 提供 `AVRSharpFlashlight`，内置 Body、Lamp、Grab 和左右手抓点。C# 在 BeginPlay 将抓点绑定到 Body 并限制各自手别，订阅 `Grab.TriggerActivationChanged`，用聚光灯可见性显示实际激活状态。Grab 的两个阈值均为零时，此示例使用 0.75/0.55。已配置的阈值保留。EndPlay 退订并关闭灯。

1. 用 UE5.7 和 UnrealSharp0.1 生成 Glue 并编译。以该类为父类创建 `/VRSharp/Tests/BP_VRSharpFlashlight`，为 Body 设置简单圆柱或手电筒 Mesh、简单碰撞、Simulate Physics，以及当前手 GrabObjectTypes 可检测的物体类型。将 Lamp 设为 Movable，在 Body 前端朝向墙面。
2. 调整 LeftGrip 和 RightGrip 的局部位置与旋转，让两侧手掌各自贴住把手。在 Grab 上开启 RequireExplicitGrabPose。可选配置左右手各自的 AnimationKey 和淡入淡出时间，按前述 AnimBP 接线使用已有手骨架对应的姿势动画。没有专用动画资源时仍可测试抓点对齐和灯光开关。
3. 将道具放在桌面测试地图及 VR 测试地图的可达位置。普通 PIE 启动后灯应关闭。抓取、按下扳机后应点亮，松扳机或放下后应关闭。允许两手持物时用桌面独立扳机同时按压，两手依次松开，灯应只在最后一只激活手松开时关闭。用 OpenXR 重跑。验证左右手对齐、姿势切换及退出恢复。销毁道具时不应残留亮灯或事件订阅。

本轮只交付 C# 示例类，蓝图、网格配置、动作映射、AnimBP 和关卡放置按上述步骤本地完成。托管测试用原生替身编译示例类，完整 UE 编译、PIE、渲染和头显待验。

## PR #8 独占抓点与双手把手（2026-11-06）
`Script/ManagedVRSharp/Core/VRSharpHandPose.cs` 新增 `ExclusiveToOneHand`。在一件允许双手抓取的工具蓝图上配置两个 HandPose，两点可以绑定同一个 Body Primitive。给两点不同的位置和 AnimationKey，勾选独占，并保留需要测试的手别。开启 Grabbable 的 RequireExplicitGrabPose 以便全部兼容抓点被占用时拒绝抓取。默认关闭独占，可继续共享旧抓点。关闭 RequireExplicitGrabPose 时，没有可用姿势仍可走普通抓法。

普通抓取跳过被占用的独占点，TryGrabAtPose 请求被占用的点时返回 false。Grabbable 在焊接成功后、Grabbed 通知前登记，释放时在 Released 通知前清除。调试 Widget 可调用 `Grab.IsGrabPoseOccupied(Pose)` 显示占用状态。退出动画尚未淡出时，抓点已可重新使用。

本地 UE5.7/UnrealSharp0.1 生成 Glue 后编译。桌面 PIE 先让左手抓最高优先级点，切到右手并普通抓取，预期改用另一个点。用按钮指定左手已占点应失败。放开左手后检查占用归零，并让空手重新取得该点，右手仍持有自己的点。再用 OpenXR 测试实际碰撞、Chaos 双手焊接和专用 AnimBP。托管测试覆盖候选、注册和释放，完整 UE 编译、PIE 和头显待验。

## PR #8 专用抓点按 Palm 对齐（2026-11-06）
`Script/ManagedVRSharp/Core/VRSharpHand.cs` 和 `VRSharpMathHelper.cs` 现在按 Palm 的世界姿态求解显式抓点对齐，补偿 Palm 相对手 Actor 的位置和旋转。显式抓点应保存期望的 Palm 世界坐标系。旧 GrabPoses 名称表回退继续按手 Actor 旋转解释，普通抓取沿用原路径。
在 UE5.7/UnrealSharp0.1 生成 Glue 并编译。复制一套测试手蓝图，将 Palm 局部位置偏移并绕另一个轴旋转 30 度。对 `/VRSharp/Tests/BP_VRSharpFlashlight` 设置左右抓点的 TargetComponent、旋转和 AnimationKey。普通桌面抓取和指定姿势抓取后，在调试器读取 Palm 与 HandPose 的世界位置和旋转，预期一致。用两个不同角度抓住同一道具并释放，验证显示姿势、扳机和淡出，再用 OpenXR 重跑。若已按旧显式实现补过旋转，重新按期望 Palm 坐标调整抓点。原名称表资产无需迁移。
独立数学测试覆盖非零偏移与不交换旋转组合。UE 编译、世界变换应用、PIE、物理焊接和头显未验证。

## PR #8 双手扳机联锁（2026-11-06）
`Script/ManagedVRSharp/Core/VRSharpGrabbable.cs` 新增 `RequireTwoTriggerHands`，在道具蓝图的 Grab 组件 Details 中开启。用于验收的 `/VRSharp/Tests/BP_VRSharpFlashlight` 沿用现有 Body、Lamp、左右手抓点及动画配置。保持 SingleHandOnly 关闭，并为两手提供兼容抓点。使用已配置的按下和松开阈值，例如 0.75 和 0.55。联锁按同一 Grabbable 上两个不同的持有手 Actor 计数。在编辑器配置该选项，默认关闭时仍由任一只手点亮。模拟扳机值和抓握动画照常更新。

先用 UE5.7/UnrealSharp0.1 生成 Glue 并编译。无头显 PIE 中用桌面锁存抓握让两手都抓住手电筒，再用 DesktopLeftTrigger、DesktopRightTrigger 或两条滑杆测试。只按一侧时灯保持关闭，两侧都越过按下阈值才亮，松开一侧到释放阈值或直接放下任一只手时立即熄灭。重新抓取时不能继承上一次的激活。检查 `GetIsTriggerActive` 与现有 `TriggerActivationChanged` 通知一致，并用 OpenXR 重跑。托管回归覆盖默认行为、联锁、释放和重新抓取，UE 编译、PIE 和头显待验。

## PR #8 可复用的抓握动画资源槽（2026-11-06）
`Script/ManagedVRSharp/Core/VRSharpHandPose.cs` 新增 `GripAnimation` 和 `PressedAnimation`，可分别给同一物体的 LeftGrip 和 RightGrip 选择匹配各自手骨架的 Animation Sequence。未填写 GripAnimation 时继续走现有 AnimationKey 或动态手指动画。未填写 PressedAnimation 时复用 GripAnimation。资源槽供动画图使用，现有蓝图不会自动切换到新图。

1. 用 UE5.7 和 UnrealSharp0.1 生成 Glue 并编译。在 `/VRSharp/Tests/BP_VRSharpFlashlight` 的左右手抓点分别填握住和按下的序列。测试可先使用两段第 0 帧即为目标姿势的序列，配置 EnterBlendSeconds=0.15、ExitBlendSeconds=0.2。
2. 在手 AnimBP 的 Event Blueprint Update Animation 调用 `GetAnimationGrabPose`，检查有效性后读取两个资源引用。把 Grip、Pressed 和是否有 Grip 缓存到动画变量。Pressed 为空时使用 Grip。读取 `GetGrabAnimationTrigger` 与 `GetGrabPoseBlendWeight` 到 float 变量。退出完成或 Pose 无效时清空资源槽并将外层 Alpha 置零。
3. AnimGraph 中设置两路 Sequence Evaluator，暴露 Sequence 资产输入，显式时间设为 0，分别输入 Grip 和 Pressed。用 Blend 的 Alpha 接 `GetGrabAnimationTrigger` 的缓存值。在第二层 Blend 中 A 接已有手动画，B 接前一层输出，Alpha 接抓握淡入淡出权重。无有效 Grip 时使用原有图，避免求值空序列。动态序列资源引脚和骨架兼容性在宿主版本验收。
4. 桌面模式按到半扳机后放下，工具扳机值和开关应立即归零，但视觉淡出应从松手前的按压姿势开始。淡出完成后重新抓取或换成普通物体，不能带入上一次按压值。用左右手及 OpenXR 重跑，检查动画资源不同也能使用同一 AnimBP 逻辑。

`Script/ManagedVRSharp/Core/VRSharpHand.cs` 只在动画淡出保留视觉采样，原 `GetGrabPoseTrigger` 仍返回实时业务输入。桌面放下入口交给手的 Release 统一归零，避免提前丢失淡出采样。本轮未制作序列和 AnimBP 资产。托管回归覆盖释放时视觉采样保留与逻辑清零。完整 UE 编译、动画图、PIE 和头显待验。

## PR #8 桌面空手预览特殊姿势（2026-11-06）
`Script/ManagedVRSharp/Core/VRSharpDesktopTestPawn.cs` 的 `PreviewActiveHandPose` 和 `StopActiveHandPosePreview` 调用 `VRSharpHand.cs` 的视觉预览入口。可在不抓取、不启动 XR 的桌面场景预览一个 HandPose 的握住和按压动画。接受当前手别允许的有效 HandPose，并要求当前手为空手。预览不占用抓点、不改手掌物理位置、不发 Grabbed/Released 或工具激活事件。

1. 在无头显的桌面测试地图放置 `/VRSharp/Tests/BP_VRSharpFlashlight`。选其 LeftGrip / RightGrip，配置 GripAnimation、PressedAnimation 和淡入淡出。手 AnimBP 仍按上一节读取 `GetAnimationGrabPose`、`GetGrabAnimationTrigger` 和 `GetGrabPoseBlendWeight`。
2. 在测试 Widget 中创建 Preview 和 Stop 按钮，分别连接 Pawn 的两个方法。Preview 参数用关卡道具的抓点引用。也可由调试按键调用。按现有桌面扳机，或通过滑条调用 `SetTrigger` 调整预览按压。无需接触道具。
3. 验证预览期间灯保持关闭、GrabCount 为 0。切换手、Stop 或 ResetDesktopInput 会结束预览并按配置淡出。真正抓取成功会接管视觉姿势。握住道具时再次点 Preview 应返回 false，当前持物动画继续。验收左右手限制及预览期间销毁抓点后的还原。
4. 本地先做 UE5.7/UnrealSharp0.1 Glue 编译，再做普通桌面 PIE。独立数学和托管回归覆盖预览隔离、触发路由、淡出与真实抓握接管。完整 UE 编译、蓝图、PIE 和头显待验。

## PR #8 桌面左右手独立抓放（2026-11-07）

`Script/ManagedVRSharp/Core/VRSharpDesktopTestPawn.cs` 提供可选的 `DesktopLeftGrip` 和 `DesktopRightGrip`，以及 Widget 或脚本可调用的 `SetHandGrip(left, pressed)`。当前手选择继续用于移动和转动手部目标。共享抓取键和锁存抓取保留原有用法。

1. 用 UE5.7 和 UnrealSharp0.1 生成 Glue 并编译。在现有桌面 Pawn 蓝图的 `IMC_VRSharpDesktop` 中创建独立的 Bool 动作 `IA_DesktopLeftGrip`、`IA_DesktopRightGrip`，例如分别绑定 J 和 K，确保键位不与现有动作冲突。分别赋给 Pawn 同侧的 Grip 属性，保留原有必填动作。C# 在 Started 抓取，在 Completed 和 Canceled 释放。若使用 Widget，按下与松开分别调用 `SetHandGrip`，传入对应侧和 true/false。失焦时沿用 `ResetDesktopInput`。
2. 在无头显的桌面 PIE，把左右手分别移到允许该侧抓取的道具旁。按住两个键，再按 Tab 切手并移动目标。两边都应持续持物。松开一个键只释放它成功抓住的物体。可用两个键抓住手电筒的不同专用抓点，再操作左右扳机测试联锁。
3. 按住一侧的抓取键，通过调试蓝图先释放该手，再用程序入口让该手重新抓同一道具。松开原键后，新抓握应保留。分别测试空抓、已经锁存的手、动作取消与 `ResetDesktopInput`。预期只释放对应输入动作取得且仍有效的抓握，未抓成功的动作不会触发释放。
4. 托管替身回归覆盖独立抓放、共享键切手、取消、重置和同物体重新抓取。完整 UE 编译、Enhanced Input 分发、PIE 双手物理与动画以及头显回归待验。

## PR #8 双手道具主手交接（2026-11-07）

`Script/ManagedVRSharp/Core/VRSharpGrabbable.cs` 公开 `PrimaryGrabbingHand` 和当前主手的 `GrabbedComponent`，蓝图可通过 `GetPrimaryGrabbingHand` 和 `GetPrimaryGrabComponent` 查询。主手取当前抓握记录中最早的一只手。主手松开后，下一只仍持有的手接任。已有代码若需要记住首次抓住的组件，可在首次 Grabbed 时自行保存，`GrabbedComponent` 现在随主手交接。

- C# 可订阅 `PrimaryGrabChanged(grabbable, oldHand, oldComponent, newHand, newComponent)`，在 EndPlay 退订。首次抓住时旧手与旧组件为空，最后放下时新手与新组件为空。常规顺序是状态写入、已有 Grabbed/Released 通知、主手通知。失败、重复抓取和不改变主手的副手抓放不会发送主手通知。若已有通知内同步发生再次抓放，主手通知发布最终观察到的变化。
- 在 UE5.7/UnrealSharp0.1 生成 Glue 并编译。在桌面测试地图复制双手工具，保留一个 Grabbable，关闭 SingleHandOnly，将左、右 HandPose 的 TargetComponent 分别指向两个可抓的 Primitive，并设置各自手别。选用桌面左右 Grip 键或 OpenXR 双手抓放。可在调试 Widget 显示两个查询节点的结果，用 C# 订阅事件输出前后手与组件名称。
- 左手先抓、右手再抓。查询应显示左手和它的组件，右手加入时无主手通知。先松左手应显示右手及其组件，右手继续持物。再松右手时两项查询为空。交换抓取顺序复测，再先松副手，确认主手保持。分别检查特殊姿势、扳机和释放期间的物理焊接。
- 两个独立数学检查和托管交接回归在云端运行。完整 UE 编译、蓝图 Glue、PIE 中的物理焊接与头显实测待本地验收。

## PR #8 桌面交互检查点（2026-11-07）

`Script/ManagedVRSharp/Core/VRSharpDesktopTestPawn.cs` 在 BeginPlay 保存桌面 Pawn 的世界位置和朝向、Camera 的局部位置和朝向、双手目标的局部位置和朝向及当前手别。可用 `CaptureDesktopCheckpoint` 覆盖本次 PIE 的检查点，用 `RestoreDesktopCheckpoint` 放下双手持物、清理桌面输入及预览并复位。正常跟随会把物理手拉向恢复后的目标，`VRSharpHand.cs` 会丢弃前一帧的追踪目标，避免把复位当作连续目标速度。未登记的道具留在释放处，登记方法见下一节。

1. 生成 UE5.7/UnrealSharp0.1 Glue 并编译。打开使用 `VRSharpDesktopTestPawn` 的无头显测试地图，确认 Origin、Camera、LeftTarget、RightTarget 均在 Pawn 上并保持现有父子层级。将 Pawn 出生点朝向转 90 度，相机局部俯角设为 -15 度。
2. 在测试 Widget 新增两个按钮，OnClicked 分别接到受控 Pawn 的 `CaptureDesktopCheckpoint` 和 `RestoreDesktopCheckpoint`。显示方法返回的 Bool。若映射键位，可用两个独立的 Bool 动作的 Started 调用同一入口。旧 `ResetHandTargets` 仍只恢复开局手目标。
3. 无头显 PIE 中移动鼠标，视角应从 90 度和 -15 度平滑变化。移动到手电筒旁，调整左右目标和当前手后保存。分别用按住及锁存方式抓住道具，按扳机，松开测试键或滑条，再点复位。两手持物和工具激活应清除，机位、相机、两目标及当前手恢复，鼠标从该视角继续。确认手经过物理跟随回到目标，附近未持有道具不随 Pawn 传送。改变关卡环境或重进 PIE 后应按需要重新保存。
4. 托管回归覆盖双手释放、相机与目标复位、鼠标连续性、组件无效与回调重新抓握。完整 UE 编译、PIE 物理与输入、头显实测仍待验收。

## PR #8 桌面检查点复位测试道具（2026-11-07）

`Script/ManagedVRSharp/Core/VRSharpDesktopTestPawn.cs` 的 `DesktopCheckpointProps` 可登记关卡中的测试道具 Actor。保存时记录这些 Actor 的世界变换。恢复时先正常放下桌面双手持物，再复位已登记的道具并清零根刚体线速度和角速度。数组留空时仅复位桌面 Pawn。

1. 在 UE5.7/UnrealSharp0.1 生成 Glue 并编译。在桌面测试地图中复制 `/VRSharp/Tests/BP_VRSharpFlashlight` 或另一件单刚体 Grabbable。确认其根组件是 Movable 的 Primitive，启用 Simulate Physics，同 Actor 上有 Grabbable。把它放在无遮挡的起始位置。选中关卡里的桌面 Pawn 实例，在 `DesktopCheckpointProps` 数组填写该道具 Actor。约束连接、多刚体和需重置自身脚本状态的道具应由各自测试场景处理。
2. 无头显 PIE 中，在空手且道具就绪时点 `CaptureDesktopCheckpoint`，确认返回 true。再抓取道具、按扳机、移动到别处，点 `RestoreDesktopCheckpoint`。预期双手放下、灯光随释放关闭、道具回到保存位置和朝向，根刚体速度归零。用同一初始布置重复抓取。再放一个未登记的道具作为对照，应留在原处。
3. 在另一只非桌面手仍持有登记道具时复位，预期返回 false，登记道具不移动，也不替其他手放下。登记道具已销毁、根被替换或停止模拟时，检查点也会拒绝复位。上述拒绝可能已清理桌面输入并释放桌面双手。若 UE 在实际传送阶段拒绝某个道具，方法返回 false，已复位的道具及 Pawn 保留已恢复状态，可在修复配置后重试。
4. 托管回归覆盖空数组兼容、重复登记、先放下再复位、速度归零、外部持握、根替换和传送失败。UE 编译、PIE 中的碰撞及焊接、头显回归待本地验收。

## PR #8 双手工具的主手扳机与副手支撑（2026-11-07）

`Script/ManagedVRSharp/Core/VRSharpGrabbable.cs` 新增 `RequireSupportHandForPrimaryTrigger`。启用时，最早仍持有且可操作扳机的手使用原有按下及释放阈值控制工具，并需要另一只手成功抓住同一道具。副手抓取成功后，如果主手的扳机已超过按下阈值，工具立即启动。任一手放开时停止，副手接任主手后仍需另一手支撑。两个选项同时开启时优先使用原有 `RequireTwoTriggerHands` 双扳机规则。默认关闭新选项。

1. 在 UE5.7/UnrealSharp0.1 生成 Glue 并编译。打开 `/VRSharp/Tests/BP_VRSharpFlashlight` 或同结构的单刚体工具。用一个 Grabbable 和两个 HandPose，保持两个抓点指向 Body，设置左右手及独占限制。在 Grabbable 上关闭 `SingleHandOnly` 和 `RequireTwoTriggerHands`，开启新选项，按下阈值设 0.75，释放阈值设 0.55。手电筒 C# 示例直接消费现有 `TriggerActivationChanged` 事件，无需修改灯光蓝图。
2. 无头显 PIE 使用两侧独立 Grip 和 Trigger。主手抓住并先按扳机，灯应保持关闭。另一手抓住后灯亮。松开副手应立即熄灭。重新抓住并单按副手扳机，灯仍保持关闭。反过来先抓右手，重复上述流程。开启旧双扳机规则后，验证两侧都按下才亮。
3. 调试输出读取 `GetIsTriggerActive` 和 `GetPrimaryGrabbingHand`。在 C# 激活回调中，Hand 与 Component 是引起状态变化的抓放或输入操作，例如支撑手抓住后，亮灯通知的 Hand 是支撑手。道具业务逻辑可用主手查询获得实际控制手。既有扳机模拟值事件与手指动画仍各自更新。
4. 托管回归覆盖失败的副手抓取、支撑加入及离开、主手交接和旧双扳机规则优先。完整 UE 编译、PIE 碰撞和动画以及 OpenXR 头显实测待本地验收。

## PR #8 抓点的扳机角色（2026-11-07）

`Script/ManagedVRSharp/Core/VRSharpHandPose.cs` 的 `SupportGripOnly` 可把抓点设为纯支撑。该手继续占用抓点并驱动按压动画，也会发出 `GrabTriggerChanged` 模拟值。只有允许控制的抓点可通过扳机输入激活工具，支撑抓放仍会改变双手模式的激活条件。所有已有抓点默认仍可控制工具。

1. 用 UE5.7 和 UnrealSharp0.1 生成 Glue 并编译。在 `/VRSharp/Tests/BP_VRSharpFlashlight` 测试副本中，把前握把的 HandPose 勾选 `SupportGripOnly`，后握把保持关闭。两个抓点继续各自设置手别、TargetComponent、ExclusiveToOneHand、GripAnimation 与 PressedAnimation。Grabbable 启用 `RequireSupportHandForPrimaryTrigger`，关闭 `RequireTwoTriggerHands`。AnimBP 沿用当前抓点动画和扳机权重节点。
2. 无头显 PIE 先抓前握把，再抓后握把。两手分别按扳机，前握把只动动画，后握把可点亮手电筒。放开前握把，灯应立即熄灭。交换抓取顺序再验一次，之后在 OpenXR 双手复测。
3. C# 或调试 Widget 调用 `GetPrimaryTriggerHand` 读取最早仍持有且允许扳机的手，和 `GetPrimaryGrabbingHand` 的物理抓握顺序可分别显示。若改用 `RequireTwoTriggerHands`，须至少两手都抓在允许扳机的点上才可激活。低层 Attach 成功换到另一组件会清除旧抓点的扳机激活。
4. 托管回归覆盖两种抓取顺序、支撑手模拟值、重新绑定组件及旧双扳机规则。完整 UE 编译、PIE 碰撞与动画、OpenXR 头显实测待验。

## PR #8 抓取配置报告与迁移检查（2026-11-07）

`Script/ManagedVRSharp/Core/VRSharpGrabbable.cs` 新增 `GetGrabSetupIssues`，C# 和蓝图均可调用。返回文本逐行包含字段或抓点名。报告检查显式抓点的 TargetComponent、左右手可用性、工具启动所需的控制抓点、扳机阈值、动画过渡时间和互斥的单/双手配置。该查询按需运行，配置修改后可重新检查。

1. 用 UE5.7/UnrealSharp0.1 生成 Glue 并编译。在桌面测试 Widget 中添加“检查道具”按钮和多行 TextBlock。OnClicked 从选定测试 Actor 取得 Grabbable 引用，调用 `GetGrabSetupIssues`，把 Return Value 接到 TextBlock 的 SetText。可同时显示 Pawn 的 `GetDesktopSetupIssues`，分别定位输入/手实例配置和道具抓点配置。报告为空表示所检查配置项通过。
2. 复制 `/VRSharp/Tests/BP_VRSharpFlashlight`，开启 RequireExplicitGrabPose。在一侧 HandPose 清空 TargetComponent，运行查询，应显示该抓点名称及缺少的手别。恢复到同 Actor 的 Body，确认该项清空。迁移后组件引用指向其他 Actor 或失效时也应定位到具体抓点。
3. 开启 SingleHandOnly，同时开启任一双手启动规则，应报告配置冲突。把两侧抓点都设为 SupportGripOnly，保持扳机启用，应报告没有可操作扳机的抓点。逐项修复再查询，随后正常抓取、扳机和放下。动画骨架兼容、碰撞响应和按键映射仍按前文进行 PIE 验收。
4. 云端托管回归覆盖缺失/外部/失效引用、手别配置、规则冲突和修复后复查。两个独立数学检查也在本轮运行。完整 UE 编译、查询蓝图 Glue、PIE 和头显实测待验。
