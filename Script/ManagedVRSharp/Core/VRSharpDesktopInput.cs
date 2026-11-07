using UnrealSharp;
using UnrealSharp.Attributes;
using UnrealSharp.CoreUObject;
using UnrealSharp.Engine;
using UnrealSharp.EnhancedInput;

namespace VRSharp.Core;

// Owns desktop input and camera-local targets. The Player keeps all body/hand physics.
[UClass]
public partial class UVRSharpDesktopInput : UActorComponent
{
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial UVRSharpDesktopInputSettings? Settings { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial float EyeHeight { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial float HandMoveSpeed { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial float HandRotateSpeed { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial FVector LeftHandOffset { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial FVector RightHandOffset { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial FRotator LeftHandRotation { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite)] public partial FRotator RightHandRotation { get; set; }

    public UVRSharpDesktopInput()
    {
        EyeHeight = 170;
        HandMoveSpeed = 60;
        HandRotateSpeed = 90;
        LeftHandOffset = new FVector(42, -20, -15);
        RightHandOffset = new FVector(42, 20, -15);
        LeftHandRotation = RightHandRotation = new FRotator(0, -90, 90);
    }

    private AVRSharpPlayer? player;
    private bool active, controlLeft;
    private FVector movement, handMovement, handRotation, fingers;
    private float leftTrigger, rightTrigger, sharedTrigger;
    private (AVRSharpHand Hand, ulong Revision)? leftHold, rightHold;
    private UEnhancedInputComponent? input;
    private APlayerController? controller;
    private UEnhancedInputLocalPlayerSubsystem? subsystem;
    private UInputMappingContext? mapping;
    private bool ownsMapping;
    private readonly List<uint> bindings = new();

    internal void Initialize(AVRSharpPlayer owner)
    {
        player = owner;
        active = true;
        owner.Camera!.LockToHmd = false;
        owner.LeftController!.ComponentTickEnabled = false;
        owner.RightController!.ComponentTickEnabled = false;
        owner.LeftControllerMesh!.SetVisibility(false, true);
        owner.RightControllerMesh!.SetVisibility(false, true);
        ApplyEyeHeight();
    }

    internal FTransform GetHandTarget(bool left)
        => MathLibrary.ComposeTransforms(new FTransform(left ? LeftHandRotation : RightHandRotation,
            left ? LeftHandOffset : RightHandOffset, new FVector(1, 1, 1)), player!.Camera!.WorldTransform);

    internal void Update(float deltaSeconds)
    {
        if (!active || player is null) return;
        RefreshInput();
        if (!float.IsFinite(deltaSeconds) || deltaSeconds <= 0) return;
        float dt = Math.Min(deltaSeconds, .1f);
        // Player's existing movement contract is X=right, Y=forward.
        player.SetMovementInput(new FVector(movement.Y, movement.X, 0));
        EyeHeight = Math.Clamp(EyeHeight + (float)movement.Z * 60 * dt, 65, 200);
        ApplyEyeHeight();
        var offset = controlLeft ? LeftHandOffset : RightHandOffset;
        offset += VRSharpMathHelper.ClampMagnitude(handMovement, 1) * Math.Max(HandMoveSpeed, 0) * dt;
        // Keep desktop targets inside a usable arm-reach envelope.
        offset.X = Math.Clamp(offset.X, 5, 90);
        offset.Y = Math.Clamp(offset.Y, -80, 80);
        offset.Z = Math.Clamp(offset.Z, -90, 40);
        var rotation = controlLeft ? LeftHandRotation : RightHandRotation;
        var axes = VRSharpMathHelper.ClampMagnitude(handRotation, 1);
        float step = Math.Max(HandRotateSpeed, 0) * dt;
        rotation = new FRotator((rotation.Pitch + axes.Y * step) % 360,
            (rotation.Yaw + axes.X * step) % 360, (rotation.Roll + axes.Z * step) % 360);
        if (controlLeft) { LeftHandOffset = offset; LeftHandRotation = rotation; }
        else { RightHandOffset = offset; RightHandRotation = rotation; }
        ApplyHandInput(player.LeftHand, true);
        ApplyHandInput(player.RightHand, false);
    }

    private void ApplyEyeHeight()
    {
        var camera = player!.Camera!;
        camera.SetRelativeLocation(camera.RelativeLocation with { Z = EyeHeight }, false, out _, false);
    }

    private void ApplyHandInput(AVRSharpHand? hand, bool left)
    {
        if (hand is null || !SystemLibrary.IsValid(hand)) return;
        bool selected = left == controlLeft;
        float trigger = Math.Max(left ? leftTrigger : rightTrigger, selected ? sharedTrigger : 0);
        if (hand.IsGrabbing) hand.SetGrabTrigger(trigger);
        else
        {
            hand.SetGrabPosePreviewTrigger(trigger);
            hand.SetFingerInput(selected ? (float)fingers.X : 0,
                Math.Max(selected ? (float)fingers.Y : 0, trigger), selected ? (float)fingers.Z : 0);
        }
    }

    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool IsDesktopInputBound() => active && input is not null && SystemLibrary.IsValid(input);

    [UFunction(FunctionFlags.BlueprintCallable)]
    public string GetDesktopSetupIssues()
    {
        if (Settings is not { } s || !SystemLibrary.IsValid(s)) return "Assign DesktopInput.Settings.";
        return s.MappingContext is null || s.Move is null || s.Look is null || s.LeftGrip is null || s.RightGrip is null
            ? "Desktop settings require MappingContext, Move, Look, LeftGrip and RightGrip." : "";
    }

    private void RefreshInput()
    {
        var next = player!.Controller as APlayerController;
        var nextInput = player.InputComponent as UEnhancedInputComponent;
        if (input is not null && (!SystemLibrary.IsValid(input) || controller != next || input != nextInput)) ClearInput();
        if (input is not null || next is null || nextInput is null || !next.IsLocalController() ||
            GetDesktopSetupIssues().Length != 0) return;
        controller = next;
        input = nextInput;
        subsystem = GetLocalPlayerSubsystem<UEnhancedInputLocalPlayerSubsystem>(next);
        mapping = Settings!.MappingContext;
        if (!subsystem.HasMappingContext(mapping!, out _))
        {
            subsystem.AddMappingContext(mapping!, 0);
            ownsMapping = true;
        }
        Bind(Settings.Move, ETriggerEvent.Triggered, OnMove);
        Bind(Settings.Move, ETriggerEvent.Completed, OnMoveStop);
        Bind(Settings.Move, ETriggerEvent.Canceled, OnMoveStop);
        Bind(Settings.Look, ETriggerEvent.Triggered, OnLook);
        Bind(Settings.LeftGrip, ETriggerEvent.Started, OnLeftGrab);
        Bind(Settings.LeftGrip, ETriggerEvent.Completed, OnLeftRelease);
        Bind(Settings.LeftGrip, ETriggerEvent.Canceled, OnLeftRelease);
        Bind(Settings.RightGrip, ETriggerEvent.Started, OnRightGrab);
        Bind(Settings.RightGrip, ETriggerEvent.Completed, OnRightRelease);
        Bind(Settings.RightGrip, ETriggerEvent.Canceled, OnRightRelease);
        BindAxis(Settings.LeftTrigger, OnLeftTrigger, OnLeftTriggerStop);
        BindAxis(Settings.RightTrigger, OnRightTrigger, OnRightTriggerStop);
        BindAxis(Settings.ActiveTrigger, OnActiveTrigger, OnActiveTriggerStop);
        BindAxis(Settings.HandMove, OnHandMove, OnHandMoveStop);
        BindAxis(Settings.HandRotate, OnHandRotate, OnHandRotateStop);
        BindAxis(Settings.Fingers, OnFingers, OnFingersStop);
        Bind(Settings.SwitchHand, ETriggerEvent.Started, OnSwitchHand);
        Bind(Settings.ToggleGrip, ETriggerEvent.Started, OnToggleGrip);
    }

    private void Bind(UInputAction? action, ETriggerEvent phase, Action<FInputActionValue, float, float, UInputAction> handler)
    {
        if (action is not null && SystemLibrary.IsValid(action) && input!.BindAction(action, phase, handler, out var handle))
            bindings.Add(handle);
    }
    private void BindAxis(UInputAction? action, Action<FInputActionValue, float, float, UInputAction> update,
        Action<FInputActionValue, float, float, UInputAction> stop)
    {
        Bind(action, ETriggerEvent.Triggered, update);
        Bind(action, ETriggerEvent.Completed, stop);
        Bind(action, ETriggerEvent.Canceled, stop);
    }

    private void ClearInput()
    {
        ResetDesktopInput();
        if (input is not null && SystemLibrary.IsValid(input)) foreach (uint h in bindings) input.RemoveBinding(h);
        bindings.Clear();
        if (ownsMapping && subsystem is not null && mapping is not null && SystemLibrary.IsValid(subsystem) && SystemLibrary.IsValid(mapping))
            subsystem.RemoveMappingContext(mapping);
        input = null; controller = null; subsystem = null; mapping = null; ownsMapping = false;
    }

    [UFunction(FunctionFlags.BlueprintCallable)]
    public void ResetDesktopInput()
    {
        Grip(ref leftHold, null, false); Grip(ref rightHold, null, false);
        movement = handMovement = handRotation = fingers = FVector.Zero;
        leftTrigger = rightTrigger = sharedTrigger = 0;
        if (player is null || !SystemLibrary.IsValid(player)) return;
        player.SetMovementInput(FVector.Zero);
        foreach (var hand in new[] { player.LeftHand, player.RightHand })
            if (hand is not null && SystemLibrary.IsValid(hand)) { hand.SetGrabTrigger(0); hand.ClearFingerInput(); }
    }

    internal void Shutdown() { active = false; ClearInput(); player = null; }
    public override void EndPlay(EEndPlayReason reason) { Shutdown(); base.EndPlay(reason); }

    // Input only releases the exact grip revision it acquired, even after switching hands.
    private static void Grip(ref (AVRSharpHand Hand, ulong Revision)? hold, AVRSharpHand? hand, bool pressed)
    {
        if (pressed)
        {
            if (hold.HasValue || hand is null || !SystemLibrary.IsValid(hand) || hand.IsGrabbing) return;
            ulong revision = unchecked(hand.GrabRevision + 1);
            if (hand.TryGrab() && SystemLibrary.IsValid(hand) && hand.GrabRevision == revision) hold = (hand, revision);
        }
        else
        {
            var old = hold; hold = null;
            if (old is { } value && SystemLibrary.IsValid(value.Hand) && value.Hand.IsGrabbing && value.Hand.GrabRevision == value.Revision)
                value.Hand.Release();
        }
    }

    [UFunction] private void OnMove(FInputActionValue v, float e, float t, UInputAction a) => movement = v.GetAxis3D();
    [UFunction] private void OnMoveStop(FInputActionValue v, float e, float t, UInputAction a) => movement = FVector.Zero;
    [UFunction] private void OnLook(FInputActionValue v, float e, float t, UInputAction a)
    {
        var value = v.GetAxis3D();
        if (!double.IsFinite(value.X) || !double.IsFinite(value.Y)) return;
        var origin = player!.VROrigin!; var rotation = origin.RelativeRotation;
        origin.SetRelativeRotation(rotation with { Yaw = (rotation.Yaw + value.X) % 360 }, false, out _, false);
        var camera = player.Camera!; var view = camera.RelativeRotation;
        camera.SetRelativeRotation(view with { Pitch = Math.Clamp(view.Pitch + value.Y, -85, 85) }, false, out _, false);
    }
    [UFunction] private void OnLeftGrab(FInputActionValue v, float e, float t, UInputAction a) => Grip(ref leftHold, player!.LeftHand, true);
    [UFunction] private void OnLeftRelease(FInputActionValue v, float e, float t, UInputAction a) => Grip(ref leftHold, null, false);
    [UFunction] private void OnRightGrab(FInputActionValue v, float e, float t, UInputAction a) => Grip(ref rightHold, player!.RightHand, true);
    [UFunction] private void OnRightRelease(FInputActionValue v, float e, float t, UInputAction a) => Grip(ref rightHold, null, false);
    private static float Trigger(FInputActionValue v) => FingerInput.Normalize((float)v.GetAxis3D().X, 0);
    [UFunction] private void OnLeftTrigger(FInputActionValue v, float e, float t, UInputAction a) => leftTrigger = Trigger(v);
    [UFunction] private void OnLeftTriggerStop(FInputActionValue v, float e, float t, UInputAction a) => leftTrigger = 0;
    [UFunction] private void OnRightTrigger(FInputActionValue v, float e, float t, UInputAction a) => rightTrigger = Trigger(v);
    [UFunction] private void OnRightTriggerStop(FInputActionValue v, float e, float t, UInputAction a) => rightTrigger = 0;
    [UFunction] private void OnActiveTrigger(FInputActionValue v, float e, float t, UInputAction a) => sharedTrigger = Trigger(v);
    [UFunction] private void OnActiveTriggerStop(FInputActionValue v, float e, float t, UInputAction a) => sharedTrigger = 0;
    [UFunction] private void OnHandMove(FInputActionValue v, float e, float t, UInputAction a) => handMovement = v.GetAxis3D();
    [UFunction] private void OnHandMoveStop(FInputActionValue v, float e, float t, UInputAction a) => handMovement = FVector.Zero;
    [UFunction] private void OnHandRotate(FInputActionValue v, float e, float t, UInputAction a) => handRotation = v.GetAxis3D();
    [UFunction] private void OnHandRotateStop(FInputActionValue v, float e, float t, UInputAction a) => handRotation = FVector.Zero;
    [UFunction] private void OnFingers(FInputActionValue v, float e, float t, UInputAction a) => fingers = v.GetAxis3D();
    [UFunction] private void OnFingersStop(FInputActionValue v, float e, float t, UInputAction a) => fingers = FVector.Zero;
    [UFunction] private void OnSwitchHand(FInputActionValue v, float e, float t, UInputAction a)
    { controlLeft = !controlLeft; handMovement = handRotation = fingers = FVector.Zero; sharedTrigger = 0; }
    [UFunction] private void OnToggleGrip(FInputActionValue v, float e, float t, UInputAction a)
    {
        var hand = controlLeft ? player!.LeftHand : player!.RightHand;
        if (hand is null || !SystemLibrary.IsValid(hand)) return;
        if (hand.IsGrabbing) hand.Release(); else hand.TryGrab();
    }
}
