using UnrealSharp;
using UnrealSharp.Attributes;
using UnrealSharp.CoreUObject;
using UnrealSharp.Engine;

namespace VRSharp.Core;

// Free-flying interaction test rig: intentionally not a locomotion/collision substitute.
[UClass]
public partial class AVRSharpDesktopTestPawn : APawn
{
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent=true, RootComponent=true)]
    public partial USceneComponent? Origin { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent=true, AttachmentComponent=nameof(Origin))]
    public partial UCameraComponent? Camera { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent=true, AttachmentComponent=nameof(Camera))]
    public partial USceneComponent? LeftTarget { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent=true, AttachmentComponent=nameof(Camera))]
    public partial USceneComponent? RightTarget { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial AVRSharpHand? LeftHand { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial AVRSharpHand? RightHand { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial bool ControlLeftHand { get; set; }

    private FVector moveInput, handInput;
    private float yaw, pitch;
    private float trigger;
    public float MoveSpeed { get; set; } = 250f;
    public float HandSpeed { get; set; } = 60f;
    private AVRSharpHand? ActiveHand => ControlLeftHand ? LeftHand : RightHand;
    private USceneComponent? ActiveTarget => ControlLeftHand ? LeftTarget : RightTarget;
    private static float Axis(float v) => float.IsFinite(v) ? Math.Clamp(v,-1f,1f) : 0;

    [UFunction(FunctionFlags.BlueprintCallable)]
    public void SetMoveInput(float forward, float right, float up)
        => moveInput = new FVector(Axis(forward),Axis(right),Axis(up));
    [UFunction(FunctionFlags.BlueprintCallable)]
    public void SetHandMoveInput(float forward, float right, float up)
        => handInput = new FVector(Axis(forward),Axis(right),Axis(up));
    [UFunction(FunctionFlags.BlueprintCallable)]
    public void Look(float yawDelta, float pitchDelta)
    {
        if (!float.IsFinite(yawDelta) || !float.IsFinite(pitchDelta)) return;
        yaw = (yaw + yawDelta) % 360f;
        pitch = Math.Clamp(pitch + pitchDelta,-85f,85f);
        SetActorRotation(new FRotator(0,yaw,0));
        if (Camera is not null) Camera.RelativeRotation = new FRotator(pitch,0,0);
    }
    [UFunction(FunctionFlags.BlueprintCallable)]
    public void SelectLeftHand(bool left)
    {
        if (ActiveHand is { } old && SystemLibrary.IsValid(old)) old.SetGrabTrigger(0);
        trigger = 0;
        handInput = FVector.Zero;
        ControlLeftHand = left;
    }
    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool GrabActiveHand()
        => ActiveHand is { } hand && SystemLibrary.IsValid(hand) && hand.TryGrab();
    [UFunction(FunctionFlags.BlueprintCallable)]
    public void ReleaseActiveHand()
    {
        if (ActiveHand is { } hand && SystemLibrary.IsValid(hand)) hand.Release();
        trigger = 0;
    }
    [UFunction(FunctionFlags.BlueprintCallable)]
    public void SetTrigger(float value)
    {
        if (float.IsFinite(value)) trigger = Math.Clamp(value,0,1);
    }
    [UFunction(FunctionFlags.BlueprintCallable)]
    public void ResetDesktopInput()
    {
        moveInput = handInput = FVector.Zero;
        trigger = 0;
        if (LeftHand is { } left && SystemLibrary.IsValid(left)) left.SetGrabTrigger(0);
        if (RightHand is { } right && SystemLibrary.IsValid(right)) right.SetGrabTrigger(0);
    }
    public override void BeginPlay()
    {
        base.BeginPlay();
        // Initialize physics only; never request XR tracking or bind VR input actions.
        if (LeftHand is { } left && SystemLibrary.IsValid(left)) left.InitializeHand(true);
        if (RightHand is { } right && SystemLibrary.IsValid(right)) right.InitializeHand(false);
    }
    public override void Tick(float deltaSeconds)
    {
        base.Tick(deltaSeconds);
        if (!float.IsFinite(deltaSeconds) || deltaSeconds <= 0) return;
        float dt = Math.Min(deltaSeconds,.1f);
        var movement = VRSharpMathHelper.ClampMagnitude(moveInput,1);
        SetActorLocation(ActorLocation + (ActorForwardVector*movement.X + ActorRightVector*movement.Y
            + new FVector(0,0,movement.Z))*Math.Max(MoveSpeed,0)*dt);
        if (ActiveTarget is { } target)
            target.RelativeLocation += VRSharpMathHelper.ClampMagnitude(handInput,1)*Math.Max(HandSpeed,0)*dt;
        Drive(LeftHand,LeftTarget,dt);
        Drive(RightHand,RightTarget,dt);
        if (ActiveHand is { } active && SystemLibrary.IsValid(active)) active.SetGrabTrigger(trigger);
    }
    private static void Drive(AVRSharpHand? hand,USceneComponent? target,float dt)
    {
        if (hand is null || target is null || !SystemLibrary.IsValid(hand) || !SystemLibrary.IsValid(target)) return;
        hand.UpdateTracking(target.WorldLocation,target.WorldRotation,dt);
    }
}
