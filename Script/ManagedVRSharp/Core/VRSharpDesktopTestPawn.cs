using UnrealSharp;
using UnrealSharp.Attributes;
using UnrealSharp.CoreUObject;
using UnrealSharp.Engine;
using UnrealSharp.EnhancedInput;

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


    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UInputAction? DesktopHandRotate { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UInputAction? DesktopToggleGrip { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UInputAction? DesktopFingers { get; set; }
    private FVector fingerInput;
    [UFunction(FunctionFlags.BlueprintCallable)]
    public void SetEmptyHandInput(float thumb, float index, float grasp)
        => fingerInput = new FVector(Math.Max(Axis(thumb),0),Math.Max(Axis(index),0),Math.Max(Axis(grasp),0));
    [UFunction]
    private void OnDesktopFingers(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    { var v=value.GetAxis3D(); SetEmptyHandInput((float)v.X,(float)v.Y,(float)v.Z); }
    [UFunction]
    private void OnDesktopFingersStop(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    { SetEmptyHandInput(0,0,0); }

    private UEnhancedInputComponent? boundDesktopInput;
    private AVRSharpHand? gripInputHand;
    private UVRSharpGrabbable? gripInputObject;
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UInputAction? DesktopMove { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UInputAction? DesktopLook { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UInputAction? DesktopHandMove { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UInputAction? DesktopGrip { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UInputAction? DesktopSwitchHand { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UInputAction? DesktopTrigger { get; set; }

    // Call after possession; Tick also retries until EnhancedInputComponent exists.
    public bool BindDesktopInput(UEnhancedInputComponent input)
    {
        if (boundDesktopInput is not null) return boundDesktopInput == input;
        if (DesktopMove is null || DesktopLook is null || DesktopHandMove is null ||
            DesktopGrip is null || DesktopSwitchHand is null || DesktopTrigger is null) return false;
        input.BindAction(DesktopMove, ETriggerEvent.Triggered, OnDesktopMove, out _);
        input.BindAction(DesktopMove, ETriggerEvent.Completed, OnDesktopMoveStop, out _);
        input.BindAction(DesktopMove, ETriggerEvent.Canceled, OnDesktopMoveStop, out _);
        input.BindAction(DesktopLook, ETriggerEvent.Triggered, OnDesktopLook, out _);
        input.BindAction(DesktopHandMove, ETriggerEvent.Triggered, OnDesktopHandMove, out _);
        input.BindAction(DesktopHandMove, ETriggerEvent.Completed, OnDesktopHandMoveStop, out _);
        input.BindAction(DesktopHandMove, ETriggerEvent.Canceled, OnDesktopHandMoveStop, out _);
        input.BindAction(DesktopTrigger, ETriggerEvent.Triggered, OnDesktopTrigger, out _);
        input.BindAction(DesktopTrigger, ETriggerEvent.Completed, OnDesktopTriggerStop, out _);
        input.BindAction(DesktopTrigger, ETriggerEvent.Canceled, OnDesktopTriggerStop, out _);
        input.BindAction(DesktopGrip, ETriggerEvent.Started, OnDesktopGrab, out _);
        input.BindAction(DesktopGrip, ETriggerEvent.Completed, OnDesktopRelease, out _);
        input.BindAction(DesktopGrip, ETriggerEvent.Canceled, OnDesktopRelease, out _);
        input.BindAction(DesktopSwitchHand, ETriggerEvent.Started, OnDesktopSwitch, out _);
        if (DesktopHandRotate is not null)
        {
            input.BindAction(DesktopHandRotate, ETriggerEvent.Triggered, OnDesktopHandRotate, out _);
            input.BindAction(DesktopHandRotate, ETriggerEvent.Completed, OnDesktopHandRotateStop, out _);
            input.BindAction(DesktopHandRotate, ETriggerEvent.Canceled, OnDesktopHandRotateStop, out _);
        }
        if (DesktopToggleGrip is not null)
            input.BindAction(DesktopToggleGrip, ETriggerEvent.Started, OnDesktopToggleGrip, out _);
        if (DesktopFingers is not null)
        {
            input.BindAction(DesktopFingers, ETriggerEvent.Triggered, OnDesktopFingers, out _);
            input.BindAction(DesktopFingers, ETriggerEvent.Completed, OnDesktopFingersStop, out _);
            input.BindAction(DesktopFingers, ETriggerEvent.Canceled, OnDesktopFingersStop, out _);
        }
        boundDesktopInput = input;
        return true;
    }
    [UFunction]
    private void OnDesktopMove(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    { var v=value.GetAxis3D(); SetMoveInput((float)v.X,(float)v.Y,(float)v.Z); }
    [UFunction]
    private void OnDesktopMoveStop(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    { SetMoveInput(0,0,0); }
    [UFunction]
    private void OnDesktopLook(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    { var v=value.GetAxis3D(); Look((float)v.X,(float)v.Y); }
    [UFunction]
    private void OnDesktopHandMove(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    { var v=value.GetAxis3D(); SetHandMoveInput((float)v.X,(float)v.Y,(float)v.Z); }
    [UFunction]
    private void OnDesktopHandMoveStop(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    { SetHandMoveInput(0,0,0); }
    [UFunction]
    private void OnDesktopTrigger(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    { SetTrigger((float)value.GetAxis3D().X); }
    [UFunction]
    private void OnDesktopTriggerStop(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    { SetTrigger(0); }
    [UFunction]
    private void OnDesktopGrab(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    {
        if (gripInputHand is not null) return;
        var hand = ActiveHand;
        if (hand is not null && SystemLibrary.IsValid(hand) && hand.TryGrab())
        {
            gripInputHand = hand;
            gripInputObject = hand.GrabbedObject;
        }
    }
    [UFunction]
    private void OnDesktopRelease(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    { ReleaseDesktopGrip(); }
    [UFunction]
    private void OnDesktopSwitch(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    { SelectLeftHand(!ControlLeftHand); }


    [UFunction]
    private void OnDesktopToggleGrip(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    { ToggleActiveGrip(); }

    // Latched grip lets one keyboard operate two hands independently.
    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool ToggleActiveGrip()
    {
        var hand = ActiveHand;
        if (hand is null || !SystemLibrary.IsValid(hand)) return false;
        if (!hand.IsGrabbing) return hand.TryGrab();
        hand.SetGrabTrigger(0);
        hand.Release();
        trigger = 0;
        return !hand.IsGrabbing;
    }

    private void ReleaseDesktopGrip()
    {
        var hand = gripInputHand;
        var item = gripInputObject;
        gripInputHand = null;
        gripInputObject = null;
        if (hand is not null && SystemLibrary.IsValid(hand) && item is not null &&
            hand.IsGrabbing && hand.GrabbedObject == item)
        {
            hand.SetGrabTrigger(0);
            hand.Release();
        }
    }

    [UFunction]
    private void OnDesktopHandRotate(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    { var v=value.GetAxis3D(); SetHandRotateInput((float)v.X,(float)v.Y,(float)v.Z); }
    [UFunction]
    private void OnDesktopHandRotateStop(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    { SetHandRotateInput(0,0,0); }
    [UFunction(FunctionFlags.BlueprintCallable)]
    public void SetHandRotateInput(float yawAxis, float pitchAxis, float rollAxis)
        => handRotateInput = new FVector(Axis(yawAxis),Axis(pitchAxis),Axis(rollAxis));

    private FVector initialLeftLocation, initialRightLocation;
    private FRotator initialLeftRotation, initialRightRotation;
    private bool targetsCaptured;

    // Restore authored camera-local targets without releasing either held object.
    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool ResetHandTargets()
    {
        if (!targetsCaptured || LeftTarget is null || RightTarget is null ||
            !SystemLibrary.IsValid(LeftTarget) || !SystemLibrary.IsValid(RightTarget)) return false;
        handInput = handRotateInput = FVector.Zero;
        LeftTarget.RelativeLocation = initialLeftLocation;
        LeftTarget.RelativeRotation = initialLeftRotation;
        RightTarget.RelativeLocation = initialRightLocation;
        RightTarget.RelativeRotation = initialRightRotation;
        return true;
    }

    private FVector moveInput, handInput, handRotateInput;
    public float HandRotateSpeed { get; set; } = 90f;
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
        handInput = handRotateInput = FVector.Zero;
        if (ActiveHand is { } previous && SystemLibrary.IsValid(previous)) previous.ClearFingerInput();
        fingerInput = FVector.Zero;
        ControlLeftHand = left;
    }
    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool GrabActiveHand()
        => ActiveHand is { } hand && SystemLibrary.IsValid(hand) && hand.TryGrab();
    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool GrabActiveHandAtPose(UVRSharpGrabbable grabbable, UVRSharpHandPose pose)
        => ActiveHand is { } hand && SystemLibrary.IsValid(hand) && hand.TryGrabAtPose(grabbable, pose);

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
        ReleaseDesktopGrip();
        fingerInput = FVector.Zero;
        if (LeftHand is { } lh && SystemLibrary.IsValid(lh)) lh.ClearFingerInput();
        if (RightHand is { } rh && SystemLibrary.IsValid(rh)) rh.ClearFingerInput();
        moveInput = handInput = handRotateInput = FVector.Zero;
        trigger = 0;
        if (LeftHand is { } left && SystemLibrary.IsValid(left)) left.SetGrabTrigger(0);
        if (RightHand is { } right && SystemLibrary.IsValid(right)) right.SetGrabTrigger(0);
    }
    public override void BeginPlay()
    {
        base.BeginPlay();
        if (LeftTarget is not null && RightTarget is not null &&
            SystemLibrary.IsValid(LeftTarget) && SystemLibrary.IsValid(RightTarget))
        {
            initialLeftLocation = LeftTarget.RelativeLocation;
            initialRightLocation = RightTarget.RelativeLocation;
            initialLeftRotation = LeftTarget.RelativeRotation;
            initialRightRotation = RightTarget.RelativeRotation;
            targetsCaptured = true;
        }
        // Initialize physics only; never request XR tracking or bind VR input actions.
        if (LeftHand is { } left && SystemLibrary.IsValid(left)) left.InitializeHand(true);
        if (RightHand is { } right && SystemLibrary.IsValid(right)) right.InitializeHand(false);
    }
    public override void Tick(float deltaSeconds)
    {
        base.Tick(deltaSeconds);
        if (boundDesktopInput is null && InputComponent is UEnhancedInputComponent input) BindDesktopInput(input);
        if (!float.IsFinite(deltaSeconds) || deltaSeconds <= 0) return;
        float dt = Math.Min(deltaSeconds,.1f);
        var movement = VRSharpMathHelper.ClampMagnitude(moveInput,1);
        SetActorLocation(ActorLocation + (ActorForwardVector*movement.X + ActorRightVector*movement.Y
            + new FVector(0,0,movement.Z))*Math.Max(MoveSpeed,0)*dt);
        if (ActiveTarget is { } target && SystemLibrary.IsValid(target))
        {
            target.RelativeLocation += VRSharpMathHelper.ClampMagnitude(handInput,1)*Math.Max(HandSpeed,0)*dt;
            var axes = VRSharpMathHelper.ClampMagnitude(handRotateInput,1);
            var rotation = target.RelativeRotation;
            float step = float.IsFinite(HandRotateSpeed) ? Math.Max(HandRotateSpeed,0)*dt : 0;
            target.RelativeRotation = new FRotator((rotation.Pitch + axes.Y*step)%360,
                (rotation.Yaw + axes.X*step)%360, (rotation.Roll + axes.Z*step)%360);
        }
        Drive(LeftHand,LeftTarget,dt);
        Drive(RightHand,RightTarget,dt);
        if (ActiveHand is { } active && SystemLibrary.IsValid(active))
        {
            if (active.IsGrabbing) active.SetGrabTrigger(trigger);
            else active.SetFingerInput((float)fingerInput.X, Math.Max((float)fingerInput.Y,trigger), (float)fingerInput.Z);
        }
    }
    private static void Drive(AVRSharpHand? hand,USceneComponent? target,float dt)
    {
        if (hand is null || target is null || !SystemLibrary.IsValid(hand) || !SystemLibrary.IsValid(target)) return;
        hand.UpdateTracking(target.WorldLocation,target.WorldRotation,dt);
    }
}
