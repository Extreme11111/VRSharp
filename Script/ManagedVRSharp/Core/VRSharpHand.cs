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

    #endregion

    #region 变量定义

    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings")]
    public partial bool IsLeft { get; set; }

    /// <summary>VRPhysicsHandSettings: default 2,000</summary>
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings"), ToolTip("default 2,000")]
    protected partial float LocationStiffness { get; set; }

    /// <summary>VRPhysicsHandSettings: default 100</summary>
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings"), ToolTip("default 100")]
    protected partial float LocationDamping { get; set; }

    /// <summary>VRPhysicsHandSettings: default 15,000</summary>
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings"), ToolTip("default 20,000")]
    protected partial float RotationStiffness { get; set; }

    /// <summary>VRPhysicsHandSettings: default 700</summary>
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings"), ToolTip("default 500")]
    protected partial float RotationDamping { get; set; }

    /// <summary>VRPhysicsHandSettings: default 80,000</summary>
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings"), ToolTip("default 80,000")]
    protected partial float MaxForce { get; set; }

    /// <summary>VRPhysicsHandSettings: default 80,000</summary>
    [UProperty(PropertyFlags.BlueprintReadWrite | PropertyFlags.EditAnywhere), Category("VRPhysicsHandSettings"), ToolTip("default 80,000")]
    protected partial float MaxTorque { get; set; }

    #endregion

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
        inputComponent.BindAction(TriggerAction!, ETriggerEvent.Started, IndexClickedAnim, out _);
        inputComponent.BindAction(GripAction!, ETriggerEvent.Started, GraspClickedAnim, out _);

        inputComponent.BindAction(TouchedAction!, ETriggerEvent.Completed, ThumbReleasedAnim, out _);
        inputComponent.BindAction(AXAction!, ETriggerEvent.Completed, ThumbReleasedAnim, out _);
        inputComponent.BindAction(BYAction!, ETriggerEvent.Completed, ThumbReleasedAnim, out _);
        inputComponent.BindAction(TriggerAction!, ETriggerEvent.Completed, IndexReleasedAnim, out _);
        inputComponent.BindAction(GripAction!, ETriggerEvent.Completed, GraspReleasedAnim, out _);
    }

    override public void Tick(float deltaSeconds)
    {
        base.Tick(deltaSeconds);
        EnvironmentCheck();

        // 非抓取状态下更新高亮
        if (!IsGrabbing)
        {
            HighlightWithHitResult(targetHitResults);
        }

        if (IsGrabbing)
        {
            UpdateGrabAnimation();
            UpdateAnimationWeights(deltaSeconds, 0.05f);
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
    {
        locationForce = VRSharpMathHelper.ComputeSpringForce(
            targetLocation,
            HandRigidbody!.WorldLocation,
            HandRigidbody!.GetPhysicsLinearVelocity(),
            LocationStiffness,
            LocationDamping);
        rotationForce = VRSharpMathHelper.ComputeRotationTorque(
            targetRotation,
            HandRigidbody!.WorldRotation,
            HandRigidbody!.GetPhysicsAngularVelocityInRadians(),
            RotationStiffness,
            RotationDamping);
        if (locationForce.LengthSquared() > MaxForce * MaxForce)
            locationForce = locationForce / locationForce.Length() * MaxForce;
        if (rotationForce.LengthSquared() > MaxTorque * MaxTorque)
            rotationForce = rotationForce / rotationForce.Length() * MaxTorque;

        // 关键：用“在位置施加力”而不是默认的质心施力。
        // 这样当两只手在不同抓握点拉拽同一个物体时，会自然产生转矩，从而更容易通过“距离拉力”控制旋转。
        if (HandRigidbody!.IsSimulatingPhysics())
        {
            HandRigidbody!.AddForceAtLocation(locationForce, HandRigidbody.WorldLocation);
            HandRigidbody!.AddTorqueInRadians(rotationForce);
        }
    }

    #region 输入事件回调

    [UFunction]
    private void OnGripStarted(FInputActionValue value, float arg1, float arg2, UInputAction action)
    {
        // 优先使用缓存的高亮 HitResult（避免重新查找）
        if (highlightedHitResult.HasValue && HighlightedObject is not null && SystemLibrary.IsValid(HighlightedObject))
        {
            GrabWithHitResult([highlightedHitResult.Value], HighlightedObject);
            return;
        }

        // Fallback: 无高亮对象时使用射线检测结果
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
        if (IsGrabbing) return;
        if (targetThumbWeight != 1f)
            targetThumbWeight = 0.5f;
    }

    [UFunction]
    private void ThumbClickedAnim(FInputActionValue value, float arg1, float arg2, UInputAction action)
    {
        if (IsGrabbing) return;
        targetThumbWeight = 1f;
    }

    [UFunction]
    private void IndexClickedAnim(FInputActionValue value, float arg1, float arg2, UInputAction action)
    {
        if (IsGrabbing) return;
        targetIndexWeight = 1f;
    }

    [UFunction]
    private void GraspClickedAnim(FInputActionValue value, float arg1, float arg2, UInputAction action)
    {
        if (IsGrabbing) return;
        targetGraspWeight = 1f;
    }

    [UFunction]
    private void ThumbReleasedAnim(FInputActionValue value, float arg1, float arg2, UInputAction action)
    {
        if (IsGrabbing) return;
        targetThumbWeight = 0f;
    }

    [UFunction]
    private void IndexReleasedAnim(FInputActionValue value, float arg1, float arg2, UInputAction action)
    {
        if (IsGrabbing) return;
        targetIndexWeight = 0f;
    }

    [UFunction]
    private void GraspReleasedAnim(FInputActionValue value, float arg1, float arg2, UInputAction action)
    {
        if (IsGrabbing) return;
        targetGraspWeight = 0f;
    }

    /// <summary>
    /// 平滑动画权重
    /// </summary>
    /// <param name="deltaSeconds"></param>
    private void UpdateAnimationWeights(float deltaSeconds, float smooth = 0.15f)
    {
        var t = Math.Clamp(smooth * 120 * deltaSeconds, 0f, 1f);
        GraspWeight = float.Lerp(GraspWeight, targetGraspWeight, t);
        IndexWeight = float.Lerp(IndexWeight, targetIndexWeight, t);
        ThumbWeight = float.Lerp(ThumbWeight, targetThumbWeight, t);
    }

    /// <summary>
    /// 抓握时检测每根手指是否碰到物体，碰到则锁定当前弯曲程度
    /// </summary>
    private void UpdateGrabAnimation()
    {
        if (HandMesh is null || GrabbedObject is null) return;

        var grabbedComponent = GrabbedObject.GrabbedComponent;
        if (grabbedComponent is null) return;

        // 拇指
        if (CheckFingerCollision(HandMesh.GetSocketLocation(ThumbName!), FingerRadius, grabbedComponent))
            targetThumbWeight = ThumbWeight;

        // 食指
        if (CheckFingerCollision(HandMesh.GetSocketLocation(IndexName!), FingerRadius, grabbedComponent))
            targetIndexWeight = IndexWeight;

        // 中指/无名指/小指（任一碰到即锁定 GraspWeight）
        if (CheckFingerCollision(HandMesh.GetSocketLocation(MiddleName!), FingerRadius, grabbedComponent) ||
            CheckFingerCollision(HandMesh.GetSocketLocation(RingName!), FingerRadius, grabbedComponent) ||
            CheckFingerCollision(HandMesh.GetSocketLocation(PinkyName!), FingerRadius, grabbedComponent))
            targetGraspWeight = GraspWeight;
    }

    private bool CheckFingerCollision(FVector position, float radius, UPrimitiveComponent targetComponent)
    {
        var hit = SphereOverlapComponents(position, radius, GrabObjectTypes, default, null, out var components)
                  && (components?.Contains(targetComponent) ?? false);

        if (DebugMode)
        {
            var color = hit ? new FLinearColor(0f, 1f, 0f, 1f) : new FLinearColor(1f, 0f, 0f, 1f);
            DrawDebugSphere(position, radius, 12, color, 0f, 0f);
        }

        return hit;
    }

    #endregion

    /// <summary>
    /// 外部调用：抓取指定的 grabbable（优先用缓存的 targetHitResults，找不到再检测指定位置）
    /// </summary>
    [UFunction(FunctionFlags.BlueprintCallable)]
    public void GrabWithGrabbable(UVRSharpGrabbable grabbable, FVector targetLocation)
    {
        if (grabbable is null || GrabSphere is null)
            return;

        // 1. 优先从缓存的 hits 里找
        if (targetHitResults.Count > 0 && GrabWithHitResult(targetHitResults, grabbable))
            return;

        // 2. 指定了目标点：从手中心朝 targetLocation 发射射线
        if (targetLocation != FVector.Zero)
        {
            var rayCenter = GrabSphere.WorldLocation + GrabSphere.UpVector * GrabSphere.ScaledSphereRadius;
            if (SystemLibrary.MultiLineTraceForObjects(rayCenter, targetLocation, GrabObjectTypes, false, null, EDrawDebugTrace.None, out var hits, true)
                && GrabWithHitResult(hits, grabbable))
                return;
        }
    }

    /// <summary>
    /// 更新高亮对象，触发进入/退出事件
    /// </summary>
    /// <param name="hits"></param>
    private void HighlightWithHitResult(List<FHitResult> hits)
    {
        // WORKAROUND: GetComponentByClass<T>() 在引擎升级后失效
        static UVRSharpGrabbable? FindGrabbable(AActor? actor)
        {
            if (actor is null) return null;
            var components = actor.GetComponentsByClass<UActorComponent>();
            return components?.OfType<UVRSharpGrabbable>().FirstOrDefault();
        }

        UVRSharpGrabbable? newHighlight = null;
        FHitResult? newHitResult = null;

        if (hits is not null && hits.Count > 0)
        {
            // 得到最近grabbable，同时保留对应的 hit
            var nearestResult = hits.Select(hit => new
            {
                grabbable = FindGrabbable(hit.Actor),
                hitResult = hit,
            })
            .Where(x => x.grabbable is not null)
            .MinBy(x => FVector.DistanceSquared(x.grabbable!.Owner!.ActorLocation, ActorLocation));

            newHighlight = nearestResult?.grabbable;
            newHitResult = nearestResult?.hitResult;
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
        if (hits is null || hits.Count == 0)
            return false;

        // WORKAROUND: GetComponentByClass<T>() 在引擎升级后失效
        // 改用 GetComponentsByClass + LINQ OfType 来获取组件
        static UVRSharpGrabbable? FindGrabbable(AActor? actor)
        {
            if (actor is null) return null;
            var components = actor.GetComponentsByClass<UActorComponent>();
            return components?.OfType<UVRSharpGrabbable>().FirstOrDefault();
        }

        // 得到最近grabbable
        var nearestGrabbable = hits.Select(hit => new
        {
            // 匿名类
            grabbable = FindGrabbable(hit.Actor),
            component = hit.Component,
            location = hit.ImpactPoint,
            normal = hit.ImpactNormal,
        })
        .Where(x => x.grabbable is not null && (specificTarget is null || x.grabbable == specificTarget)) //过滤得到grabbable
        .MinBy(hit => FVector.DistanceSquared(hit.location, ActorLocation));    //找到最近grabbable

        if (nearestGrabbable is not null)
        {
            Grab(nearestGrabbable.grabbable!, nearestGrabbable.location, nearestGrabbable.normal, nearestGrabbable.component.Object!);
            return true;
        }

        return false;
    }


    /// <summary>
    /// 内部抓取调用
    /// </summary>
    /// <param name="grabbable"></param>
    /// <param name="location"></param>
    /// <param name="normal"></param>
    /// <param name="component"></param>
    private void Grab(UVRSharpGrabbable grabbable, FVector location, FVector normal, UPrimitiveComponent component)
    {
        // 事件
        OnBeforeGrab?.Invoke(grabbable);
        grabbable.CallOnBeforeGrab();

        // 检查是否有预定义的手部姿态
        var componentName = SystemLibrary.GetObjectName(component);
        UVRSharpHandPose? handPose = null;

        if (grabbable.GrabPoses is not null)
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
                handPose = poseComponents?.FirstOrDefault(p => SystemLibrary.GetObjectName(p).Contains(poseName));
            }
        }

        if (handPose is not null)
        {
            // 使用预定义姿态：让 Palm 对齐到 HandPose 的位置和旋转
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

        SetAllAnimationWeights(1f);
        grabbable.Attach(this, component);

        // 事件
        OnAfterGrab?.Invoke(grabbable);
        grabbable.CallOnAfterGrab();
    }

    [UFunction(FunctionFlags.BlueprintCallable)]
    public void Release()
    {
        if (!IsGrabbing)
            return;

        // 缓存：回调里可能会清空/销毁
        var grabbable = GrabbedObject;

        OnBeforeRelease?.Invoke(grabbable);
        if (grabbable is not null && SystemLibrary.IsValid(grabbable))
            grabbable.CallOnBeforeRelease();

        grabbable?.Detach(this);

        // 松开抓握时，手指回到张开（空手时再按原有输入逻辑调整）
        SetAllAnimationWeights(0f);

        OnAfterRelease?.Invoke(grabbable);
        if (grabbable is not null && SystemLibrary.IsValid(grabbable))
            grabbable.CallOnAfterRelease();

        HandRigidbody!.SimulatePhysics = true;
    }

    /// <summary>
    /// 每帧检测手下方的 grabbable，缓存到 targetHitResults
    /// </summary>
    private void EnvironmentCheck()
    {
        EDrawDebugTrace eDrawDebugTrace = DebugMode ? EDrawDebugTrace.ForOneFrame : EDrawDebugTrace.None;

        targetHitResults.Clear();
        if (GrabSphere is null) return;

        var rayCenter = GrabSphere.WorldLocation + GrabSphere.UpVector * GrabSphere.ScaledSphereRadius;
        var rayEnd = rayCenter - GrabSphere.UpVector * GrabSphere.ScaledSphereRadius * 2;

        // 优先射线检测
        // TODO: 检测对象类型为 EGrabObjectTypes
        if (MultiLineTraceForObjects(rayCenter, rayEnd, GrabObjectTypes, false, null, eDrawDebugTrace, out var lineHits, true)
            && lineHits?.Count > 0)
        {
            foreach (var hit in lineHits)
                targetHitResults.Add(hit);
        }

        // 射线没有结果则用球形检测
        if (targetHitResults.Count == 0
            && MultiSphereTraceForObjects(GrabSphere.WorldLocation, GrabSphere.WorldLocation, GrabSphere.ScaledSphereRadius, GrabObjectTypes, false, null, eDrawDebugTrace, out var sphereHits, true)
            && sphereHits?.Count > 0)
        {
            foreach (var hit in sphereHits)
                targetHitResults.Add(hit);
        }
    }

    private void SetAllAnimationWeights(float weight)
    {
        targetGraspWeight = weight;
        targetIndexWeight = weight;
        targetThumbWeight = weight;
    }
}