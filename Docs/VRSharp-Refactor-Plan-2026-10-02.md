# VRSharp 重构计划：物理身体、滑动抓取、PC 模拟与 Quinn Avatar

日期：2026-10-02。状态：源码审阅与设计方案；尚未实施、编译或运行验证。

## 1. 结论与范围

直接在 VRSharp 中建立新的 Runtime，现有 Core 和 Demo 作为行为参考及迁移基线。HeadMountedVR 用来建立功能覆盖清单，VRExpansion 的坐标、网络经验可作为研究参考；不让它们成为第二套角色或抓取执行器。

最终目标：

- C# 管理输入、追踪、状态、配置、交互与事件；Chaos 和 UE 原生 Drive 负责物理求解，不用 C# 重写弹簧积分、阻尼力或旋转扭矩。
- APawn 使用一个权威的物理运动根，身体、手臂和手能真实传力。攀爬、投掷和重物阻力由这条受力链产生。
- 固定抓取保持“物理手附着/Weld 到物体”的方向。滑动抓取使用允许切向运动的原生接触约束。
- 距离过远时进入握持退化判断；高速、切向负载较大时先滑动，再恢复握持或脱手。
- VR 和 PC 模式共享物理身体、双手、抓取和交互；PC 只替换设备姿态与输入来源。
- 全身第一版采用 UE 默认女性机器人 Quinn；保留 HandsOnly 和未来自定义 Avatar 的数据契约。
- 网络契约从第一阶段设计；核心多人闭环在扩展库存、武器之前验证。
- 原对话要求的 HeadMountedVR 大部分功能继续纳入后续迁移，不因新增四项功能而取消。

## 2. 原对话总结：以用户最后的决定为准

引用对话：`019e9b8f-fb78-76a2-a1e7-b070d9359721`。本次通过 read_thread 两页读取了全部可用回合。

### 2.1 需求演变

1. 最初比较 C# VRSharp 与 Lab6 使用的 C++ VR 插件。
2. 用户反馈 HeadMountedVR 运行问题：攀爬失效、全身 Avatar 崩溃、抓取手感不佳；希望用 C# 重建多数功能。
3. 确定物理手使用 UE 自带的 Drive，保留 VRSharp 的局部坐标思路，同时支持全身、只有手、自定义 Avatar、自动手指贴合、对外事件与网络。
4. 用户纠正抓取方向：应当把物理手 Attach/Weld 到物体，保证掌心接触关系，而不是把物体附到控制器，也不是一律软约束抓取。
5. 曾研究以 VRExpansion 为底座；之后用户决定直接重构 VRSharp。
6. 全身从视觉 IK 升级为真正参与物理模拟的身体。
7. 用户明确不要手写攀爬、投掷算法；它们应由抓取和身体受力自然产生。
8. 对外事件采用 VRGameplayEvents 的静态分类入口，实例订阅用 extension 门面。
9. 本次新增滑动抓取、超距高速退化、PC 双手模拟、Quinn 全身原型。

### 2.2 保留与废弃的旧方案

| 旧对话中的方案 | 本次归属 |
|---|---|
| VRSharp 小型物理核心作为参考 | 保留 |
| 全部普通抓取都用软约束 | 已被后续需求取代 |
| 将物体 Attach 到手或控制器 | 已被用户明确纠正 |
| VRE CharacterMovement 作为权威移动外壳 | 已被物理身体方向取代 |
| 独立 ClimbSystem 计算控制器偏移并搬动玩家 | 不作为核心实现 |
| 根据控制器历史额外补投掷速度 | 不作为核心实现 |
| FullBody 仅作为视觉 FBIK | 已升级为物理身体 |
| 非 VR 模式放在最后 | 本次提升为基础输入提供者与早期验证工具 |
| 网络最后再考虑 | 契约前置、实现逐步落地 |

旧回答中“计划已更新”主要是对话里的设计调整。本次才将可继续实施的计划落为这份文件。

## 3. 本次核对了哪些代码

### 3.1 VRSharp

实际游戏代码来自：

`D:/_Programming/Unreal/VRSharp/Plugins/VRSharp/Script/ManagedVRSharp`

读取了 Core 的五个文件、Demo 两个文件、模块入口、using、README、使用说明、项目配置和实际构建入口。核心文件：Player 308 行、Hand 620 行、Grabbable 178 行、MathHelper 98 行、HandPose 10 行。

实际编译入口是 [Script/ManagedVRSharp/ManagedVRSharp.csproj](D:/_Programming/Unreal/VRSharp/Script/ManagedVRSharp/ManagedVRSharp.csproj)，它包含插件目录的源码，并排除插件目录中的重复模块入口。它导入 `Plugins/UnrealSharp-main/UnrealSharp.Shared.props`。项目旁另有 UnrealSharp-fork，但不能因为目录存在就把它当成当前构建依赖。

当前工程 UE 5.7、目标 net9.0；`Script/global.json` 固定 SDK 9 的版本选择范围。机器已安装 .NET 10 SDK，但当前构建不会因此自动使用它。

### 3.2 Lab6 / HeadMountedVR

Lab6 是 UE 5.6 宿主工程，本地没有 Plugins 目录，uproject 启用 HeadMountedVR。

本次找到其 UE 5.6 安装版：

`C:/Program Files/Epic Games/UE_5.6/Engine/Plugins/Marketplace/HeadMoun617e2962c0c8V7`

并与以下源码副本逐文件比较：

`D:/_Programming/Unreal/VRPluginLab5/Plugins/HeadMountedVR`

两份 Source 中 120 个文件均一致。插件版本为 3.0.2。118 个 .h/.cpp 合计 32,276 行；HandComponent.cpp 7,703 行，Player.cpp 4,472 行，GrabComponent.cpp 1,795 行。

本次重点阅读了玩家初始化/输入模式/攀爬、手部 Drive 与模拟切换、抓取及几何吸附、Avatar 动画、房间尺度移动、相机与控制器复制、StaticAnimation 的底层焊接，并查看机械件、库存、武器、UI、加载与存档的模块接口和部分实现。没有声称逐行读完全部 32,276 行。

### 3.3 引擎和 Glue

核对了本机 UE 5.7 中 PrimitiveComponentPhysics、BodyInstance 的 Weld 路径，PhysicsControl 插件描述与组件接口，以及 UnrealSharp 生成的 Constraint、Primitive 和 PhysicalAnimation 绑定。

已存在的 C# 绑定包括：`SetConstrainedComponents`、`SetConstraintReferenceFrame`、`SetLinearDriveParams`、`GetConstraintForce`、`GetClosestPointOnCollision` 等。它们是优先使用的接口，不应先自行实现同名底层能力。

PhysicsControl 在本机 UE 5.7 描述文件中标记为 Beta；当前工程未启用它，也未发现相应生成 Glue。本计划默认用 PhysicsAsset + Constraint Drive + PhysicalAnimation，PhysicsControl 只作为能力原型的可选比较项。

### 3.4 验证边界

本次是源码、配置、文件与绑定审阅；没有启动编辑器，没有解码 Blueprint 图表，没有运行 PIE，没有复现用户报告的崩溃。已发现的风险点不能直接等同于用户实际故障的根因。

## 4. 当前代码的可复用点与重构理由

| 位置 | 当前行为 / 发现 | 重构处理 |
|---|---|---|
| [VRSharpPlayer.cs:155](D:/_Programming/Unreal/VRSharp/Plugins/VRSharp/Script/ManagedVRSharp/Core/VRSharpPlayer.cs:155) | 模拟物理胶囊、CCD | 保留物理 Pawn 方向，重新定义全身根与碰撞职责 |
| [VRSharpPlayer.cs:203](D:/_Programming/Unreal/VRSharp/Plugins/VRSharp/Script/ManagedVRSharp/Core/VRSharpPlayer.cs:203) | 手的跟随力取反后手动施加给 Capsule | 真实手臂关节传力通过验收后删除补偿，不能同时保留两条受力链 |
| [VRSharpPlayer.cs:267](D:/_Programming/Unreal/VRSharp/Plugins/VRSharp/Script/ManagedVRSharp/Core/VRSharpPlayer.cs:267) | 手 Actor 到 Pawn 原点超距立即 Release | 改为逐手、逐接触点的负载与滑动状态机 |
| [VRSharpPlayer.cs:281](D:/_Programming/Unreal/VRSharp/Plugins/VRSharp/Script/ManagedVRSharp/Core/VRSharpPlayer.cs:281) | 普通 Tick 直接搬动物理根，并反向补偿 VROrigin | 分离追踪空间和物理根，正常运行通过 Drive 响应目标 |
| [VRSharpPlayer.cs:182](D:/_Programming/Unreal/VRSharp/Plugins/VRSharp/Script/ManagedVRSharp/Core/VRSharpPlayer.cs:182) | 使用 GetPlayerController(0) 绑定输入 | 使用拥有该 Pawn 的本地 Controller；远端与服务器不注册本地输入 |
| [VRSharpPlayer.cs:224](D:/_Programming/Unreal/VRSharp/Plugins/VRSharp/Script/ManagedVRSharp/Core/VRSharpPlayer.cs:224) | Triggered 回调中 Actor 和 VROrigin 都转动 | 审核叠加转角，Snap Turn 增加阈值、回中重触发与冷却 |
| [VRSharpHand.cs:221](D:/_Programming/Unreal/VRSharp/Plugins/VRSharp/Script/ManagedVRSharp/Core/VRSharpHand.cs:221) | C# 计算弹簧力与扭矩 | 替换为 UE 原生 Drive 配置 |
| [VRSharpHand.cs:337](D:/_Programming/Unreal/VRSharp/Plugins/VRSharp/Script/ManagedVRSharp/Core/VRSharpHand.cs:337) | Socket 球重叠冻结 curl，中/无名/小指共享权重 | 扩展为逐指逐节接触，滑动时重新求贴合 |
| [VRSharpHand.cs:463](D:/_Programming/Unreal/VRSharp/Plugins/VRSharp/Script/ManagedVRSharp/Core/VRSharpHand.cs:463) | 注释记录 IList<FHitResult> 的 UFunction 生成器问题 | 内部集合算法与反射 API 分离，生成器可支持的结构作为对外接口 |
| [VRSharpHand.cs:519](D:/_Programming/Unreal/VRSharp/Plugins/VRSharp/Script/ManagedVRSharp/Core/VRSharpHand.cs:519) | Contains 匹配组件及姿态名字 | 改成显式组件引用、稳定抓取点 ID 或 Socket 名；旧字符串表经适配层迁移 |
| [VRSharpHand.cs:532](D:/_Programming/Unreal/VRSharp/Plugins/VRSharp/Script/ManagedVRSharp/Core/VRSharpHand.cs:532) | 直接移动/旋转手再 Attach | 接近并验证容差后提交握持，避免大幅瞬移 |
| [VRSharpGrabbable.cs:125](D:/_Programming/Unreal/VRSharp/Plugins/VRSharp/Script/ManagedVRSharp/Core/VRSharpGrabbable.cs:125) | 手 Weld 到物体，列表管理双手拆焊 | 保留方向，提升为事务式拓扑管理；LIFO 是当前实现策略，不能直接当成引擎通用规则 |
| [Rod.cs:16](D:/_Programming/Unreal/VRSharp/Plugins/VRSharp/Script/ManagedVRSharp/Demo/Rod.cs:16) | 原生约束机械件 | 保留 Demo；提取铰链、滑轨、旋转读值与阈值事件组件 |

HeadMountedVR 的主要价值是功能覆盖，不是把超大 HandComponent 逐类翻译成 C#。

几个明确的源码问题：

- [VR_Player.cpp:843](D:/_Programming/Unreal/VRPluginLab5/Plugins/HeadMountedVR/Source/HeadMountedVR/Private/VR/VR_Player/VR_Player.cpp:843) 转换 AvatarAnimInstance 后直接解引用；材质实例也直接使用。动画类错误、实例未建立或材质不存在时存在崩溃风险。
- Avatar 动画里依赖 `foot_l`、`foot_r`、`Legs_Z`、`pelvis`，并使用固定旋转偏移；不适合直接当作通用骨架契约。
- [VR_Player.cpp:1452](D:/_Programming/Unreal/VRPluginLab5/Plugins/HeadMountedVR/Source/HeadMountedVR/Private/VR/VR_Player/VR_Player.cpp:1452) 双手中点写成 `(Left - Right) / 2 + Left`，不是 `(Left + Right) / 2`。这是明确数学错误，但未证明是攀爬失效的唯一原因。
- [VR_HandComponent.cpp:2283](D:/_Programming/Unreal/VRPluginLab5/Plugins/HeadMountedVR/Source/HeadMountedVR/Private/VR/VR_Components/VR_HandComponent.cpp:2283) 的 HandPhysicsTick 混合 Drive、模拟开关和 Attach。在纯物理新 Runtime 中应避免普通跟随路径反复切换模拟。
- [VR_MovementComponent.cpp:384](D:/_Programming/Unreal/VRPluginLab5/Plugins/HeadMountedVR/Source/HeadMountedVR/Private/VR/VR_Components/VR_MovementComponent.cpp:384) 在 Tick 路径更新 VR 模式并发送 RPC；多处 Validate 恒返回 true。新系统使用模式变更事件和服务器验证。
- Plane/Cylinder 的 PrimitiveSnap 是几何抓取位置选择，不能直接当成具有摩擦、负载和持续接触的滑动抓取。

## 5. 必须修正的物理前提

### 5.1 Weld 之后约束不会当然继续有效

UE 5.7 的 FBodyInstance::Weld 合并碰撞形状后会释放子体原来的 PhysicsActor。以该句柄建立的跟手/手腕约束，需要确认是否重建到新的合并根；不能假定 Attach 之后自动迁移所有约束。

新增“逻辑手端点”概念：稳定的 HandId、组件/骨骼引用、掌心局部帧；当前原生刚体可以是独立 Palm，也可以是被抓物体的合并根。拓扑变化时统一解析端点并重绑定。

固定抓取时的原则：被抓物体仍是合并体的物理根，手是附着侧；跟手作用点与手腕作用点位于掌心接触帧。它们在原生层解析到物体，并不改变“物理手驱动物体”的逻辑语义。

### 5.2 静态附着不是动态 Weld 的同一条路径

本机 UPrimitiveComponent::WeldToImplementation 对非模拟父体的默认分支会关闭子体模拟并返回 false。抓静态墙体应显式建立世界锚点/手腕到静态体的连接；不能以 `weldSimulatedBodies=true` 参数推断动态合并已成功。

### 5.3 全身骨架的一只手不能通过整个 Mesh Attach 单独焊出去

USkeletalMeshComponent 有多个骨骼刚体。对整个组件做 Attach，不能被当作“只把 hand_l 焊到物体，其余人体保持原有约束”的完整能力。

首选原型：独立 PalmBody 作为抓取刚体，通过原生手腕关节接到 forearm；全身骨架对应手掌碰撞禁用或由代理接管，视觉手腕最终匹配 PalmBody。HandsOnly 可以隐藏相同人体/手臂代理，保持同一受力模型。若后续单骨骼焊接证明稳定，再评估替换代理。

PalmBody 被 Weld 后，手腕连接必须重绑定到合并根的掌心局部帧。不能在代理掌心之外再放一只独立受驱动物理手，造成两套掌部刚体争夺同一姿态。

### 5.4 只有世界目标拉手，不足以保证自然攀爬

手固定在世界时，对已经固定的手施加世界空间跟随力，并不自动形成“拉身体”的正确内力链。

需要前臂、上臂、躯干关节的有限强度姿态驱动；它们尝试满足追踪空间内的姿态，固定手产生反作用并带动身体。悬挂时解除骨盆对地面站立目标的强位置约束。身体仍被地面目标钉死、或者所有驱动都只有世界空间目标时，攀爬不会自然成立。

保留支撑/悬挂状态以选择 Drive Profile、判断地面和报告事件；不根据控制器位移直接移动玩家，不加入人工 ClimbVelocity。

### 5.5 滑动与固定 Weld 互斥

不能每帧拆焊再移动手来模拟滑动。那会反复改变质量/惯性/句柄，破坏速度连续性，并导致双手和网络状态不稳定。

固定握持只在入/出状态时变更拓扑；滑动期间独立 PalmBody 与物体通过法向保持、切向可动的约束连接。

## 6. Runtime 模块与职责

这些是代码目录和职责划分，初期不要求拆成十几个程序集。

```text
ManagedVRSharp/
  Runtime/
    Core/           Pawn、生命周期、World 范围运行时上下文
    Input/          InputRouter、OpenXR/PC/Remote 姿态提供者
    Tracking/       TrackingSpace、校准、坐标变换、追踪有效性
    Physics/        DriveProfile、刚体端点、拓扑事务、物理快照
    Body/           PhysicsRoot、物理关节姿态、地面支撑与悬挂
    Hands/          PalmBody、跟手目标、接触检测、手指贴合
    Grip/           候选选择、GripSession、固定/滑动/释放策略
    Locomotion/     平移、转向、传送、房间尺度目标
    Avatar/         QuinnDefinition、骨架映射、目标姿势、视觉适配
    Events/         VRGameplayEvents 分类门面、订阅与事件上下文
    Network/        输入帧、抓取状态、权威、校正与远端表现
    Interaction/    铰链/滑轨/按钮/旋钮/装备使用契约
  Gameplay/         Inventory、Weapons、Menus、Save 等可选扩展
  Compatibility/    Legacy API/资产迁移适配
  Demo/             保留旧 Demo，新建验证地图和模板
```

Pawn 负责组装，Controller/InputRouter 负责本地输入，Grip 管理状态，Physics 执行原生资源变更，Avatar 消费姿态和配置，玩法只请求动作和订阅结果。

避免新建一个同时负责输入、焊接、动画、传送、背包和 RPC 的超大 Hand 类。

### 6.1 主要数据契约

| 数据 | 关键内容 |
|---|---|
| TrackingFrame | 序号、时间、OriginEpoch、头/左右手局部变换、有效性、Grip/Trigger/curl |
| PhysicsBodyEndpoint | 组件、可选 BoneName、逻辑端点 ID、接触局部帧、原生句柄版本 |
| GripSession | GripId、手、目标组件/骨骼、抓取点 ID、状态、局部接触帧、拓扑版本、权威状态 |
| GripProfile | 固定策略、是否允许滑动、摩擦/握力、法向脱离阈值、恢复/释放条件、双手权限 |
| GripSurfaceDefinition | Plane/Cylinder/Rail/CollisionPatch、局部坐标、边界、可滑方向、曲面延续规则 |
| HandDriveProfile | 跟随强度/阻尼/最大力、角驱动、CCD、Profile 切换时间 |
| AvatarDefinition | Mesh、PhysicsAsset、AnimBP/Rig、骨骼与刚体映射、追踪偏移、手掌代理参数 |
| VRRuntimeProfile | 运行模式、物理频率预算、碰撞设置、平台配置、网络配置 |

纯 C# 内部状态可用小型 record struct、枚举和普通类型；需要 Unreal 序列化/Blueprint/RPC 的边界使用生成器支持的 USTRUCT/UCLASS。不要把内部接口、任意泛型或托管事件直接标成反射 API。

## 7. 追踪空间、身体与帧顺序

### 7.1 三种状态必须分开

- 原始设备姿态：OpenXR 的本地追踪值或 PC 的虚拟设备值。
- 游戏内目标：TrackingSpace、校准偏移和移动命令转换出的期望姿态。
- 实际物理状态：Chaos 解算出的掌心、身体和物体位置。

头部相机使用 HMD 呈现路径，物理头部尝试追踪它；不让布娃娃抖动直接摇晃 HMD 相机。头部遮挡通过已有思路扩展淡出/视线限制，物理身体仍处理碰撞。

TrackingSpace 保存可控的世界变换，包含移动、转向与重定位；原始设备局部姿态不从实际物理手反推。避免身体每移动一点就把它重新解释为现实房间移动。

### 7.2 物理根选择

先用物理 Capsule 做手腕/手臂传力原型。Quinn 全身阶段优先让骨盆成为完整人体的动力学参考；Pawn 的 Scene 包装根仅汇报骨盆结果，不执行第二次运动。

若保留 Capsule，它必须是同一个受力模型中的代理，明确是否承重；全身骨盆和 Capsule 不能各自被世界位置目标独立钉住，也不能重复碰撞/质量。

站立、移动和蹲伏由目标姿态、有限强度根驱动及地面支撑辅助产生。纯物理不排斥姿态生成和地面状态判断，但所有实际位移应由求解器执行。移动中的法向支撑、空气中骨盆自由度、落地、站台与坐姿应分别有 Profile。

### 7.3 帧顺序

1. 采样输入及追踪，生成一个带时间戳的目标帧。
2. 更新目标姿势、接触几何与允许提交的拓扑事务。
3. PrePhysics 设置约束帧、目标及参数；避免 Actor Tick 和 Hand Tick 分别写相同目标。
4. Chaos 子步解算。原生焊接要求游戏线程，不在物理回调中直接触碰 UObjects 或调用 Weld。
5. PostPhysics 收集负载、接触和实际速度；形成下一轮状态决策。
6. 视觉/手指贴合消费稳定快照，对外派发状态变化事件和网络数据。

先核对引擎更新组与动画目标更新顺序，不能只把所有 Tick 设置为 PrePhysics 就认为同步完成。必要的子步输入/历史回放通过薄原生层处理。

物理手和持有物不放在控制器渲染 Late Update 的附加列表中，避免渲染侧把它们拉离接触结果。HMD 相机保留标准 XR 路径。

## 8. 固定抓取、拓扑和自然释放

### 8.1 抓取提交

候选结果包括组件、骨骼、点、法线和 SurfaceId。优先级根据有效抓取区域、手掌到接触点距离、姿态容差、权限与已持有状态计算，不用 Actor 原点距离代替接触点距离。

流程：候选 → 请求验证 → 接近/对齐 → 达到容差 → 提交拓扑 → 发布 GrabStarted。

接近时以原生 Drive 收拢手；大位移超容差时拒绝或继续接近，不瞬移手穿过障碍。UI 操作、触觉和高亮独立订阅结果。

### 8.2 动态固定握持

在拓扑事务中记录掌心世界帧、目标局部帧、线/角速度、碰撞状态、手腕和跟手连接；结束旧连接，Weld，重新解析合并根，再绑定连接。任何失败都回滚为有效的独立掌心状态。

第一次原型必须证明 Drive 在 Weld 后仍能通过接触位置正确施力和施加力矩，否则停止扩展双手，不把“调用 Attach 返回成功”当作通过。

### 8.3 静态/机械物

静态世界：建立明确静态接触锚点，手腕与世界的连接承担身体受力。动态机械件：手绑定到活动刚体；门自身铰链、抽屉滑轨仍存在，不能把门焊死到世界。

抓取点是否允许滑动由物体 Profile 决定。例如光滑杆允许轴向滑动，工具握把默认高摩擦，带挡边把手通过表面边界限制滑脱。

### 8.4 双手

每只手有独立 GripSession，物体维护握持集合与拓扑版本。左手滑动时右手可保持固定；释放一只手只更新相关连接。

两手不要各自把物体变换拉向自己的绝对目标；对同一合并体作用于各自握点。冲突由有限力驱动、握持负载与 Profile 仲裁解决。双人同抓首个多人版本默认拒绝第二个玩家，后续单独实现协同搬运。

### 8.5 释放速度

释放不额外生成投掷冲量。物体已有线/角速度继续模拟。拆焊后如引擎未正确恢复手代理的速度，可按刚体点速度恢复：`v(point) = v(COM) + ω × (point - COM)`，它是拓扑拆分的连续性修复，不是根据设备历史增强投掷。

必须验证质量/惯性改变与拆分前后的动量；不得给所有拆分体简单赋相同质心线速度，不得给静态物体意外打开物理模拟。

## 9. 新功能一：沿抓取表面的滑动抓取

### 9.1 预期表现

玩家抓住光滑平面或杆，法向仍保留握持关系，手可沿切向滑动；阻力来自握力、表面参数和原生 Drive 的有限摩擦近似。手到边缘、失去表面或法向被拉开后才脱手。

接触几何、实际 PalmBody、视觉掌心与手指贴合使用同一个接触帧。不能只滑动画网格，实际物理握点还停在原处。

### 9.2 首版原生约束方案

平面定义局部正交帧 `(t1, t2, n)`：

- 法向轴锁定或在接触厚度内限位，保持掌心接触偏移。
- 两个切向轴允许运动，移除把它们拉回最初抓取点的位置 Drive。
- 切向启用目标相对速度为零的有限力 Velocity Drive，提供滑动阻力。
- 姿态用有限角驱动贴合法线；是否允许绕法线旋转由 Profile 决定。
- 保留手到追踪目标的跟随驱动和手到身体的手腕连接，但各自职责不同。

这不是 UE 自动提供的精确库仑摩擦：限力速度 Drive 是可调的摩擦近似；C# 负责接触几何、静止/滑动状态与参数，Chaos 负责求解。若测试表明近似不满足需求，再评估原生接触摩擦/定制约束，不能未经验证就承诺真实摩擦完全还原。

### 9.3 摩擦与握力

GripProfile 暴露：`StaticGripCapacity`、`DynamicFriction`、`GripStrength`、`NormalRetentionLimit`、`MaxSlideSpeed`、允许方向、边缘行为及恢复条件。

以 Grip 模拟量调节握力；PC 按住鼠标默认握力 1，可在调试工具中改变。静止阈值大于滑动摩擦阈值，提供迟滞。

如果用 `μN` 调节切向限力，N 必须定义为可信的压紧/握持能力，区分接触压缩与法向拉脱；不能把锁定法向约束的任意反力（包括拉力）直接当成夹紧力。初版可使用明确配置的夹紧力上限和实测负载标定。

`GetConstraintForce` 的来源、坐标系、峰值稳定性必须原型验证；不能把两个驱动的绝对力简单相加，重复计算同一负载。

### 9.4 曲面与边界

第一版只保证可配置平面和杆/圆柱：

- Plane：表面局部参数和边界，始终跟随物体变换。
- Cylinder/Rail：优先轴向滑动；环向是否允许由 Profile 控制；接触法线随参数更新。
- CollisionPatch：后续用局部 Sweep/投影重建连续接触，不保证任意复杂网格一开始都支持。

每一步滑动后的接触必须留在相同有效组件/表面邻域；禁止跳到物体背面或附近另一个零件。曲面不能永远沿第一次命中的无限切平面移动。

`GetClosestPointOnCollision` 可作为简单碰撞的辅助，但它不能替代所有曲面连续性和法线求解。复杂碰撞失败、尖角、无效法线、缩放异常要有清晰失败策略。

边缘默认滑出并释放；带挡边的抓取区域可限位；法向离开则按拉脱阈值释放，不能沿切面把手无限拉回。

## 10. 新功能二：超距、高速与握持退化

“玩家与抓取物体速度插值较大”在本计划中按“速度差较大”解释。速度平滑只用于抗追踪噪声，不作为发生滑动的物理原因。

### 10.1 判据

同时观察：

- 跟随误差：期望掌心位置与实际掌心的距离。
- 身体可达性：肩部到掌心，结合校准臂长；不使用手到 Pawn 原点的单一球半径。
- 期望手部目标点速度与物体接触点速度的差。
- 玩家物理根相对物体的速度，作为身体运动/悬挂场景的辅助判据。
- 切向负载、法向拉脱负载、有效接触、握力及超限持续时间。

固定 Weld 中手与物体接触点的实际速度相同，因此 `ActualHandVelocity - ObjectPointVelocity` 无法预测滑脱。

对象接触点速度包含角速度：`v_object(p) = v_COM + ω × (p - COM)`。否则旋转长杆端部会被当成静止。

目标点速度包含 TrackingSpace 自身平移/转向与设备运动，统一同一时间、同一世界参考系。传送、Snap Turn、Recenter、网络硬校正通过 OriginEpoch 标记跳变，不能将这类不连续变换求导成超高速。

### 10.2 状态机

```text
Idle → Candidate → Aligning → FixedGrip
                              ↓ 超距/切向负载持续超过能力
                           SlidingGrip
                            ↙        ↘
              低速低负载且握力足够     边缘/法向拉脱/表面失效
                      ReStick             Releasing → Idle
                         ↓
                      FixedGrip
```

`FixedGrip → SlidingGrip` 条件必须允许滑动、存在切向自由度、接触有效，并且持续负载或目标速度差已超过配置阈值。

滑动解除固定 Weld，恢复独立 PalmBody 的连续速度，建立切向可动约束。整个切换在物理步之间提交，不能留下一个无连接的游戏帧，也不能同时存在固定 Weld 和滑动约束。

恢复时基于当前接触点重新固定，不吸回最初抓取点。恢复要求低速、低负载、足够握力和驻留时间。

### 10.3 释放边界

以下情况可直接释放：玩家主动松手、目标销毁/卸载、状态无效、追踪失效超过宽限、不可滑物体持续超载、法向拉脱超过上限、硬可达距离严重超限。

沿表面滑动无法解决纯法向拉开或人体明显越过硬关节限制；这类场景仍需释放，不能为了“先滑”强行制造不存在的切向路径。

增加滞回与最短状态驻留时间，避免同一阈值附近每帧拆焊。进入和退出阈值、速度滤波时常、硬距离、宽限时间由 Profile 配置并实测标定。

## 11. 新功能三：没有 VR 设备时的 PC 双手模拟

### 11.1 提供者

InputRouter 接收 OpenXRTrackingProvider、DesktopTrackingProvider 或 RemoteTrackingProvider 的统一 TrackingFrame。AvatarMode 与 TrackingMode 是两个独立设置。

启动使用 Auto：只有本地 XR 会话有效且启用时选择 VR；否则 PC。支持显式强制 PC 以便有头显连接但普通窗口运行。远端角色模式由复制状态决定，服务器不读取本机 HMD 来判断所有玩家。

短时设备追踪丢失进入恢复策略，不立即反复切换 PC/VR。运行中模式转换走一笔事务：暂停请求、处理现有握持、重新校准、重置目标速度历史、更换 Mapping Context、恢复。

### 11.2 首版操作

| 输入 | 操作 |
|---|---|
| WASD | 请求物理身体移动 |
| 鼠标移动 | Yaw/Pitch 视角，Pitch 限位 |
| 鼠标左键按住/松开 | 左手 Grip / Release |
| 鼠标右键按住/松开 | 右手 Grip / Release |
| Q / E | 左/右手 Use 或 Trigger，初版可重映射 |
| Ctrl | 蹲伏目标 |
| Space | 物理跳跃请求；不在手部处理 |
| Esc | 菜单及输入焦点切换 |
| 可选滚轮/修饰键 | 虚拟手伸距、选手调试，不影响默认双手屏幕跟随 |

按你的要求，默认左右键分别控制左右手，不套用传统 FPS 的“左键开火、右键瞄准”。

两只期望手位置设在相机视野下方左右，使用相机朝向和可配置手腕旋转偏移生成；只更新运动学目标，不直接把物理手 Attach 到 Camera。手在碰撞或抓取后可以滞后，屏幕上的目标仍继续跟随视角。

默认近距离掌心抓取，不从屏幕中心无条件远距拿物。没有候选时按键不开始抓取；UI 获得焦点时不把同一次鼠标事件也交给物体。

### 11.3 验收用途

从第一阶段开始用 PC 模式验证相同抓取状态机、左右手独立操作、双手持物、滑动和多人。可加固定轨迹/受控速度调试提供者复现高速条件，避免每次戴头显靠手动重复。

PC 模式便于自动回归，但 VR 跟手、头部舒适性和设备丢追踪仍须实际设备验证。

## 12. 新功能四：Quinn 全身物理 Avatar

### 12.1 资产

将“UE 默认女性机器人”作为 Quinn。项目当前的 QuinnXR left/right 是手部资产，不是完整 Quinn。

本机 UE 5.7 中可见完整模板资产：

`D:/Program Files/Epic Games/UE_5.7/Templates/TemplateResources/High/Characters/Content/Mannequins/Meshes/SKM_Quinn_Simple.uasset`

正式实施时通过编辑器/内容迁移建立插件内自有引用，迁移对应 skeleton、material、texture 与相关动画依赖；不要让运行时读取引擎安装目录。为 VR 驱动新建并调校 PhysicsAsset，不能假定模板普通 Ragdoll 参数直接合适。

建议资产：`DA_Avatar_Quinn`、`PA_QuinnVR`、`ABP_QuinnVR_Target`、`CR_QuinnVR_Target`、手掌与手指接触 Profile。这里只规定规划名称，本次不创建资产。

### 12.2 物理结构

第一步建立骨盆、胸腔、头、双上臂、双前臂和两个 PalmBody；第二步加入腿、脚、落地支撑和移动姿态。主动力学骨骼使用真实关节，不能把整个人焊成一个刚体。

目标姿势来自 HMD 和双手，腰脚使用姿态/地面估计，未来再接受可选追踪器。它是姿态目标，不是实际身体的最终 Transform。实际渲染主体来自物理结果，手指小骨骼可以由接触动画驱动。

手臂必须有有限力父子空间驱动，地面/身体根驱动不得抹掉手拉身体的反应。抓静态杆时验证身体离地，松手由重力落下；抓光滑杆时验证沿杆下滑。

### 12.3 姿态与碰撞

- 骨骼映射、眼睛到头骨偏移、左右手腕偏移显式配置；不要沿用旧插件固定 90 度偏移。
- 物理结果与目标骨架分开，避免 AnimBP 后写目标把物理结果覆盖。
- PalmBody 接管手掌碰撞时，禁用重复手掌/手腕碰撞体，并避免与自己的前臂持续碰撞。
- 身体相邻骨骼的自碰撞按 PhysicsAsset 配置；保留有价值的身体与环境碰撞。
- 本地头部可通过专用材质/网格可见性方案隐藏；不假定 Quinn 材质必有 `HeadOpacity`。
- 身高校准优先调整目标和映射，非均匀缩放物理骨架必须专项验证。

### 12.4 自动手指贴合

每指每节 Probe 沿 curl 路径查询；由输入/Socket Pose 提供最大弯曲目标，由接触深度限制实际 curl。滑动时重新求接触，接触离开后允许恢复，不能永久冻结第一次碰撞的手型。

OpenXR 手部追踪是可选输入源；真实手指追踪与抓取表面贴合是两项不同能力。

### 12.5 安全降级

加载前验证 Mesh、骨骼索引、PhysicsAsset 关键刚体、AnimBP/Rig 类型、左右手端点和必要材质设置。失败给出缺项清单，保留 HandsOnly 有效路径。降级要同步清理旧连接、重复碰撞和网络状态。

## 13. 事件与外部 API

保留用户想要的静态分类入口：

```text
VRGameplayEvents
  Lifecycle / Input / Tracking / Hand / Grip / Body /
  Physics / Avatar / Interaction / Inventory / Network
```

静态门面路由到 World/RuntimeContext 范围事件流，不用一个无限生存的全局列表混合所有 PIE 世界。

重要事件：候选进入/离开、抓取请求/拒绝/开始、滑动开始/停止/重固定、释放及原因、双手集合变化、接触/负载阈值、追踪失效/恢复、模式切换、Avatar 加载/失败、权威确认/纠正。

事件数据包含 WorldId、PawnId、HandId、GripId、目标引用、接触帧、原因、时间/帧号、预测/权威阶段、拓扑版本。不可变数据不等于 UObject 永远有效；异步订阅者仍须检查生命周期。

订阅返回 IDisposable，在 EndPlay/退出 PIE/重生时统一解除。物理子步不直接执行任意用户回调；在游戏线程的稳定状态后派发。处理回调中销毁对象、重入抓放、跨 World 订阅等情况。

可取消的抓取许可使用明确的请求验证接口；普通“Before”广播不承担隐式取消语义。C# 事件与 Blueprint 动态委托分开适配，避免以为 `public event` 自动出现在蓝图。

extension block 或传统 extension method 提供 `hand.OnGripStarted(...)` 等门面；事件实际存储在运行时上下文。C# 14 的 extension 文档列举方法、属性和运算符，不能据此向已有类型直接添加实例 event。[Microsoft 扩展成员文档](https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/classes-and-structs/extension-methods)

SDK、LangVersion、Source Generator、托管 Host 与目标框架都通过验证后再用新语法；不为事件 API 先强制升级整个运行时。当前 net9/SDK9 基线先用传统扩展方法即可。

## 14. 网络：先完成可信闭环，再扩大预测

### 14.1 初期契约

- 输入帧包含 OriginEpoch、序号、时间、局部目标与握力；移动命令也必须传给服务器。
- 抓取请求通过拥有该 Pawn 的对象发给服务器，不让客户端直接 RPC 到尚未拥有的可抓物体。
- 服务器验证距离/可达性、表面区域、目标有效性、手的状态和物体占用。
- 复制 GripId、对象/组件/骨骼标识、Fixed/Sliding 状态、局部接触帧、表面参数、拓扑版本和释放原因。
- 状态复制保证晚加入/重新相关时能重建，不依赖此前收到过某次 Multicast。
- 抓取点/模式/拓扑是权威状态，视觉平滑与权威物理变更分开。
- 超距/滑动判断在服务器使用相同语义，远端不能仅用稀疏包间差分自行决定掉落。

固定对象抓取可本地预测表现，但首版不能承诺完全低延迟的物理 Pawn 预测。PC/VR 与身体复制统一，远端需要可见的手接触与主要身体姿态；只复制 HMD/控制器不能恢复每个碰撞后的身体骨骼结果。

首版可对远端采用主要骨骼物理快照插值与低成本姿态重建，服务器保持真实物理身体；这是表现侧策略，不改变本地玩家的物理目标。

### 14.2 原生预测边界

UE 5.7 官方 Networked Physics 文档区分 Predictive Interpolation 与 Resimulation，并明确低层 Network Physics Component 的历史/输入/状态需要 C++ 实现。[UE 5.7 网络物理](https://dev.epicgames.com/documentation/en-us/unreal-engine/networked-physics-overview?application_version=5.7)

因此旧计划“只有极少私有接口才可能需要 C++”不够完整。若目标要求完整物理 Pawn 输入回放与预测，薄原生网络适配也属于必要边界。

先验收服务器权威 + 远端平滑，再评估 Pawn Resimulation；道具可评估 Predictive Interpolation。Weld/Unweld 会改变拓扑，不能假定现成回放会自动恢复：必须记录拓扑事件或以版本作为不能跨越的校正边界。未验证时不在预测历史中做任意动态焊接。

不让各客户端独立模拟后期待 Chaos 结果完全一致，也不同时让手预测和 ReplicateMovement 每帧覆盖同一刚体。

### 14.3 薄原生层准入

只有已证明现有 Glue 无法完成的功能才进入原生桥接：Weld 后端点重绑定/骨骼句柄、物理子步输入与快照、Network Physics 回放适配。业务状态机、几何抓取、事件、输入和玩法仍由 C# 负责。

平台首先 Win64。当前 UnrealSharp 插件描述只列 Win64/Mac；HeadMountedVR 的 Android 支持不能当作新 C# Runtime 的 Quest 打包能力。Android/Quest 先完成独立托管运行时与打包能力验证，再进入承诺的功能支持范围。

## 15. HeadMountedVR 功能迁移矩阵

| 功能 | 新归属 | 优先级 / 说明 |
|---|---|---|
| OpenXR、设备与手指输入 | Input/Tracking | 核心第一批 |
| PC 非 VR 双手 | DesktopTrackingProvider | 核心第一批 |
| 房间尺度、校准、坐姿/蹲伏 | Tracking/Body | 核心 |
| 平滑移动、Snap/Smooth Turn、跳跃 | Locomotion/Body | 核心；实际运动由物理驱动 |
| Blink/Shift Teleport | Locomotion | 明确释放/携带策略与 OriginEpoch |
| 物理手、碰撞、自动贴合 | Hands/Physics | 核心 |
| 近表面、预设姿态、Socket、组件抓取 | Grip | 核心 |
| Plane/Cylinder/Rail 与滑动 | GripSurface | 核心；Circle/Points 随迁移完善 |
| 双手、优先级、单手限制 | Grip | 核心 |
| 拉取抓取 | Grip 扩展 | 核心稳定后；独立开启，不能伪装自然投掷 |
| 攀爬与投掷 | Body/Grip 的受力结果 | 作为验收场景；不迁移旧移动算法 |
| Quinn 全身 / HandsOnly | Avatar/Body | 核心 |
| 自定义 Avatar | AvatarDefinition + 校验 | Quinn 通过后验证第二套骨架 |
| 门/抽屉/按钮/杠杆/阀门/密码锁 | Interaction | 通用机械组件 + 少量玩法 |
| 手腕库存/容器/插槽 | Gameplay.Inventory | 核心多人闭环之后 |
| 装备、枪械、弹匣、弹药、近战、投射物 | Gameplay.Weapons | 订阅 Use 契约，不直接访问内部手状态 |
| 腕部菜单/屏幕提示/WidgetInteraction | Gameplay.UI | 与输入焦点、握持状态协作 |
| 偏好/库存跨关卡/加载流程 | Gameplay.Save/Loading | 保存高层物品与配置，重新构建瞬态约束 |
| 相机防穿/触觉/声音 | Tracking + 事件订阅 | 身体核心后完善 |
| 语音/健康/体力 | 可选 Gameplay | 不纳入手或 Pawn 物理核心 |
| 编辑器抓取区域可视化 | Editor 工具 | Runtime 数据稳定后，独立于打包运行时 |
| 实验 OpenXR HMD 替换、私有形状焊接 | 不逐类搬运 | 优先公开引擎 API；缺口经验证再桥接 |

旧 BP 的 C++ 父类不会因类名相同自动变成新 C# 类型。迁移以新模板 Actor/组件、配置数据转换和逐场景对照为主。旧 Demo 保留到新地图覆盖其行为。

## 16. 实施顺序与通过条件

### P0：基线与高风险能力原型

- 建立可恢复的版本基线；当前根目录不是 Git 仓库，正式实施前先落实源码与二进制资产备份。
- 固定 UE5.7、实际 UnrealSharp-main、SDK9 基线，建立最小 BlueprintCallable 签名样例。
- 验证：原生 Drive 独立掌心；动态 Weld 后 Drive 和手腕重绑定；静态锚点；拆焊速度连续；一只手到胸/根的传力；平面滑动约束。
- 每个原型单独记录支持的组件/骨骼类型和调用限制。

通过条件：没有大物体瞬移、无效约束句柄或明显爆飞；固定、滑动、松手均有有效物理链。未通过时只增加最小桥接或调整掌心表示，不继续堆完整 Avatar/玩法。

### P1：输入、坐标与生命周期

- 建 RuntimeContext、InputRouter、TrackingFrame、GripId/OriginEpoch 与事件契约。
- PC/VR/Remote 三个提供者，PC 左右键双手操作立即可用。
- 统一本地 Controller 绑定与 EndPlay 清理；模式转换只在状态改变时发生。

通过条件：普通窗口无头显可运行；两只手目标随视角；双客户端不会互绑输入；Recenter/SnapTurn 不制造滑脱速度峰值。

### P2：物理根、手臂与固定握持

- 原生跟手 Drive、有限力关节姿态、静态握持及支撑 Profile。
- GripSession、候选过滤、容差提交、双手拓扑和安全释放。
- 保留旧 Blueprint 的适配入口，移除新路径中的自写弹簧和重复反作用力。

通过条件：轻物跟手，重物有阻力；手和物体接触关系稳定；左右任意释放顺序正确；抓静态物能带动根，松手由重力响应；道具自然抛出。

### P3：滑动与超距退化

- Plane、Cylinder/Rail、摩擦 Profile、切向/法向负载、速度与迟滞。
- Fixed → Sliding → ReStick/Release，接触边缘与事件。
- 调试可视化：目标/实际手、法线/切向、负载、速度差、状态原因、拓扑版本。

通过条件：高摩擦握持稳定，低摩擦持续滑动；共速高速不滑脱，相对切向高速会滑；纯法向拉脱可释放；曲面持续贴合；左右手状态独立；切换不额外增加物体速度。

### P4：Quinn 全身

- 迁移完整 Quinn 依赖，定义 PhysicsAsset、目标姿势和骨骼映射。
- 上半身先通，再腿脚/地面支撑/坐姿；全身与 HandsOnly 共享端点和抓取。
- 逐指贴合、滑动重新贴合、本地头部显示、Avatar 校验与降级。

通过条件：弯腰、伸手、抓重物、撞墙、悬挂、沿光滑杆滑落及落地稳定；视觉手与物理接触点一致；缺骨骼/错动画类可读降级。

### P5：核心多人闭环

- P1 已具备数据契约，本阶段接通服务器模拟、抓取确认、滑动状态与晚加入恢复。
- 先服务器权威和远端平滑，再通过原型决定完整物理预测与桥接范围。

通过条件：PC 与 VR 玩家可同场；单手/双手抓放与滑脱最终一致；第二玩家争抢按规则拒绝；目标销毁/断线/重连能清理；100ms RTT 与抖动下无重复 Grip 或悬空连接。

### P6：多数旧功能迁移

- 机械件 → 传送与拉取 → 库存/装备 → 枪械/近战 → UI/偏好/跨关卡加载。
- 每类交互依赖公开接口与事件，不把专用字段塞回 Hand 核心。
- 补充第二套 Avatar 映射和编辑器区域可视化。

通过条件：迁移矩阵逐项有场景、输入、事件和网络归属，旧 Sandbox 主要玩法可在新模板复现。

### P7：性能、打包与 Legacy 收尾

- Win64 开发/Shipping、PC/VR、Listen/独立服务器验证。
- 72/90/120Hz 性能与约束负载测量，远端物理/手指查询分级。
- Android/Quest 在托管能力验证通过后单独验收。
- 迁移完才淘汰旧路径；稳定后整理 README、API、资产依赖和迁移说明。

## 17. 验收矩阵与初始测量指标

以下是拟定验收目标，不是本次已经测得的性能。

| 场景 | 关键断言 |
|---|---|
| 空手、轻物、重物、推墙、狭缝 | Drive 限力，重量与碰撞有反馈，手不靠每帧瞬移贴合 |
| 单手与双手、左右任意释放顺序 | Grip 数、拓扑版本、碰撞恢复一致 |
| 固定握持 ↔ 滑动重复切换 | 无连接空窗，无连续高频重焊，无额外能量增长 |
| 两者共同高速平移/转动 | 相对速度小，不因绝对速度大误判滑脱 |
| 快速相对运动、旋转长杆末端 | 正确使用接触点角速度，切向先滑动 |
| 纯法向拉开、超臂长、表面消失 | 不制造无效滑动路径，明确释放原因 |
| 曲面/平面边缘、尖角 | 连续接触，不跳到背面或其他零件 |
| 身体悬挂、自然攀爬、松手落下 | 力经关节传递，无人工玩家位置搬动 |
| 松手投掷、带角速度拆焊 | 保持已有物理速度，无控制器历史增强投掷 |
| Recenter/传送/快速转向/追踪丢失 | Epoch 与恢复策略阻止假速度峰值 |
| 无头显普通窗口 | 双手跟随视角，左右键独立，UI 焦点不串操作 |
| Quinn/HandsOnly/错误 Avatar | 没有重复掌部碰撞，错误可读降级 |
| 晚加入/抢物/销毁/断线 | 服务器状态可重建，不能依赖旧 Multicast |
| PIE 重启/热重载/切图 | 无静态订阅泄漏、旧世界引用或孤立约束 |

建议记录：目标到实际掌心误差 RMS/P95、法向接触误差、最大约束力、物体能量变化、一次状态切换的速度跳变、每秒拓扑变更次数、物理/查询耗时及网络带宽。

初始可讨论目标：空手及轻物在慢速运动下掌心误差 P95 约 1–2cm；接触法向偏离约 0.5–1cm；固定/滑动转换的握点跳变不超过约 1cm。高速、重物和碰撞滞后不套用空手指标，而以 Profile 与体验验收。所有数值需 P0/P3 实测后冻结。

状态逻辑和坐标计算用小型确定性测试验证；真实 Weld、静态锚定、关节与速度连续性用 UE 场景测试，不能只用 mock 证明。网络用延迟/丢包/乱序场景。静态配置和简单样板不堆镜像实现测试。

## 18. 本轮产物与下一步

本轮完成对话归纳、两套源码关系确认、关键实现检查、引擎能力核对，以及这份详细计划。未改变游戏代码、碰撞配置或二进制资产，未做运行验证。

第一项实施工作应是 P0 的最小物理闭环：原生 Drive 的 PalmBody、动态固定握持、静态锚点、手腕重绑定、平面滑动和释放速度连续性。它同时回答旧对话里尚未验证的 Weld 假设，并直接决定 Quinn 全身、双手和网络应该建立在什么端点表示上。
