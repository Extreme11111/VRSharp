namespace VRSharp.Core;

using System.Collections.Generic;
using UnrealSharp;
using UnrealSharp.Attributes;
using UnrealSharp.Chaos;
using UnrealSharp.Core.Attributes;
using UnrealSharp.CoreUObject;
using UnrealSharp.Engine;
using UnrealSharp.EnhancedInput;

[UClass]
public partial class AVRSharpHand : AActor
{
    #region 组件定义
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, RootComponent = true)] public partial UBoxComponent? HandRigidbody { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, AttachmentComponent = nameof(HandRigidbody))] public partial USkeletalMeshComponent? HandMesh { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, AttachmentComponent = nameof(HandRigidbody))] public partial USphereComponent? GrabSphere { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, AttachmentComponent = nameof(HandRigidbody))] public partial UBoxComponent? CollisionBox { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere, DefaultComponent = true, AttachmentComponent = nameof(HandRigidbody))] protected partial USceneComponent? Palm { get; set; }

    #endregion

    #region 抓握

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial TArray<EObjectTypeQuery>? GrabObjectTypes { get; set; }

    #endregion

    #region 输入事件

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRInputActions")]
    public partial UInputAction? AxisAction { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRInputActions")]
    public partial UInputAction? StickAction { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRInputActions")]
    public partial UInputAction? GripAction { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRInputActions")]
    public partial UInputAction? TriggerAction { get; set; }
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere)]
    public partial UInputAction? AnalogTriggerAction { get; set; }
    private bool xrTriggerBound;
    private float xrTrigger;


    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRInputActions")]
    public partial UInputAction? AXAction { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRInputActions")]
    public partial UInputAction? BYAction { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRInputActions")]
    public partial UInputAction? TouchedAction { get; set; }

    #endregion

    #region 动画权重

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRAnimationWeight")]
    public partial float GraspWeight { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRAnimationWeight")]
    public partial float IndexWeight { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRAnimationWeight")]
    public partial float ThumbWeight { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRAnimationBoneNames")]
    public partial string? ThumbName { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRAnimationBoneNames")]
    public partial string? IndexName { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRAnimationBoneNames")]
    public partial string? MiddleName { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRAnimationBoneNames")]
    public partial string? RingName { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRAnimationBoneNames")]
    public partial string? PinkyName { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRAnimationWeight")]
    public partial float FingerRadius { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRAnimationWeight")]
    public partial bool DebugMode { get; set; }

    private float targetGraspWeight;
    private float targetIndexWeight;
    private float targetThumbWeight;
    private UVRSharpHandPose? animationPose;
    private float poseBlendWeight;
    private bool poseExiting;
    private float exitPoseTrigger;

    // Visual pose survives logical release until its configured fade has completed.
    [UFunction(FunctionFlags.BlueprintCallable)]
    public UVRSharpHandPose? GetAnimationGrabPose()
        => animationPose is not null && SystemLibrary.IsValid(animationPose) ? animationPose : null;
    [UFunction(FunctionFlags.BlueprintCallable)]
    public float GetGrabPoseBlendWeight() => GetAnimationGrabPose() is null ? 0 : poseBlendWeight;
    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool IsGrabPoseExiting() => GetAnimationGrabPose() is not null && poseExiting;

    [UFunction(FunctionFlags.BlueprintCallable)]
    public float GetGrabAnimationTrigger()
    {
        if (GetAnimationGrabPose() is null) return 0;
        return poseExiting ? exitPoseTrigger : activePoseTrigger;
    }

    private void BeginPoseAnimation(UVRSharpHandPose? pose)
    {
        animationPose = pose;
        poseExiting = false;
        exitPoseTrigger = 0;
        poseBlendWeight = pose is not null && float.IsFinite(pose.EnterBlendSeconds) && pose.EnterBlendSeconds > 0 ? 0 : 1;
        if (pose is null) poseBlendWeight = 0;
    }

    private void AdvancePoseAnimation(float deltaSeconds)
    {
        var pose = GetAnimationGrabPose();
        if (pose is null) { animationPose = null; poseBlendWeight = 0; poseExiting = false; return; }
        if (!float.IsFinite(deltaSeconds) || deltaSeconds <= 0) return;
        float duration = poseExiting ? pose.ExitBlendSeconds : pose.EnterBlendSeconds;
        float step = float.IsFinite(duration) && duration > 0 ? deltaSeconds / duration : 1;
        poseBlendWeight = Math.Clamp(poseBlendWeight + (poseExiting ? -step : step),0,1);
        if (poseExiting && poseBlendWeight == 0) { animationPose = null; poseExiting = false; }
    }

    private UVRSharpHandPose? activeGrabPose;
    private float activePoseTrigger;
    // Only changed accepted values; context is the actual held primitive.
    public event Action<AVRSharpHand, UVRSharpGrabbable, UPrimitiveComponent, float>? GrabTriggerChanged;
    public event Action<AVRSharpHand, UVRSharpHandPose>? GrabPoseEntered;
    public event Action<AVRSharpHand, UVRSharpHandPose>? GrabPoseExited;
    [UFunction(FunctionFlags.BlueprintCallable)]
    public UVRSharpHandPose? GetActiveGrabPose()
        => activeGrabPose is not null && SystemLibrary.IsValid(activeGrabPose) ? activeGrabPose : null;
    [UFunction(FunctionFlags.BlueprintCallable)]
    public float GetGrabPoseTrigger() => activePoseTrigger;

    private bool useAuthoredFingerWeights;
    private bool useTriggerBlend;
    private float authoredIndexWeight, triggerIndexWeight;
    private bool externalFingerInput;

    #endregion

    #region 变量定义

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings")]
    public partial bool IsLeft { get; set; }

    /// <summary>质量归一化位置刚度，单位 s^-2。</summary>
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings"), ToolTip("位置响应刚度 (s^-2)，独立于手质量。临界阻尼为 2*sqrt(LocationStiffness)。")]
    protected partial float LocationStiffness { get; set; }

    /// <summary>质量归一化位置阻尼，单位 s^-1。</summary>
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings"), ToolTip("位置阻尼 (s^-1)。运行时不会低于临界值 2*sqrt(LocationStiffness)。")]
    protected partial float LocationDamping { get; set; }

    /// <summary>惯量归一化旋转刚度，单位 s^-2。</summary>
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings"), ToolTip("旋转响应刚度 (s^-2)，独立于质量、转动惯量与左右手镜像。")]
    protected partial float RotationStiffness { get; set; }

    /// <summary>惯量归一化旋转阻尼，单位 s^-1。</summary>
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings"), ToolTip("旋转阻尼 (s^-1)。运行时不会低于临界值 2*sqrt(RotationStiffness)。")]
    protected partial float RotationDamping { get; set; }

    /// <summary>VRPhysicsHandSettings: default 80,000</summary>
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings"), ToolTip("default 80,000")]
    protected partial float MaxForce { get; set; }

    /// <summary>VRPhysicsHandSettings: default 80,000</summary>
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings"), ToolTip("default 80,000")]
    protected partial float MaxTorque { get; set; }

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings"), ToolTip("向玩家身体传递拉力的标定系数，不是手的物理质量。降低手质量时可保留攀爬拉力。")]
    protected partial float BodyPullStrength { get; set; }

    private UPhysicsSettings? physicsSettings;
    private bool hasTrackingTarget;
    private FVector previousTargetLocation;
    private FQuat previousTargetRotation;

    #endregion


    public event Action<AVRSharpHand, UVRSharpGrabbable, UPrimitiveComponent>? Grabbed;
    public event Action<AVRSharpHand, UVRSharpGrabbable, UPrimitiveComponent>? Released;
    internal void NotifyGrabbed(UVRSharpGrabbable item, UPrimitiveComponent component)
        => Grabbed?.Invoke(this, item, component);
    internal void NotifyReleased(UVRSharpGrabbable item, UPrimitiveComponent component)
        => Released?.Invoke(this, item, component);

    [UFunction(FunctionFlags.BlueprintCallable)]
    public UPrimitiveComponent? GetCurrentGrabComponent()
        => IsGrabbing && GrabbedObject is { } item && SystemLibrary.IsValid(item)
            ? item.GetHeldComponent(this) : null;

    #region  抓握事件

    public event Action<UVRSharpGrabbable?>? OnBeforeGrab;
    public event Action<UVRSharpGrabbable?>? OnAfterGrab;
    public event Action<UVRSharpGrabbable?>? OnBeforeRelease;
    public event Action<UVRSharpGrabbable?>? OnAfterRelease;
    public event Action<UVRSharpGrabbable?>? OnEnterHighlighted;
    public event Action<UVRSharpGrabbable?>? OnExitHighlighted;

    #endregion

    #region  内部变量

    [UProperty(PropertyFlags.BlueprintCallable)] public partial bool IsGrabbing { get; set; }
    [UProperty(PropertyFlags.BlueprintCallable)] public partial UVRSharpGrabbable? GrabbedObject { get; set; }
    [UProperty(PropertyFlags.BlueprintCallable)] public partial UVRSharpGrabbable? HighlightedObject { get; set; }

    private FHitResult? highlightedHitResult = null;
    private List<FHitResult> targetHitResults = [];

    #endregion

    /// <summary>
    /// 初始化手
    /// </summary>
    /// <param name="isLeft"></param>
    public void InitializeHand(bool isLeft)
    {
        IsLeft = isLeft;
        physicsSettings = GetDefault<UPhysicsSettings>();
        hasTrackingTarget = false;
        if (IsLeft)
        {
            // HandRigidbody!.RelativeScale3D = new(-HandRigidbody!.RelativeScale3D.X, HandRigidbody!.RelativeScale3D.Y, HandRigidbody!.RelativeScale3D.Z);
        }

        HandRigidbody!.SetBoxExtent(FVector.Zero);
        HandRigidbody!.SimulatePhysics = true;
        HandRigidbody!.SetUseCCD(true);
        HandRigidbody!.SetCollisionProfileName("VRHand");
        GrabSphere!.SetCollisionProfileName("NoCollision");
        CollisionBox!.SetCollisionProfileName("VRHand");
        HandMesh!.SetCollisionProfileName("VRHand");
        // WORKFLOW 在蓝图设置碰撞形状

        // GrabObjectTypes = [EObjectTypeQuery.ObjectTypeQuery1, EObjectTypeQuery.ObjectTypeQuery2, EObjectTypeQuery.ObjectTypeQuery3, EObjectTypeQuery.ObjectTypeQuery4, EObjectTypeQuery.ObjectTypeQuery5, EObjectTypeQuery.ObjectTypeQuery6, EObjectTypeQuery.ObjectTypeQuery7, EObjectTypeQuery.ObjectTypeQuery8, EObjectTypeQuery.ObjectTypeQuery9, EObjectTypeQuery.ObjectTypeQuery10, EObjectTypeQuery.ObjectTypeQuery11, EObjectTypeQuery.ObjectTypeQuery12, EObjectTypeQuery.ObjectTypeQuery13, EObjectTypeQuery.ObjectTypeQuery14, EObjectTypeQuery.ObjectTypeQuery15, EObjectTypeQuery.ObjectTypeQuery16, EObjectTypeQuery.ObjectTypeQuery17, EObjectTypeQuery.ObjectTypeQuery18, EObjectTypeQuery.ObjectTypeQuery19, EObjectTypeQuery.ObjectTypeQuery20, EObjectTypeQuery.ObjectTypeQuery21, EObjectTypeQuery.ObjectTypeQuery22, EObjectTypeQuery.ObjectTypeQuery23, EObjectTypeQuery.ObjectTypeQuery24, EObjectTypeQuery.ObjectTypeQuery25, EObjectTypeQuery.ObjectTypeQuery26, EObjectTypeQuery.ObjectTypeQuery27, EObjectTypeQuery.ObjectTypeQuery28, EObjectTypeQuery.ObjectTypeQuery29, EObjectTypeQuery.ObjectTypeQuery30, EObjectTypeQuery.ObjectTypeQuery31, EObjectTypeQuery.ObjectTypeQuery32];

    }

    public void InitializeInputEvents(UEnhancedInputComponent inputComponent)
    {
        // 抓握输入
        inputComponent.BindAction(GripAction!, ETriggerEvent.Started, OnGripStarted, out _);
        inputComponent.BindAction(GripAction!, ETriggerEvent.Completed, OnGripReleased, out _);

        // 动画输入
        inputComponent.BindAction(TouchedAction!, ETriggerEvent.Started, ThumbTouchedAnim, out _);
        inputComponent.BindAction(AXAction!, ETriggerEvent.Started, ThumbClickedAnim, out _);
        inputComponent.BindAction(BYAction!, ETriggerEvent.Started, ThumbClickedAnim, out _);
        var triggerAction = AnalogTriggerAction ?? TriggerAction;
        if (triggerAction is not null)
        {
            if (AnalogTriggerAction is not null)
                inputComponent.BindAction(triggerAction, ETriggerEvent.Triggered, OnAnalogTrigger, out _);
            else
                inputComponent.BindAction(triggerAction, ETriggerEvent.Started, IndexClickedAnim, out _);
            inputComponent.BindAction(triggerAction, ETriggerEvent.Completed, IndexReleasedAnim, out _);
            inputComponent.BindAction(triggerAction, ETriggerEvent.Canceled, IndexReleasedAnim, out _);
            xrTriggerBound = true;
        }
        inputComponent.BindAction(GripAction!, ETriggerEvent.Started, GraspClickedAnim, out _);

        inputComponent.BindAction(TouchedAction!, ETriggerEvent.Completed, ThumbReleasedAnim, out _);
        inputComponent.BindAction(AXAction!, ETriggerEvent.Completed, ThumbReleasedAnim, out _);
        inputComponent.BindAction(BYAction!, ETriggerEvent.Completed, ThumbReleasedAnim, out _);
        inputComponent.BindAction(GripAction!, ETriggerEvent.Completed, GraspReleasedAnim, out _);
    }

    override public void Tick(float deltaSeconds)
    {
        base.Tick(deltaSeconds);
        AdvancePoseAnimation(deltaSeconds);
        ApplyXrTrigger();
        if (!IsGrabbing)
            RefreshGrabTarget();

        if (IsGrabbing)
        {
            if (!useAuthoredFingerWeights) UpdateGrabAnimation(deltaSeconds);
            UpdateAnimationWeights(deltaSeconds, 0.20f);
        }
        else
        {
            UpdateAnimationWeights(deltaSeconds, 0.15f);
        }
    }

    /// <summary>
    /// 将手拉向控制器位置
    /// </summary>
    /// <param name="targetLocation"></param>
    /// <param name="targetRotation"></param>
    /// <param name="locationForce"></param>
    /// <param name="rotationForce"></param>
    public void PullHand(FVector targetLocation, FQuat targetRotation, out FVector locationForce, out FVector rotationForce)
        => PullHand(targetLocation, targetRotation, (float)WorldDeltaSeconds, out locationForce, out rotationForce);

    /// <summary>提交一帧追踪目标，供 VR、桌面或蓝图控制器共用；返回向玩家传递的拉力。</summary>
    [UFunction(FunctionFlags.BlueprintCallable)]
    public FVector UpdateTracking(FVector targetLocation, FQuat targetRotation, float deltaSeconds)
    {
        PullHand(targetLocation, targetRotation, deltaSeconds, out var force, out _);
        return force;
    }

    public void PullHand(FVector targetLocation, FQuat targetRotation, float deltaSeconds, out FVector locationForce, out FVector rotationForce)
    {
        locationForce = rotationForce = FVector.Zero;
        if (HandRigidbody is not { } body || !float.IsFinite(deltaSeconds) || deltaSeconds <= 0)
            return;

        physicsSettings ??= GetDefault<UPhysicsSettings>();
        // Chaos 对卡顿帧的物理时间也会截断；必须使用同一个有效时间步。
        float h = Math.Min(deltaSeconds, Math.Max(physicsSettings.MaxPhysicsDeltaTime, 1e-6f));

        FVector targetVelocity = FVector.Zero;
        FVector targetAngularVelocity = FVector.Zero;
        if (hasTrackingTarget && deltaSeconds <= 0.1f && FVector.DistanceSquared(targetLocation, previousTargetLocation) < 10000)
        {
            targetVelocity = (targetLocation - previousTargetLocation) / deltaSeconds;
            targetAngularVelocity = VRSharpMathHelper.RotationVector(targetRotation, previousTargetRotation) / deltaSeconds;
        }
        previousTargetLocation = targetLocation;
        previousTargetRotation = targetRotation;
        hasTrackingTarget = true;

        // Weld 后手组件不再拥有独立刚体，必须读取并驱动被抓物体的物理岛。
        var rigidbody = IsGrabbing && GetCurrentGrabComponent() is { } grabbedBody ? grabbedBody : body;
        var angularVelocity = rigidbody.GetPhysicsAngularVelocityInRadians();
        var angularAcceleration = VRSharpMathHelper.ComputeSpringAcceleration(
            VRSharpMathHelper.RotationVector(targetRotation, body.WorldRotation),
            targetAngularVelocity - angularVelocity,
            RotationStiffness, RotationDamping, h);
        rotationForce = rigidbody.ScaleByMomentOfInertia(angularAcceleration);
        double torqueLength = rotationForce.Length();
        if (torqueLength > MaxTorque && torqueLength > 0)
            angularAcceleration *= Math.Max(MaxTorque, 0) / torqueLength;
        rotationForce = VRSharpMathHelper.ClampMagnitude(rotationForce, MaxTorque);

        // 用跟随点处的速度计算阻尼。COM 速度不能代表偏心抓握点的速度。
        var linearAcceleration = VRSharpMathHelper.ComputeSpringAcceleration(
            targetLocation - body.WorldLocation,
            targetVelocity - rigidbody.GetPhysicsLinearVelocityAtPoint(body.WorldLocation),
            LocationStiffness, LocationDamping, h);
        locationForce = VRSharpMathHelper.ClampMagnitude(linearAcceleration * Math.Max(BodyPullStrength, 0), MaxForce);

        if (rigidbody.IsSimulatingPhysics())
        {
            float mass = Math.Max(rigidbody.Mass, 1e-6f);
            if (IsGrabbing)
            {
                // 抓握时保留杠杆作用：双手不同抓点仍然能够转动物体。
                int count = Math.Max(GrabbedObject?.GrabCount ?? 1, 1);
                // 沿当前驱动方向计算抓点有效质量，避免用无关的最小惯量过度削弱阻尼。
                var inertia = rigidbody.GetInertiaTensor();
                var lever = body.WorldLocation - rigidbody.GetCenterOfMass();
                double accelerationLength = linearAcceleration.Length();
                var direction = accelerationLength > 1e-6 ? linearAcceleration / accelerationLength : FVector.Zero;
                var localTorque = FQuat.Inverse(rigidbody.WorldRotation).RotateVector(FVector.Cross(lever, direction));
                double inverseMass = 1 / mass + localTorque.X * localTorque.X / Math.Max(inertia.X, 1e-6)
                    + localTorque.Y * localTorque.Y / Math.Max(inertia.Y, 1e-6)
                    + localTorque.Z * localTorque.Z / Math.Max(inertia.Z, 1e-6);
                double effectiveMass = 1 / inverseMass;
                var force = VRSharpMathHelper.ClampMagnitude(linearAcceleration * effectiveMass, MaxForce);
                rigidbody.AddImpulseAtLocation(force * (h / count), body.WorldLocation);
                rigidbody.AddAngularImpulseInRadians(angularAcceleration * (h / count), velChange: true);
            }
            else
            {
                // 空手在质心施力，不让 COM 偏移把位置弹簧变成额外的旋转弹簧。
                // 从下一帧手腕位置反算质心速度，补偿旋转时偏心质心的圆弧位移。
                var offset = body.WorldLocation - rigidbody.GetCenterOfMass();
                var rotationStep = MathLibrary.MakeFromRotationVector((angularVelocity + angularAcceleration * h) * h);
                var offsetAfterStep = rotationStep.RotateVector(offset);
                var centerVelocityChange = linearAcceleration * h + FVector.Cross(angularVelocity, offset)
                    - (offsetAfterStep - offset) / h;
                var equivalentForce = centerVelocityChange * (mass / h);
                rigidbody.AddImpulse(VRSharpMathHelper.ClampMagnitude(equivalentForce, MaxForce) * h);
                rigidbody.AddAngularImpulseInRadians(angularAcceleration * h, velChange: true);
            }
        }
    }

    #region 输入事件回调

    [UFunction]
    private void OnGripStarted(FInputActionValue value, float arg1, float arg2, UInputAction action)
    {
        TryGrab();
    }

    [UFunction]
    private void OnGripReleased(FInputActionValue value, float arg1, float arg2, UInputAction action)
    {
        Release();
    }


    // 动画设置
    [UFunction]
    private void ThumbTouchedAnim(FInputActionValue value, float arg1, float arg2, UInputAction action)
    {
        if (IsGrabbing || externalFingerInput) return;
        if (targetThumbWeight != 1f)
            targetThumbWeight = 0.5f;
    }

    [UFunction]
    private void ThumbClickedAnim(FInputActionValue value, float arg1, float arg2, UInputAction action)
    {
        if (IsGrabbing || externalFingerInput) return;
        targetThumbWeight = 1f;
    }

    [UFunction]
    private void IndexClickedAnim(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    {
        xrTrigger = 1;
    }

    [UFunction]
    private void OnAnalogTrigger(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    {
        xrTrigger = FingerInput.Normalize((float)value.GetAxis3D().X, xrTrigger);
    }

    private void ApplyXrTrigger()
    {
        if (!xrTriggerBound) return;
        if (IsGrabbing)
        {
            if (xrTrigger != activePoseTrigger) SetGrabTrigger(xrTrigger);
        }
        else if (!externalFingerInput)
        {
            targetIndexWeight = xrTrigger;
        }
    }

    [UFunction]
    private void GraspClickedAnim(FInputActionValue value, float arg1, float arg2, UInputAction action)
    {
        if (IsGrabbing || externalFingerInput) return;
        targetGraspWeight = 1f;
    }

    [UFunction]
    private void ThumbReleasedAnim(FInputActionValue value, float arg1, float arg2, UInputAction action)
    {
        if (IsGrabbing || externalFingerInput) return;
        targetThumbWeight = 0f;
    }

    [UFunction]
    private void IndexReleasedAnim(FInputActionValue value, float elapsed, float triggered, UInputAction action)
    {
        xrTrigger = 0;
    }

    [UFunction]
    private void GraspReleasedAnim(FInputActionValue value, float arg1, float arg2, UInputAction action)
    {
        if (IsGrabbing || externalFingerInput) return;
        targetGraspWeight = 0f;
    }

    /// <summary>
    /// 平滑动画权重
    /// </summary>
    /// <param name="deltaSeconds"></param>
    private void UpdateAnimationWeights(float deltaSeconds, float smooth = 0.15f)
    {
        var t = 1f - MathF.Exp(-Math.Max(smooth, 0f) * 120f * Math.Max(deltaSeconds, 0f));
        GraspWeight = float.Lerp(GraspWeight, targetGraspWeight, t);
        IndexWeight = float.Lerp(IndexWeight, targetIndexWeight, t);
        ThumbWeight = float.Lerp(ThumbWeight, targetThumbWeight, t);
    }

    /// <summary>
    /// 每帧累积接触反馈：深入 0.8 半径以内张开，浅接触保持，无接触继续闭合。
    /// </summary>
    private void UpdateGrabAnimation(float deltaSeconds)
    {
        if (HandMesh is null || GetCurrentGrabComponent() is not { } component) return;
        targetThumbWeight = VRSharpMathHelper.StepFingerContactTarget(ThumbWeight, targetThumbWeight,
            FingerContactDistance(ThumbName, component), FingerRadius, deltaSeconds);
        targetIndexWeight = VRSharpMathHelper.StepFingerContactTarget(IndexWeight, targetIndexWeight,
            FingerContactDistance(IndexName, component), FingerRadius, deltaSeconds);
        // 三指共用一个姿势通道，使用最深的接触，避免另一根手指抵消回弹。
        float graspDistance = Math.Min(FingerContactDistance(MiddleName, component),
            Math.Min(FingerContactDistance(RingName, component), FingerContactDistance(PinkyName, component)));
        targetGraspWeight = VRSharpMathHelper.StepFingerContactTarget(GraspWeight, targetGraspWeight,
            graspDistance, FingerRadius, deltaSeconds);
    }

    private float FingerContactDistance(string? socket, UPrimitiveComponent component)
    {
        // 未配置骨骼不反馈，避免把整个 HandMesh 原点误判成指尖。
        if (HandMesh is null || string.IsNullOrWhiteSpace(socket) || !HandMesh.DoesSocketExist(socket))
            return float.PositiveInfinity;
        var position = HandMesh.GetSocketLocation(socket);
        float distance = component.GetClosestPointOnCollision(position, out var point);
        if (distance == 0) point = position; // 球心已位于碰撞体内部，视作最深接触。
        if (distance < 0)
        {
            // 复杂碰撞无凸体最近点时，只保持浅接触，不使用无效 ImpactPoint 触发回弹。
            bool overlaps = SphereOverlapComponents(position, FingerRadius, GrabObjectTypes, default,
                null, out var components) && components.Contains(component);
            distance = overlaps ? FingerRadius : float.PositiveInfinity;
        }
        if (DebugMode)
        {
            var color = distance < FingerRadius * 0.8f ? new FLinearColor(1, 0, 0, 1)
                : distance <= FingerRadius ? new FLinearColor(0, 1, 0, 1) : new FLinearColor(0, 0.5f, 1, 1);
            DrawDebugSphere(position, FingerRadius, 12, color, 0, 0);
        }
        return distance;
    }

    #endregion

    /// <summary>
    /// 外部调用：重新检测抓取范围内指定的 grabbable，不使用旧缓存或远距离射线。
    /// </summary>
    [UFunction(FunctionFlags.BlueprintCallable)]
    public void GrabWithGrabbable(UVRSharpGrabbable grabbable, FVector targetLocation)
    {
        if (grabbable is null || GrabSphere is null)
            return;

        if (IsGrabbing) return;
        EnvironmentCheck(grabbable);
        GrabWithHitResult(targetHitResults, grabbable);
    }

    /// <summary>
    /// 更新高亮对象，触发进入/退出事件
    /// </summary>
    /// <param name="hits"></param>
    private void HighlightWithHitResult(List<FHitResult> hits)
    {
        UVRSharpGrabbable? newHighlight = null;
        FHitResult? newHitResult = null;
        if (TrySelectGrabHit(hits, null, out var selected, out var grabbable))
        {
            newHighlight = grabbable;
            newHitResult = selected;
        }

        // 如果高亮对象没有变化，只更新 hitResult（不触发事件）
        if (newHighlight == HighlightedObject)
        {
            highlightedHitResult = newHitResult;
            return;
        }

        // 退出旧的高亮对象
        if (HighlightedObject is not null && SystemLibrary.IsValid(HighlightedObject))
        {
            OnExitHighlighted?.Invoke(HighlightedObject);
            HighlightedObject.CallOnExitHighlighted();
        }

        // 更新高亮对象和缓存的 HitResult
        HighlightedObject = newHighlight;
        highlightedHitResult = newHitResult;

        // 进入新的高亮对象
        if (HighlightedObject is not null)
        {
            OnEnterHighlighted?.Invoke(HighlightedObject);
            HighlightedObject.CallOnEnterHighlighted();
        }
    }

    /// <summary>
    /// OnGripStarted已经检测过则传入hitResult
    /// </summary>
    /// <param name="hits"></param>
    /// <param name="specificTarget">选中hits中特定grabbable</param>
    // TODO: UnrealSharp Source Generator 在解析该 UFunction 时会崩溃（USG001）。
    // 先移除 UFunction 以恢复热重载/编译；后续如需蓝图调用，再改成生成器支持的签名。
    public bool GrabWithHitResult(IList<FHitResult> hits, UVRSharpGrabbable? specificTarget = null)
    {
        if (IsGrabbing || !TrySelectGrabHit(hits, specificTarget, out var selected, out var grabbable))
            return false;
        return Grab(grabbable!, selected.ImpactPoint, selected.ImpactNormal, selected.Component.Object!);
    }

    // Use the actual collision surface and the same origin/range for highlight and grip.
    private bool TrySelectGrabHit(IList<FHitResult> hits, UVRSharpGrabbable? specificTarget,
        out FHitResult selected, out UVRSharpGrabbable? grabbable, UPrimitiveComponent? specificComponent = null)
    {
        selected = default;
        grabbable = null;
        if (GrabSphere is null || hits is null) return false;
        var origin = GrabSphere.WorldLocation;
        double best = double.PositiveInfinity;
        double radius = GrabSphere.ScaledSphereRadius + 0.01;
        foreach (var hit in hits)
        {
            var component = hit.Component.Object;
            if (specificComponent is not null && component != specificComponent) continue;
            var candidate = FindGrabbable(component);
            if (candidate is null || (specificTarget is not null && candidate != specificTarget)) continue;
            var point = hit.ImpactPoint;
            if (hit.StartPenetrating && !TryGetGrabPoint(component!, origin, out point)) continue;
            double distance = FVector.DistanceSquared(origin, point);
            if (!double.IsFinite(distance) || distance > radius * radius || distance >= best) continue;
            if (candidate.RequireExplicitGrabPose && FindExplicitGrabPose(candidate, component!) is null) continue;
            best = distance;
            selected = hit;
            selected.ImpactPoint = point;
            if (selected.ImpactNormal.LengthSquared() < 1e-8) selected.ImpactNormal = GrabSphere.UpVector;
            grabbable = candidate;
        }
        return grabbable is not null;
    }

    private UVRSharpGrabbable? FindGrabbable(UPrimitiveComponent? component)
    {
        if (component is null || !SystemLibrary.IsValid(component) || component.Owner == this) return null;
        foreach (var item in component.Owner.GetComponentsByClass<UActorComponent>())
            if (item is UVRSharpGrabbable grabbable && SystemLibrary.IsValid(grabbable) && grabbable.CanGrab(this)) return grabbable;
        return null;
    }

    private bool TryGetGrabPoint(UPrimitiveComponent component, FVector origin, out FVector point)
    {
        float distance = component.GetClosestPointOnCollision(origin, out point);
        if (distance >= 0)
        {
            // UE returns zero when the hand is inside a collision volume.
            if (distance == 0) point = origin;
            return true;
        }
        // Complex-only collision has no convex closest-point query. Use a bounded
        // component trace instead of treating its bounds/Actor pivot as a surface.
        var end = origin + MathLibrary.Normal(component.WorldLocation - origin) * GrabSphere!.ScaledSphereRadius;
        return component.LineTraceComponent(origin, end, true, false, false, out point, out _, out _, out _);
    }

    [UFunction(FunctionFlags.BlueprintCallable)]
    public UVRSharpGrabbable? RefreshGrabTarget()
    {
        if (IsGrabbing) return GrabbedObject;
        EnvironmentCheck();
        HighlightWithHitResult(targetHitResults);
        return HighlightedObject;
    }

    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool TryGrab()
    {
        if (IsGrabbing) return false;
        RefreshGrabTarget();
        return GrabWithHitResult(targetHitResults);
    }


    /// <summary>
    /// 内部抓取调用
    /// </summary>
    /// <param name="grabbable"></param>
    /// <param name="location"></param>
    /// <param name="normal"></param>
    /// <param name="component"></param>
    private UVRSharpHandPose? FindExplicitGrabPose(UVRSharpGrabbable grabbable, UPrimitiveComponent component)
    {
        UVRSharpHandPose? best = null;
        double bestDistance = double.PositiveInfinity;
        if (Palm is null || !SystemLibrary.IsValid(Palm)) return null;
        var palmLocation = Palm.WorldLocation;
        var candidates = grabbable.Owner?.GetComponentsByClass<USceneComponent>();
        if (candidates is null) return null;
        foreach (var candidate in candidates.OfType<UVRSharpHandPose>())
        {
            if (!grabbable.CanUseGrabPose(candidate) || candidate.TargetComponent != component ||
                (IsLeft ? candidate.DisableLeftHand : candidate.DisableRightHand)) continue;
            var distance = FVector.DistanceSquared(palmLocation, candidate.WorldLocation);
            if (!double.IsFinite(distance)) continue;
            if (best is null || candidate.Priority > best.Priority ||
                (candidate.Priority == best.Priority && (distance < bestDistance ||
                 (distance == bestDistance && string.CompareOrdinal(SystemLibrary.GetObjectName(candidate), SystemLibrary.GetObjectName(best)) < 0))))
            {
                best = candidate;
                bestDistance = distance;
            }
        }
        return best;
    }

    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool TryGrabAtPose(UVRSharpGrabbable grabbable, UVRSharpHandPose pose)
    {
        if (IsGrabbing || grabbable is null || !SystemLibrary.IsValid(grabbable) ||
            pose is null || !SystemLibrary.IsValid(pose)) return false;
        var component = pose.TargetComponent;
        if (component is null || !IsRequestedPoseValid(grabbable, component, pose)) return false;

        EnvironmentCheck(grabbable, component);
        if (!TrySelectGrabHit(targetHitResults, grabbable, out var hit, out _, component)) return false;
        return Grab(grabbable, hit.ImpactPoint, hit.ImpactNormal, component, pose);
    }

    private bool IsRequestedPoseValid(UVRSharpGrabbable grabbable, UPrimitiveComponent component, UVRSharpHandPose pose)
    {
        if (!grabbable.CanUseGrabPose(pose) || !SystemLibrary.IsValid(component) ||
            grabbable.Owner is null || pose.Owner != grabbable.Owner || component.Owner != grabbable.Owner ||
            pose.TargetComponent != component || (IsLeft ? pose.DisableLeftHand : pose.DisableRightHand) || Palm is null)
            return false;
        return double.IsFinite(FVector.DistanceSquared(Palm.WorldLocation, pose.WorldLocation));
    }

    private bool Grab(UVRSharpGrabbable grabbable, FVector location, FVector normal, UPrimitiveComponent component,
        UVRSharpHandPose? requestedPose = null)
    {
        if (!SystemLibrary.IsValid(grabbable) || !SystemLibrary.IsValid(component) || !grabbable.CanGrab(this)) return false;
        // 事件
        OnBeforeGrab?.Invoke(grabbable);
        if (!SystemLibrary.IsValid(grabbable) || !SystemLibrary.IsValid(component) || !grabbable.CanGrab(this)) return false;
        grabbable.CallOnBeforeGrab();
        if (!SystemLibrary.IsValid(grabbable) || !SystemLibrary.IsValid(component) || !grabbable.CanGrab(this)) return false;

        // 检查是否有预定义的手部姿态
        var componentName = SystemLibrary.GetObjectName(component);
        if (requestedPose is not null && (IsGrabbing || !IsRequestedPoseValid(grabbable, component, requestedPose)))
            return false;
        UVRSharpHandPose? handPose = requestedPose ?? FindExplicitGrabPose(grabbable, component);
        bool alignPalmFrame = handPose is not null;
        if (handPose is null && grabbable.RequireExplicitGrabPose) return false;

        if (handPose is null && grabbable.GrabPoses is not null)
        {
            // 使用 Contains 匹配：只要组件名包含字典中的 key 就匹配
            var matchedKey = grabbable.GrabPoses.Keys.FirstOrDefault(key => componentName.Contains(key));
            if (matchedKey is not null && grabbable.GrabPoses.TryGetValue(matchedKey, out var poseName))
            {
                // 查找对应名称的 HandPose 组件
                // WORKAROUND: GetComponentsByClass<T>() 在引擎升级后失效，使用 OfType 替代
                var allComponents = grabbable.Owner?.GetComponentsByClass<USceneComponent>();
                var poseComponents = allComponents?.OfType<UVRSharpHandPose>().ToList();

                // 使用 Contains 匹配 HandPose 组件名称
                handPose = poseComponents?.FirstOrDefault(p => grabbable.CanUseGrabPose(p) && !(IsLeft ? p.DisableLeftHand : p.DisableRightHand) && SystemLibrary.GetObjectName(p).Contains(poseName));
            }
        }

        if (handPose is not null && alignPalmFrame)
        {
            if (Palm is not { } palm || !SystemLibrary.IsValid(palm) ||
                HandRigidbody is not { } root || !SystemLibrary.IsValid(root)) return false;

            var alignment = VRSharpMathHelper.SolvePalmAlignment(
                ActorLocation, root.WorldRotation, palm.WorldLocation, palm.WorldRotation,
                handPose.WorldLocation, handPose.WorldRotation);
            SetActorTransform(new FTransform(alignment.Rotation, alignment.Location, ActorScale3D), false, out _, true);
        }
        else if (handPose is not null)
        {
            // 旧名称表抓点按手 Actor 旋转制作，保持原有对齐方式。
            SetActorRotation(handPose.WorldRotation);
            SetActorLocation(handPose.WorldLocation - (Palm!.WorldLocation - ActorLocation));
        }
        else
        {
            // 默认抓取逻辑
            // 1. 移动：让 Palm 到达目标点
            SetActorLocation(location - (Palm!.WorldLocation - ActorLocation));

            // 2. 旋转：手心朝向法线，然后补偿 Palm 偏移
            SetActorRotation(MathLibrary.MakeRotFromZX(normal, ActorForwardVector));
            SetActorLocation(ActorLocation - (Palm!.WorldLocation - location));
        }

        useAuthoredFingerWeights = handPose is not null && handPose.UseFingerWeights;
        useTriggerBlend = useAuthoredFingerWeights && handPose!.UseTriggerBlend;
        if (useAuthoredFingerWeights)
        {
            targetThumbWeight = VRSharpMathHelper.NormalizePoseWeight(handPose!.ThumbWeight);
            authoredIndexWeight = targetIndexWeight = VRSharpMathHelper.NormalizePoseWeight(handPose.IndexWeight);
            triggerIndexWeight = VRSharpMathHelper.NormalizePoseWeight(handPose.TriggerIndexWeight);
            targetGraspWeight = VRSharpMathHelper.NormalizePoseWeight(handPose.GraspWeight);
        }
        else SetAllAnimationWeights(1f);
        grabbable.AttachWithPose(this, component, handPose);
        if (!IsGrabbing || GrabbedObject != grabbable) return false;
        if (IsGrabbing && GrabbedObject == grabbable)
        {
            activeGrabPose = handPose;
            BeginPoseAnimation(handPose);
            activePoseTrigger = 0;
            if (handPose is not null) GrabPoseEntered?.Invoke(this, handPose);
        }

        // 事件
        OnAfterGrab?.Invoke(grabbable);
        if (SystemLibrary.IsValid(grabbable)) grabbable.CallOnAfterGrab();
        return true;
    }

    [UFunction(FunctionFlags.BlueprintCallable)]
    public void Release()
    {
        if (!IsGrabbing)
            return;

        // 缓存：回调里可能会清空/销毁
        var grabbable = GrabbedObject;

        float releasedTrigger = activePoseTrigger;
        SetGrabTrigger(0);
        OnBeforeRelease?.Invoke(grabbable);
        if (grabbable is not null && SystemLibrary.IsValid(grabbable))
            grabbable.CallOnBeforeRelease();

        // 回调可能销毁原对象，不能仅用 CLR null 判断原生对象生命周期。
        if (grabbable is not null && SystemLibrary.IsValid(grabbable))
            grabbable.Detach(this);
        else
        {
            DetachFromActor(EDetachmentRule.KeepWorld, EDetachmentRule.KeepWorld, EDetachmentRule.KeepWorld);
            IsGrabbing = false;
            GrabbedObject = null;
        }

        // 松开抓握时，手指回到张开（空手时再按原有输入逻辑调整）
        var exitedPose = activeGrabPose;
        activeGrabPose = null;
        var visualPose = GetAnimationGrabPose();
        poseExiting = visualPose is not null && float.IsFinite(visualPose.ExitBlendSeconds) && visualPose.ExitBlendSeconds > 0;
        exitPoseTrigger = poseExiting ? releasedTrigger : 0;
        if (!poseExiting)
        {
            animationPose = null;
            poseBlendWeight = 0;
        }
        activePoseTrigger = 0;
        useAuthoredFingerWeights = false;
        useTriggerBlend = false;
        SetAllAnimationWeights(0f);
        if (exitedPose is not null && SystemLibrary.IsValid(exitedPose)) GrabPoseExited?.Invoke(this, exitedPose);

        OnAfterRelease?.Invoke(grabbable);
        if (grabbable is not null && SystemLibrary.IsValid(grabbable))
            grabbable.CallOnAfterRelease();

        if (HandRigidbody is { } body && SystemLibrary.IsValid(body)) body.SimulatePhysics = true;
    }

    /// <summary>
    /// 每帧检测手下方的 grabbable，缓存到 targetHitResults
    /// </summary>
    private void EnvironmentCheck(UVRSharpGrabbable? specificTarget = null, UPrimitiveComponent? specificComponent = null)
    {
        targetHitResults.Clear();
        if (GrabSphere is null) return;
        var origin = GrabSphere.WorldLocation;
        float radius = GrabSphere.ScaledSphereRadius;
        var debug = DebugMode ? EDrawDebugTrace.ForOneFrame : EDrawDebugTrace.None;
        // Preserve the configured palm-facing axis (-GrabSphere.UpVector), but
        // start at the sphere centre: the rear half must not win the forward ray.
        MultiLineTraceForObjects(origin, origin - GrabSphere.UpVector * radius,
            GrabObjectTypes, false, [this], debug, out var lineHits, true);
        if (TrySelectGrabHit(lineHits, specificTarget, out var lineHit, out _, specificComponent))
        {
            targetHitResults.Add(lineHit);
            return;
        }

        // A hit on a non-grabbable object must not suppress nearby candidates.
        if (!SphereOverlapComponents(origin, radius, GrabObjectTypes, default, [this], out var components)) return;
        foreach (var component in components)
        {
            if (specificComponent is not null && component != specificComponent) continue;
            var candidate = FindGrabbable(component);
            if (candidate is null || (specificTarget is not null && candidate != specificTarget)
                || !TryGetGrabPoint(component, origin, out var point)) continue;
            targetHitResults.Add(new FHitResult
            {
                Component = component,
                BlockingHit = true,
                ImpactPoint = point,
                Location = point,
                ImpactNormal = MathLibrary.Normal(origin - point),
            });
        }
        // Cache a single winner so highlighting and actual grabbing cannot diverge.
        if (TrySelectGrabHit(targetHitResults, specificTarget, out var nearest, out _, specificComponent))
        {
            targetHitResults.Clear();
            targetHitResults.Add(nearest);
        }
        else targetHitResults.Clear();
    }

    /// <summary>已抓取预设姿势的食指扳机混合；无配置或异常样本返回false。</summary>
    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool SetGrabTrigger(float value)
    {
        if (!IsGrabbing || !float.IsFinite(value)) return false;
        var item = GrabbedObject;
        var component = GetCurrentGrabComponent();
        if (item is null || !SystemLibrary.IsValid(item) || component is null || !SystemLibrary.IsValid(component)) return false;
        float next = Math.Clamp(value,0,1);
        bool changed = next != activePoseTrigger;
        activePoseTrigger = next;
        if (useTriggerBlend) targetIndexWeight = VRSharpMathHelper.BlendPoseWeight(authoredIndexWeight, triggerIndexWeight, activePoseTrigger);
        if (changed)
        {
            GrabTriggerChanged?.Invoke(this, item, component, activePoseTrigger);
            if (SystemLibrary.IsValid(item)) item.NotifyGrabTrigger(this, component, activePoseTrigger);
        }
        return true;
    }


    /// <summary>空手模拟输入入口；PC滑条与OpenXR模拟轴共用。抓取接触期间返回false。</summary>
    [UFunction(FunctionFlags.BlueprintCallable)]
    public bool SetFingerInput(float thumb, float index, float grasp)
    {
        if (IsGrabbing) return false;
        externalFingerInput = true;
        targetThumbWeight = FingerInput.Normalize(thumb, targetThumbWeight);
        targetIndexWeight = FingerInput.Normalize(index, targetIndexWeight);
        targetGraspWeight = FingerInput.Normalize(grasp, targetGraspWeight);
        return true;
    }

    /// <summary>适配器断开时交还旧输入；抓握期间不覆盖接触姿势。</summary>
    [UFunction(FunctionFlags.BlueprintCallable)]
    public void ClearFingerInput()
    {
        externalFingerInput = false;
        if (!IsGrabbing) SetAllAnimationWeights(0f);
    }

    private void SetAllAnimationWeights(float weight)
    {
        targetGraspWeight = weight;
        targetIndexWeight = weight;
        targetThumbWeight = weight;
    }
}
