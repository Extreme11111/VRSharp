using UnrealSharp.Attributes;
using UnrealSharp.Engine;
using VRSharp.Core;

namespace VRSharp.Demo;

// A test prop that consumes the same Grabbable events in desktop and OpenXR modes.
[UClass]
public partial class AVRSharpFlashlight : AActor
{
    [UProperty(PropertyFlags.BlueprintReadOnly, DefaultComponent = true, RootComponent = true)]
    public partial UStaticMeshComponent? Body { get; set; }

    [UProperty(PropertyFlags.BlueprintReadOnly, DefaultComponent = true, AttachmentComponent = nameof(Body))]
    public partial USpotLightComponent? Lamp { get; set; }

    [UProperty(PropertyFlags.BlueprintReadOnly, DefaultComponent = true)]
    public partial UVRSharpGrabbable? Grab { get; set; }

    [UProperty(PropertyFlags.BlueprintReadOnly, DefaultComponent = true, AttachmentComponent = nameof(Body))]
    public partial UVRSharpHandPose? LeftGrip { get; set; }

    [UProperty(PropertyFlags.BlueprintReadOnly, DefaultComponent = true, AttachmentComponent = nameof(Body))]
    public partial UVRSharpHandPose? RightGrip { get; set; }

    private UVRSharpGrabbable? subscribedGrab;

    public override void BeginPlay()
    {
        base.BeginPlay();

        if (Body is { } body && SystemLibrary.IsValid(body))
        {
            if (LeftGrip is { } left && SystemLibrary.IsValid(left))
            {
                left.TargetComponent = body;
                left.DisableRightHand = true;
            }
            if (RightGrip is { } right && SystemLibrary.IsValid(right))
            {
                right.TargetComponent = body;
                right.DisableLeftHand = true;
            }
        }

        if (Grab is not { } grab || !SystemLibrary.IsValid(grab))
        {
            SetLamp(false);
            return;
        }

        // Give the example usable thresholds while respecting authored values.
        if (grab.TriggerPressThreshold == 0 && grab.TriggerReleaseThreshold == 0)
        {
            grab.TriggerPressThreshold = 0.75f;
            grab.TriggerReleaseThreshold = 0.55f;
        }

        subscribedGrab = grab;
        grab.TriggerActivationChanged += OnTriggerActivationChanged;
        SetLamp(grab.IsTriggerActive);
    }

    public override void EndPlay(EEndPlayReason endPlayReason)
    {
        if (subscribedGrab is { } grab)
            grab.TriggerActivationChanged -= OnTriggerActivationChanged;
        subscribedGrab = null;
        SetLamp(false);
        base.EndPlay(endPlayReason);
    }

    private void OnTriggerActivationChanged(AVRSharpHand hand, UVRSharpGrabbable item,
        UPrimitiveComponent component, bool active)
    {
        SetLamp(active);
    }

    private void SetLamp(bool active)
    {
        if (Lamp is { } lamp && SystemLibrary.IsValid(lamp))
            lamp.SetVisibility(active, false);
    }
}
