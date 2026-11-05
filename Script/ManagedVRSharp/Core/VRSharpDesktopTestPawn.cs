using System.Collections.Generic;
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
    public partial TSubclassOf<AVRSharpHand> LeftHandClass { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial TSubclassOf<AVRSharpHand> RightHandClass { get; set; }

    private AVRSharpHand? spawnedLeftHand;
    private AVRSharpHand? spawnedRightHand;

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

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UInputMappingContext? DesktopMappingContext { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial int DesktopMappingPriority { get; set; }

    private APlayerController? mappingController;
    private UEnhancedInputLocalPlayerSubsystem? mappingSubsystem;
    private UInputMappingContext? mappedContext;
    private bool ownsMappingContext;

    private void RefreshDesktopMapping()
    {
        var context = DesktopMappingContext;
        var controller = GetController() as APlayerController;
        if (controller != mappingController || context != mappedContext)
            ClearDesktopMapping();
        if (mappingSubsystem is not null || context is null || controller is null ||
            !SystemLibrary.IsValid(context) || !SystemLibrary.IsValid(controller) || !controller.IsLocalController()) return;
        var subsystem = GetLocalPlayerSubsystem<UEnhancedInputLocalPlayerSubsystem>(controller);
        if (subsystem is null || !SystemLibrary.IsValid(subsystem)) return;

        mappingController = controller;
        mappingSubsystem = subsystem;
        mappedContext = context;
        if (subsystem.HasMappingContext(context, out _)) return;
        subsystem.AddMappingContext(context, DesktopMappingPriority);
        ownsMappingContext = true;
    }

    private void ClearDesktopMapping()
    {
        var subsystem = mappingSubsystem;
        var context = mappedContext;
        bool remove = ownsMappingContext;
        mappingController = null;
        mappingSubsystem = null;
        mappedContext = null;
        ownsMappingContext = false;
        if (remove && subsystem is not null && context is not null &&
            SystemLibrary.IsValid(subsystem) && SystemLibrary.IsValid(context))
            subsystem.RemoveMappingContext(context);
        if (subsystem is not null) ResetDesktopInput();
    }

    public override void EndPlay(EEndPlayReason endPlayReason)
    {
        ClearDesktopMapping();
        DestroySpawnedHand(spawnedLeftHand);
        DestroySpawnedHand(spawnedRightHand);
        spawnedLeftHand = spawnedRightHand = null;
        base.EndPlay(endPlayReason);
    }

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

    private bool desktopHandsPrepared;

    // An empty report means that the required object references are configured.
    // Mapping asset contents and physical hand components still need editor validation.
    [UFunction(FunctionFlags.BlueprintCallable)]
    public string GetDesktopSetupIssues()
    {
        var issues = new List<string>();
        if (Camera is null || !SystemLibrary.IsValid(Camera)) issues.Add("Camera is missing or invalid.");
        CheckDesktopHandSetup(issues, "Left", LeftHand, LeftHandClass, LeftTarget);
        CheckDesktopHandSetup(issues, "Right", RightHand, RightHandClass, RightTarget);
        if (LeftHand is not null && LeftHand == RightHand) issues.Add("LeftHand and RightHand reference the same actor.");
        if (LeftTarget is not null && LeftTarget == RightTarget) issues.Add("LeftTarget and RightTarget reference the same component.");
        if (DesktopMappingContext is not null && !SystemLibrary.IsValid(DesktopMappingContext))
            issues.Add("DesktopMappingContext is invalid. Assign a valid context or leave it empty for host-managed mapping.");

        var usedActions = new Dictionary<UInputAction, string>();
        CheckDesktopAction(issues, usedActions, nameof(DesktopMove), DesktopMove, true);
        CheckDesktopAction(issues, usedActions, nameof(DesktopLook), DesktopLook, true);
        CheckDesktopAction(issues, usedActions, nameof(DesktopHandMove), DesktopHandMove, true);
        CheckDesktopAction(issues, usedActions, nameof(DesktopGrip), DesktopGrip, true);
        CheckDesktopAction(issues, usedActions, nameof(DesktopSwitchHand), DesktopSwitchHand, true);
        CheckDesktopAction(issues, usedActions, nameof(DesktopTrigger), DesktopTrigger, true);
        CheckDesktopAction(issues, usedActions, nameof(DesktopHandRotate), DesktopHandRotate, false);
        CheckDesktopAction(issues, usedActions, nameof(DesktopToggleGrip), DesktopToggleGrip, false);
        CheckDesktopAction(issues, usedActions, nameof(DesktopFingers), DesktopFingers, false);
        return string.Join("\n", issues);
    }

    private void CheckDesktopHandSetup(List<string> issues, string side, AVRSharpHand? hand,
        TSubclassOf<AVRSharpHand> handClass, USceneComponent? target)
    {
        if (target is null || !SystemLibrary.IsValid(target)) issues.Add($"{side}Target is missing or invalid.");
        if (hand is not null && SystemLibrary.IsValid(hand)) return;
        if (desktopHandsPrepared)
            issues.Add($"{side}Hand is unavailable after BeginPlay. Check the placed actor or {side}HandClass and target.");
        else if (handClass.Equals(default(TSubclassOf<AVRSharpHand>)))
            issues.Add($"Assign {side}Hand or {side}HandClass.");
    }

    private static void CheckDesktopAction(List<string> issues, Dictionary<UInputAction, string> usedActions,
        string name, UInputAction? action, bool required)
    {
        if (action is null || !SystemLibrary.IsValid(action))
        {
            if (required || action is not null) issues.Add($"{name} is missing or invalid.");
            return;
        }
        if (usedActions.TryGetValue(action, out var previous)) issues.Add($"{name} reuses the action assigned to {previous}.");
        else usedActions.Add(action, name);
    }

    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool IsDesktopInputBound() => boundDesktopInput is not null &&
        SystemLibrary.IsValid(boundDesktopInput) && boundDesktopInput == InputComponent;

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
        LeftHand = PrepareDesktopHand(LeftHand, LeftHandClass, LeftTarget, true, out spawnedLeftHand);
        RightHand = PrepareDesktopHand(RightHand, RightHandClass, RightTarget, false, out spawnedRightHand);
        desktopHandsPrepared = true;
    }
    private AVRSharpHand? PrepareDesktopHand(AVRSharpHand? assignedHand, TSubclassOf<AVRSharpHand> handClass,
        USceneComponent? target, bool isLeft, out AVRSharpHand? spawnedHand)
    {
        spawnedHand = null;
        if (assignedHand is not null && SystemLibrary.IsValid(assignedHand))
        {
            assignedHand.InitializeHand(isLeft);
            return assignedHand;
        }
        if (target is null || !SystemLibrary.IsValid(target) || handClass.Equals(default(TSubclassOf<AVRSharpHand>)))
            return null;

        var transform = new FTransform(target.WorldRotation, target.WorldLocation, new FVector(1, 1, 1));
        var hand = SpawnActor(handClass, transform, ESpawnActorCollisionHandlingMethod.AlwaysSpawn);
        if (hand is null || !SystemLibrary.IsValid(hand)) return null;
        hand.InitializeHand(isLeft);
        spawnedHand = hand;
        return hand;
    }

    private static void DestroySpawnedHand(AVRSharpHand? hand)
    {
        if (hand is null || !SystemLibrary.IsValid(hand)) return;
        if (hand.GrabbedObject is { } item && SystemLibrary.IsValid(item)) hand.Release();
        if (SystemLibrary.IsValid(hand)) hand.DestroyActor();
    }

    public override void Tick(float deltaSeconds)
    {
        base.Tick(deltaSeconds);
        if (boundDesktopInput is not null && !SystemLibrary.IsValid(boundDesktopInput)) boundDesktopInput = null;
        if (boundDesktopInput is null && InputComponent is UEnhancedInputComponent input) BindDesktopInput(input);
        if (DesktopMappingContext is not null || mappedContext is not null) RefreshDesktopMapping();
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
