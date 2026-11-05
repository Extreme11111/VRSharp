"""Production Attach/Detach subset; native calls are doubles, not UE validation."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
s=(root/"Script/ManagedVRSharp/Core/VRSharpGrabbable.cs").read_text()
def method(sig):
 start=s.index(sig); i=s.index("{",start); depth=1; end=i+1
 while depth:
  depth+=(s[end]=="{")-(s[end]=="}");end+=1
 return s[start:end]
members="\n".join(l for l in s.splitlines() if any(x in l for x in ["public UPrimitiveComponent? GrabbedComponent {","public int GrabCount =>","public bool IsGrabbed =>","public bool IsTriggerActive =>","public event Action<AVRSharpHand","public bool IsHeldBy(","public AVRSharpHand[] GetGrabbingHands()"]))
code="""using System; using System.Linq; using System.Collections.Generic;
enum EAttachmentRule {KeepWorld} enum EDetachmentRule {KeepWorld}
class UPrimitiveComponent {
 public bool Valid=true,Simulating=true;
 public int LinearVelocity=10,AngularVelocity=20;
 public bool IsSimulatingPhysics()=>Simulating;
 public void SetPhysicsLinearVelocity(int velocity){LinearVelocity=velocity;}
 public void SetPhysicsAngularVelocityInRadians(int velocity,bool add,string? bone){AngularVelocity=velocity;}
}
static class SystemLibrary {public static bool IsValid(object o)=>o is UPrimitiveComponent c?c.Valid:o!=null;}
class AVRSharpHand {
 public int GrabNotices,ReleaseNotices;
 public void NotifyGrabbed(UVRSharpGrabbable g,UPrimitiveComponent c){if(!IsGrabbing||GrabbedObject!=g)throw new Exception();GrabNotices++;}
 public void NotifyReleased(UVRSharpGrabbable g,UPrimitiveComponent c){if(IsGrabbing||GrabbedObject!=null)throw new Exception();ReleaseNotices++;}
 public bool IsGrabbing,Success=true; public UVRSharpGrabbable? GrabbedObject;
 public int Attaches,Detaches;
 public bool AttachToComponent(UPrimitiveComponent c,string s,EAttachmentRule a,EAttachmentRule b,EAttachmentRule d,bool w){Attaches++;return Success;}
 public void DetachFromActor(EDetachmentRule a,EDetachmentRule b,EDetachmentRule c){Detaches++;}
}
class UVRSharpGrabbable {
 public bool DropWithoutMomentum;
 public float TriggerPressThreshold,TriggerReleaseThreshold;
 private readonly HashSet<AVRSharpHand> activeTriggerHands=new();
 public UPrimitiveComponent? GetHeldComponent(AVRSharpHand hand)=>components.TryGetValue(hand,out var c)&&c.Valid?c:null;
 public bool AdmissionAllowed=true; public bool CanGrab(AVRSharpHand hand)=>AdmissionAllowed;
 private readonly List<AVRSharpHand> hands=new();
 private readonly Dictionary<AVRSharpHand,UPrimitiveComponent> components=new();
"""
tests="""}
class Program {
 static void Check(bool x){if(!x)throw new Exception("grab lifecycle regression");}
 static void Main(){
 var g=new UVRSharpGrabbable();var a=new AVRSharpHand();var b=new AVRSharpHand();var c=new UPrimitiveComponent();int entered=0,left=0;
 g.Grabbed+=(h,o,p)=>{Check(o==g&&p==c&&g.IsHeldBy(h)&&h.GrabbedObject==g);entered++;};
 g.Released+=(h,o,p)=>{Check(o==g&&p==c&&!g.IsHeldBy(h)&&!h.IsGrabbing);left++;};
 g.AdmissionAllowed=false;g.Attach(a,c);Check(!g.IsGrabbed&&entered==0);g.AdmissionAllowed=true;
 Check(!g.IsGrabbed);a.Success=false;g.Attach(a,c);Check(!g.IsGrabbed&&entered==0);
 a.Success=true;g.Attach(a,c);g.Attach(a,c);Check(g.GrabCount==1&&entered==1);
 g.Attach(b,c);var snapshot=g.GetGrabbingHands();g.Detach(a);g.Detach(a);
 Check(g.IsGrabbed&&g.GrabCount==1&&left==1&&snapshot.Length==2&&b.IsGrabbing);
 g.Detach(b);Check(!g.IsGrabbed&&g.GrabCount==0&&left==2&&entered==2);
 Check(c.LinearVelocity==10&&c.AngularVelocity==20);
 Check(a.GrabNotices==1&&b.GrabNotices==1&&a.ReleaseNotices==1&&b.ReleaseNotices==1);
 var drop=new UVRSharpGrabbable{DropWithoutMomentum=true};
 var first=new UPrimitiveComponent();var last=new UPrimitiveComponent();
 drop.Attach(a,first);drop.Attach(b,last);drop.Detach(a);
 Check(first.LinearVelocity==10&&last.LinearVelocity==10&&last.AngularVelocity==20);
 drop.Released+=(h,o,p)=>Check(!o.IsGrabbed&&p==last&&p.LinearVelocity==0&&p.AngularVelocity==0);
 drop.Detach(b);Check(first.LinearVelocity==10&&first.AngularVelocity==20);
 foreach(var skipped in new[]{new UPrimitiveComponent{Simulating=false},new UPrimitiveComponent()}){
  var item=new UVRSharpGrabbable{DropWithoutMomentum=true};item.Attach(a,skipped);
  if(skipped.Simulating)skipped.Valid=false;
  item.Detach(a);Check(!item.IsGrabbed&&skipped.LinearVelocity==10&&skipped.AngularVelocity==20);
 }
 Check(b.Attaches>1&&b.Detaches>0);

 c.Valid=false;g.Attach(a,c);Check(entered==2);
 var tool=new UVRSharpGrabbable{TriggerPressThreshold=.75f,TriggerReleaseThreshold=.55f};
 var grip=new UPrimitiveComponent();var secondGrip=new UPrimitiveComponent();
 var activation=new List<(AVRSharpHand, UPrimitiveComponent, bool)>();
 tool.TriggerActivationChanged+=(h,o,p,v)=>{Check(o==tool&&o.IsTriggerActive==v);activation.Add((h,p,v));};
 tool.NotifyGrabTrigger(a,grip,1);Check(!tool.IsTriggerActive);
 tool.Attach(a,grip);tool.Attach(b,secondGrip);
 tool.NotifyGrabTrigger(a,secondGrip,1);Check(!tool.IsTriggerActive);
 tool.NotifyGrabTrigger(a,grip,.8f);tool.NotifyGrabTrigger(a,grip,.6f);Check(tool.IsTriggerActive&&activation.Count==1);
 tool.NotifyGrabTrigger(b,secondGrip,.9f);tool.NotifyGrabTrigger(a,grip,0);tool.Detach(a);
 Check(tool.IsTriggerActive&&activation.Count==1);
 tool.Detach(b);Check(!tool.IsTriggerActive&&activation.SequenceEqual(new[]{(a,grip,true),(b,secondGrip,false)}));
 tool.Attach(b,secondGrip);tool.NotifyGrabTrigger(b,secondGrip,.6f);Check(!tool.IsTriggerActive);
 tool.NotifyGrabTrigger(b,secondGrip,.8f);tool.NotifyGrabTrigger(b,secondGrip,.55f);Check(!tool.IsTriggerActive&&activation.Count==4);
 tool.Detach(b);Check(activation.Count==4);
 Console.WriteLine("Tool trigger activation: hysteresis, per-hand aggregation, context rejection, release and regrab passed.");
 Console.WriteLine("Production grab subset: contextual events, state, failed/duplicate attachment and dual-hand release, and opt-in momentum reset passed.");
 }
}"""
with tempfile.TemporaryDirectory(prefix="vrsharp-grab-check-") as d:
 p=Path(d)
 (p/"Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable></PropertyGroup></Project>')
 (p/"Program.cs").write_text(code+members+method("public void Attach(")+method("public void Detach(")+method("internal void NotifyGrabTrigger(")+method("private void SetTriggerHandActive(")+tests)
 subprocess.run(["dotnet","run","--project",str(p/"Check.csproj"),"--configuration","Release"],check=True)
