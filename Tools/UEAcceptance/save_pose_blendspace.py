import unreal
blend=unreal.load_asset('/VRSharp/Tests/BS_ToolGrip')
assert unreal.EditorAssetLibrary.save_loaded_asset(blend,only_if_is_dirty=False)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(blend)
print('Saved native BlendSpace triangulation')
