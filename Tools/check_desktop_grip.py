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
 (p/"Program.cs").write_text(code+body("private void OnDesktopGrab(")+" public void Cancel() "+body("private void ReleaseDesktopGrip(")+" public bool ToggleActiveGrip() "+body("public bool ToggleActiveGrip()")+tests)
 subprocess.run(["dotnet","run","--project",str(p/"Check.csproj"),"--configuration","Release"],check=True)
