# 本地 UE 交接

## 每手抓取组件（cloud/per-hand-grab-component）

源码：Script/ManagedVRSharp/Core/VRSharpGrabbable.cs 的 GetGrabbedComponent；VRSharpHand.cs 的 PullHand 与 UpdateGrabAnimation。保留旧 GrabbedComponent 属性以兼容调用方，内部跟随和指尖反馈改用每手的登记组件。未修改资产。

本地操作：在 UE5.7 / UnrealSharp0.1 宿主生成 Glue 并编译；创建临时 Actor，添加一个 Grabbable 和两个独立简单碰撞 Primitive，位置分开、质量不同。沿用 VRSharpDemo 左右手及碰撞配置。左手抓 A、右手抓 B，分别移动控制器并观察对应组件及指尖接触。依次测试先释放左手、先释放右手、同手重复登记、抓取组件销毁后查询。

验收：每手查询返回自己的组件；未登记手与失效组件返回 null；释放一手不会使另一手改为使用已释放手的组件。现有单组件双手抓取行为应保持；在30/60/90/120Hz记录实际帧时间及接触表现。不同组件的物理装配行为不在此变更内重新定义。

状态：完整UE编译、蓝图、PIE、头显均未执行；上述为待执行步骤，不是验证结果。独立数学检查不能证明此字典/原生组件接入正确。PR #2 的释放销毁回归须另行验证，未自动纳入本分支。
