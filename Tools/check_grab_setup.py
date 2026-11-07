"""Compile the production setup report with native references replaced by doubles."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "Script/ManagedVRSharp/Core/VRSharpGrabbable.cs").read_text()
start = source.index("public string GetGrabSetupIssues()")
opening = source.index("{", start)
end = opening + 1
depth = 1
while depth:
    depth += (source[end] == "{") - (source[end] == "}")
    end += 1

code = """using System;
using System.Collections.Generic;
class Native { public bool Valid=true; }
class Actor : Native {
 public List<USceneComponent> Components=new();
 public IEnumerable<USceneComponent> GetComponentsByClass<T>()=>Components;
}
class USceneComponent : Native { public Actor? Owner; }
class UPrimitiveComponent : USceneComponent {}
class UVRSharpHandPose : USceneComponent {
 public string Name="Grip";
 public UPrimitiveComponent? TargetComponent;
 public bool DisableLeftHand,DisableRightHand,SupportGripOnly;
 public float EnterBlendSeconds,ExitBlendSeconds;
}
static class SystemLibrary {
 public static bool IsValid(Native value)=>value.Valid;
 public static string GetObjectName(UVRSharpHandPose pose)=>pose.Name;
}
class Setup {
 public Actor? Owner=new();
 public bool SingleHandOnly,RequireTwoTriggerHands,RequireSupportHandForPrimaryTrigger;
 public bool RequireExplicitGrabPose,DisableGrabbing,DisableLeftHand,DisableRightHand;
 public float TriggerPressThreshold,TriggerReleaseThreshold;
"""
tests = """}
class Program {
 static void Check(bool ok){if(!ok)throw new Exception("grab authoring report");}
 static void Main(){
  var s=new Setup();Check(s.GetGrabSetupIssues()=="");
  var actor=s.Owner!;
  s.RequireExplicitGrabPose=true;
  Check(s.GetGrabSetupIssues().Contains("Left hand has no compatible")&&s.GetGrabSetupIssues().Contains("Right hand has no compatible"));
  var body=new UPrimitiveComponent{Owner=actor};
  var left=new UVRSharpHandPose{Name="LeftHandle",Owner=actor,TargetComponent=body,DisableRightHand=true};
  var right=new UVRSharpHandPose{Name="RightHandle",Owner=actor,TargetComponent=body,DisableLeftHand=true};
  actor.Components.Add(left);actor.Components.Add(right);
  Check(s.GetGrabSetupIssues()=="");
  left.TargetComponent=new(){Owner=new()};
  Check(s.GetGrabSetupIssues().Contains("LeftHandle: TargetComponent")&&s.GetGrabSetupIssues().Contains("Left hand has no compatible"));
  left.TargetComponent=body;body.Valid=false;Check(s.GetGrabSetupIssues().Contains("TargetComponent"));body.Valid=true;
  right.TargetComponent=null;
  Check(s.GetGrabSetupIssues().Contains("RightHandle: assign TargetComponent"));
  right.TargetComponent=body;
  left.EnterBlendSeconds=float.NaN;
  Check(s.GetGrabSetupIssues().Contains("LeftHandle: animation blend"));left.EnterBlendSeconds=0;
  s.TriggerPressThreshold=.75f;s.TriggerReleaseThreshold=.55f;
  left.SupportGripOnly=right.SupportGripOnly=true;
  Check(s.GetGrabSetupIssues().Contains("no trigger-capable"));
  right.SupportGripOnly=false;Check(s.GetGrabSetupIssues()=="");
  s.SingleHandOnly=true;s.RequireSupportHandForPrimaryTrigger=true;
  Check(s.GetGrabSetupIssues().Contains("SingleHandOnly prevents"));
  s.RequireSupportHandForPrimaryTrigger=false;s.RequireTwoTriggerHands=true;
  Check(s.GetGrabSetupIssues().Contains("SingleHandOnly prevents"));
  s.SingleHandOnly=false;s.TriggerReleaseThreshold=1;
  Check(s.GetGrabSetupIssues().Contains("Trigger thresholds"));
  s.TriggerReleaseThreshold=.55f;s.TriggerPressThreshold=0;
  Check(s.GetGrabSetupIssues()=="");
  actor.Components.Clear();s.DisableGrabbing=true;
  Check(s.GetGrabSetupIssues()=="");
  s.Owner=null;Check(s.GetGrabSetupIssues().Contains("Owner"));
  Console.WriteLine("Grab setup report: migrated references, handed poses, activation conflicts and repaired configuration passed.");
 }
}
"""
with tempfile.TemporaryDirectory(prefix="vrsharp-grab-setup-") as directory:
    project = Path(directory)
    (project / "Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><Nullable>enable</Nullable></PropertyGroup></Project>')
    (project / "Program.cs").write_text(code + source[start:end] + tests)
    subprocess.run(["dotnet", "run", "--project", str(project / "Check.csproj"), "--configuration", "Release"], check=True)
