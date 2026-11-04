"""Managed desktop grip method subset; excludes Unreal input dispatch and physics."""
from pathlib import Path
import tempfile,subprocess
root=Path(__file__).resolve().parents[1]
src=(root/"Script/ManagedVRSharp/Core/VRSharpDesktopTestPawn.cs").read_text()
def body(signature):
 i=src.index("{",src.index(signature)); end=i+1;depth=1
 while depth:
  depth+=(src[end]=="{")-(src[end]=="}");end+=1
 return src[i:end]
code="""using System;
struct FVector {public static FVector Zero=>new();}
struct FRotator {}
class Target {public FVector RelativeLocation;public FRotator RelativeRotation;}
class UVRSharpGrabbable {}
static class SystemLibrary {public static bool IsValid(object x)=>x!=null;}
class AVRSharpHand {
 public bool IsGrabbing,CanGrab=true;public UVRSharpGrabbable? GrabbedObject;public int Releases;
 public bool TryGrab(){if(!CanGrab||IsGrabbing)return false;IsGrabbing=true;GrabbedObject=new();return true;}
 public void SetGrabTrigger(float x){}
 public void Release(){IsGrabbing=false;GrabbedObject=null;Releases++;}
}
class Rig {
 public AVRSharpHand? ActiveHand;
 private float trigger;
 private bool targetsCaptured=true;
 private FVector handInput,handRotateInput,initialLeftLocation,initialRightLocation;
 private FRotator initialLeftRotation,initialRightRotation;
 public Target? LeftTarget=new(),RightTarget=new();
 private AVRSharpHand? gripInputHand;
 private UVRSharpGrabbable? gripInputObject;
 public void Press()
"""
tests="""
}
class Program {
 static void Check(bool x){if(!x)throw new Exception("desktop grip ownership");}
 static void Main(){
 var a=new AVRSharpHand();var b=new AVRSharpHand();var r=new Rig{ActiveHand=a};
 r.Press();r.Press();b.TryGrab();r.ActiveHand=b;r.Cancel();
 Check(a.Releases==1&&b.Releases==0&&b.IsGrabbing);
 r.Cancel();Check(a.Releases==1);
 var failed=new AVRSharpHand{CanGrab=false};r.ActiveHand=failed;r.Press();r.ActiveHand=b;r.Cancel();
 Check(b.Releases==0);
 r.ActiveHand=a;r.Press();a.Release();a.TryGrab();int before=a.Releases;r.Cancel();
 Check(a.Releases==before&&a.IsGrabbing);
 Check(r.ResetHandTargets());r.LeftTarget=null;Check(!r.ResetHandTargets());
 var left=new AVRSharpHand();var right=new AVRSharpHand();var latch=new Rig{ActiveHand=left};
 Check(latch.ToggleActiveGrip()&&left.IsGrabbing);latch.Cancel();Check(left.IsGrabbing);
 latch.ActiveHand=right;Check(latch.ToggleActiveGrip()&&right.IsGrabbing&&left.IsGrabbing);
 Check(latch.ToggleActiveGrip()&&!right.IsGrabbing&&left.IsGrabbing);
 latch.ActiveHand=left;Check(latch.ToggleActiveGrip()&&!left.IsGrabbing);
 latch.ActiveHand=failed;Check(!latch.ToggleActiveGrip());latch.ActiveHand=null;Check(!latch.ToggleActiveGrip());
 Console.WriteLine("Latched desktop grip: independent two-hand holding, release and rejected requests passed.");
 Console.WriteLine("Desktop grip subset: hand switching, duplicate/cancel, rejected press and replacement object passed.");
 }
}
"""
with tempfile.TemporaryDirectory(prefix="vrsharp-desktop-grip-") as d:
 p=Path(d)
 (p/"Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable></PropertyGroup></Project>')
 (p/"Program.cs").write_text(code+body("private void OnDesktopGrab(")+" public void Cancel() "+body("private void ReleaseDesktopGrip(")+" public bool ToggleActiveGrip() "+body("public bool ToggleActiveGrip()")+" public bool ResetHandTargets() "+body("public bool ResetHandTargets()")+tests)
 subprocess.run(["dotnet","run","--project",str(p/"Check.csproj"),"--configuration","Release"],check=True)

# Production held-trigger method; native validity/component access are doubles.
src=(root/"Script/ManagedVRSharp/Core/VRSharpHand.cs").read_text()
trigger_code='''using System;
class UVRSharpGrabbable {}
class UPrimitiveComponent {}
static class SystemLibrary {public static bool IsValid(object x)=>x!=null;}
static class VRSharpMathHelper {public static float BlendPoseWeight(float a,float b,float t)=>a+(b-a)*t;}
class Rig {
public bool IsGrabbing=true; public UVRSharpGrabbable? GrabbedObject=new();
public UPrimitiveComponent? Component=new();
public UPrimitiveComponent? GetCurrentGrabComponent()=>Component;
private float activePoseTrigger, targetIndexWeight, authoredIndexWeight, triggerIndexWeight;
private bool useTriggerBlend;
public event Action<Rig,UVRSharpGrabbable,UPrimitiveComponent,float>? GrabTriggerChanged;
public bool SetGrabTrigger(float value)
'''
trigger_tests='''}
class Program {static void Check(bool b){if(!b)throw new Exception("held trigger");}
static void Main(){var r=new Rig();int count=0;float last=0;
r.GrabTriggerChanged+=(h,i,c,v)=>{Check(h==r&&i==r.GrabbedObject&&c==r.Component);count++;last=v;};
Check(r.SetGrabTrigger(.5f)&&count==1&&last==.5f);Check(r.SetGrabTrigger(.5f)&&count==1);
Check(!r.SetGrabTrigger(float.NaN)&&count==1);Check(r.SetGrabTrigger(2)&&last==1);
Check(r.SetGrabTrigger(0)&&last==0&&count==3);r.Component=null;Check(!r.SetGrabTrigger(1));
r.IsGrabbing=false;Check(!r.SetGrabTrigger(1));Console.WriteLine("Held trigger production subset: changed events, context, clamping and rejected input passed.");}}
'''
with tempfile.TemporaryDirectory(prefix="vrsharp-held-trigger-") as d:
 p=Path(d)
 (p/"Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework></PropertyGroup></Project>')
 (p/"Program.cs").write_text(trigger_code+body("public bool SetGrabTrigger(")+trigger_tests)
 subprocess.run(["dotnet","run","--project",str(p/"Check.csproj"),"--configuration","Release"],check=True)
