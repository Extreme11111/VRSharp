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

    #region 抓握姿态

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial TMap<string, string> GrabPoses { get; set; }

    #endregion

    #region  抓握事件

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
    {
        if (hand is null || component is null || !SystemLibrary.IsValid(component))
            return;

        GrabbedComponent ??= component;
        components[hand] = component;
        hands.Remove(hand);
        hands.Add(hand);

        hand.AttachToComponent(component, "", EAttachmentRule.KeepWorld, EAttachmentRule.KeepWorld, EAttachmentRule.KeepWorld, true);
        hand.IsGrabbing = true;
        hand.GrabbedObject = this;
    }

    /// <summary>
    /// 安全 Detach：保证 LIFO 顺序（先临时 detach 后抓的手，再 detach 当前手，最后把后抓的手焊回去）
    /// </summary>
    public void Detach(AVRSharpHand hand)
    {
        if (hand is null || !components.ContainsKey(hand))
            return;

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
        hand.IsGrabbing = false;
        hand.GrabbedObject = null;

        // 把之后的手按原顺序焊回去
        toReattach.Reverse();
        foreach (var (h, c) in toReattach)
            if (SystemLibrary.IsValid(c))
                h.AttachToComponent(c, "", EAttachmentRule.KeepWorld, EAttachmentRule.KeepWorld, EAttachmentRule.KeepWorld, true);

        if (hands.Count == 0)
            GrabbedComponent = null;
    }

}