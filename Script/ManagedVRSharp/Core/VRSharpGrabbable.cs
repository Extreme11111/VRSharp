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

    // Run on demand after authoring or migration, outside the physics/input tick.
    [UFunction(FunctionFlags.BlueprintCallable)]
    public string GetGrabSetupIssues()
    {
        var issues = new List<string>();
        var owner = Owner;
        if (owner is null || !SystemLibrary.IsValid(owner)) return "Grabbable Owner is missing or invalid.";
        bool triggerEnabled = TriggerPressThreshold != 0;
        if (triggerEnabled && (!float.IsFinite(TriggerPressThreshold) || !float.IsFinite(TriggerReleaseThreshold) ||
            TriggerPressThreshold <= 0 || TriggerPressThreshold > 1 ||
            TriggerReleaseThreshold < 0 || TriggerReleaseThreshold >= TriggerPressThreshold))
            issues.Add("Trigger thresholds require 0 <= release < press <= 1.");
        if (SingleHandOnly && (RequireTwoTriggerHands || RequireSupportHandForPrimaryTrigger))
            issues.Add("SingleHandOnly prevents the configured two-hand activation rule.");

        bool hasLeftPose = false, hasRightPose = false, hasTriggerPose = false;
        foreach (var component in owner.GetComponentsByClass<USceneComponent>())
        {
            if (component is not UVRSharpHandPose pose || !SystemLibrary.IsValid(pose)) continue;
            string name = SystemLibrary.GetObjectName(pose);
            if (!float.IsFinite(pose.EnterBlendSeconds) || pose.EnterBlendSeconds < 0 ||
                !float.IsFinite(pose.ExitBlendSeconds) || pose.ExitBlendSeconds < 0)
                issues.Add($"{name}: animation blend times must be finite and non-negative.");
            var target = pose.TargetComponent;
            if (target is null)
            {
                if (RequireExplicitGrabPose) issues.Add($"{name}: assign TargetComponent for explicit grabbing.");
                continue;
            }
            if (!SystemLibrary.IsValid(target) || target.Owner != owner)
            {
                issues.Add($"{name}: TargetComponent must be a valid Primitive on this Actor.");
                continue;
            }
            bool left = !DisableLeftHand && !pose.DisableLeftHand;
            bool right = !DisableRightHand && !pose.DisableRightHand;
            hasLeftPose |= left;
            hasRightPose |= right;
            hasTriggerPose |= !pose.SupportGripOnly && (left || right);
        }
        if (RequireExplicitGrabPose && !DisableGrabbing)
        {
            if (!DisableLeftHand && !hasLeftPose) issues.Add("Left hand has no compatible explicit grab pose.");
            if (!DisableRightHand && !hasRightPose) issues.Add("Right hand has no compatible explicit grab pose.");
            if (triggerEnabled && !hasTriggerPose) issues.Add("Tool activation has no trigger-capable explicit grab pose.");
        }
        return string.Join("\n", issues);
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

    // Authoring option: an interlocked tool needs two distinct gripping hands to press.
    [UProperty(PropertyFlags.BlueprintReadOnly | PropertyFlags.EditAnywhere)]
    public partial bool RequireTwoTriggerHands { get; set; }

    // The first trigger-capable holder controls the tool with another hand for support.
    [UProperty(PropertyFlags.BlueprintReadOnly | PropertyFlags.EditAnywhere)]
    public partial bool RequireSupportHandForPrimaryTrigger { get; set; }

    private readonly HashSet<AVRSharpHand> activeTriggerHands = new();
    private bool publishedTriggerActive;
    public bool IsTriggerActive => EvaluateTriggerActivation();

    private bool EvaluateTriggerActivation()
    {
        if (RequireTwoTriggerHands) return activeTriggerHands.Count >= 2;
        if (!RequireSupportHandForPrimaryTrigger) return activeTriggerHands.Count != 0;
        return GrabCount >= 2 && GetPrimaryTriggerHand() is { } primary && activeTriggerHands.Contains(primary);
    }

    [UFunction(FunctionFlags.BlueprintCallable)]
    public AVRSharpHand? GetPrimaryTriggerHand()
    {
        foreach (var hand in hands)
            if (AllowsToolTrigger(hand)) return hand;
        return null;
    }

    private bool AllowsToolTrigger(AVRSharpHand hand)
        => !heldPoses.TryGetValue(hand, out var pose) || (SystemLibrary.IsValid(pose) && !pose.SupportGripOnly);

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
        bool active = enabled && AllowsToolTrigger(hand) &&
            (activeTriggerHands.Contains(hand) ? value > release : value >= press);
        SetTriggerHandActive(hand, component, active);
        GrabTriggerChanged?.Invoke(hand, this, component, value);
    }

    private void SetTriggerHandActive(AVRSharpHand hand, UPrimitiveComponent component, bool active)
    {
        if (active) activeTriggerHands.Add(hand);
        else activeTriggerHands.Remove(hand);
        PublishTriggerActivationChange(hand, component);
    }

    private void PublishTriggerActivationChange(AVRSharpHand hand, UPrimitiveComponent component)
    {
        bool active = IsTriggerActive;
        if (publishedTriggerActive == active) return;
        publishedTriggerActive = active;
        TriggerActivationChanged?.Invoke(hand, this, component, active);
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

    public AVRSharpHand? PrimaryGrabbingHand => hands.Count == 0 ? null : hands[0];
    public UPrimitiveComponent? GrabbedComponent => PrimaryGrabbingHand is { } hand ? GetHeldComponent(hand) : null;
    public int GrabCount => hands.Count;
    public bool IsGrabbed => hands.Count != 0;
    public event Action<AVRSharpHand, UVRSharpGrabbable, UPrimitiveComponent>? Grabbed;
    public event Action<AVRSharpHand, UVRSharpGrabbable, UPrimitiveComponent>? Released;

    // Published after Grabbed/Released. Nested operations publish the final pair
    // without sending an older notification when the outer callback resumes.
    private (AVRSharpHand? Hand, UPrimitiveComponent? Component) publishedPrimaryGrab;
    public event Action<UVRSharpGrabbable, AVRSharpHand?, UPrimitiveComponent?, AVRSharpHand?, UPrimitiveComponent?>? PrimaryGrabChanged;

    [UFunction(FunctionFlags.BlueprintCallable)]
    public AVRSharpHand? GetPrimaryGrabbingHand() => PrimaryGrabbingHand;
    [UFunction(FunctionFlags.BlueprintCallable)]
    public UPrimitiveComponent? GetPrimaryGrabComponent() => GrabbedComponent;

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
        activeTriggerHands.Remove(hand);
        components[hand] = component;
        if (pose is not null) heldPoses[hand] = pose;
        else heldPoses.Remove(hand);
        hands.Remove(hand);
        hands.Add(hand);

        hand.IsGrabbing = true;
        hand.GrabbedObject = this;
        hand.NotifyGrabbed(this, component);
        Grabbed?.Invoke(hand, this, component);
        PublishPrimaryGrabChange();
        PublishTriggerActivationChange(hand, component);
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
            if (DropWithoutMomentum && SystemLibrary.IsValid(releasedComponent) && releasedComponent.IsSimulatingPhysics())
            {
                releasedComponent.SetPhysicsLinearVelocity(default);
                releasedComponent.SetPhysicsAngularVelocityInRadians(default, false, default);
            }
        }
        SetTriggerHandActive(hand, releasedComponent, false);
        hand.NotifyReleased(this, releasedComponent);
        Released?.Invoke(hand, this, releasedComponent);
        PublishPrimaryGrabChange();
    }

    private void PublishPrimaryGrabChange()
    {
        var previous = publishedPrimaryGrab;
        var current = (Hand: PrimaryGrabbingHand, Component: GrabbedComponent);
        if (previous == current) return;
        publishedPrimaryGrab = current;
        PrimaryGrabChanged?.Invoke(this, previous.Hand, previous.Component, current.Hand, current.Component);
    }

}
