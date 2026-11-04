# Continuous improvement / 持续推进

Repository: https://github.com/Extreme11111/VRSharp

Requested cadence: every two hours, cloud execution, Asia/Shanghai. The actual schedule and cloud permission validation must be confirmed by the task scheduler; this file is durable working context, not proof that a schedule exists.

## 每次运行

1. 从远端读取当前 main、已有改进 PR、CI 结果和最新人工反馈；先处理阻塞问题，避免同一任务重复开 PR。
2. 选一个可完成、可验证的小增量，写清问题、预期行为与验收依据，再实施。提交到主题分支并创建/更新 PR，更新本文件的进展记录。
3. 至少运行两个独立数学检查。涉及 UnrealSharp/蓝图/资源的修改还需相应的 UE 编译、PIE 或实机验证；没有工具时明确标记未验证，不能用模型推理冒充运行证据。
4. 仅在有实际改动、明确发现、失败或需要用户处理时报告；无变化时不重复发布进度。不要无限重试同一个权限问题。

## 优先级

- P0：不平地面/台阶的物理移动、手部跟随与抓取可用性。已有移动实现尚缺完整的真实通行验证，先补充可复现用例，避免盲目继续扩展。
- P1：抓取目标筛选、接触回弹、无效引用/切换目标/多人或多手状态一致性与回归测试。
- P2：单个 Grabbable 的配置化设计、预设姿势与扳机等动态姿势混合、PC 模拟和 OpenXR 输入兼容性。
- P3：性能测量、插件迁移/打包、可维护文档与示例。联网功能需明确权威端、所有权和同步边界后再做。

实验室的动态光照闪烁尚未解决。此前将局部灯改成硬阴影的方案已按用户要求撤回，不应在无人值守运行中反复应用同一方案或声称问题已解决。

## Cloud prerequisites

A cloud task does not inherit the local editor, Git Credential Manager login, generated Glue or headset. Its own environment must have repository read/write access, Git LFS, .NET 9 and appropriate network access. Permit the GitHub/LFS URLs in the published cloud environment's official network controls; never work around a denial by exporting local credentials. See [OpenAI cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments).

Run `bash Tools/cloud/check-environment.sh`. For LFS proof, download the repository's tracked assets and use `git lfs fsck`; upload permission requires an actual successful LFS upload in that same cloud identity, not just a successful GitHub API query. GitHub PR/contents access through a connector is not itself a Git/LFS credential.

## Validation available in this repository

`Tools/cloud/check-environment.sh` checks the checkout, tools and local LFS objects. `Tools/cloud/run-checks.sh` runs production-linked standalone math checks. GitHub Actions runs those checks on pull requests and main commits, with an LFS-enabled checkout. It is validation infrastructure, not the two-hour AI work scheduler.

## Progress

- 2026-10-31: Added LFS tracking, cloud environment checks, CI and durable unattended-work guidance. Cloud scheduling/identity tests must be recorded separately when completed.

- 2026-10-31: Local authenticated Git/LFS upload passed (556 objects, about 114 MB). GitHub Actions run 41211244151 passed Linux LFS checkout and both .NET checks. Creating the requested Work Cloud task returned cloudflare_challenge twice; no task ID or two-hour schedule was created. Browser login showed no verification prompt. Do not mark the cloud schedule active until the service can create and read it back. A separate trusted-main Actions job probes its own branch/LFS upload/download permissions; this validates the Actions identity, not a future Codex/Work identity.

- 2026-10-31 verification update: GitHub Actions run 41211738115 succeeded, including cloud-repository-access (branch push, new LFS object upload, independent clone/download and byte comparison; probe branch removed). A separate fresh local clone also completed git lfs pull and git lfs fsck. A later Work Cloud creation request returned a queued client identifier, but no usable cloud conversation ID or schedule has been confirmed. This remains pending; Actions access does not prove the queued Work Cloud identity.

- 2026-11-03: Implemented opt-in authored finger weights on existing HandPose. Selected poses can supply fixed thumb/index/grasp targets with explicit ownership over contact correction until release; default disabled preserves old behavior. Both standalone math suites and added pose weight boundary tests passed at 31dc992. UE/Glue compilation, serialized defaults, animation and headset acceptance remain pending in Docs/LocalUEHandover.md. Does not implement trigger blending, alter naming selection or edit binary assets. Prior input PR CI green/no feedback; separate feature PR, no auto-merge.

- 2026-11-03：新增UseTriggerBlend与TriggerIndexWeight；在UseFingerWeights开启的抓握姿势中，SetGrabTrigger(value)把食指从基础IndexWeight混合至TriggerIndexWeight，0/1为端点、范围外钳制，非有限样本返回false并保持旧目标。释放后禁用；拇指/三指保持预设。该增量取代“扳机混合未实现”的历史描述。UE侧需将XR轴或PC滑条接入并在扳机松开时提交0，不自动修改旧TriggerAction。验收0/.5/1、反向端点、释放后拒绝、异常值保持、重新抓取回基础姿态。两个独立数学检查及新增混合边界检查在01e005c通过；完整UE/Glue编译、PIE和头显仍待验证，未合并。

- 2026-11-04: Added desktop test Pawn source (no XR session dependency): free-fly movement, mouse look, camera-local dual hand targets, per-hand physics tracking, active-hand selection, local grab/release, authored trigger drive and input reset. Stacked on authored pose branch to compose the real trigger path rather than use reflection or placeholders. Complete local Pawn/controller/map/input wiring in LocalUEHandover. Both math projects and authored pose/trigger boundary tests passed at fe3697e; these do not compile the new Unreal Pawn or validate input integration. Full UE build, PIE and interaction regression remain pending. This is source plus local wiring handoff, NOT a runtime-validated complete nonVR mode, and free-fly movement is not physics locomotion validation. No binary changes/auto-merge; session LFS upload remains unverified.

- 2026-11-04 桌面输入链路：Pawn新增六个可编辑动作引用DesktopMove/DesktopLook/DesktopHandMove/DesktopGrip/DesktopSwitchHand/DesktopTrigger；C# BindDesktopInput在EnhancedInputComponent可用后自动绑定一次，动作未全部赋值时不做部分绑定，重复调用同组件不重复注册。Move/Look/HandMove/Trigger使用Axis3D（Trigger取X、Look取XY），Grip/Switch使用Bool。Completed/Canceled显式归零移动/手移动/扳机并释放活动手。请在BP详情赋六个动作、PlayerController添加IMC，移除旧的手动动作事件→Pawn方法接线以免重复执行；不用再逐个蓝图连接事件。映射方向与前述键位一致，鼠标灵敏度放在输入Modifier。失焦/取消映射仍调用ResetDesktopInput。UE验收需测试开始/持续/Completed/Canceled、迟到的InputComponent、重复Bind调用、不完整配置、切换手与左右手抓放。数学检查不能证明绑定签名、source-generator或引擎事件路由，完整UE编译/PIE仍待执行。

- 2026-11-04 桌面抓握输入所有权：Grip Started成功时保存响应手和被抓对象，Completed/Canceled释放该次输入对应的手/对象，不随当前活动手切换；失败按下不登记，重复开始/结束幂等，已换抓其他对象时不误放。ResetDesktopInput也终止该次输入抓握（更新此前仅清轴值的说明）。显式ReleaseActiveHand仍作用于当前活动手。UE验收：左手按下→Tab切右手→松键仅放左手；右手已持物时不能被失败点击或旧按键释放；失焦Reset释放输入持有者、保留其他独立抓握。新增生产方法子集回归使用手/物体替身，不含UE事件路由/原生生命周期；完整UE编译、PIE仍待执行。


- 2026-11-04 特殊姿势动画链路：HandPose新增AnimationKey和DisableLeftHand/DisableRightHand（默认允许）；名称候选同时经过手别筛选。成功登记抓取后手保存GetActiveGrabPose、触发C# GrabPoseEntered(hand,pose)；Release清空状态/归零扳机并触发GrabPoseExited。旧抓放事件保留。SetGrabTrigger现在对任何有效活动姿势提供0..1 GetGrabPoseTrigger；启用UseTriggerBlend时额外驱动原食指目标，未启用时可只驱动专用动画。

本地动画接线：手的AnimBP使用Get Owning Actor→Cast AVRSharpHand，Event Blueprint Update Animation读取GetActiveGrabPose，IsValid后读取AnimationKey；无有效姿势则空字符串并回默认动画。新增专用Grab状态：条件AnimationKey等于例如ToolGrip，进入/退出用0.1秒过渡。Hold内将同Skeleton的ToolIdleGrip/ToolPressedGrip两个Sequence Player接Blend(float)，Alpha取GetGrabPoseTrigger；或用1D BlendSpace，轴0..1。最终与默认手动画按HasActivePose选择；只需静态姿势时Sequence Player保持对应帧。专用动画图自行决定是否使用Thumb/Index/GraspWeight，避免同时由两套图覆盖同骨骼。

Actor上分别放置Pose_Left/Pose_Right，设相同AnimationKey、不同掌心变换和相应禁止手别；Grabbable.GrabPoses的名称映射保留已有匹配方式。C#订阅GrabPoseEntered/Exited可启动/停止自定义动画逻辑，结束播放时仍以GetActiveGrabPose状态为准，EndPlay退订，失效姿势引用先IsValid。

验收：两手选中各自抓点；成功进入一次；持续抓握读取同姿势和0/.5/1扳机；释放退出并清状态；再次抓不同姿势不沿用旧动画；禁用对应手的姿势不参与选择。手别无匹配时回默认抓取。完整UE编译、动画资产/图、PIE、头显及这些生命周期用例尚未执行。PR8需顺序同步最新PR6再使用这些新增查询。当前不是宣称完整特殊动画系统已实测完成。

- 2026-11-04: Integrated latest authored-pose lifecycle/animation key/hand eligibility into desktop test branch; preserved desktop input/grip ownership changes and both handoff histories. This is a merge checkpoint on the topic branch, not a main merge or UE validation.

- 2026-11-03: Implemented contextual Grabbed/Released C# events at actual Grabbable attachment state transitions, read-only IsGrabbed/GrabCount and holder/component queries, holder snapshots, TryGrabWith/ReleaseFrom/ReleaseAll. Preserved old events/API. Attachment records only after native AttachToComponent reports success; duplicate same-hand attachment suppresses duplicate event. Concrete usage, ordering, limits and UE regression matrix in Docs/LocalUEHandover.md. Both independent mathematical suites passed at 595d783; these do not compile the changed native-facing component or validate event transitions. UE build/PIE/headset/event integration remain pending. Must reconcile with PR3/4 before integration, no main overwrite or merge. Binary assets untouched; session LFS upload remains unverified.

- 2026-11-04: Added CI-managed regression harness extracting production Attach/Detach and query/event declarations. With explicit native-call doubles, verified successful/failed registration, contextual event state/timing, duplicate suppression, dual-hand release with LIFO reattachment and holder snapshot isolation. Both standalone math suites and harness passed at 8ac6bc7. A transient connector disconnect initially omitted the script; confirmed 404, repaired file, reran successful checks. This compiles a managed method subset, NOT full gameplay or native physics; UE build/PIE/headset and native attach semantics remain pending. No new PR or merge.

- 2026-11-04: Integrated grab event/state API and managed event regressions into desktop+authored-pose branch. Preserved both test scripts and consolidated handoff into one checkout. Main unchanged; full UE integration still pending.

Validation of this combined tree: both math projects, authored pose/trigger boundaries, desktop grip ownership subset and Grabbable event/state subset passed. Subsets use native test doubles; no UE/PIE/headset proof is implied.

- 2026-11-03: Added Grabbable admission configuration: disable globally, disable either hand, single-hand-only. Zero defaults preserve legacy behavior; selection and attachment consult the same CanGrab predicate, with recheck after callbacks. No forced release when configuration changes. Concrete Blueprint/serialization and runtime acceptance in Docs/LocalUEHandover.md. Full UE build, PIE/headset and new admission-path runtime regression remain pending; math suites do not cover this path. Existing PR checks were green with no review comments. Separate feature branch avoids duplicating prior fixes; no auto-merge or binary edits.

- 2026-11-03 regression increment: Extracted engine-independent GrabAdmission policy used directly by Grabbable.CanGrab. Added standalone production-linked checks for all 192 flag/hand/ownership combinations plus release/reacquire sequence; added suite to run-checks.sh. Both math suites and the new admission suite passed with .NET9.0.320 on an isolated fetched branch checkout. LFS local fsck passed. This validates policy decisions only, not Unreal bindings, callback ordering, Blueprint serialization or real holder bookkeeping; UE/PIE/headset still pending. PR #4 previously green with no review feedback; continued same PR. Command-line LFS upload credentials remain unverified as before; no binary assets changed.

- 2026-11-03 follow-up: Grab now returns rejection to GrabWithHitResult/TryGrab instead of unconditional success. Revalidate grabbable and primitive between each before-grab callback; suppress successful completion if attachment did not register this hand. Runtime regression pending: disable/destroy target or primitive in either before-grab callback, expect false and no success callbacks; normal grab expects true. Full UE build/PIE/headset not run. Attempt to rerun standalone checks failed before process creation (exec-server: no such file or directory), so no new test pass is claimed. Previous PR CI was green, reviews/comments empty. Connector text write succeeded; this does not establish LFS upload authorization.

- 2026-11-03: Execution environment recovered by using an existing workspace path and a fresh isolated worktree. Both math suites and 192 admission policy cases passed against 9fd5774; these do not compile the Unreal hand callback code. Added CanGrab null/native-invalid hand rejection before reading IsLeft. This subsequent guard is source-reviewed only; UE runtime acceptance must call CanGrab with null and a destroyed hand and expect false without native access, then verify a valid hand still follows policy. UE build/PIE/headset remain pending. Local LFS fsck passed; upload authorization remains unproven. PR #4 CI green at inspection, no review feedback; no merge.

- 2026-11-04: Integrated admission configuration into desktop/pose/events branch; resolved native hand validity + policy guard together and retained pose entry only after successful registration. Updated event harness with explicit admission double to test rejection before registration; policy combinations are tested separately against production GrabAdmission. Full UE/PIE still pending.

Combined math, pose/trigger, desktop grip, event state and 192 admission policy checks all passed; native bindings and actual integration remain UE handoff work.

- 2026-11-04 手侧接口组：AVRSharpHand新增Grabbed/Released C#事件，签名同物体事件(hand,item,component)。Grabbable在实际Attach/Detach完成状态变更后先通知手、再通知物体；重复/失败动作仍不通知。GetCurrentGrabComponent提供蓝图/C#按手查询；弹簧与指尖反馈改为该查询，避免另一手先抓组件的共享缓存误用（覆盖PR3相同用途，不直接覆写旧分支）。C#可 hand.Grabbed += handler / hand.Released += handler，EndPlay配对退订；旧OnBefore/After API保留。不能在同步通知内递归抓放同一对象。UE组合验收：两手抓同Actor不同Primitive，事件回调读取手/物体状态应一致，分别驱动各自Primitive，释放一手不改变另一手查询，最后释放返回null。完整UE编译、PIE与原生组件生命周期仍待执行；隔离测试仅检查生产物体方法调用手通知桥接时的状态，不编译完整手类或实际物理。
