# Development tools

The Blender authoring scripts use the sibling `ArtSource/VRSharpLab` folder. Use Blender 4.x and the saved final `.blend` for geometry checks or edits. `build_lab_models.py` constructs the initial kit; later part separation, dais repair, and coplanar-face union steps are separate scripts. Prefer editing the saved final sources when maintaining the imported scene.

Editor import/assembly scripts and PIE checks were authored against a host project layout:

```
<UEProject>/Tools/
<UEProject>/ArtSource/VRSharpLab/
<UEProject>/Plugins/VRSharp/
<UEProject>/Saved/Tests/
```

For those workflows, copy these Python files to the host project's `Tools` folder and the authoring assets to its `ArtSource` folder. The scripts operate on `/VRSharp/Maps/VRSharpLab` and its named actors/assets. Inspect each script first; scene assembly/import scripts can rebuild or modify assets. Run tests in a disposable project copy when using a different layout. Historical setup/patch snippets and local caches were deliberately left out of this directory.

The editor MCP adapter uses the official Python MCP SDK. Set up a Python environment with `mcp`, start `editor_mcp_bridge.py` in the UE Python console, then invoke the client with the host-project test script:

```powershell
python Tools/editor_mcp.py Tools/test_grab_selection.py
python Tools/editor_mcp.py Tools/test_finger_feedback.py
```

UE must have its Python editor scripting plugin enabled. The adapter only dispatches project `Tools/*.py` scripts on the editor thread. The bridge must be reloaded after reopening UE.

The standalone C# check projects in this repository are configured for this plugin directory layout. Keep them in place and use the commands in the root README; their source includes point to the production math helper. No UE editor or generated Glue assembly is needed for these math-only checks.
