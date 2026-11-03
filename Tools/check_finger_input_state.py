"""Compile selected production method bodies without Unreal bindings; not a gameplay build."""
from pathlib import Path
import subprocess, tempfile
root = Path(__file__).resolve().parents[1]
source = (root / "Script/ManagedVRSharp/Core/VRSharpHand.cs").read_text(encoding="utf-8-sig")
def extract(signature):
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]
methods = [extract(s) for s in ["public bool SetFingerInput(", "public void ClearFingerInput(", "private void SetAllAnimationWeights("]]
handlers = ["ThumbTouchedAnim", "ThumbClickedAnim", "IndexClickedAnim", "GraspClickedAnim", "ThumbReleasedAnim", "IndexReleasedAnim", "GraspReleasedAnim"]
for name in handlers:
    method = extract("private void " + name + "(")
    methods.append("public void " + name + "() " + method[method.index("{"):])
test = """
static void Check(bool ok) { if (!ok) throw new Exception("finger input ownership regression"); }
public static void Main() {
 var h = new TestHand(); var other = new TestHand();
 Check(h.SetFingerInput(.2f,.4f,.6f));
 h.ThumbTouchedAnim(); h.ThumbClickedAnim(); h.IndexClickedAnim(); h.GraspClickedAnim();
 h.ThumbReleasedAnim(); h.IndexReleasedAnim(); h.GraspReleasedAnim();
 Check(h.targetThumbWeight==.2f && h.targetIndexWeight==.4f && h.targetGraspWeight==.6f);
 other.GraspClickedAnim(); Check(other.targetGraspWeight==1);
 h.IsGrabbing=true; Check(!h.SetFingerInput(0,0,0));
 h.ClearFingerInput(); Check(h.targetGraspWeight==.6f);
 h.IsGrabbing=false; h.ClearFingerInput(); h.ClearFingerInput();
 Check(h.targetThumbWeight==0 && h.targetIndexWeight==0 && h.targetGraspWeight==0);
 h.GraspClickedAnim(); Check(h.targetGraspWeight==1);
 Console.WriteLine("Production method subset: ownership, release, grab protection and hand isolation passed.");
}
"""
with tempfile.TemporaryDirectory(prefix="vrsharp-input-state-") as directory:
    path = Path(directory)
    (path/"Check.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings></PropertyGroup></Project>')
    (path/"FingerInput.cs").write_text((root/"Script/ManagedVRSharp/Core/FingerInput.cs").read_text())
    (path/"Program.cs").write_text("using VRSharp.Core; class TestHand { public bool IsGrabbing; private bool externalFingerInput; public float targetThumbWeight,targetIndexWeight,targetGraspWeight;\n"+"\n".join(methods)+test+"}")
    subprocess.run(["dotnet","run","--project",str(path/"Check.csproj"),"--configuration","Release"],check=True)
