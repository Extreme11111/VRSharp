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
code='using System;\nusing System.Linq;\nclass USceneComponent {public FVector WorldLocation;public string Name="";}\nclass UPrimitiveComponent {}\nclass UVRSharpHandPose:USceneComponent {public UPrimitiveComponent? TargetComponent;public int Priority;public bool DisableLeftHand,DisableRightHand;}\nclass Owner {public USceneComponent[] Items=[];public USceneComponent[] GetComponentsByClass<T>()=>Items;}\nclass UVRSharpGrabbable {public Owner? Owner;}\nstruct FVector {public double X;public static double DistanceSquared(FVector a,FVector b)=>(a.X-b.X)*(a.X-b.X);}\nstatic class SystemLibrary {public static bool IsValid(object? x)=>x!=null;public static string GetObjectName(USceneComponent x)=>x.Name;}\nclass Rig {public bool IsLeft;public USceneComponent Palm=new();\npublic UVRSharpHandPose? Select(UVRSharpGrabbable g,UPrimitiveComponent c)=>FindExplicitGrabPose(g,c);\n'
tests='}\nclass Program {\nstatic void Check(bool x){if(!x)throw new Exception("pose selection");}\nstatic void Main(){var c=new UPrimitiveComponent();var g=new UVRSharpGrabbable{Owner=new()};var r=new Rig{IsLeft=true};\nUVRSharpHandPose Pose(string name,int priority,double x)=>new(){Name=name,Priority=priority,TargetComponent=c,WorldLocation=new(){X=x}};\nvar near=Pose("near",0,1);var high=Pose("high",1,10);var wrong=Pose("wrong",99,0);wrong.TargetComponent=new();var right=Pose("right",99,0);right.DisableLeftHand=true;var invalid=Pose("invalid",100,double.NaN);\ng.Owner.Items=[near,high,wrong,right,invalid];Check(r.Select(g,c)==high);\nhigh.Priority=0;Check(r.Select(g,c)==near);\nvar tie=Pose("a",0,1);g.Owner.Items=[near,tie];Check(r.Select(g,c)==tie);g.Owner.Items=[tie,near];Check(r.Select(g,c)==tie);\nr.IsLeft=false;g.Owner.Items=[right];Check(r.Select(g,c)==right);right.DisableRightHand=true;Check(r.Select(g,c)==null);g.Owner=null;Check(r.Select(g,c)==null);\nConsole.WriteLine("Authored pose selector method subset passed: collider, handedness, priority, distance, stable ties and missing candidates.");}}\n'
with tempfile.TemporaryDirectory(prefix="vrsharp-desktop-grip-") as d:
 p=Path(d)
 (p/"Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable></PropertyGroup></Project>')
 (p/"Program.cs").write_text(code+"private UVRSharpHandPose? FindExplicitGrabPose(UVRSharpGrabbable grabbable, UPrimitiveComponent component)"+body("private UVRSharpHandPose? FindExplicitGrabPose(")+tests)
 subprocess.run(["dotnet","run","--project",str(p/"Check.csproj"),"--configuration","Release"],check=True)
