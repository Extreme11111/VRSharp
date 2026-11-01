using UnrealSharp.CoreUObject;

namespace VRSharp.Core;

public static class VRSharpMovementMath
{
    /// <summary>
    /// Removes invalid planar input before it can reach the physical movement impulse.
    /// Values inside the unit circle are preserved; larger finite values are normalized.
    /// </summary>
    public static FVector SanitizePlanarInput(FVector axes)
    {
        double x = double.IsFinite(axes.X) ? axes.X : 0;
        double y = double.IsFinite(axes.Y) ? axes.Y : 0;
        double scale = Math.Max(Math.Abs(x), Math.Abs(y));

        // Scale first so even very large finite inputs cannot overflow LengthSquared().
        if (scale > 1)
        {
            x /= scale;
            y /= scale;
            double magnitude = Math.Sqrt(x * x + y * y);
            x /= magnitude;
            y /= magnitude;
        }
        else
        {
            double magnitudeSquared = x * x + y * y;
            if (magnitudeSquared > 1)
            {
                double inverseMagnitude = 1 / Math.Sqrt(magnitudeSquared);
                x *= inverseMagnitude;
                y *= inverseMagnitude;
            }
        }

        return new FVector(x, y, 0);
    }
}
