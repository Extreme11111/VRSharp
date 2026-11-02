# UE 本地交接：Grabbable 抓取准入

分支 cloud/grabbable-admission；类 UVRSharpGrabbable / AVRSharpHand，源码 Script/ManagedVRSharp/Core/。

新增四个 BlueprintReadWrite/EditAnywhere 布尔值：DisableGrabbing、DisableLeftHand、DisableRightHand、SingleHandOnly。默认 false，保留旧资产允许左右手共同抓取的行为。准入用于目标筛选、Grab入口、回调后及Attach入口。运行时更改配置仅限制后续抓取，不强制释放已抓手；原有释放流程保留。释放行为配置、姿势混合、PC/OpenXR为后续功能，未在本轮实现。

本地步骤：UE5.7/UnrealSharp0.1宿主生成Glue并完整编译。打开 /VRSharp/Maps/VRSharpDemo 的测试副本，使用现有左右手和简单碰撞可抓Actor。检查Grabbable详情面板与蓝图读写四项属性；保存重开确认序列化。无需增加辅助组件或改输入映射。

验收矩阵：全false保持旧行为；DisableGrabbing拒绝左右手高亮/抓取；仅DisableLeftHand时右手可抓；仅DisableRightHand时左手可抓；两手均禁用时均不可抓。SingleHandOnly开启后第一手可抓、第二手不可抓，释放第一手后第二手可抓；同手重复准入不应被误拒。已抓取期间禁用仍应可正常释放。OnBeforeGrab中切换禁用或占用状态后不得继续Attach。测试前向射线拒绝目标后可继续找到球内其他允许目标。

状态：完整UE编译、PIE、头显均待执行。独立数学测试不覆盖本轮新增准入逻辑；不得把它们的通过视作该功能运行验证。关联PR创建后见对应PR标题。
