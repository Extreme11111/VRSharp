import unreal
assert unreal.EditorLevelLibrary.get_game_world() is None
bp=unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpPlayer')
assert unreal.get_default_object(bp.generated_class()).get_editor_property('ControlMode')==unreal.VRSharpControlMode.AUTO
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/VRSharp/Maps/VRSharpLab')
print('Opened the existing VRSharpLab without changing its Pawn or GameMode')
