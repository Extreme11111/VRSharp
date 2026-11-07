using UnrealSharp.Attributes;
using UnrealSharp.Engine;

namespace VRSharp.Core;

// Reusable animation configuration. Handedness and contact geometry stay on each grab point.
[UClass]
public partial class UVRSharpHandPosePreset : UDataAsset
{
    // Optional native playback: X = trigger, Y = entry/exit weight (both 0..1).
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UBlendSpace? PoseBlendSpace { get; set; }
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

    // Optional state key for existing animation graphs.
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial string? AnimationKey { get; set; }
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
