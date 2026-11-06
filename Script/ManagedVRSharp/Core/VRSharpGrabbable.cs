using System.Collections.Generic;
using UnrealSharp;
using UnrealSharp.Attributes;
using UnrealSharp.Engine;

namespace VRSharp.Core;

[UClass]
public partial class UVRSharpGrabbable : UActorComponent
{
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UMaterial? HighlightMaterial { get; set; }
    private int highlightCount = 0;
    private bool isGrabbed = false;


    // 默认均为 false，旧资产保持允许双手抓取的行为。
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial bool DisableGrabbing { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial bool DisableLeftHand { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial bool DisableRightHand { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial bool SingleHandOnly { get; set; }

    // Require a hand-compatible HandPose explicitly bound to the contacted primitive.
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial bool RequireExplicitGrabPose { get; set; }

    // Applies to the last released primitive after unwelding the final hand.
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial bool DropWithoutMomentum { get; set; }

    public bool CanGrab(AVRSharpHand hand)
    {
        if (hand is null || !SystemLibrary.IsValid(hand)) return false;
        return GrabAdmission.Allows(DisableGrabbing, DisableLeftHand, DisableRightHand,
            SingleHandOnly, hand.IsLeft, hands.Count, hands.Contains(hand));
    }

    #region 抓握姿态

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial TMap<string, string> GrabPoses { get; set; }

    #endregion

    #region  抓握事件

    // A zero press threshold disables activation for existing assets.
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial float TriggerPressThreshold { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial float TriggerReleaseThreshold { get; set; }

    private readonly HashSet<AVRSharpHand> activeTriggerHands = new();
    public bool IsTriggerActive => activeTriggerHands.Count > 0;

    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool GetIsTriggerActive() => IsTriggerActive;

    public event Action<AVRSharpHand, UVRSharpGrabbable, UPrimitiveComponent, bool>? TriggerActivationChanged;

    public event Action<AVRSharpHand, UVRSharpGrabbable, UPrimitiveComponent, float>? GrabTriggerChanged;

    internal void NotifyGrabTrigger(AVRSharpHand hand, UPrimitiveComponent component, float value)
    {
        if (!float.IsFinite(value) || !IsHeldBy(hand) || GetHeldComponent(hand) != component) return;
        float press = TriggerPressThreshold;
        float release = TriggerReleaseThreshold;
        bool enabled = float.IsFinite(press) && float.IsFinite(release) &&
            press > 0 && press <= 1 && release >= 0 && release < press;
        bool active = enabled && (activeTriggerHands.Contains(hand) ? value > release : value >= press);
        SetTriggerHandActive(hand, component, active);
        GrabTriggerChanged?.Invoke(hand, this, component, value);
    }

    private void SetTriggerHandActive(AVRSharpHand hand, UPrimitiveComponent component, bool active)
    {
        bool wasActive = IsTriggerActive;
        if (active) activeTriggerHands.Add(hand);
        else activeTriggerHands.Remove(hand);
        if (wasActive != IsTriggerActive)
            TriggerActivationChanged?.Invoke(hand, this, component, IsTriggerActive);
    }

    public event Action<UVRSharpGrabbable?>? OnBeforeGrab;
    public event Action<UVRSharpGrabbable?>? OnAfterGrab;
    public event Action<UVRSharpGrabbable?>? OnBeforeRelease;
    public event Action<UVRSharpGrabbable?>? OnAfterRelease;
    public event Action<UVRSharpGrabbable?>? OnEnterHighlighted;
    public event Action<UVRSharpGrabbable?>? OnExitHighlighted;
    #endregion

    #region  事件调用

    public void CallOnBeforeGrab()
    {
        OnBeforeGrab?.Invoke(this);
    }
    public void CallOnAfterGrab()
    {
        OnAfterGrab?.Invoke(this);
    }
    public void CallOnBeforeRelease()
    {
        OnBeforeRelease?.Invoke(this);
    }
    public void CallOnAfterRelease()
    {
        OnAfterRelease?.Invoke(this);
    }
    public void CallOnEnterHighlighted()
    {
        OnEnterHighlighted?.Invoke(this);
    }
    public void CallOnExitHighlighted()
    {
        OnExitHighlighted?.Invoke(this);
    }
    #endregion

    // 抓握顺序列表：末尾是最后抓的（LIFO 栈顶）
    private readonly List<AVRSharpHand> hands = new();
    private readonly Dictionary<AVRSharpHand, UPrimitiveComponent> components = new();

    public UPrimitiveComponent? GrabbedComponent { get; private set; }
    public int GrabCount => hands.Count;
    public bool IsGrabbed => hands.Count != 0;
    public event Action<AVRSharpHand, UVRSharpGrabbable, UPrimitiveComponent>? Grabbed;
    public event Action<AVRSharpHand, UVRSharpGrabbable, UPrimitiveComponent>? Released;

    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool GetIsGrabbed() => IsGrabbed;
    [UFunction(FunctionFlags.BlueprintCallable)]
    public int GetGrabCount() => GrabCount;

    public bool IsHeldBy(AVRSharpHand hand) => hand is not null && components.ContainsKey(hand);
    public UPrimitiveComponent? GetHeldComponent(AVRSharpHand hand)
        => hand is not null && components.TryGetValue(hand, out var value) && SystemLibrary.IsValid(value) ? value : null;
    // Explicit snapshot: callers can enumerate safely while callbacks change holders.
    public AVRSharpHand[] GetGrabbingHands() => hands.ToArray();

    public bool TryGrabWith(AVRSharpHand hand)
    {
        if (hand is null || !SystemLibrary.IsValid(hand) || !SystemLibrary.IsValid(this)) return false;
        if (hand.IsGrabbing) return hand.GrabbedObject == this && IsHeldBy(hand);
        hand.GrabWithGrabbable(this, default);
        return hand.IsGrabbing && hand.GrabbedObject == this && IsHeldBy(hand);
    }

    public bool ReleaseFrom(AVRSharpHand hand)
    {
        if (hand is null || !SystemLibrary.IsValid(hand) || !IsHeldBy(hand) || hand.GrabbedObject != this) return false;
        hand.Release();
        return !IsHeldBy(hand);
    }

    public void ReleaseAll()
    {
        foreach (var hand in GetGrabbingHands()) ReleaseFrom(hand);
    }

    /// <summary>
    /// 获取 Owner 上所有的 UMeshComponent（包括 StaticMesh 和 SkeletalMesh）
    /// </summary>
    public IList<UMeshComponent> GetAllMeshComponents()
    {
        return Owner.GetComponentsByClass<UMeshComponent>();
    }

    public override void BeginPlay()
    {
        base.BeginPlay();
        if (HighlightMaterial is null)
            return;
        OnBeforeGrab += (grabbable) =>
        {
            isGrabbed = true;
            var mesh = GetAllMeshComponents();
            foreach (var m in mesh)
            {
                if (m.OverlayMaterial == HighlightMaterial)
                    m.OverlayMaterial = null;
            }
        };
        OnBeforeRelease += (grabbable) =>
        {
            isGrabbed = false;
        };
        OnEnterHighlighted += (grabbable) =>
        {
            highlightCount++;
            if (highlightCount == 1 || (highlightCount == 2 && isGrabbed))
            {
                var mesh = GetAllMeshComponents();
                foreach (var m in mesh)
                {
                    m.OverlayMaterial ??= HighlightMaterial;
                }
            }
        };
        OnExitHighlighted += (grabbable) =>
        {
            highlightCount--;
            if (highlightCount == 0 || (highlightCount == 1 && isGrabbed))
            {
                var mesh = GetAllMeshComponents();
                foreach (var m in mesh)
                {
                    if (m.OverlayMaterial == HighlightMaterial)
                        m.OverlayMaterial = null;
                }
            }
        };
    }

    /// <summary>
    /// 将 Hand 焊接到物体上，记录抓握顺序
    /// </summary>
    public void Attach(AVRSharpHand hand, UPrimitiveComponent component)
        => AttachWithPose(hand, component, null);

    private readonly Dictionary<AVRSharpHand, UVRSharpHandPose> heldPoses = new();

    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool IsGrabPoseOccupied(UVRSharpHandPose pose)
    {
        if (pose is null || !SystemLibrary.IsValid(pose)) return false;
        foreach (var entry in heldPoses)
        {
            if (entry.Value == pose && SystemLibrary.IsValid(entry.Key)) return true;
        }
        return false;
    }

    internal bool CanUseGrabPose(UVRSharpHandPose pose)
        => SystemLibrary.IsValid(pose) && (!pose.ExclusiveToOneHand || !IsGrabPoseOccupied(pose));

    internal void AttachWithPose(AVRSharpHand hand, UPrimitiveComponent component, UVRSharpHandPose? pose)
    {
        if (hand is null || !SystemLibrary.IsValid(hand) || component is null || !SystemLibrary.IsValid(component) || !CanGrab(hand))
            return;

        if (components.TryGetValue(hand, out var previous) && previous == component) return;
        if (hand.IsGrabbing && hand.GrabbedObject != this) return;
        if (pose is not null && !CanUseGrabPose(pose)) return;
        if (!hand.AttachToComponent(component, "", EAttachmentRule.KeepWorld, EAttachmentRule.KeepWorld, EAttachmentRule.KeepWorld, true)) return;
        GrabbedComponent ??= component;
        components[hand] = component;
        if (pose is not null) heldPoses[hand] = pose;
        else heldPoses.Remove(hand);
        hands.Remove(hand);
        hands.Add(hand);

        hand.IsGrabbing = true;
        hand.GrabbedObject = this;
        hand.NotifyGrabbed(this, component);
        Grabbed?.Invoke(hand, this, component);
    }

    /// <summary>
    /// 安全 Detach：保证 LIFO 顺序（先临时 detach 后抓的手，再 detach 当前手，最后把后抓的手焊回去）
    /// </summary>
    public void Detach(AVRSharpHand hand)
    {
        if (hand is null || !components.ContainsKey(hand))
            return;

        var releasedComponent = components[hand];
        var idx = hands.IndexOf(hand);
        if (idx < 0) return;

        // 临时 detach 所有在当前 hand 之后抓的手（按 LIFO 顺序：从末尾往回）
        var toReattach = new List<(AVRSharpHand h, UPrimitiveComponent c)>();
        for (int i = hands.Count - 1; i > idx; i--)
        {
            var h = hands[i];
            h.DetachFromActor(EDetachmentRule.KeepWorld, EDetachmentRule.KeepWorld, EDetachmentRule.KeepWorld);
            if (components.TryGetValue(h, out var c))
                toReattach.Add((h, c));
        }

        // Detach 当前 hand 并清理状态
        hand.DetachFromActor(EDetachmentRule.KeepWorld, EDetachmentRule.KeepWorld, EDetachmentRule.KeepWorld);
        hands.RemoveAt(idx);
        components.Remove(hand);
        heldPoses.Remove(hand);
        hand.IsGrabbing = false;
        hand.GrabbedObject = null;

        // 把之后的手按原顺序焊回去
        toReattach.Reverse();
        foreach (var (h, c) in toReattach)
            if (SystemLibrary.IsValid(c))
                h.AttachToComponent(c, "", EAttachmentRule.KeepWorld, EAttachmentRule.KeepWorld, EAttachmentRule.KeepWorld, true);

        if (hands.Count == 0)
        {
            GrabbedComponent = null;
            if (DropWithoutMomentum && SystemLibrary.IsValid(releasedComponent) && releasedComponent.IsSimulatingPhysics())
            {
                releasedComponent.SetPhysicsLinearVelocity(default);
                releasedComponent.SetPhysicsAngularVelocityInRadians(default, false, default);
            }
        }
        SetTriggerHandActive(hand, releasedComponent, false);
        hand.NotifyReleased(this, releasedComponent);
        Released?.Invoke(hand, this, releasedComponent);
    }

}