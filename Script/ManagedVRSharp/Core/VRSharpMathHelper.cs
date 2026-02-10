// AI Gemini3 Pro
using UnrealSharp.CoreUObject;
using UnrealSharp.Engine;

namespace VRSharp.Core;

public static class VRSharpMathHelper
{
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
        // 计算旋转差
        FQuat deltaQuat = targetRotation * FQuat.Inverse(currentRotation);
        deltaQuat = FQuat.Normalize(deltaQuat);

        // 确保四元数走最短路径（避免绕远路导致的抖动）
        // 当 W < 0 时，取反四元数（表示相同旋转但走短路）
        if (deltaQuat.W < 0)
        {
            deltaQuat = new FQuat(-deltaQuat.X, -deltaQuat.Y, -deltaQuat.Z, -deltaQuat.W);
        }

        GetAxisAndAngle(deltaQuat, out var axis, out var angle);

        // 弹簧力矩 = 刚度 * 角度偏差
        FVector springTorque = axis * (angle * stiffness);

        // 阻尼力矩 = 阻尼系数 * 角速度
        FVector dampingTorque = currentAngularVelocity * damping;

        // 总力矩
        FVector torque = springTorque - dampingTorque;

        return torque;
    }

    private static void GetAxisAndAngle(FQuat q, out FVector axis, out float angle)
    {
        // 修复：确保使用标准化后的四元数
        q = FQuat.Normalize(q);

        // 限制 W 在 [-1, 1] 范围内，防止浮点误差导致 Acos 返回 NaN
        float w = Math.Clamp((float)q.W, -1f, 1f);
        angle = 2.0f * MathF.Acos(w);

        // 处理角度范围 [-π, π]（由于已确保 W >= 0，这里 angle 在 [0, π]）
        // if (angle > MathF.PI)
        //     angle -= 2 * MathF.PI;

        float s = MathF.Sqrt((float)(1 - w * w));

        // 增加阈值，提高数值稳定性
        if (s < 0.001f)
        {
            // 接近 0 度或 180 度时，轴向量不重要（角度很小时力矩也很小）
            axis = new FVector(1, 0, 0);
        }
        else
        {
            axis = new FVector(q.X / s, q.Y / s, q.Z / s);
        }
    }
}