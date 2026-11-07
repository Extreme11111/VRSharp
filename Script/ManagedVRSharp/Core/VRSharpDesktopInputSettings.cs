using UnrealSharp.Attributes;
using UnrealSharp.Engine;
using UnrealSharp.EnhancedInput;

namespace VRSharp.Core;

[UClass]
public partial class UVRSharpDesktopInputSettings : UDataAsset
{
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial UInputMappingContext? MappingContext { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial UInputAction? Move { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial UInputAction? Look { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial UInputAction? LeftGrip { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial UInputAction? RightGrip { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial UInputAction? LeftTrigger { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial UInputAction? RightTrigger { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial UInputAction? ActiveTrigger { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial UInputAction? SwitchHand { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial UInputAction? HandMove { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial UInputAction? HandRotate { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial UInputAction? ToggleGrip { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial UInputAction? Fingers { get; set; }
}
