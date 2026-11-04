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
members="\n".join(l for l in s.splitlines() if any(x in l for x in ["public UPrimitiveComponent? GrabbedComponent {","public int GrabCount =>","public bool IsGrabbed =>","public event Action<AVRSharpHand","public bool IsHeldBy(","public AVRSharpHand[] GetGrabbingHands()"]))
code="""using System; using System.Linq; using System.Collections.Generic;
enum EAttachmentRule {KeepWorld} enum EDetachmentRule {KeepWorld}
class UPrimitiveComponent {public bool Valid=true;}
static class SystemLibrary {public static bool IsValid(object o)=>o is UPrimitiveComponent c?c.Valid:o!=null;}
class AVRSharpHand {
 public bool IsGrabbing,Success=true; public UVRSharpGrabbable? GrabbedObject;
 public int Attaches,Detaches;
 public bool AttachToComponent(UPrimitiveComponent c,string s,EAttachmentRule a,EAttachmentRule b,EAttachmentRule d,bool w){Attaches++;return Success;}
 public void DetachFromActor(EDetachmentRule a,EDetachmentRule b,EDetachmentRule c){Detaches++;}
}
class UVRSharpGrabbable {
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
 Check(b.Attaches>1&&b.Detaches>0);
 c.Valid=false;g.Attach(a,c);Check(entered==2);
 Console.WriteLine("Production grab subset: contextual events, state, failed/duplicate attachment and dual-hand release passed.");
 }
}"""
with tempfile.TemporaryDirectory(prefix="vrsharp-grab-check-") as d:
 p=Path(d)
 (p/"Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable></PropertyGroup></Project>')
 (p/"Program.cs").write_text(code+members+method("public void Attach(")+method("public void Detach(")+tests)
 subprocess.run(["dotnet","run","--project",str(p/"Check.csproj"),"--configuration","Release"],check=True)
