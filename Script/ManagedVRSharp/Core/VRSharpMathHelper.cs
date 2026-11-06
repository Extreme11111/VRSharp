using UnrealSharp.CoreUObject;

namespace VRSharp.Core;

public static class VRSharpMathHelper
{
    public static (FVector Location, FQuat Rotation) SolvePalmAlignment(
        FVector handLocation, FQuat handRotation, FVector palmLocation, FQuat palmRotation,
        FVector targetLocation, FQuat targetRotation)
    {
        // Rotate the whole hand about its current palm, then translate that palm onto the grab point.
        var delta = FQuat.Normalize(targetRotation * FQuat.Inverse(palmRotation));
        var rotation = FQuat.Normalize(delta * handRotation);
        var location = targetLocation - delta.RotateVector(palmLocation - handLocation);
        return (location, rotation);
    }

    public static float BlendPoseWeight(float start, float end, float alpha)
        => float.Lerp(NormalizePoseWeight(start), NormalizePoseWeight(end), NormalizePoseWeight(alpha));

    public static float NormalizePoseWeight(float weight)
        => float.IsFinite(weight) ? Math.Clamp(weight, 0f, 1f) : 0f;

    /// <summary>
    /// 将连续弹簧的极点映射到当前物理时间步。输出为加速度增益，与刚体质量无关。
    /// 配合每帧一次的速度冲量使用；物理子步只处理漂移与碰撞，不重复施加反馈。
    /// </summary>
    public static FVector ComputeSpringAcceleration(FVector displacement, FVector velocityError,
        float stiffness, float damping, float deltaSeconds)
    {
        if (!float.IsFinite(deltaSeconds) || deltaSeconds <= 0)
            return FVector.Zero;

        double h = Math.Max(deltaSeconds, 1e-6f);
        double k = float.IsFinite(stiffness) ? Math.Max(stiffness, 0) : 0;
        double d = float.IsFinite(damping) ? Math.Max(damping, 0) : 0;
        // 手部伺服默认不允许欠阻尼：低阻尼在变帧率下容易把镜像/采样噪声放大。
        d = Math.Max(d, 2 * Math.Sqrt(k));
        double halfDamping = d * 0.5;
        // 稳定计算过阻尼/临界阻尼的两个实极点，避免相近大数相减。
        double fastRate = halfDamping + Math.Sqrt(Math.Max(halfDamping * halfDamping - k, 0));
        double slowRate = fastRate > 0 ? k / fastRate : 0;
        double slowPole = Math.Exp(-slowRate * h);
        double fastPole = Math.Exp(-fastRate * h);
        double springGain = (1 - slowPole) * (1 - fastPole) / (h * h);
        double velocityGain = (1 - slowPole * fastPole) / h;

        return displacement * springGain + velocityError * velocityGain;
    }

    /// <summary>四元数的最短旋转向量（世界空间，弧度）；q 和 -q 得到相同结果。</summary>
    public static FVector RotationVector(FQuat targetRotation, FQuat currentRotation)
    {
        var delta = FQuat.Normalize(targetRotation * FQuat.Inverse(currentRotation));
        // 180° 时 W 可能为 +0/-0，使用固定轴符号消除 q/-q 的二义性。
        bool negativeAxis = delta.X < 0 || (delta.X == 0 && (delta.Y < 0 || (delta.Y == 0 && delta.Z < 0)));
        if (delta.W < 0 || (delta.W == 0 && negativeAxis))
            delta = new FQuat(-delta.X, -delta.Y, -delta.Z, -delta.W);

        double length = Math.Sqrt(delta.X * delta.X + delta.Y * delta.Y + delta.Z * delta.Z);
        if (!double.IsFinite(length) || !double.IsFinite(delta.W))
            return FVector.Zero;
        if (length < 1e-8)
            return new FVector(delta.X * 2, delta.Y * 2, delta.Z * 2);

        double scale = 2 * Math.Atan2(length, Math.Max(0, delta.W)) / length;
        return new FVector(delta.X * scale, delta.Y * scale, delta.Z * scale);
    }

    public static FVector ClampMagnitude(FVector value, float maximum)
    {
        if (!float.IsFinite(maximum) || maximum <= 0)
            return FVector.Zero;
        double square = value.LengthSquared();
        if (!double.IsFinite(square))
            return FVector.Zero;
        return square > (double)maximum * maximum ? value * (maximum / Math.Sqrt(square)) : value;
    }

    /// <summary>
    /// 计算弹簧力
    /// </summary>
    /// <param name="targetLocation"></param>
    /// <param name="currentLocation"></param>
    /// <param name="currentVelocity"></param>
    /// <param name="stiffness"></param>
    /// <param name="damping"></param>
    /// <returns></returns>
    public static FVector ComputeSpringForce(
    FVector targetLocation,
    FVector currentLocation,
    FVector currentVelocity,
    float stiffness = 5000f,   // K: 弹簧系数
    float damping = 50f       // D: 阻尼系数
    )
    {
        // 位移差
        var displacement = targetLocation - currentLocation;

        // 弹簧力 = K * 位移差
        var springForce = displacement * stiffness;

        // 阻尼力 = -D * 当前速度
        var dampingForce = currentVelocity * -damping;

        // 合力
        return springForce + dampingForce;
    }

    public static FVector ComputeRotationTorque(
    FQuat targetRotation,
    FQuat currentRotation,
    FVector currentAngularVelocity,
    float stiffness = 100f,    // 降低到合理范围
    float damping = 20f         // 降低阻尼
    )
    {
        return RotationVector(targetRotation, currentRotation) * stiffness - currentAngularVelocity * damping;
    }

    /// <summary>接触深度驱动的姿势积分；距离和半径使用相同单位，权重限制到 0..1。</summary>
    public static float StepFingerContactTarget(float current, float target, float distance, float radius, float dt)
    {
        current = Math.Clamp(current, 0f, 1f);
        target = Math.Clamp(target, 0f, 1f);
        if (!float.IsFinite(dt) || dt <= 0 || !float.IsFinite(radius) || radius <= 0) return target;
        if (float.IsNaN(distance)) return current;
        if (distance > radius)
            return Math.Clamp(Math.Max(current, target) + 3f * dt, 0f, 1f);
        float ratio = Math.Max(distance, 0f) / radius;
        if (ratio < 0.8f)
            return Math.Clamp(Math.Min(current, target) - 6f * (1f - ratio / 0.8f) * dt, 0f, 1f);
        return current; // 0.8R..R 为稳定接触带，避免临界点反复开合。
    }

}
