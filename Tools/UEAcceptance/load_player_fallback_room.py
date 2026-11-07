import unreal
assert unreal.EditorLevelLibrary.get_game_world() is None
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/VRSharp/Maps/VRSharpVRInteractionTest')
print('Opened the same VRSharpPlayer test level; automatic PC fallback will be selected without XR')
