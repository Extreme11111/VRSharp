import unreal
assert unreal.EditorLevelLibrary.get_game_world() is None
bp=unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpPlayer')
unreal.get_default_object(bp.generated_class()).set_editor_property('ControlMode',unreal.VRSharpControlMode.VIRTUAL_REALITY,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
print('Temporarily forced the VR initialization branch on the CDO; no asset save')
