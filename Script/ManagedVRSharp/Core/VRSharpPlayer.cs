namespace VRSharp.Core;

using System.Collections.Generic;
using UnrealSharp;
using UnrealSharp.Attributes;
using UnrealSharp.Core.Attributes;
using UnrealSharp.CoreUObject;
using UnrealSharp.Engine;
using UnrealSharp.EnhancedInput;
using UnrealSharp.HeadMountedDisplay;
using UnrealSharp.UnrealSharpCore;
using UnrealSharp.XRBase;

[UClass]
public partial class AVRSharpPlayer : APawn
{

    #region 组件定义 (Components Definition)

    // 物理胶囊体，作为根组件，代表玩家在世界中的物理实体。
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, RootComponent = true)]
    public partial UCapsuleComponent? BodyCapsule { get; set; }

    // VR内容的“原点”或“追踪空间”。相机和控制器都附着于此。
    // 它负责处理HMD相对于物理胶囊体的位置偏移。
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, AttachmentComponent = nameof(BodyCapsule))]
    public partial USceneComponent? VROrigin { get; set; }

    // VR相机
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, AttachmentComponent = nameof(VROrigin))]
    public partial UCameraComponent? Camera { get; set; }

    // Camera 局部空间中的颈部标记，可直接在蓝图中调整位置。
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, AttachmentComponent = nameof(Camera))]
    public partial USceneComponent? Neck { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, AttachmentComponent = nameof(Camera))]
    public partial USphereComponent? HeadCollision { get; set; }

    // 左手运动控制器
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, AttachmentComponent = nameof(VROrigin))]
    public partial UMotionControllerComponent? LeftController { get; set; }

    // 右手运动控制器
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, AttachmentComponent = nameof(VROrigin))]
    public partial UMotionControllerComponent? RightController { get; set; }

    // 左手控制器的视觉模型（非手部模型，仅用于调试）
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, AttachmentComponent = nameof(LeftController))]
    public partial UStaticMeshComponent? LeftControllerMesh { get; set; }

    // 右手控制器的视觉模型
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, AttachmentComponent = nameof(RightController))]
    public partial UStaticMeshComponent? RightControllerMesh { get; set; }


    // 左右手
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)] public partial TSubclassOf<AVRSharpHand> LeftHandClass { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)] public partial TSubclassOf<AVRSharpHand> RightHandClass { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRInputSettings")] public partial UInputMappingContext? InputMappingContext { get; set; }


    #endregion

    #region 输入事件 (Input Events)

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRInputActions")]
    public partial UInputAction? MoveAction { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRInputActions")]
    public partial UInputAction? RotateAction { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRInputActions")]
    public partial UInputAction? JumpAction { get; set; }

    #endregion

    #region 移动逻辑 (Movement Logic)

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRMovementSettings")]
    public partial bool EnableMovement { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRMovementSettings")]
    public partial bool EnableJump { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRMovementSettings")]
    public partial float MaxMoveSpeed { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRMovementSettings")]
    public partial float CrouchMoveSpeed { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRMovementSettings")]
    public partial float ClimbMoveSpeed { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRMovementSettings")]
    public partial float MoveForce { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRMovementSettings")]
    public partial float CrouchHeight { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRMovementSettings")]
    public partial float ClimbHeight { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRMovementSettings")]
    public partial float RotateDegree { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRMovementSettings")]
    protected partial float CheckRadius { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRMovementSettings")]
    protected partial float ReleaseRadius { get; set; }

    #endregion

    #region 变量定义 (Variables Definition)

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRBodySettings")]
    public partial float CapsuleRadius { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRBodySettings")]
    public partial float CapsuleAdditionalHeight { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRBodySettings")]
    public partial float CapsuleSubHeight { get; set; }

    #endregion

    #region 内部变量

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRHandSettings")]
    public partial AVRSharpHand? LeftHand { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRHandSettings")]
    public partial AVRSharpHand? RightHand { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRBodySettings")]
    public partial float MaxSpeed { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRBodySettings")]
    protected partial float AccelerationSpeed { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRBodySettings")]
    protected partial FVector CurrentVelocity { get; set; }

    protected FVector inputVelocity;
    protected float height;

    #endregion

    /// <summary>
    /// 构造函数：配置组件的核心属性，特别是物理设置。
    /// </summary>
    public AVRSharpPlayer()
    {
        // 初始化默认值
        EnableMovement = true;
        EnableJump = true;
        CapsuleRadius = 18.0f;
        CapsuleAdditionalHeight = 15.0f;
        CapsuleSubHeight = 0f;
        MaxStepHeight = 35f;
        WalkableSlopeAngle = 46f;
        GroundProbeDistance = 6f;
        MovementResponse = 12f;
        AirControl = 0.15f;
        StepSmoothingSpeed = 10f;

        // 1. 配置物理胶囊体
        BodyCapsule!.SetCollisionProfileName("VRPlayer");
        BodyCapsule!.SetCapsuleSize(CapsuleRadius, 88.0f);
        BodyCapsule!.SimulatePhysics = true;
        BodyCapsule!.SetUseCCD(true);

        Neck!.SetRelativeLocation(new FVector(-5, 0, -12), false, out _, false);
        HeadCollision!.SetSphereRadius(15);
        HeadCollision.SetCollisionProfileName("VRPlayer");
        HeadCollision.SimulatePhysics = false;
        HeadCollision.SetUseCCD(true);

        // 2. 约束运动控制器的旋转，防止玩家角色像球一样转动
        // WORKFLOW 在蓝图约束旋转
        // WORKFLOW 修正控制器偏移

        // 3. 配置运动控制器追踪源
        LeftController!.MotionSource = "Left";
        RightController!.MotionSource = "Right";
    }

    public override void BeginPlay()
    {
        base.BeginPlay();
        TickGroup = ETickingGroup.TG_PrePhysics;
        AddTickPrerequisiteComponent(LeftController!);
        AddTickPrerequisiteComponent(RightController!);

        // Copy custom object-channel responses as well as the named profile.
        HeadCollision!.SetCollisionProfileName(BodyCapsule!.CollisionProfileName);
        HeadCollision.CollisionObjectType = BodyCapsule.CollisionObjectType;
        HeadCollision.CollisionEnabled = BodyCapsule.CollisionEnabled;
        for (int channel = 0; channel < (int)ECollisionChannel.ECC_OverlapAll_Deprecated; channel++)
            HeadCollision.SetCollisionResponseToChannel((ECollisionChannel)channel,
                BodyCapsule.GetCollisionResponseToChannel((ECollisionChannel)channel));

        // 设置追踪原点为"地面"，确保HMD的高度计算是基于玩家游玩空间的地面。
        UHeadMountedDisplayFunctionLibrary.TrackingOrigin = EHMDTrackingOrigin.LocalFloor;

        // 创建手部
        LeftHand = SpawnActor(LeftHandClass, default, ESpawnActorCollisionHandlingMethod.AlwaysSpawn);
        RightHand = SpawnActor(RightHandClass, default, ESpawnActorCollisionHandlingMethod.AlwaysSpawn);
        LeftHand.InitializeHand(true);
        RightHand.InitializeHand(false);
        LeftHand.SetActorTransform(new FTransform(LeftControllerMesh!.WorldRotation, LeftControllerMesh.WorldLocation, LeftHand.ActorScale3D), false, out _, true);
        RightHand.SetActorTransform(new FTransform(RightControllerMesh!.WorldRotation, RightControllerMesh.WorldLocation, RightHand.ActorScale3D), false, out _, true);

        GetLocalPlayerSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetPlayerController(0)).AddMappingContext(InputMappingContext, 0);

        if (InputComponent is UEnhancedInputComponent uEnhancedInputComponent)
        {
            LeftHand.InitializeInputEvents(uEnhancedInputComponent);
            RightHand.InitializeInputEvents(uEnhancedInputComponent);
            uEnhancedInputComponent.BindAction(MoveAction!, ETriggerEvent.Triggered, OnMoveInput);
            uEnhancedInputComponent.BindAction(MoveAction!, ETriggerEvent.Completed, OnMoveInput);
            uEnhancedInputComponent.BindAction(MoveAction!, ETriggerEvent.Canceled, OnMoveInput);
            uEnhancedInputComponent.BindAction(RotateAction!, ETriggerEvent.Triggered, OnRotateInput);
            uEnhancedInputComponent.BindAction(JumpAction!, ETriggerEvent.Triggered, OnJumpInput);
        }
    }

    public override void Tick(float deltaSeconds)
    {
        base.Tick(deltaSeconds);

        // 修正碰撞(匹配身高&水平位移)
        stepVisualOffset *= Math.Exp(-Math.Max(StepSmoothingSpeed, 0) * deltaSeconds);
        MoveCapsuleXYToCamera();
        MatchCapsuleHeight();
        ConstrainHeadCollision();

        // 手部跟随
        var locationForceLeft = LeftHand!.UpdateTracking(LeftControllerMesh!.WorldLocation, LeftControllerMesh!.WorldRotation, deltaSeconds);
        BodyCapsule!.AddForceAtLocation(-locationForceLeft, LeftHand!.ActorLocation);
        var locationForceRight = RightHand!.UpdateTracking(RightControllerMesh!.WorldLocation, RightControllerMesh!.WorldRotation, deltaSeconds);
        BodyCapsule!.AddForceAtLocation(-locationForceRight, RightHand!.ActorLocation);

        // 移动
        if (EnableMovement)
        {
            MovementUpdate(deltaSeconds);
        }

        // 检测手部距离，过远则强制松开
        CheckHandDistance();
    }

    [UFunction]
    private void OnMoveInput(FInputActionValue inputValue, float arg1, float arg2, UInputAction uInputAction)
    {
        SetMovementInput(inputValue.GetAxis3D());
    }
    [UFunction]
    private void OnRotateInput(FInputActionValue inputValue, float arg1, float arg2, UInputAction uInputAction)
    {
        var val = inputValue.GetAxis1D();
        AddActorLocalRotation(new FRotator(0, RotateDegree * MathF.Sign(val), 0), false, out _, false);
        var camPrevious = Camera!.WorldLocation;
        VROrigin!.AddLocalRotation(new FRotator(0, RotateDegree * MathF.Sign(val), 0), false, out _, false);
        VROrigin!.AddWorldOffset(camPrevious - Camera!.WorldLocation, false, out _, false);

    }
    [UFunction]
    private void OnJumpInput(FInputActionValue inputValue, float arg1, float arg2, UInputAction uInputAction)
    {

    }

    /// <summary>
    /// 移动逻辑
    /// </summary>
    /// <param name="deltaSeconds"></param>
    /// <summary>
    /// 检测手部与玩家距离，超出 ReleaseRadius 时强制松开抓握
    /// </summary>
    private void CheckHandDistance()
    {
        if (LeftHand!.IsGrabbing && FVector.Distance(LeftHand.ActorLocation, ActorLocation) > ReleaseRadius)
            LeftHand.Release();

        if (RightHand!.IsGrabbing && FVector.Distance(RightHand.ActorLocation, ActorLocation) > ReleaseRadius)
            RightHand.Release();
    }

    /// <summary>
    /// 身体始终和头部在相同水平位置。
    /// 应用现实世界的移动
    /// </summary>
    /// <param name="deltaSeconds"></param>
    private void MoveCapsuleXYToCamera()
    {
        FVector headOffset = Neck!.WorldLocation - ActorLocation;
        headOffset -= FVector.Dot(headOffset, ActorUpVector) * ActorUpVector;
        var previous = ActorLocation;
        AddActorWorldOffset(headOffset, true, out _, true);
        // Only compensate the displacement that collision actually allowed.
        VROrigin!.AddWorldOffset(previous - ActorLocation, false, out _, false);
    }

    /// <summary>
    /// 匹配胶囊体高度到现实身高
    /// 胶囊体半高为：相机高度 + 胶囊高度补偿
    /// </summary>
    private void MatchCapsuleHeight()
    {
        var body = BodyCapsule!;
        float oldHalfHeight = body.ScaledCapsuleHalfHeight;
        // 保留旧参数语义：AdditionalHeight 是头顶余量，SubHeight 是脚底升高差。
        // 默认球半径 15、AdditionalHeight 15 时，球心恰好位于 Camera。
        HeadCollision!.SetRelativeLocation(HeadCollision.RelativeLocation with
        { Z = CapsuleAdditionalHeight - HeadCollision.UnscaledSphereRadius }, false, out _, false);
        float height = (float)Camera!.RelativeLocation.Z + CapsuleAdditionalHeight;
        float halfHeight = oldHalfHeight;
        if (Camera.RelativeLocation.Z > 20)
        {
            // 在追踪空间计算高度，避免身体中心下降后反过来改变 HMD 高度。
            var head = VROrigin!.WorldTransform.InverseTransformPosition(HeadCollision.WorldLocation);
            var bodyLocal = VROrigin.WorldTransform.InverseTransformPosition(body.WorldLocation);
            double dx = head.X - bodyLocal.X, dy = head.Y - bodyLocal.Y;
            double radiusSum = CapsuleRadius + HeadCollision.ScaledSphereRadius;
            double horizontalSquared = dx * dx + dy * dy;
            // 胶囊顶端是半球：两球心间距为半径之和时才真正相切。
            double top = head.Z - Math.Sqrt(Math.Max(radiusSum * radiusSum - horizontalSquared, 0)) + CapsuleRadius;
            halfHeight = Math.Max(CapsuleRadius, (float)(top - CapsuleSubHeight) * 0.5f);
        }
        float change = halfHeight - oldHalfHeight;
        if (Math.Abs(change) > 0.25f)
        {
            var target = ActorLocation + new FVector(0, 0, change);
            // Keep the feet fixed while crouching; reject growth into a low ceiling.
            bool blocked = change > 0 && SystemLibrary.CapsuleTraceByProfile(
                target, target + new FVector(0, 0, 0.01), Math.Max(CapsuleRadius - Skin, 1),
                Math.Max(halfHeight - Skin, CapsuleRadius), body.CollisionProfileName,
                false, MovementIgnoredActors, EDrawDebugTrace.None, out _, true);
            if (!blocked)
            {
                if (change < 0) body.SetCapsuleSize(CapsuleRadius, halfHeight);
                SetActorLocation(target, false, out _, true);
                if (change > 0) body.SetCapsuleSize(CapsuleRadius, halfHeight);
            }
        }
        VROrigin!.SetRelativeLocation(VROrigin.RelativeLocation with
        {
            Z = -body.ScaledCapsuleHalfHeight - CapsuleSubHeight + stepVisualOffset
        }, false, out _, false);

        // 根据身高设置速度
        MaxSpeed = MathLibrary.MapRangeClamped(
            height,          // 要映射的输入值 (当前身高)
            ClimbHeight,     // 输入范围的起点 (攀爬高度)
            CrouchHeight,    // 输入范围的终点 (蹲姿高度)
            ClimbMoveSpeed,  // 输出范围的起点 (最低速度)
            MaxMoveSpeed     // 输出范围的终点 (最高速度)
        ).ToFloat();
    }

    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite), Category("VRMovementSettings|Ground")]
    public partial float MaxStepHeight { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite), Category("VRMovementSettings|Ground")]
    public partial float WalkableSlopeAngle { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite), Category("VRMovementSettings|Ground")]
    public partial float GroundProbeDistance { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite), Category("VRMovementSettings")]
    public partial float MovementResponse { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite), Category("VRMovementSettings")]
    public partial float AirControl { get; set; }
    [UProperty(PropertyFlags.EditAnywhere | PropertyFlags.BlueprintReadWrite), Category("VRMovementSettings|Ground")]
    public partial float StepSmoothingSpeed { get; set; }

    private FVector previousHeadLocation;
    private bool hasHeadLocation;

    private void ConstrainHeadCollision()
    {
        var desired = HeadCollision!.WorldLocation;
        // Child collision shapes do not participate in the root capsule's movement sweep.
        // Sweep the tracked head explicitly so a low beam cannot be bypassed by the HMD.
        if (hasHeadLocation && HeadCollision.IsQueryCollisionEnabled()
            && SystemLibrary.SphereTraceByProfile(previousHeadLocation, desired,
                HeadCollision.ScaledSphereRadius, HeadCollision.CollisionProfileName, false,
                MovementIgnoredActors, EDrawDebugTrace.None, out var hit, true)
            && !hit.StartPenetrating)
        {
            VROrigin!.AddWorldOffset(hit.Location - desired, false, out _, false);
        }
        previousHeadLocation = HeadCollision.WorldLocation;
        hasHeadLocation = true;
    }

    private const float Skin = 0.5f;
    private double stepVisualOffset;
    private bool wasGrounded;
    private List<AActor>? movementIgnoredActors;
    private List<AActor> MovementIgnoredActors => movementIgnoredActors ??= [this, LeftHand!, RightHand!];
    private double WalkableNormalZ => Math.Cos(Math.Clamp(WalkableSlopeAngle, 0, 75) * Math.PI / 180);

    // Shared input entry for XR, desktop controls and scripted movement.
    [UFunction(FunctionFlags.BlueprintCallable)]
    public void SetMovementInput(FVector axes)
    {
        axes.Z = 0;
        inputVelocity = axes.LengthSquared() > 1 ? MathLibrary.Normal(axes) : axes;
    }

    private bool SweepBody(FVector start, FVector end, out FHitResult hit)
    {
        var body = BodyCapsule!;
        return SystemLibrary.CapsuleTraceByProfile(start, end,
            Math.Max(body.ScaledCapsuleRadius - Skin, 1),
            Math.Max(body.ScaledCapsuleHalfHeight - Skin, body.ScaledCapsuleRadius),
            body.CollisionProfileName, false, MovementIgnoredActors, EDrawDebugTrace.None, out hit, true);
    }

    private bool FindGround(float distance, out FHitResult hit) =>
        SweepBody(ActorLocation + new FVector(0, 0, 2), ActorLocation - new FVector(0, 0, distance), out hit)
        && !hit.StartPenetrating && hit.ImpactNormal.Z >= WalkableNormalZ;

    private void MovementUpdate(float deltaSeconds)
    {
        if (deltaSeconds <= 0 || !float.IsFinite(deltaSeconds)) return;
        var body = BodyCapsule!;
        var velocity = body.GetPhysicsLinearVelocity();
        var grounded = FindGround(Math.Max(GroundProbeDistance, 2), out var floor)
            && FVector.Dot(velocity, floor.ImpactNormal) < 80;

        // Follow small drops only from a supported state, never during a jump or fall.
        if (!grounded && wasGrounded && velocity.Z <= 0 && MaxStepHeight > 0
            && FindGround(MaxStepHeight, out var lowerFloor))
        {
            MoveGroundedBody(lowerFloor.Location + new FVector(0, 0, Skin));
            grounded = true;
            floor = lowerFloor;
        }

        var forward = MathLibrary.Normal(Camera!.ForwardVector with { Z = 0 });
        if (forward.LengthSquared() < 0.5) forward = MathLibrary.Normal(ActorForwardVector with { Z = 0 });
        var right = new FVector(-forward.Y, forward.X, 0);
        var direction = forward * inputVelocity.Y + right * inputVelocity.X;
        double amount = Math.Min(Math.Sqrt(direction.LengthSquared()), 1);
        var horizontal = amount > 0.001 ? MathLibrary.Normal(direction) : FVector.Zero;

        if (grounded && amount > 0.001 && MaxStepHeight > 0)
        {
            TryStepUp(horizontal, Math.Max(Math.Sqrt((velocity with { Z = 0 }).LengthSquared()), 30) * deltaSeconds);
            grounded = FindGround(Math.Max(GroundProbeDistance, 2), out floor);
            velocity = body.GetPhysicsLinearVelocity();
        }

        var normal = grounded ? floor.ImpactNormal : new FVector(0, 0, 1);
        var tangent = direction - FVector.Dot(direction, normal) * normal;
        CurrentVelocity = MathLibrary.Normal(tangent) * Math.Max(MaxSpeed, 0) * amount;
        // Preserve the normal component: gravity, jumping and hand pull still work.
        var error = CurrentVelocity - velocity;
        error -= FVector.Dot(error, normal) * normal;
        double response = Math.Max(MovementResponse, 0) * (grounded ? 1 : Math.Clamp(AirControl, 0, 1));
        var impulse = error * (1 - Math.Exp(-response * deltaSeconds));
        double limit = Math.Max(AccelerationSpeed, 0) * deltaSeconds * (grounded ? 1 : Math.Clamp(AirControl, 0, 1));
        if (impulse.LengthSquared() > limit * limit) impulse = MathLibrary.Normal(impulse) * limit;
        body.AddImpulse(impulse, velChange: true);
        wasGrounded = grounded;
    }

    private void TryStepUp(FVector direction, double travel)
    {
        var start = ActorLocation;
        if (!SweepBody(start, start + direction * (travel + Skin), out var obstacle)
            || obstacle.StartPenetrating || obstacle.ImpactNormal.Z >= WalkableNormalZ) return;

        var up = new FVector(0, 0, MaxStepHeight + 2 * Skin);
        if (SweepBody(start, start + up, out _)) return;
        // Advance beyond the rounded capsule edge so the centre has real support.
        var advance = direction * (travel + BodyCapsule!.ScaledCapsuleRadius + 2 * Skin);
        var raised = start + up;
        if (SweepBody(raised, raised + advance, out _)) return;
        if (!SweepBody(raised + advance, start + advance - new FVector(0, 0, 2), out var landing)
            || landing.StartPenetrating || landing.ImpactNormal.Z < WalkableNormalZ) return;
        double rise = landing.Location.Z + Skin - start.Z;
        if (rise <= Skin || rise > MaxStepHeight + Skin) return;

        var foot = landing.Location - new FVector(0, 0, BodyCapsule.ScaledCapsuleHalfHeight - Skin);
        if (!SystemLibrary.LineTraceByProfile(foot + new FVector(0, 0, 3), foot - new FVector(0, 0, 3),
            BodyCapsule.CollisionProfileName, false, MovementIgnoredActors, EDrawDebugTrace.None,
            out var support, true) || support.ImpactNormal.Z < WalkableNormalZ) return;

        var velocity = BodyCapsule.GetPhysicsLinearVelocity();
        // Preflight all three legs, then sweep the actual body; never teleport through a wall.
        SetActorLocation(raised, true, out var upHit, true);
        if (upHit.BlockingHit) { SetActorLocation(start, false, out _, true); return; }
        SetActorLocation(raised + advance, true, out var forwardHit, true);
        if (forwardHit.BlockingHit) { SetActorLocation(start, false, out _, true); return; }
        SetActorLocation(landing.Location + new FVector(0, 0, Skin), true, out _, true);
        BodyCapsule.SetPhysicsLinearVelocity(velocity with { Z = Math.Max(velocity.Z, 0) });
        ApplyStepVisualOffset(ActorLocation.Z - start.Z);
    }

    private void MoveGroundedBody(FVector destination)
    {
        var previous = ActorLocation;
        SetActorLocation(destination, true, out _, true);
        ApplyStepVisualOffset(ActorLocation.Z - previous.Z);
    }

    private void ApplyStepVisualOffset(double rise)
    {
        stepVisualOffset = Math.Clamp(stepVisualOffset - rise, -Math.Max(MaxStepHeight, 0), Math.Max(MaxStepHeight, 0));
        VROrigin!.SetRelativeLocation(VROrigin.RelativeLocation with
        { Z = -BodyCapsule!.ScaledCapsuleHalfHeight - CapsuleSubHeight + stepVisualOffset }, false, out _, false);
    }
}
