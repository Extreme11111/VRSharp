using UnrealSharp.Attributes;
using UnrealSharp.Engine;
using VRSharp.Core;

namespace VRSharp.Demo;

[UEnum]
public enum ERotationAxis : byte
{
    Roll,   // X轴旋转
    Pitch,  // Y轴旋转
    Yaw     // Z轴旋转
}

[UClass]
public partial class ARod : AActor
{
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, RootComponent = true)]
    public partial UStaticMeshComponent? RootComponent { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true)]
    public partial UStaticMeshComponent? Base { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true)]
    public partial UStaticMeshComponent? Axis { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true)]
    public partial UPhysicsConstraintComponent PhysicsConstraint { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true)]
    public partial UVRSharpGrabbable Grab { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true)]
    public partial UTextRenderComponent Text { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial ERotationAxis RotationAxis { get; set; }

    [UProperty(PropertyFlags.BlueprintReadOnly)]
    public partial double Value { get; set; }


    public override void Tick(float deltaSeconds)
    {
        base.Tick(deltaSeconds);

        if (Axis is not null)
        {
            var rot = Axis.RelativeRotation;
            Value = RotationAxis switch
            {
                ERotationAxis.Roll => rot.Roll,
                ERotationAxis.Pitch => rot.Pitch,
                ERotationAxis.Yaw => rot.Yaw,
                _ => 0
            };
        }

        Text.Text = Value.ToString("00.00");
    }
}