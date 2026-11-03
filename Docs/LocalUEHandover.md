# 抓放事件与状态 API 交接

分支 cloud/grab-events-state；UVRSharpGrabbable新增只读IsGrabbed、GrabCount，GetIsGrabbed/GetGrabCount蓝图查询，IsHeldBy/GetHeldComponent/GetGrabbingHands（快照）；TryGrabWith/ReleaseFrom/ReleaseAll提供C#调用入口。TryGrabWith仍遵守手附近的局部抓取检测，不是远距离强制吸取。

C#使用示例：
```csharp
grabbable.Grabbed += HandleGrabbed;
grabbable.Released += HandleReleased;
// 在EndPlay对应 -=，不要用无法解除的临时lambda。
void HandleGrabbed(AVRSharpHand hand, UVRSharpGrabbable item, UPrimitiveComponent component)
{
    // 此时item.IsGrabbed为true，登记状态已更新。
}
void HandleReleased(AVRSharpHand hand, UVRSharpGrabbable item, UPrimitiveComponent component)
{
    // hand已从登记移除；双手只放开一只时item仍可IsGrabbed。
}
// if (grabbable.TryGrabWith(hand)) ...
// grabbable.ReleaseFrom(hand); grabbable.ReleaseAll();
```

新事件为C#事件，不是蓝图动态委托；旧OnBefore/OnAfter事件和签名保留。Grabbed在Attach成功并完成登记后触发；Released在Detach和LIFO重附着完成后触发。不是动画完成事件，早于手侧旧OnAfter事件。相同手/组件重复Attach不重复发送，未登记Detach不发送。订阅者可读状态；不要从事件同步递归修改同一次抓握，复杂变更排至下一帧。异常按普通C#事件传播，未实现异常隔离。生命周期销毁清理未完成，不承诺销毁自动发Released。

本地UE5.7/UnrealSharp0.1完整编译并生成Glue。使用/VRSharp/Maps/VRSharpDemo测试副本，添加C#监听器，记录手/物/组件和事件时的状态；分别测试单手抓放、双手依次释放、重复Attach/Detach、原生Attach失败、近距离TryGrabWith成功与远距离失败、ReleaseAll回调期间持有者列表变化。首次抓取仅1次Grabbed，单手释放仅1次Released，失败动作不发送成功事件。核对AttachToComponent返回值绑定。蓝图仅查询状态，若需可绑定蓝图事件需后续动态委托适配。

完整UE编译、PIE、头显和上述事件回归均待执行。独立数学检查不覆盖这些原生调用。非VR控制器与特殊动画逻辑是后续主线，不能因这些API存在就标完成。合并时须与PR #3/#4同文件改动协调，不能直接覆盖其逻辑。
