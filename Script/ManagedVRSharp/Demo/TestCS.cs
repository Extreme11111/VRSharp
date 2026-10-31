using UnrealSharp.Attributes;
using UnrealSharp.CoreUObject;
using UnrealSharp.Engine;

namespace VRSharp.Demo;

[UClass]
public partial class ATestCS : AActor
{
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial float TestFloat { get; set; }
}