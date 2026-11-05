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
class UVRSharpGrabbable {public int TriggerNotifications; public void NotifyGrabTrigger(object h,object c,float v){TriggerNotifications++;}}
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
class UVRSharpGrabbable {public int TriggerNotifications; public void NotifyGrabTrigger(object h,object c,float v){TriggerNotifications++;}}
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
Check(r.SetGrabTrigger(.5f)&&count==1&&last==.5f&&r.GrabbedObject.TriggerNotifications==1);Check(r.SetGrabTrigger(.5f)&&count==1);
Check(!r.SetGrabTrigger(float.NaN)&&count==1);Check(r.SetGrabTrigger(2)&&last==1);
Check(r.SetGrabTrigger(0)&&last==0&&count==3);r.Component=null;Check(!r.SetGrabTrigger(1));
r.IsGrabbing=false;Check(!r.SetGrabTrigger(1));Console.WriteLine("Held trigger production subset: changed events, context, clamping and rejected input passed.");}}
'''
with tempfile.TemporaryDirectory(prefix="vrsharp-held-trigger-") as d:
 p=Path(d)
 (p/"Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework></PropertyGroup></Project>')
 (p/"Program.cs").write_text(trigger_code+body("public bool SetGrabTrigger(")+trigger_tests)
 subprocess.run(["dotnet","run","--project",str(p/"Check.csproj"),"--configuration","Release"],check=True)

# Verify that the Pawn only removes contexts that it installed itself.
src = (root / "Script/ManagedVRSharp/Core/VRSharpDesktopTestPawn.cs").read_text()
code = '''using System;
using System.Collections.Generic;
class UInputMappingContext {}
class APlayerController {
 public bool Local=true;
 public UEnhancedInputLocalPlayerSubsystem Subsystem=new();
 public bool IsLocalController()=>Local;
}
class UEnhancedInputLocalPlayerSubsystem {
 public Dictionary<UInputMappingContext,int> Contexts=new();
 public int Adds,Removes;
 public bool HasMappingContext(UInputMappingContext context,out int priority)=>Contexts.TryGetValue(context,out priority);
 public void AddMappingContext(UInputMappingContext context,int priority){Contexts.Add(context,priority);Adds++;}
 public void RemoveMappingContext(UInputMappingContext context){Contexts.Remove(context);Removes++;}
}
static class SystemLibrary {public static bool IsValid(object? x)=>x!=null;}
class Rig {
 public UInputMappingContext? DesktopMappingContext;
 public int DesktopMappingPriority=3;
 public APlayerController? Controller;
 private APlayerController? mappingController;
 private UEnhancedInputLocalPlayerSubsystem? mappingSubsystem;
 private UInputMappingContext? mappedContext;
 private bool ownsMappingContext;
 public int Resets;
 private void ResetDesktopInput(){Resets++;}
 private APlayerController? GetController()=>Controller;
 private T? GetLocalPlayerSubsystem<T>(APlayerController c) where T:class=>c.Subsystem as T;
 public void RefreshDesktopMapping()
'''
code += body('private void RefreshDesktopMapping(')
code += ' public void ClearDesktopMapping() ' + body('private void ClearDesktopMapping(')
code += '''}
class Program {
 static void Check(bool result){if(!result)throw new Exception("mapping lifecycle regression");}
 static void Main(){
  var context=new UInputMappingContext();var a=new APlayerController();var b=new APlayerController();
  var rig=new Rig{DesktopMappingContext=context};rig.RefreshDesktopMapping();
  rig.Controller=a;rig.RefreshDesktopMapping();rig.RefreshDesktopMapping();
  Check(a.Subsystem.Adds==1&&a.Subsystem.Contexts[context]==3);
  rig.Controller=null;rig.RefreshDesktopMapping();Check(a.Subsystem.Removes==1&&rig.Resets==1);
  b.Subsystem.Contexts.Add(context,9);rig.Controller=b;rig.RefreshDesktopMapping();rig.ClearDesktopMapping();
  Check(b.Subsystem.Adds==0&&b.Subsystem.Removes==0&&b.Subsystem.Contexts[context]==9);
  rig.Controller=a;rig.RefreshDesktopMapping();rig.ClearDesktopMapping();rig.ClearDesktopMapping();
  Check(a.Subsystem.Adds==2&&a.Subsystem.Removes==2&&rig.Resets==3);
  a.Local=false;rig.RefreshDesktopMapping();Check(a.Subsystem.Adds==2);
  Console.WriteLine("Desktop mapping ownership: possession, loss, re-entry, external context and remote controller passed.");
 }
}
'''
with tempfile.TemporaryDirectory(prefix="vrsharp-desktop-mapping-") as d:
 p=Path(d)
 (p/"Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><Nullable>enable</Nullable></PropertyGroup></Project>')
 (p/"Program.cs").write_text(code)
 subprocess.run(["dotnet","run","--project",str(p/"Check.csproj"),"--configuration","Release"],check=True)

# Hand creation and teardown with substitutes for the Unreal actor calls.
code = '''using System;
struct TSubclassOf<T> { public int ClassId; }
struct FVector { public FVector(int x,int y,int z){} }
record FTransform(int Rotation,int Location,FVector Scale);
enum ESpawnActorCollisionHandlingMethod { AlwaysSpawn }
class USceneComponent { public int WorldRotation=2,WorldLocation=3; }
class AVRSharpHand {
 public bool? Left; public object? GrabbedObject; public bool Destroyed;
 public int Releases;
 public void InitializeHand(bool left){Left=left;}
 public void Release(){Releases++;GrabbedObject=null;}
 public void DestroyActor(){if(GrabbedObject!=null)throw new Exception("still held");Destroyed=true;}
}
static class SystemLibrary {public static bool IsValid(object? x)=>x!=null;}
class Rig {
 public int Spawns;
 public bool SpawnFails;
 private AVRSharpHand? SpawnActor(TSubclassOf<AVRSharpHand> cls,FTransform transform,ESpawnActorCollisionHandlingMethod mode)
 {if(transform.Location!=3||transform.Rotation!=2)throw new Exception("wrong target transform");Spawns++;return SpawnFails?null:new();}
 public AVRSharpHand? PrepareDesktopHand(AVRSharpHand? assignedHand,TSubclassOf<AVRSharpHand> handClass,USceneComponent? target,bool isLeft,out AVRSharpHand? spawnedHand)
'''
code += body('private AVRSharpHand? PrepareDesktopHand(')
code += ' public static void DestroySpawnedHand(AVRSharpHand? hand) ' + body('private static void DestroySpawnedHand(')
code += '''}
class Program {
 static void Check(bool ok){if(!ok)throw new Exception("desktop hand setup regression");}
 static void Main(){
  var rig=new Rig();var target=new USceneComponent();var cls=new TSubclassOf<AVRSharpHand>{ClassId=1};
  var assigned=new AVRSharpHand();
  Check(rig.PrepareDesktopHand(assigned,cls,target,true,out var owned)==assigned&&owned==null&&assigned.Left==true&&rig.Spawns==0);
  Check(rig.PrepareDesktopHand(null,default,target,false,out owned)==null&&owned==null&&rig.Spawns==0);
  Check(rig.PrepareDesktopHand(null,cls,null,false,out owned)==null&&rig.Spawns==0);
  var hand=rig.PrepareDesktopHand(null,cls,target,false,out owned);
  Check(hand!=null&&hand==owned&&hand.Left==false&&rig.Spawns==1);
  hand!.GrabbedObject=new();Rig.DestroySpawnedHand(owned);Check(hand.Releases==1&&hand.Destroyed&&!assigned.Destroyed);
  rig.SpawnFails=true;Check(rig.PrepareDesktopHand(null,cls,target,true,out owned)==null&&owned==null);
  Console.WriteLine("Desktop hand setup: preplaced hand, spawn transform, missing/failed class and owned cleanup passed.");
 }
}
'''
with tempfile.TemporaryDirectory(prefix="vrsharp-desktop-hands-") as d:
 p=Path(d)
 (p/"Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><Nullable>enable</Nullable></PropertyGroup></Project>')
 (p/"Program.cs").write_text(code)
 subprocess.run(["dotnet","run","--project",str(p/"Check.csproj"),"--configuration","Release"],check=True)

# Compile the setup report with fake native references and test authored/runtime setup.
code = '''using System;
using System.Collections.Generic;
class Native {public bool Valid=true;}
class AVRSharpHand:Native {}
class USceneComponent:Native {}
class UInputAction:Native {}
struct TSubclassOf<T> {public int ClassId;}
static class SystemLibrary {public static bool IsValid(Native? value)=>value?.Valid==true;}
class Rig {
 public Native? Camera=new(),DesktopMappingContext;
 public AVRSharpHand? LeftHand,RightHand;
 public TSubclassOf<AVRSharpHand> LeftHandClass=new(){ClassId=1},RightHandClass=new(){ClassId=2};
 public USceneComponent? LeftTarget=new(),RightTarget=new();
 public UInputAction? DesktopMove=new(),DesktopLook=new(),DesktopHandMove=new(),DesktopGrip=new(),
  DesktopSwitchHand=new(),DesktopTrigger=new(),DesktopHandRotate,DesktopToggleGrip,DesktopFingers,DesktopLeftTrigger,DesktopRightTrigger;
 public bool desktopHandsPrepared;
 public string GetDesktopSetupIssues()
'''
code += body('public string GetDesktopSetupIssues(')
code += ' private void CheckDesktopHandSetup(List<string> issues,string side,AVRSharpHand? hand,TSubclassOf<AVRSharpHand> handClass,USceneComponent? target) ' + body('private void CheckDesktopHandSetup(')
code += ' private static void CheckDesktopAction(List<string> issues,Dictionary<UInputAction,string> usedActions,string name,UInputAction? action,bool required) ' + body('private static void CheckDesktopAction(')
code += '''}
class Program {
 static void Check(bool ok){if(!ok)throw new Exception("desktop setup report regression");}
 static void Main(){
  var rig=new Rig();Check(rig.GetDesktopSetupIssues()=="");
  rig.DesktopGrip=rig.DesktopTrigger;rig.LeftHandClass=default;rig.LeftTarget=null;
  var report=rig.GetDesktopSetupIssues();Check(report.Contains("DesktopTrigger reuses")&&report.Contains("Assign LeftHand")&&report.Contains("LeftTarget is missing"));
  rig.desktopHandsPrepared=true;rig.RightHand=new();rig.DesktopMappingContext=new(){Valid=false};
  report=rig.GetDesktopSetupIssues();Check(report.Contains("LeftHand is unavailable")&&report.Contains("DesktopMappingContext is invalid"));
  rig.LeftTarget=new();rig.LeftHand=rig.RightHand;rig.DesktopMappingContext=null;rig.DesktopGrip=new();
  Check(rig.GetDesktopSetupIssues().Contains("same actor"));
  rig.LeftHand=new();Check(rig.GetDesktopSetupIssues()=="");
  Console.WriteLine("Desktop setup report: classes, missing references, duplicate actions, failed runtime hand and recovery passed.");
 }
}
'''
with tempfile.TemporaryDirectory(prefix="vrsharp-desktop-setup-") as d:
 p=Path(d)
 (p/"Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><Nullable>enable</Nullable></PropertyGroup></Project>')
 (p/"Program.cs").write_text(code)
 subprocess.run(["dotnet","run","--project",str(p/"Check.csproj"),"--configuration","Release"],check=True)

# A keyboard/UI test can hold both triggers while moving only one hand.
code = '''using System;
struct FVector { public double X,Y,Z; public static FVector Zero=>default; }
class AVRSharpHand {
 public bool IsGrabbing=true;
 public float HeldTrigger,Index;
 public void SetGrabTrigger(float value){if(IsGrabbing)HeldTrigger=value;}
 public void ClearFingerInput(){Index=0;}
 public void SetFingerInput(float thumb,float index,float grasp){Index=index;}
}
static class SystemLibrary {public static bool IsValid(object? x)=>x!=null;}
class Rig {
 private float? leftTrigger,rightTrigger;
 private float trigger;
 private FVector fingerInput,moveInput,handInput,handRotateInput;
 public bool ControlLeftHand=true;
 public AVRSharpHand LeftHand=new(),RightHand=new();
 private AVRSharpHand ActiveHand=>ControlLeftHand?LeftHand:RightHand;
 private void ReleaseDesktopGrip(){}
 public void Sample(){ApplyDesktopFingerInput(LeftHand,ControlLeftHand,leftTrigger);ApplyDesktopFingerInput(RightHand,!ControlLeftHand,rightTrigger);}
'''
for signature in ['public void SetHandTrigger(bool left, float value)', 'public void SetTrigger(float value)',
                  'public void SelectLeftHand(bool left)', 'public void ResetDesktopInput()',
                  'private void ApplyDesktopFingerInput(AVRSharpHand? hand, bool active, float? dedicatedTrigger)']:
 code += signature + body(signature) + '\n'
code += '''}
class Program {
 static void Check(bool ok){if(!ok)throw new Exception("desktop dual trigger regression");}
 static void Main(){
  var rig=new Rig();rig.RightHand.HeldTrigger=.4f;rig.Sample();Check(rig.RightHand.HeldTrigger==.4f);
  rig.SetHandTrigger(true,.75f);rig.SetHandTrigger(false,.8f);rig.SetTrigger(1);rig.Sample();
  Check(rig.LeftHand.HeldTrigger==1&&rig.RightHand.HeldTrigger==.8f);
  rig.SelectLeftHand(false);rig.Sample();Check(rig.LeftHand.HeldTrigger==.75f&&rig.RightHand.HeldTrigger==.8f);
  rig.SetHandTrigger(true,0);rig.Sample();Check(rig.LeftHand.HeldTrigger==0&&rig.RightHand.HeldTrigger==.8f);
  rig.LeftHand.IsGrabbing=false;rig.SetHandTrigger(true,.5f);rig.Sample();Check(rig.LeftHand.Index==.5f);
  rig.ResetDesktopInput();rig.Sample();Check(rig.LeftHand.Index==0&&rig.RightHand.HeldTrigger==0);
  Console.WriteLine("Desktop dual triggers: simultaneous hold, switch, isolated release, empty hand and reset passed.");
 }
}
'''
with tempfile.TemporaryDirectory(prefix="vrsharp-desktop-triggers-") as d:
 p=Path(d)
 (p/"Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><Nullable>enable</Nullable></PropertyGroup></Project>')
 (p/"Program.cs").write_text(code)
 subprocess.run(["dotnet","run","--project",str(p/"Check.csproj"),"--configuration","Release"],check=True)
