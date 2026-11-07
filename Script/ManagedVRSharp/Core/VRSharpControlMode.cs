using UnrealSharp.Attributes;

namespace VRSharp.Core;

[UEnum]
public enum EVRSharpControlMode : byte
{
    Auto,
    VirtualReality,
    Desktop
}

public static class VRSharpControlModeSelection
{
    // Tracking validity can briefly disappear inside a running XR session.
    // Only session availability determines the initial automatic selection.
    public static EVRSharpControlMode Resolve(EVRSharpControlMode requested, bool connected, bool enabled)
        => requested == EVRSharpControlMode.Auto
            ? connected && enabled ? EVRSharpControlMode.VirtualReality : EVRSharpControlMode.Desktop
            : requested;
}
