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
    return result.stdout


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

    occupied = '+DefaultChannelResponses=(Channel=ECC_GameTraceChannel1,Name="HostWeaponTrace")'
    overlay.write_text(section + "!DefaultChannelResponses=ClearArray\n" + occupied + "\n", encoding="utf-8")
    plan = run("--plan", reference, overlay, expected=0)
    assert "3DWidget: ECC_GameTraceChannel1 -> ECC_GameTraceChannel5 (add)" in plan
    assert "VRPlayer: ECC_GameTraceChannel2 -> ECC_GameTraceChannel2 (add)" in plan
    additions = [line for line in plan.splitlines() if line.startswith("+DefaultChannelResponses=")]
    assert len(additions) == 4
    assert overlay.read_text(encoding="utf-8") == section + "!DefaultChannelResponses=ClearArray\n" + occupied + "\n"
    migrated = directory / "MigratedEngine.ini"
    migrated.write_text(section + "\n".join(additions) + "\n", encoding="utf-8")
    run(reference, overlay, migrated, expected=1, contains="3DWidget: channel is ECC_GameTraceChannel5")
    run("--allow-remapped-channels", reference, overlay, migrated, expected=0)
    plan = run("--plan", reference, overlay, migrated, expected=0)
    assert "3DWidget: ECC_GameTraceChannel1 -> ECC_GameTraceChannel5 (keep)" in plan
    assert "+DefaultChannelResponses=" not in plan

    migrated.write_text(section + "\n".join(additions + [occupied.replace("Channel1", "Channel5")]) + "\n", encoding="utf-8")
    run("--allow-remapped-channels", reference, overlay, migrated, expected=1, contains="ECC_GameTraceChannel5 also used by HostWeaponTrace")
    run("--plan", reference, overlay, migrated, expected=1, contains="resolve the existing definitions or occupied slot")
    migrated.write_text(section + "\n".join(additions).replace("ECC_GameTraceChannel5", "ECC_GameTraceChannel19") + "\n",
                        encoding="utf-8")
    run("--allow-remapped-channels", reference, overlay, migrated, expected=1, contains="not a project custom collision slot")
    overlay.write_text(section + "!DefaultChannelResponses=ClearArray\n" + "\n".join(
        f'+DefaultChannelResponses=(Channel=ECC_GameTraceChannel{i},Name="Host{i}")' for i in range(1, 19)
    ) + "\n", encoding="utf-8")
    assert not run("--plan", reference, overlay, expected=1, contains="no free custom collision slot")
print("Host collision checker: strict checks, ordered overrides, slot planning and remapped verification passed.")
