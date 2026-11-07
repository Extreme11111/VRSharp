"""Create a separate, repeatable native desktop acceptance level; leave the lab intact."""
import unreal

level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert unreal.EditorLevelLibrary.get_game_world() is None
path='/VRSharp/Maps/VRSharpDesktopTest'
assert not unreal.EditorAssetLibrary.does_asset_exist(path), 'Acceptance map exists; use targeted changes.'
assert level.new_level(path)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
with unreal.ScopedEditorTransaction('Build desktop interaction acceptance room'):
    world.get_world_settings().set_editor_property('default_game_mode',unreal.load_asset('/VRSharp/Tests/BP_DesktopTestGameMode').generated_class())
    cube=unreal.load_asset('/Engine/BasicShapes/Cube')
    def box(label,location,scale):
        a=ed.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*location))
        a.set_actor_label(label);a.static_mesh_component.set_static_mesh(cube);a.set_actor_scale3d(unreal.Vector(*scale));return a
    box('Floor',(100,0,-10),(12,10,.2))
    box('Flashlight projection wall',(450,0,180),(.2,10,3.6))
    box('Left test bench',(85,-60,96),(.6,.75,.12))
    box('Right test bench',(85,60,96),(.6,.75,.12))
    start=ed.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(0,0,160));start.set_actor_label('Desktop start')
    flash=unreal.load_asset('/VRSharp/Tests/BP_VRSharpFlashlight').generated_class()
    for side,y in [('Left',-60),('Right',60)]:
        a=ed.spawn_actor_from_class(flash,unreal.Vector(85,y,115),unreal.Rotator())
        a.set_actor_label('DesktopFlashlight_'+side)
    light=ed.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,400),unreal.Rotator(pitch=-55,yaw=30))
    light.get_component_by_class(unreal.DirectionalLightComponent).set_intensity(3)
    sky=ed.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,400))
    sky.get_component_by_class(unreal.SkyLightComponent).set_intensity(1)
    ed.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector())
    text=ed.spawn_actor_from_class(unreal.TextRenderActor,unreal.Vector(438,-210,280),unreal.Rotator(yaw=180))
    text.text_render.set_text('VRSHARP / DESKTOP ACCEPTANCE\nWASD + Q/E: Fly | Mouse: Look\nLMB / RMB: Left / Right grip\nTab: Select hand | IJKL UO: Hand move\nR/F T/G Y/H: Hand rotate | P: Latch\nV / B: Left / Right trigger | Shift: Active trigger\nZ X C: Thumb / Index / Grasp')
    text.text_render.set_world_size(10)
assert level.save_current_level()
unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(-250,-330,270),unreal.Rotator(pitch=-10,yaw=35))
print('SAVED',path)
