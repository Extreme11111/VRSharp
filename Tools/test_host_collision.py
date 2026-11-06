"""Exercise the migration CLI against the repository reference and host edits."""
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
reference = root / "Examples/VRSharpLab/DefaultEngine.ini"
tool = root / "Tools/check_host_collision.py"


def run(*paths, expected, contains=None):
    result = subprocess.run([sys.executable, str(tool), *map(str, paths)], capture_output=True, text=True)
    assert result.returncode == expected, result.stdout + result.stderr
    if contains:
        assert contains in result.stdout + result.stderr, result.stdout + result.stderr


run(reference, expected=0)
with tempfile.TemporaryDirectory(prefix="vrsharp-collision-") as directory:
    directory = Path(directory)
    host = directory / "DefaultEngine.ini"
    overlay = directory / "WindowsEngine.ini"
    contents = reference.read_text(encoding="utf-8-sig")
    host.write_text(contents.replace('Name="VRGrabCheck")', 'Name="HostWeaponTrace")'), encoding="utf-8")
    run(host, expected=1, contains="ECC_GameTraceChannel3 reserved by VRSharp for VRGrabCheck: also used by HostWeaponTrace")
    run(host, expected=1, contains="VRGrabCheck: missing")
    host.write_text(contents.replace('bTraceType=True,bStaticObject=False,Name="VRGrabCheck")',
                                     'bTraceType=False,bStaticObject=False,Name="VRGrabCheck")'), encoding="utf-8")
    run(host, expected=1, contains="VRGrabCheck: btracetype")
    host.write_text(contents.replace('Channel="VRGrabCheck",Response=ECR_Ignore',
                                     'Channel="VRGrabCheck",Response=ECR_Block'), encoding="utf-8")
    run(host, expected=1, contains="VRHand: expected ECR_Ignore response to VRGrabCheck")
    section = "[/Script/Engine.CollisionProfile]\n"
    entry = next(line for line in contents.splitlines() if line.startswith('+DefaultChannelResponses=') and 'Name="VRHand"' in line)
    overlay.write_text(section + entry + "\n", encoding="utf-8")
    run(reference, overlay, expected=0)
    overlay.write_text(section + "." + entry[1:] + "\n", encoding="utf-8")
    run(reference, overlay, expected=1, contains="VRHand: multiple definitions")
    overlay.write_text(section + "-" + entry[1:] + "\n", encoding="utf-8")
    run(reference, overlay, expected=1, contains="VRHand: missing")
    overlay.write_text(section + "!Profiles=ClearArray\n", encoding="utf-8")
    run(reference, overlay, expected=1, contains="VRHand: missing from profiles")
    overlay.write_text(section + "+Profiles=(Name=Broken\n", encoding="utf-8")
    run(reference, overlay, expected=2, contains="Cannot check collision configuration")
print("Host collision checker: reference, occupied slot, type/response drift, ordered overrides and malformed input passed.")
