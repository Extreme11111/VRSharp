import unreal
assert unreal.EditorLevelLibrary.get_game_world() is None
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/VRSharp/Maps/VRSharpDesktopTest')
print('Returned to the saved desktop acceptance room')
