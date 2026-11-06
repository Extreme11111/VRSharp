"""Managed desktop grip method subset; excludes Unreal input dispatch and physics."""
from pathlib import Path
import tempfile,subprocess
root=Path(__file__).resolve().parents[1]
src=(root/"Script/ManagedVRSharp/Core/VRSharpHand.cs").read_text()
def body(signature):
 i=src.index("{",src.index(signature)); end=i+1;depth=1
 while depth:
  depth+=(src[end]=="{")-(src[end]=="}");end+=1
 return src[i:end]
code='using System;\nusing System.Linq;\nclass USceneComponent {public FVector WorldLocation;public string Name="";}\nclass UPrimitiveComponent {}\nclass UVRSharpHandPose:USceneComponent {public UPrimitiveComponent? TargetComponent;public int Priority;public bool DisableLeftHand,DisableRightHand;}\nclass Owner {public USceneComponent[] Items=[];public USceneComponent[] GetComponentsByClass<T>()=>Items;}\nclass UVRSharpGrabbable {public Owner? Owner;public UVRSharpHandPose? Blocked;public bool CanUseGrabPose(UVRSharpHandPose p)=>p!=Blocked;}\nstruct FVector {public double X;public static double DistanceSquared(FVector a,FVector b)=>(a.X-b.X)*(a.X-b.X);}\nstatic class SystemLibrary {public static bool IsValid(object? x)=>x!=null;public static string GetObjectName(USceneComponent x)=>x.Name;}\nclass Rig {public bool IsLeft;public USceneComponent Palm=new();\npublic UVRSharpHandPose? Select(UVRSharpGrabbable g,UPrimitiveComponent c)=>FindExplicitGrabPose(g,c);\n'
tests='}\nclass Program {\nstatic void Check(bool x){if(!x)throw new Exception("pose selection");}\nstatic void Main(){var c=new UPrimitiveComponent();var g=new UVRSharpGrabbable{Owner=new()};var r=new Rig{IsLeft=true};\nUVRSharpHandPose Pose(string name,int priority,double x)=>new(){Name=name,Priority=priority,TargetComponent=c,WorldLocation=new(){X=x}};\nvar near=Pose("near",0,1);var high=Pose("high",1,10);var wrong=Pose("wrong",99,0);wrong.TargetComponent=new();var right=Pose("right",99,0);right.DisableLeftHand=true;var invalid=Pose("invalid",100,double.NaN);\ng.Owner.Items=[near,high,wrong,right,invalid];Check(r.Select(g,c)==high);g.Blocked=high;Check(r.Select(g,c)==near);g.Blocked=null;\nhigh.Priority=0;Check(r.Select(g,c)==near);\nvar tie=Pose("a",0,1);g.Owner.Items=[near,tie];Check(r.Select(g,c)==tie);g.Owner.Items=[tie,near];Check(r.Select(g,c)==tie);\nr.IsLeft=false;g.Owner.Items=[right];Check(r.Select(g,c)==right);right.DisableRightHand=true;Check(r.Select(g,c)==null);g.Owner=null;Check(r.Select(g,c)==null);\nConsole.WriteLine("Authored pose selector method subset passed: collider, handedness, priority, distance, stable ties and missing candidates.");}}\n'
with tempfile.TemporaryDirectory(prefix="vrsharp-desktop-grip-") as d:
 p=Path(d)
 (p/"Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable></PropertyGroup></Project>')
 (p/"Program.cs").write_text(code+"private UVRSharpHandPose? FindExplicitGrabPose(UVRSharpGrabbable grabbable, UPrimitiveComponent component)"+body("private UVRSharpHandPose? FindExplicitGrabPose(")+tests)
 subprocess.run(["dotnet","run","--project",str(p/"Check.csproj"),"--configuration","Release"],check=True)

# Visual lifecycle methods from production; native component validity is doubled.
code='''using System;
class UVRSharpHandPose {public float EnterBlendSeconds,ExitBlendSeconds;}
static class SystemLibrary {public static bool IsValid(object x)=>x!=null;}
class Rig {
private UVRSharpHandPose? animationPose; private float poseBlendWeight, exitPoseTrigger; private bool poseExiting;
public UVRSharpHandPose? GetAnimationGrabPose()=>animationPose;
public float Weight=>poseBlendWeight;public bool Present=>animationPose!=null;
public void Exit(){poseExiting=true;}
public void BeginPoseAnimation(UVRSharpHandPose? pose)
'''
code+=body('private void BeginPoseAnimation(')+' public void AdvancePoseAnimation(float deltaSeconds) '+body('private void AdvancePoseAnimation(')
code+='''}
class Program {static void Check(bool b){if(!b)throw new Exception("pose animation lifecycle");}
static void Main(){foreach(int hz in new[]{30,60,120}){var r=new Rig();var pose=new UVRSharpHandPose{EnterBlendSeconds=.5f,ExitBlendSeconds=.25f};
r.BeginPoseAnimation(pose);Check(r.Weight==0&&r.Present);
for(int i=0;i<hz;i++)r.AdvancePoseAnimation(1f/hz);Check(r.Weight==1);
r.Exit();for(int i=0;i<hz;i++)r.AdvancePoseAnimation(1f/hz);Check(!r.Present&&r.Weight==0);
r.BeginPoseAnimation(pose);r.AdvancePoseAnimation(.125f);Check(r.Weight==.25f);r.Exit();r.AdvancePoseAnimation(.1f);Check(!r.Present);
r.BeginPoseAnimation(pose);r.AdvancePoseAnimation(float.NaN);Check(r.Weight==0);r.BeginPoseAnimation(null);Check(!r.Present);
r.BeginPoseAnimation(new());Check(r.Weight==1);r.Exit();r.AdvancePoseAnimation(.01f);Check(!r.Present);
}Console.WriteLine("Pose visual lifecycle production subset: entry, hold, exit, interruption, legacy defaults and 30/60/120Hz passed.");}}
'''
with tempfile.TemporaryDirectory(prefix="vrsharp-pose-animation-") as d:
 p=Path(d)
 (p/"Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework></PropertyGroup></Project>')
 (p/"Program.cs").write_text(code)
 subprocess.run(["dotnet","run","--project",str(p/"Check.csproj"),"--configuration","Release"],check=True)

# Exercise the requested-pose entry point and production contact filter together.
code = '''using System;
using System.Collections.Generic;
class Owner {}
class UPrimitiveComponent { public Owner? Owner; }
class UVRSharpGrabbable { public Owner? Owner; public bool RequireExplicitGrabPose; public UVRSharpHandPose? Blocked; public bool CanUseGrabPose(UVRSharpHandPose p)=>p!=Blocked; }
class UVRSharpHandPose { public Owner? Owner; public UPrimitiveComponent? TargetComponent;
 public FVector WorldLocation; public bool DisableLeftHand, DisableRightHand; }
struct FVector { public double X; public double LengthSquared()=>X*X;
 public static double DistanceSquared(FVector a,FVector b)=>(a.X-b.X)*(a.X-b.X); }
class Sphere { public FVector WorldLocation; public float ScaledSphereRadius=10; public FVector UpVector=new(){X=1}; }
struct ComponentRef { public UPrimitiveComponent? Object; }
struct FHitResult { public ComponentRef Component; public FVector ImpactPoint,ImpactNormal; public bool StartPenetrating; }
static class SystemLibrary { public static bool IsValid(object? value)=>value!=null; }
class Rig {
 public bool IsGrabbing,IsLeft;
 public Sphere? Palm=new(),GrabSphere=new();
 public UVRSharpGrabbable? Item;
 public UVRSharpHandPose? Attached, Authored;
 private UVRSharpHandPose? FindExplicitGrabPose(UVRSharpGrabbable g,UPrimitiveComponent c)
     => Authored?.TargetComponent==c?Authored:null;
 public List<FHitResult> targetHitResults=new();
 private void EnvironmentCheck(UVRSharpGrabbable g,UPrimitiveComponent c) {}
 private UVRSharpGrabbable? FindGrabbable(UPrimitiveComponent? c)=>c?.Owner==Item?.Owner?Item:null;
 private bool TryGetGrabPoint(UPrimitiveComponent c,FVector origin,out FVector point){point=origin;return true;}
 private bool Grab(UVRSharpGrabbable g,FVector p,FVector n,UPrimitiveComponent c,UVRSharpHandPose pose){Attached=pose;return true;}
 public UPrimitiveComponent? SelectContact() => TrySelectGrabHit(targetHitResults,null,out var hit,out _) ? hit.Component.Object : null;
 public bool TryGrabAtPose(UVRSharpGrabbable grabbable,UVRSharpHandPose pose)
'''
code += body('public bool TryGrabAtPose(')
code += ' private bool IsRequestedPoseValid(UVRSharpGrabbable grabbable,UPrimitiveComponent component,UVRSharpHandPose pose)' + body('private bool IsRequestedPoseValid(')
code += ' private bool TrySelectGrabHit(IList<FHitResult> hits,UVRSharpGrabbable? specificTarget,out FHitResult selected,out UVRSharpGrabbable? grabbable,UPrimitiveComponent? specificComponent=null)' + body('private bool TrySelectGrabHit(')
code += '''}
class Program {
 static void Check(bool result){if(!result)throw new Exception("requested pose contact regression");}
 static void Main(){
  var owner=new Owner();var item=new UVRSharpGrabbable{Owner=owner};var hand=new Rig{Item=item,IsLeft=true};
  var requested=new UPrimitiveComponent{Owner=owner};var sibling=new UPrimitiveComponent{Owner=owner};
  var pose=new UVRSharpHandPose{Owner=owner,TargetComponent=requested};
  FHitResult Hit(UPrimitiveComponent c,double x)=>new(){Component=new(){Object=c},ImpactPoint=new(){X=x}};
  hand.targetHitResults=[Hit(sibling,1),Hit(requested,11)];Check(!hand.TryGrabAtPose(item,pose));
  hand.targetHitResults.Add(Hit(requested,7));Check(hand.TryGrabAtPose(item,pose)&&hand.Attached==pose);
  Check(hand.SelectContact()==sibling);
  item.RequireExplicitGrabPose=true;Check(hand.SelectContact()==null);
  hand.Authored=pose;Check(hand.SelectContact()==requested&&hand.TryGrabAtPose(item,pose));
  item.Blocked=pose;Check(!hand.TryGrabAtPose(item,pose));item.Blocked=null;
  pose.DisableLeftHand=true;Check(!hand.TryGrabAtPose(item,pose));pose.DisableLeftHand=false;
  pose.Owner=new Owner();Check(!hand.TryGrabAtPose(item,pose));pose.Owner=owner;
  pose.WorldLocation=new(){X=double.NaN};Check(!hand.TryGrabAtPose(item,pose));pose.WorldLocation=default;
  hand.IsGrabbing=true;Check(!hand.TryGrabAtPose(item,pose));
  Console.WriteLine("Requested pose: exact local collider, side, owner and already-held guards passed.");
 }
}
'''
with tempfile.TemporaryDirectory(prefix="vrsharp-requested-pose-") as d:
 p=Path(d)
 (p/"Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><Nullable>enable</Nullable></PropertyGroup></Project>')
 (p/"Program.cs").write_text(code)
 subprocess.run(["dotnet","run","--project",str(p/"Check.csproj"),"--configuration","Release"],check=True)
