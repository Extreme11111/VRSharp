using UnrealSharp.Attributes;
using UnrealSharp.Engine;

namespace VRSharp.Core;

[UClass]
public partial class UVRSharpHandPose : USceneComponent
{
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UVRSharpHandPosePreset? AnimationPreset { get; set; }

    public override void BeginPlay()
    {
        base.BeginPlay();
        ApplyAnimationPreset();
    }

    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool ApplyAnimationPreset()
    {
        var preset = AnimationPreset;
        if (preset is null || !SystemLibrary.IsValid(preset)) return false;
        if (Owner is { } owner && SystemLibrary.IsValid(owner))
        {
            foreach (var component in owner.GetComponentsByClass<UActorComponent>())
                if (component is UVRSharpGrabbable grab && SystemLibrary.IsValid(grab) && grab.IsGrabPoseOccupied(this))
                    return false;
        }
        EnterBlendSeconds = preset.EnterBlendSeconds;
        PoseBlendSpace = preset.PoseBlendSpace;
        ExitBlendSeconds = preset.ExitBlendSeconds;
        GripAnimation = preset.GripAnimation;
        PressedAnimation = preset.PressedAnimation;
        AnimationKey = preset.AnimationKey;
        UseFingerWeights = preset.UseFingerWeights;
        UseTriggerBlend = preset.UseTriggerBlend;
        TriggerIndexWeight = preset.TriggerIndexWeight;
        ThumbWeight = preset.ThumbWeight;
        IndexWeight = preset.IndexWeight;
        GraspWeight = preset.GraspWeight;
        return true;
    }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial bool ExclusiveToOneHand { get; set; }

    // This grip still drives hand animation and counts as physical support.
    [UProperty(PropertyFlags.BlueprintReadOnly | PropertyFlags.EditAnywhere)]
    public partial bool SupportGripOnly { get; set; }

    // Explicit collider association takes precedence over legacy name mappings.
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UPrimitiveComponent? TargetComponent { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial int Priority { get; set; }

    // Seconds; zero preserves the legacy immediate animation switch.
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial float EnterBlendSeconds { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial float ExitBlendSeconds { get; set; }

    // Optional clips for a shared AnimBP. A missing pressed clip reuses the grip clip.
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UAnimSequence? GripAnimation { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UAnimSequence? PressedAnimation { get; set; }

    // Four samples: idle at (0,0)/(1,0), grip at (0,1), pressed at (1,1).
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UBlendSpace? PoseBlendSpace { get; set; }

    // Optional state key for existing animation graphs.
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial string? AnimationKey { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial bool DisableLeftHand { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial bool DisableRightHand { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial bool UseFingerWeights { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial bool UseTriggerBlend { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial float TriggerIndexWeight { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial float ThumbWeight { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial float IndexWeight { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial float GraspWeight { get; set; }

}
