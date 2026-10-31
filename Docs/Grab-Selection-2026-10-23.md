# 抓取目标判定修复（2026-10-23）

修改 VRSharpHand.cs。遵循原抓取球配置的手心朝向（-GrabSphere.UpVector），将优先射线改为从抓取球中心向前延伸一个抓取半径，避免后半段也作为“正前方”优先。只有射线命中了有效 Grabbable 才停止兜底检测；命中不可抓物体时继续在抓取球内寻找有效目标。

球内兜底使用原生 SphereOverlapComponents 获取重叠组件，然后通过 GetClosestPointOnCollision 获取手到真实碰撞表面的距离；不再使用 Actor 原点，也不再用静止球形 Sweep 的初始重叠 ImpactPoint 当距离依据。手在碰撞体内时距离按零处理，并为退化法线提供稳定方向。高亮和实际抓取共享筛选器、GrabSphere.WorldLocation 和半径范围验证。

GrabWithHitResult 也校验距离，按键入口 TryGrab 在按键当下重新查询，避免使用已经移远或销毁的高亮缓存。新增 RefreshGrabTarget / TryGrab 蓝图可调用入口。GrabWithGrabbable 保留函数签名，但重新查询指定对象并限制在局部抓取球范围，不再通过旧缓存或任意长度射线吸取远处物体。

复杂碰撞体若没有原生凸体最近点查询，使用限长的组件射线作后备，不把包围盒或 Actor 原点冒充表面。此后备不能保证找到任意凹形复杂网格的数学最近点；可交互物建议使用合适的简单/凸碰撞。

验证：C# 编译成功，UnrealSharp 热重载成功。通过 MCP PIE 运行左右手生产 RefreshGrabTarget / TryGrab 方法，18 项检查通过，包括前向优先、最近表面、射线命中非抓取物仍兜底、大物体原点远但表面近、远目标拒绝、后方不抢前向优先、手在碰撞体内、抓握前重新检测。左右手测试保留原有镜像/缩放，测试修改仅在 PIE；编辑器临时物体已清理，手蓝图已保存。没有头显实机验证。

原始报告 Saved/Tests/GrabSelection-20261023.json；脚本 Tools/test_grab_selection.py；源码备份 Saved/RepairBackup/GrabSelection-20261023/VRSharpHand.cs。
