namespace VRSharp.Core;

// Engine-independent policy shared by gameplay and standalone regression checks.
public static class GrabAdmission
{
    public static bool Allows(bool disabled, bool leftDisabled, bool rightDisabled,
        bool singleHandOnly, bool isLeft, int holderCount, bool alreadyHolding)
        => !disabled && !(isLeft ? leftDisabled : rightDisabled)
            && (!singleHandOnly || holderCount == 0 || alreadyHolding);
}
