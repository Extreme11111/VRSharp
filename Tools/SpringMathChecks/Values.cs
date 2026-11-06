// Engine-free value types for exercising the actual production controller, without a UE process.
namespace UnrealSharp.CoreUObject;

public readonly record struct FVector(double X, double Y, double Z)
{
    public static FVector Zero => default;
    public double LengthSquared() => X * X + Y * Y + Z * Z;
    public static FVector operator +(FVector a, FVector b) => new(a.X + b.X, a.Y + b.Y, a.Z + b.Z);
    public static FVector operator -(FVector a, FVector b) => new(a.X - b.X, a.Y - b.Y, a.Z - b.Z);
    public static FVector operator *(FVector a, double b) => new(a.X * b, a.Y * b, a.Z * b);
}

public readonly record struct FQuat(double X, double Y, double Z, double W)
{
    public static FQuat Normalize(FQuat q)
    {
        double length = Math.Sqrt(q.X * q.X + q.Y * q.Y + q.Z * q.Z + q.W * q.W);
        return new(q.X / length, q.Y / length, q.Z / length, q.W / length);
    }
    public static FQuat Inverse(FQuat q) => new(-q.X, -q.Y, -q.Z, q.W);
    public FVector RotateVector(FVector vector)
    {
        var rotated = this * new FQuat(vector.X, vector.Y, vector.Z, 0) * Inverse(this);
        return new FVector(rotated.X, rotated.Y, rotated.Z);
    }
    public static FQuat operator *(FQuat a, FQuat b) => new(
        a.W * b.X + a.X * b.W + a.Y * b.Z - a.Z * b.Y,
        a.W * b.Y - a.X * b.Z + a.Y * b.W + a.Z * b.X,
        a.W * b.Z + a.X * b.Y - a.Y * b.X + a.Z * b.W,
        a.W * b.W - a.X * b.X - a.Y * b.Y - a.Z * b.Z);
}
