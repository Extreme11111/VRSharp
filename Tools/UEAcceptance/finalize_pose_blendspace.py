import unreal
blend=unreal.load_asset('/VRSharp/Tests/BS_ToolGrip')
sub=unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
sub.open_editor_for_assets([blend])
print('Opened native BlendSpace editor to rebuild its sample triangulation')
