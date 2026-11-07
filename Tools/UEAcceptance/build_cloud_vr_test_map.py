"""Provide a headset acceptance variant using the existing VR Pawn and XR input assets."""
import unreal
assert unreal.EditorLevelLibrary.get_game_world() is None
editor=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
tools=unreal.AssetToolsHelpers.get_asset_tools()
mode_path='/VRSharp/Tests/BP_VRInteractionTestGameMode'
mode=unreal.load_asset(mode_path) if unreal.EditorAssetLibrary.does_asset_exist(mode_path) else None
if mode is None:
    f=unreal.BlueprintFactory();f.set_editor_property('parent_class',unreal.GameModeBase)
    mode=tools.create_asset('BP_VRInteractionTestGameMode','/VRSharp/Tests',unreal.Blueprint,f)
unreal.get_default_object(mode.generated_class()).set_editor_property('default_pawn_class',unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpPlayer').generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(mode)
assert unreal.EditorAssetLibrary.save_loaded_asset(mode,only_if_is_dirty=False)
path='/VRSharp/Maps/VRSharpVRInteractionTest'
assert not unreal.EditorAssetLibrary.does_asset_exist(path), 'VR acceptance map exists; use targeted updates.'
assert level.new_level_from_template(path,'/VRSharp/Maps/VRSharpDesktopTest')
with unreal.ScopedEditorTransaction('Configure existing VR player for interaction acceptance'):
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    world.get_world_settings().set_editor_property('default_game_mode',mode.generated_class())
    for actor in editor.get_all_level_actors():
        if actor.get_class()==unreal.load_asset('/VRSharp/Tests/BP_DesktopTestPawn').generated_class():
            editor.destroy_actor(actor)  # Remove our desktop-only rig from this newly duplicated test fixture.
        elif isinstance(actor,unreal.PlayerStart):actor.set_actor_location(unreal.Vector(0,0,100),False,True)
        elif isinstance(actor,unreal.TextRenderActor):
            actor.text_render.set_text('VRSHARP / XR INTERACTION ACCEPTANCE\nGrip: Grab / Release | Trigger: Tool + Finger pose\nTwo separate tools and reusable grip presets\nExisting VRSharp Player / OpenXR mapping\nHeadset acceptance required')
    assert level.save_current_level()
print('Saved VRSharpVRInteractionTest; return to the desktop map in a separate MCP call')
