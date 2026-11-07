# VRSharpPlayer 自动 PC 模式

日常运行继续使用 `BP_VRSharpPlayer`，不需要切换 Pawn、GameMode 或关卡。默认 `ControlMode=Auto`：在 BeginPlay 检测头显已连接且 XR 已启用时走原 VR 初始化，否则启用 PC 模式。可在玩家默认值选择 `VirtualReality` 或 `Desktop`，用于明确覆盖自动选择。

模式在每次游戏开始时选定，不因短暂丢失头部追踪而切换，也不实现同一局游戏中的设备热插拔切换。接入/移除头显后重新开始游戏即可重新检测。

## 模块边界

- `VRSharpControlMode.cs`：启动模式策略，可脱离 UE 验证。
- `VRSharpDesktopInput.cs`：独立默认组件。管理键鼠绑定/解绑、PC 视角、相机局部的双手目标、模拟扳机与手指输入。不处理刚体跟随或地面移动算法。
- `VRSharpDesktopInputSettings.cs`：输入 DataAsset，集中配置 Mapping Context 和 Action，避免将大量 PC 输入属性塞入玩家。
- `VRSharpPlayer.cs`：选择模式、创建原有物理手、从当前模式取得跟随目标，继续执行共用的身体碰撞、颈部/头部约束、物理手驱动和地面移动。退出时释放并清理自己创建的手。

生产资产位于 `/VRSharp/Input/Desktop/`，默认组件的 Settings 指向 `DA_DesktopInput`。这些资产独立于原来的自由飞行测试 Pawn。`VRSharpDesktopTestPawn` 保留为历史验收工具；正式 PC 玩法由原玩家中的独立组件提供。

## 操作

WASD 使用原玩家的物理地面移动，鼠标控制视角；左右键分别按住左/右手抓取，松键释放该输入取得的抓握。双手位置相对相机计算，转动视角时跟随屏幕，继续使用现有弹簧与碰撞。

V/B 分别模拟左右扳机，Shift 操作当前手扳机，Tab 切换当前手。I/K、L/J、U/O 调整当前手位置；R/F、T/G、Y/H 调整手部旋转；Z/X/C 控制空手拇指/食指/三指；P 切换当前手锁存抓放。Q/E 调整模拟眼高（65–200 cm），用于蹲姿/身高测试，不是自由飞行。

鼠标输入沿用修正后的 0.70 Scalar，上下不反转。移动适配器将桌面输入的“前/右”转换为原玩家已有的 `X=右、Y=前` 契约，避免前进变成侧移。

PC 模式关闭 Camera 的 HMD Lock 和运动控制器 Tick，隐藏控制器调试网格。VR 分支保留原追踪目标、HMD Lock、控制器更新及 VR 动作绑定。

## 宿主配置

`DefaultInputComponentClass` 和 `DefaultPlayerInputClass` 需使用 Enhanced Input，示意见 `Examples/PlayerInput/DefaultInput.ini`。

本地原宿主把 `/VRSharp/Input/VRSharpInputContext` 放在了 `EnhancedInputDeveloperSettings.DefaultMappingContexts`，导致每种模式都会自动加载 VR 映射。已只移除这一条全局默认项；VR 模式仍由玩家原有初始化加入该映射，PC 组件只管理自己的 PC 映射。其他宿主默认映射保持不变。迁移时也应避免把 VRSharp 的模式专用映射全局添加。

PC 组件延迟到本地控制器及 EnhancedInputComponent 就绪后绑定；失去控制权时清零输入、释放输入持有的抓握并移除自己添加的映射，重新控制后可重新绑定。不会清除宿主其他输入上下文或移除宿主预先添加的同一 PC 上下文。

## 验证

完整宿主 C# 编译通过（0 错误，42 项警告），四个独立 .NET 项目及九个托管/CLI 入口通过。新增 12 个生产模式策略组合检查。

本次 UE 验证共 35 项，报告在 `Docs/Validation/2026-11-07/`：

- `Player-Desktop-Fallback`：23 项，原玩家自动 PC、映射隔离、物理身体保留、眼高与落地、WASD 轴向、视角方向与手目标跟随、独立抓放/扳机、失去控制权及重新绑定。
- `Player-VR-Initialization`：7 项，无头显环境中临时强制 VR 分支，检查 VR 映射、Camera Lock、控制器 Tick 和 PC 组件未绑定。测试结束恢复 Auto，未保存强制模式。
- `Player-Lab-Fallback`：5 项，在现有 VRSharpLab 中确认受控对象仍是原玩家，自动 PC、组件配置、物理身体和双手可用，未修改该地图的 Pawn 或 GameMode。

输入通过 UE 原生 Enhanced Input 注入，包含实际物理移动和跟随，但不替代人工键鼠焦点验证。VR 初始化检查不等同于 Quest 3 实机追踪、移动或手感验收。未测试设备热插拔切换、完整台阶通行、联网及打包。
