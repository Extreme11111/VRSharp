using UnrealSharp.Attributes;
using UnrealSharp.Engine;

namespace VRSharp.Core;

[UClass]
public partial class UVRSharpHandPose : USceneComponent
{
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial bool UseFingerWeights { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial float ThumbWeight { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial float IndexWeight { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial float GraspWeight { get; set; }

}