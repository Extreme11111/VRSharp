# 云端改动本地整合与 UE 验收（2026-11-07）

本次以 `cloud/desktop-test-pawn` 的 `3eff914` 为组合基线，合入独立的无效手指输入修复、移动输入防护和宿主碰撞预检。桌面组合分支已包含抓取准入、手/物体事件、按手组件查询、失效物体释放恢复、预设姿势和工具扳机功能。PR #3 的同类组件查询以组合版本实现为准，并保留 `GetGrabbedComponent(hand)` 兼容入口。

环境保持 UE 5.7.4、UnrealSharp 0.1、.NET 9。源码、生成绑定和完整宿主 C# 编译已在本机执行；未升级运行时。

## 已落地的 UE 资产

- `/VRSharp/Maps/VRSharpDesktopTest`：独立的无头显交互验收室，只有一个受控桌面 Pawn。关卡实例登记两件手电筒为检查点道具。
- `/VRSharp/Maps/VRSharpVRInteractionTest`：沿用现有 VR 玩家和 OpenXR 映射的头显验收室。此地图供人工 VR Preview 验收，不代表头显已测。
- `/VRSharp/Tests/BP_DesktopTestPawn`、桌面/VR 测试 GameMode、`BP_VRSharpFlashlight`。
- `IMC_VRSharpDesktop` 与 15 个桌面 Action；两个 XR Analog Trigger Action，分别接入现有左右手和 VRSharpInputContext。
- `DA_ToolGrip_Left/Right` 与 `BS_ToolGrip`：共享动画配置、左右手独立抓点、工具激活阈值。

原有 VRSharpLab 的场景、默认玩法和灯光配置未修改。工具仍使用一个 Grabbable 作为交互配置入口；两个 HandPose 表达左右手的空间抓点，不是额外业务控制器。

## 桌面操作

| 输入 | 行为 |
| --- | --- |
| WASD、Q/E | 自由飞行；本 Pawn 不用于台阶/物理移动验收 |
| 鼠标 | 视角；X/Y Scalar 均为 0.70，较初版 0.14 提高 5 倍；取消 Y 轴 Negate |
| 鼠标左/右键 | 分别按住左/右手抓取，松键释放该输入取得的抓握 |
| Tab | 切换用于手部移动/旋转的当前手 |
| I/K、L/J、U/O | 当前手前后、左右、上下 |
| R/F、T/G、Y/H | 当前手 yaw、pitch、roll |
| P | 当前手锁存抓放；中键保留共享按住抓取 |
| V/B | 左/右手独立扳机 |
| Shift | 当前手共享扳机 |
| Z/X/C | 当前空手的拇指/食指/三指闭合输入 |
| F5/F9 | 保存/恢复本次 PIE 检查点，包括已登记的两件道具 |

测试道具已移至出生点附近。F9 正常释放双手并复位登记的单刚体道具及其速度；不负责约束多刚体或任意游戏脚本状态。

## 专用动画播放

新增可选 `HandPose.PoseBlendSpace` 和预设中的同名引用。配置原生二维 BlendSpace，X 为扳机值、Y 为姿势进入/退出权重，均为 0..1：

| 采样坐标 | 动画 |
| --- | --- |
| (0,0)、(1,0) | 空手过渡姿势 |
| (0,1) | 握住姿势 |
| (1,1) | 按下姿势 |

`BS_ToolGrip` 使用现有手骨架的 Idle、Grasp、Close 序列第 0 帧。左右手共用骨架，左手沿用原网格镜像。抓握/预览时由 UE 原生 Single Node 实例求值；进入、保持、退出和扳机值来自现有手部生命周期。退出后恢复原手部 AnimBP，原有接触闭合与空手输入继续工作。没有配置 BlendSpace 的对象仍使用原路径。

该模式使用作者指定的空手采样作为过渡起点，不保存任意瞬时空手姿势快照；不要据此宣称任意姿势切换绝对无跳变。资产需使用当前手的同一 Skeleton。`GripAnimation` / `PressedAnimation` 保留供自定义 AnimBP 使用；默认示例通过 BlendSpace 播放，无需修改原 AnimBP 图。自定义骨架、兼容骨架重定向及打包运行仍需另行验收。

编辑器脚本修改 BlendSpace 的 sample_data 后，需打开原生 BlendSpace 编辑器重建采样三角化，再保存。仅写入 sample_data 不足以生成有效运行时采样数据。

## 本地验证与边界

完整宿主 `ManagedVRSharp.csproj` 编译通过（0 错误，保留 41 项警告）。Windows 可用 `Tools/cloud/run-checks.ps1`，覆盖四个 .NET 项目及八个托管/CLI 回归入口；源文件读取明确使用 UTF-8。

UE 原生检查共 93 项，结果在 `Docs/Validation/2026-11-07/`：

| 报告 | 项数 | 验证内容 |
| --- | ---: | --- |
| Cloud-Native | 47 | Enhanced Input 移动/停止、左右抓取、Palm 对齐、预设与扳机、释放/预览、准入、主手交接、销毁后重抓 |
| Cloud-Input-Checkpoint | 12 | 原生独立 Grip/Trigger 分发、切手后独立释放、F9 路由、道具与机位复位、清速 |
| Cloud-Components | 14 | 两手不同 Primitive、主手组件交接、双扳机和主手+支撑手规则 |
| Cloud-Pose-Playback | 12 | 左右手实际骨骼求值、半扳机插值、退出后原 AnimBP 恢复 |
| Cloud-Mouse | 8 | 两轴映射与 5 倍 Scalar、原生 yaw/pitch 方向、单一受控 Pawn 和场景道具登记 |

输入验收通过 UE Enhanced Input 注入执行，覆盖原生绑定和事件分发；不替代人工按键/焦点测试。抓取边界检查将目标放到隔离位置，并有部分同步 Tick；这不等同于长时间物理稳定性或真实头显手感验证。骨骼检查为避免窗口可见性影响，在测试实例上强制刷新骨骼，不修改正式手部的可见性 Tick 策略。

真实 Quest 3 / OpenXR 半按、运动、双手物理手感、完整台阶/不平地面通行、Lumen 闪烁、帧率预算和打包测试均未在本轮验收完成。

## 编辑器问题记录

首次使用 `-ExecutePythonScript` 启动会话后，UE 自动退出并在旧蓝图预览窗口的关闭阶段访问异常。改为普通编辑器会话，通过控制台 `py <脚本路径>` 恢复 MCP。

另一次尝试以通用 `EditorAssetLibrary.duplicate_asset` 复制正在使用的 World，再立即加载，触发 `World Memory Leaks` 断言。该操作未生成持久化 VR 地图；改用地图专用 `new_level_from_template`（内部以模板加载并另存地图），并将返回原地图放在独立 MCP 调用中。不要重复使用通用资产复制接口处理这些测试地图。

## 可复现工具

`Tools/UEAcceptance/` 保存了资产创建和原生验收脚本。现有 MCP 适配器要求脚本位于宿主 `Tools` 内，先将这个子目录复制到宿主 `Tools/UEAcceptance`，再用宿主 `Tools/editor_mcp.py` 调用；无需复制任何 DLL。

新宿主创建顺序：`setup_cloud_assets.py` → `build_cloud_test_map.py` → `finalize_cloud_test_room.py` → `setup_cloud_pose_clips.py` → `finalize_pose_blendspace.py` → 下一次 MCP 调用 `save_pose_blendspace.py`。需要 VR 变体时再运行 `build_cloud_vr_test_map.py`。地图创建脚本拒绝覆盖已有地图。原生测试需要先打开桌面验收图，通过 `start_cloud_pie.py` 开始 PIE，之后运行一项 `test_cloud_*.py`；该项测试完成后会自行退出 PIE。
