"""Compile the demo actor with native doubles to verify its event and component wiring."""
from pathlib import Path
import subprocess
import tempfile

source = Path(__file__).resolve().parents[1] / "Script/ManagedVRSharp/Demo/VRSharpFlashlight.cs"
doubles = r"""
using System;
namespace UnrealSharp.Attributes {
    [AttributeUsage(AttributeTargets.Class)] class UClassAttribute : Attribute {}
    [Flags] enum PropertyFlags { BlueprintReadOnly = 1 }
    [AttributeUsage(AttributeTargets.Property)] class UPropertyAttribute(PropertyFlags flags) : Attribute {
        public bool DefaultComponent { get; set; }
        public bool RootComponent { get; set; }
        public string? AttachmentComponent { get; set; }
    }
}
namespace UnrealSharp.Engine {
    public class Native { public bool Valid = true; }
    public class AActor : Native {
        public virtual void BeginPlay() {}
        public virtual void EndPlay(EEndPlayReason reason) {}
    }
    public enum EEndPlayReason { Destroyed }
    public class UPrimitiveComponent : Native {}
    public class UStaticMeshComponent : UPrimitiveComponent {}
    public class USpotLightComponent : Native {
        public bool Visible = true;
        public int Updates;
        public void SetVisibility(bool active, bool propagate) {
            if (!Valid || propagate) throw new Exception("incorrect light target");
            Visible = active;
            Updates++;
        }
    }
    public static class SystemLibrary {
        public static bool IsValid(Native value) => value.Valid;
    }
}
namespace VRSharp.Core {
    using UnrealSharp.Engine;
    public class AVRSharpHand : AActor {}
    public class UVRSharpHandPose : Native {
        public UPrimitiveComponent? TargetComponent;
        public bool DisableLeftHand, DisableRightHand;
    }
    public class UVRSharpGrabbable : Native {
        public float TriggerPressThreshold, TriggerReleaseThreshold;
        public bool IsTriggerActive;
        public event Action<AVRSharpHand, UVRSharpGrabbable, UPrimitiveComponent, bool>? TriggerActivationChanged;
        public void SetActive(bool active, UPrimitiveComponent body) {
            IsTriggerActive = active;
            TriggerActivationChanged?.Invoke(new AVRSharpHand(), this, body, active);
        }
    }
}
namespace VRSharp.Demo {
    using UnrealSharp.Engine;
    using VRSharp.Core;
    public partial class AVRSharpFlashlight {
        private UStaticMeshComponent? body;
        public partial UStaticMeshComponent? Body { get => body; set => body = value; }
        private USpotLightComponent? lamp;
        public partial USpotLightComponent? Lamp { get => lamp; set => lamp = value; }
        private UVRSharpGrabbable? grab;
        public partial UVRSharpGrabbable? Grab { get => grab; set => grab = value; }
        private UVRSharpHandPose? leftGrip;
        public partial UVRSharpHandPose? LeftGrip { get => leftGrip; set => leftGrip = value; }
        private UVRSharpHandPose? rightGrip;
        public partial UVRSharpHandPose? RightGrip { get => rightGrip; set => rightGrip = value; }
    }
    class Program {
        static void Check(bool ok) {
            if (!ok) throw new Exception("flashlight demo wiring regression");
        }
        static void Main() {
            var body = new UStaticMeshComponent();
            var lamp = new USpotLightComponent();
            var grab = new UVRSharpGrabbable();
            var left = new UVRSharpHandPose();
            var right = new UVRSharpHandPose();
            var demo = new AVRSharpFlashlight { Body = body, Lamp = lamp, Grab = grab, LeftGrip = left, RightGrip = right };
            demo.BeginPlay();
            Check(!lamp.Visible && grab.TriggerPressThreshold == .75f && grab.TriggerReleaseThreshold == .55f);
            Check(left.TargetComponent == body && left.DisableRightHand && !left.DisableLeftHand);
            Check(right.TargetComponent == body && right.DisableLeftHand && !right.DisableRightHand);
            grab.SetActive(true, body);
            Check(lamp.Visible);
            grab.SetActive(false, body);
            Check(!lamp.Visible);
            grab.SetActive(true, body);
            demo.EndPlay(EEndPlayReason.Destroyed);
            int updates = lamp.Updates;
            grab.SetActive(true, body);
            Check(!lamp.Visible && lamp.Updates == updates);

            grab.TriggerPressThreshold = .9f;
            grab.TriggerReleaseThreshold = .6f;
            var custom = new AVRSharpFlashlight { Lamp = lamp, Grab = grab };
            custom.BeginPlay();
            Check(lamp.Visible && grab.TriggerPressThreshold == .9f && grab.TriggerReleaseThreshold == .6f);
            lamp.Valid = false;
            custom.EndPlay(EEndPlayReason.Destroyed);
            new AVRSharpFlashlight().BeginPlay();
            Console.WriteLine("Flashlight demo: handed grips, threshold defaults, activation and teardown passed.");
        }
    }
}
"""

with tempfile.TemporaryDirectory(prefix="vrsharp-flashlight-") as directory:
    path = Path(directory)
    (path / "Check.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType>'
        '<TargetFramework>net9.0</TargetFramework><Nullable>enable</Nullable></PropertyGroup></Project>'
    )
    (path / source.name).write_text(source.read_text(encoding="utf-8-sig"))
    (path / "Doubles.cs").write_text(doubles)
    subprocess.run(["dotnet", "run", "--project", str(path / "Check.csproj"), "--configuration", "Release"], check=True)
