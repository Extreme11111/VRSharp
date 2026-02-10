namespace VRSharp.Core;

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

        // 1. 配置物理胶囊体
        BodyCapsule!.SetCollisionProfileName("VRPlayer");
        BodyCapsule!.SetCapsuleSize(CapsuleRadius, 88.0f);
        BodyCapsule!.SimulatePhysics = true;
        BodyCapsule!.SetUseCCD(true);

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

        // 设置追踪原点为"地面"，确保HMD的高度计算是基于玩家游玩空间的地面。
        UHeadMountedDisplayFunctionLibrary.TrackingOrigin = EHMDTrackingOrigin.LocalFloor;

        // 创建手部
        LeftHand = SpawnActor(LeftHandClass, default, ESpawnActorCollisionHandlingMethod.AlwaysSpawn);
        RightHand = SpawnActor(RightHandClass, default, ESpawnActorCollisionHandlingMethod.AlwaysSpawn);
        LeftHand.InitializeHand(true);
        RightHand.InitializeHand(false);

        GetLocalPlayerSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetPlayerController(0)).AddMappingContext(InputMappingContext, 0);

        if (InputComponent is UEnhancedInputComponent uEnhancedInputComponent)
        {
            LeftHand.InitializeInputEvents(uEnhancedInputComponent);
            RightHand.InitializeInputEvents(uEnhancedInputComponent);
            uEnhancedInputComponent.BindAction(MoveAction!, ETriggerEvent.Triggered, OnMoveInput);
            uEnhancedInputComponent.BindAction(RotateAction!, ETriggerEvent.Triggered, OnRotateInput);
            uEnhancedInputComponent.BindAction(JumpAction!, ETriggerEvent.Triggered, OnJumpInput);
        }
    }

    public override void Tick(float deltaSeconds)
    {
        base.Tick(deltaSeconds);

        // 修正碰撞(匹配身高&水平位移)
        MatchCapsuleHeight();
        MoveCapsuleXYToCamera();

        // 手部跟随
        LeftHand!.PullHand(LeftControllerMesh!.WorldLocation, LeftControllerMesh!.WorldRotation, out var locationForceLeft, out _);
        BodyCapsule!.AddForceAtLocation(-locationForceLeft, LeftHand!.ActorLocation);
        RightHand!.PullHand(RightControllerMesh!.WorldLocation, RightControllerMesh!.WorldRotation, out var locationForceRight, out _);
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
        inputVelocity = inputValue.GetAxis3D();
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
    private void MovementUpdate(float deltaSeconds)
    {
        // 移动方向向量
        FVector moveFwdDir = Camera!.ForwardVector - FVector.Dot(Camera!.ForwardVector, ActorUpVector) * ActorUpVector;
        FVector moveRightDir = -FVector.Cross(moveFwdDir, ActorUpVector);

        CurrentVelocity = moveFwdDir * inputVelocity.Y * AccelerationSpeed * deltaSeconds * 100
                        + moveRightDir * inputVelocity.X * AccelerationSpeed * deltaSeconds * 100;
        if (CurrentVelocity.LengthSquared() > MaxSpeed * MaxSpeed)
        {
            CurrentVelocity = MathLibrary.Normal(CurrentVelocity) * MaxSpeed;
        }

        var force = (CurrentVelocity - BodyCapsule!.GetPhysicsLinearVelocity()) * MoveForce;
        BodyCapsule!.AddForce(force);

        inputVelocity *= 0.9f;
        if (inputVelocity.LengthSquared() < 0.1f)
            inputVelocity = FVector.Zero;
    }

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
        FVector headOffset = Camera!.WorldLocation - ActorLocation;
        headOffset -= FVector.Dot(headOffset, ActorUpVector) * ActorUpVector;
        AddActorWorldOffset(headOffset, false, out _, false);
        VROrigin!.AddWorldOffset(-headOffset, false, out _, false);
    }

    /// <summary>
    /// 匹配胶囊体高度到现实身高
    /// 胶囊体半高为：相机高度 + 胶囊高度补偿
    /// </summary>
    private void MatchCapsuleHeight()
    {
        var height = (float)Camera!.RelativeLocation.Z + CapsuleAdditionalHeight;
        BodyCapsule!.SetCapsuleSize(CapsuleRadius, height / 2 - CapsuleSubHeight / 2);
        VROrigin!.SetRelativeLocation(VROrigin.RelativeLocation with { Z = -height / 2 - CapsuleSubHeight / 2 }, false, out _, false);

        // 根据身高设置速度
        MaxSpeed = MathLibrary.MapRangeClamped(
            height,          // 要映射的输入值 (当前身高)
            ClimbHeight,     // 输入范围的起点 (攀爬高度)
            CrouchHeight,    // 输入范围的终点 (蹲姿高度)
            ClimbMoveSpeed,  // 输出范围的起点 (最低速度)
            MaxMoveSpeed     // 输出范围的终点 (最高速度)
        ).ToFloat();
    }
}
