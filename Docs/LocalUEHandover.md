# Local UE handover / 本地 UE 交接

## 宿主碰撞配置预检（2026-11-06）

关联分支 `cloud/host-collision-preflight`。入口 `Tools/check_host_collision.py`，参考 `Examples/VRSharpLab/DefaultEngine.ini` 中的 CollisionProfile 段。

1. 将插件放入宿主 UE5.7 项目的 Plugins 目录，先运行 `python3 Tools/check_host_collision.py <宿主>/Config/DefaultEngine.ini`。如宿主有平台 Engine INI，按实际覆盖顺序将这些文件追加到命令行。退出码 0 表示所给文件的所需显式条目匹配，1 表示配置差异，2 表示输入不可读或无法解析。脚本只读，不合并或覆盖宿主配置。
2. 对照报告检查 Project Settings > Engine > Collision。保留宿主已有通道。若有槽位冲突，确认可用槽位后再手工选择迁移方案。调整槽位会影响已序列化的通道枚举，需逐一复核左右手蓝图的 `GrabObjectTypes`、玩家及头部碰撞、道具 Primitive 的 Object Type 与 Profile。参考手部类 `Script/ManagedVRSharp/Core/VRSharpHand.cs` 和玩家类 `VRSharpPlayer.cs`。
3. 在 UE 中打开 `/VRSharp/Maps/VRSharpDemo` 和 `/VRSharp/Maps/VRSharpLab`。PIE 验收普通物体的高亮、抓放和手指接触。头显验收手与自身玩家不互相阻挡、手碰环境、角色头部碰撞及移动。使用桌面测试分支时也跑一次相同抓放场景。

预检只比较传入的 INI 文件内显式声明的槽位、Trace/Object 类型、默认响应及所需 Profile 字段。不会自动查找引擎/插件配置层，也不求值 EditProfiles、重定向、运行时设置或蓝图里的序列化值。自定义重映射即使在宿主可用也会列为差异。已跑 CLI 回归和两个独立数学检查，未运行 UE 编译、PIE 或头显。
