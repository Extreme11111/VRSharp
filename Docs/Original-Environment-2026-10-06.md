# 原版 VRSharp 环境基线 — 2026-10-06

## 工程与归档

- 当前工程：`D:\_Programming\Unreal\VRSharp2\VRSharp.uproject`。
- 来源：原 `D:\_Programming\Unreal\VRSharp` 整个工程，保留内部项目名 VRSharp。
- 已废弃的重写工程：`D:\_Programming\AI\废弃VRSharp重置\VRSharp2-20261006`。
- 归档包含 28,399 个文件，共 13,926,800,312 字节；隐藏文件、构建产物、资源、工具与历史诊断一并保留。
- 两份移动前清单位于归档根目录，已按相对路径、文件大小、目录逐项核对。原工程共 24,040 个文件/目录项目，移动后清单一致。
- 原 VRSharp 根目录因当前聊天工作区占用而保留为空目录。

## 环境

- Unreal Engine 5.7.4：`D:\Program Files\Epic Games\UE_5.7`。
- UnrealSharp 0.1：沿用原工程 `Plugins/UnrealSharp-main`，TargetFramework 为 net9.0。
- `Script/global.json` 实际选择 .NET SDK 9.0.310；.NET 9 运行时已安装。
- 编译工具：Visual Studio 2022 Community，MSVC 14.44.35222，Windows SDK 10.0.22621.0。
- 显式启用 UnrealSharp、VRSharp、EnhancedInput；保留原有 OpenXR 与 XRBase 等设置。
- 两个 C# 调试启动配置已指向迁移后的 VRSharp.uproject。

## 官网配置核对

文档：https://space-art.net/vrsharp/index.html 。HTTPS 证书名称不匹配，本次通过原 README 提供的 HTTP 地址读取正文和三张设置截图。
仓库：https://github.com/Extreme11111/VRSharp 。

- 碰撞通道保留原配置：3DWidget（1）、VRPlayer（2）、VRGrabCheck（3）、VRHand（4），以及 VRPlayer/VRHand 预设。
- 默认 Enhanced Input 上下文：`/VRSharp/Input/VRSharpInputContext`，Priority=0，立即添加，启用默认映射上下文。
- NearClipPlane=0.1。
- 启动地图和游戏地图：`/VRSharp/Maps/VRSharpDemo`。
- 活跃 OpenXR 运行时：Oculus，运行时清单存在。当前 UE 启动返回 XR_ERROR_RUNTIME_UNAVAILABLE，头显连接/Link 会话未在本次验证中建立；未修改系统运行时选择。

## 验证

- UE 工程文件重新生成成功。
- VRSharpEditor Win64 Development 原生构建成功。
- `dotnet build ManagedVRSharp/ManagedVRSharp.csproj --configuration Debug` 成功，21 个原有/生成代码警告，0 个错误。
- 编辑器中原版 C# 程序集正常加载；玩家、左右手、Grabbable 蓝图生成类有效。
- 原版演示地图已加载，场景中存在 BP_VRSharpPlayer。
- 22 条输入映射已读取；LeftAxis 使用 OculusTouch_Left_Thumbstick_2D。
- 未修改原版玩法 C# 代码或场景资产；原工程中已有的地图修改和 TestCS.cs 也保留。
- 未进行 Quest 3 实机或打包验证。

验证记录：

- `Saved/Tests/OriginalNativeBuild-20261006.log`
- `Saved/Tests/OriginalEnvironment-20261006.json`
- `Tools/verify_original_environment.py`：只读资产校验，普通启动无需执行。

## 后续操作入口

直接打开当前工程的 VRSharp.uproject。C# 主项目位于 `Script/ManagedVRSharp`，玩法源码位于 `Plugins/VRSharp/Script/ManagedVRSharp`。目录名虽然是 VRSharp2，工程和模块名仍是 VRSharp。

原生编译命令（PowerShell）：

```powershell
& 'D:\Program Files\Epic Games\UE_5.7\Engine\Build\BatchFiles\Build.bat' VRSharpEditor Win64 Development '-Project=D:\_Programming\Unreal\VRSharp2\VRSharp.uproject' -WaitMutex -NoHotReloadFromIDE
```

C# 编译验证：

```powershell
Set-Location -LiteralPath 'D:\_Programming\Unreal\VRSharp2\Script'
dotnet build '.\ManagedVRSharp\ManagedVRSharp.csproj' --configuration Debug
```

C# 热重载由原工程 UnrealSharp 管理，编译验证后不要手动复制 DLL。