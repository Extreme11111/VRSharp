# VRSharp

A physical VR framework plugin for Unreal Engine, with C# gameplay through UnrealSharp.

## Environment

- Unreal Engine 5.7
- UnrealSharp 0.1 (the original .NET 9 integration used by this project)
- .NET 9 SDK for the managed checks

## Current work

- Mass-normalized hand spring response and variable-frame-time handling.
- Local grab selection: palm-facing ray first, then the nearest collision surface within the grab sphere; refresh selection when gripping.
- Finger contact feedback: open below 0.8 probe radius, hold shallow contact, and close again after separation.
- Camera-local neck marker, head collision sphere, and a shorter body capsule with the existing height adjustments preserved.
- Modular VRSharpLab environment, editable Blender sources, imported meshes/materials, and lab collision helpers.
- Physics locomotion and Lumen stability work in progress.

The framework is still under development. Automated checks do not replace headset testing. Stair/uneven-ground traversal still needs a complete runtime validation pass, and reported time-varying lighting artifacts remain unresolved. The experimental hard-shadow workaround was reverted.

## Using the plugin

Place this repository at `<UEProject>/Plugins/VRSharp` in an UnrealSharp-enabled UE 5.7 project. The UnrealSharp plugin/runtime is a separate dependency and is not vendored here. The plugin maps are `/VRSharp/Maps/VRSharpDemo` and `/VRSharp/Maps/VRSharpLab`.

The host project needs the VRSharp collision profiles/channels and suitable physics configuration. `VRSharpCollesion.ini` is the original collision-profile reference. `Examples/VRSharpLab/DefaultEngine.ini` is the current lab host configuration snapshot, including substepping and rendering settings; review and merge the relevant sections instead of replacing an existing project's configuration wholesale. Custom channel indices can conflict with other projects.

Before opening the migrated map, run the read-only collision preflight with Python 3:

```text
python3 Tools/check_host_collision.py /path/to/host/Config/DefaultEngine.ini
```

Pass any relevant platform Engine INI files after the base file in load order.
The check reports reserved slot collisions and incompatible VRSharp profiles. See
[the migration handover](Docs/LocalUEHandover.md) for Blueprint remapping and PIE acceptance.

## Sources and checks

- `ArtSource/VRSharpLab/`: final editable Blender scene, separate FBX parts, textures, and assembly manifests. The `.blend` and exported assets include geometry repairs; the initial modeling script alone does not reproduce every subsequent repair.
- `Tools/`: modeling/import helpers, the local editor MCP adapter, and regression checks. See [Tools/README.md](Tools/README.md) before running editor scripts.
- `Docs/`: implementation notes, validation limits, and historical planning/environment records. Local paths in older records describe the original development workspace.

Run the standalone math checks from this repository:

```powershell
dotnet run --project Tools/SpringMathChecks/SpringMathChecks.csproj --configuration Release
dotnet run --project Tools/FingerContactChecks/FingerContactChecks.csproj --configuration Release
```

## Documentation

Original framework documentation: http://space-art.net/vrsharp/index.html

## Continuous cloud development

See [Docs/Continuous-Improvement.md](Docs/Continuous-Improvement.md) and [AGENTS.md](AGENTS.md) for priorities, validation limits and unattended-work rules. Binary assets are tracked with Git LFS; install Git LFS before cloning or run `git lfs pull` after checkout. GitHub Actions validates standalone math and LFS downloads; it does not by itself schedule AI development.
