"""Compile production pose/preset classes with generated properties and native calls substituted."""
from pathlib import Path
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
sources = []
for name in ("VRSharpHandPosePreset.cs", "VRSharpHandPose.cs"):
    source = (root / "Script/ManagedVRSharp/Core" / name).read_text()
    source = re.sub(r"^using UnrealSharp\..*;\n|^namespace VRSharp.Core;\n|^\s*\[(?:UClass|UProperty|UFunction).*\]\n", "", source, flags=re.M)
    sources.append(source.replace("public partial ", "public "))

doubles = """using System;
using System.Collections.Generic;
public class Native { public bool Valid=true; }
public class UAnimSequence : Native {}
public class UDataAsset : Native {}
public class Actor : Native {
 public List<UActorComponent> Components=new();
 public IEnumerable<UActorComponent> GetComponentsByClass<T>()=>Components;
}
public class UActorComponent : Native {
 public Actor? Owner;
 public virtual void BeginPlay(){}
}
public class USceneComponent : UActorComponent {}
public class UPrimitiveComponent : USceneComponent {}
public class UVRSharpGrabbable : UActorComponent {
 public UVRSharpHandPose? HeldPose;
 public bool IsGrabPoseOccupied(UVRSharpHandPose pose)=>pose==HeldPose;
}
static class SystemLibrary { public static bool IsValid(Native value)=>value.Valid; }
"""
tests = """
class Program {
 static void Check(bool ok){if(!ok)throw new Exception("pose preset regression");}
 static void Main(){
  var legacy=new UVRSharpHandPose{EnterBlendSeconds=.3f,AnimationKey="Legacy"};
  legacy.BeginPlay();Check(legacy.EnterBlendSeconds==.3f&&legacy.AnimationKey=="Legacy");
  var preset=new UVRSharpHandPosePreset{
   EnterBlendSeconds=.1f,ExitBlendSeconds=.2f,AnimationKey="Drill",GripAnimation=new(),PressedAnimation=new(),
   UseFingerWeights=true,UseTriggerBlend=true,ThumbWeight=.6f,IndexWeight=.2f,GraspWeight=.8f,TriggerIndexWeight=.9f
  };
  var body=new UPrimitiveComponent();var owner=new Actor();
  var grab=new UVRSharpGrabbable();owner.Components.Add(grab);
  var left=new UVRSharpHandPose{Owner=owner,AnimationPreset=preset,TargetComponent=body,
   DisableRightHand=true,ExclusiveToOneHand=true,SupportGripOnly=true,Priority=5};
  var right=new UVRSharpHandPose{Owner=owner,AnimationPreset=preset,DisableLeftHand=true};
  left.BeginPlay();right.BeginPlay();
  Check(left.GripAnimation==preset.GripAnimation&&left.PressedAnimation==preset.PressedAnimation);
  Check(left.EnterBlendSeconds==.1f&&left.ExitBlendSeconds==.2f&&left.AnimationKey=="Drill");
  Check(left.UseFingerWeights&&left.UseTriggerBlend&&left.ThumbWeight==.6f&&left.IndexWeight==.2f&&left.GraspWeight==.8f&&left.TriggerIndexWeight==.9f);
  Check(left.DisableRightHand&&left.TargetComponent==body&&left.ExclusiveToOneHand&&left.SupportGripOnly&&left.Priority==5);
  Check(right.DisableLeftHand&&!right.SupportGripOnly&&right.AnimationKey=="Drill");
  preset.AnimationKey="Updated";Check(left.AnimationKey=="Drill");
  grab.HeldPose=left;Check(!left.ApplyAnimationPreset()&&left.AnimationKey=="Drill");
  Check(right.ApplyAnimationPreset()&&right.AnimationKey=="Updated");
  grab.HeldPose=null;Check(left.ApplyAnimationPreset()&&left.AnimationKey=="Updated");
  preset.Valid=false;Check(!left.ApplyAnimationPreset());
  left.AnimationPreset=null;Check(!left.ApplyAnimationPreset()&&left.AnimationKey=="Updated");
  Console.WriteLine("Pose presets: shared initialization, clips, dynamic weights, local geometry, held guards and legacy configuration passed.");
 }
}
"""
with tempfile.TemporaryDirectory(prefix="vrsharp-pose-preset-") as directory:
    project = Path(directory)
    (project / "Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><Nullable>enable</Nullable></PropertyGroup></Project>')
    (project / "Program.cs").write_text(doubles + "\n".join(sources) + tests)
    subprocess.run(["dotnet", "run", "--project", str(project / "Check.csproj"), "--configuration", "Release"], check=True)
