namespace VRSharp.Core;
public static class FingerInput
{
    public static float Normalize(float sample, float previous)
        => float.IsFinite(sample) ? Math.Clamp(sample, 0f, 1f)
            : float.IsFinite(previous) ? Math.Clamp(previous, 0f, 1f) : 0f;
}
