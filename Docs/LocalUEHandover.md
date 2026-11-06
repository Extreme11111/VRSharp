# Local UE handover / 本地 UE 交接

## 宿主碰撞配置预检（2026-11-06）

关联 [PR #9](https://github.com/Extreme11111/VRSharp/pull/9) 和分支 `cloud/host-collision-preflight`。入口 `Tools/check_host_collision.py`，参考 `Examples/VRSharpLab/DefaultEngine.ini` 中的 CollisionProfile 段。

1. 将插件放入宿主 UE5.7 项目的 Plugins 目录，先运行 `python3 Tools/check_host_collision.py <宿主>/Config/DefaultEngine.ini`。如宿主有平台 Engine INI，按实际覆盖顺序将这些文件追加到命令行。退出码 0 表示所给文件的所需显式条目匹配，1 表示配置差异，2 表示输入不可读或无法解析。脚本只读，不合并或覆盖宿主配置。
2. 如有冲突，用相同文件顺序加 `--plan`。输出 `keep` 表示沿用宿主同名通道，`add` 表示新增。对照 Project Settings > Engine > Collision 核实空位，再将建议的 `+DefaultChannelResponses` 条目手工加入宿主对应 INI 的 CollisionProfile 段。重复定义或槽位不足时先解决报告中的问题。对照参考手工合并 `VRPlayer` 和 `VRHand` Profile，并用 `--allow-remapped-channels` 重新检查。预期退出码 0，宿主原有通道保留，所有 VRSharp 通道占用各自唯一的项目自定义槽位。
3. 重启编辑器加载配置。调整槽位会影响已序列化的通道枚举，需逐一复核左右手蓝图的 `GrabObjectTypes`、玩家及头部碰撞、道具 Primitive 的 Object Type 与 Profile。参考手部类 `Script/ManagedVRSharp/Core/VRSharpHand.cs` 和玩家类 `VRSharpPlayer.cs`。按通道名称重新选择并保存受影响的组件和蓝图。
4. 在 UE 中打开 `/VRSharp/Maps/VRSharpDemo` 和 `/VRSharp/Maps/VRSharpLab`。PIE 验收普通物体的高亮、抓放和手指接触。头显验收手与自身玩家不互相阻挡、手碰环境、角色头部碰撞及移动。使用桌面测试分支时也跑一次相同抓放场景。复测占用原槽位的宿主对象或射线，预期维持迁移前的碰撞响应。

预检只比较传入的 INI 文件内显式声明的槽位、Trace/Object 类型、默认响应及所需 Profile 字段。引擎和插件配置层须手工纳入，EditProfiles、重定向、运行时设置和蓝图序列化值须在编辑器中复核。`--plan` 仅分配槽位，通道语义与 Profile 以重新检查的结果为准。云端验证范围为 CLI 回归和两个独立数学检查。UE 编译、PIE 和头显实测待本地验收。
