"""Finish the handoff room and apply the requested mouse direction/sensitivity."""
import unreal
assert unreal.EditorLevelLibrary.get_game_world() is None
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name()=='/VRSharp/Maps/VRSharpDesktopTest.VRSharpDesktopTest'
ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
with unreal.ScopedEditorTransaction('Finalize desktop camera mapping and repeatable room checkpoint'):
    imc=unreal.load_asset('/VRSharp/Tests/IMC_VRSharpDesktop')
    data=imc.get_editor_property('default_key_mappings');rows=list(data.get_editor_property('mappings'))
    for row in rows:
        if row.get_editor_property('action')!=unreal.load_asset('/VRSharp/Tests/IA_DesktopLook'):continue
        modifiers=[]
        for mod in row.get_editor_property('modifiers'):
            if isinstance(mod,unreal.InputModifierNegate):continue
            if isinstance(mod,unreal.InputModifierScalar):mod.set_editor_property('scalar',unreal.Vector(.7,.7,.7))
            modifiers.append(mod)
        row.set_editor_property('modifiers',modifiers)
    imc.set_editor_property('default_key_mappings',unreal.InputMappingContextMappingData(mappings=rows))
    assert unreal.EditorAssetLibrary.save_loaded_asset(imc,only_if_is_dirty=False)
    props=[]
    for a in ed.get_all_level_actors():
        n=a.get_actor_label()
        if n in ['Left test bench','Right test bench']:
            a.set_actor_location(unreal.Vector(45,-35 if n.startswith('Left') else 35,107),False,True)
        if n.startswith('DesktopFlashlight_'):
            a.set_actor_location_and_rotation(unreal.Vector(30,-20 if n.endswith('Left') else 20,128),unreal.Rotator(),False,True)
            props.append(a)
        if isinstance(a,unreal.TextRenderActor):
            a.text_render.set_text('VRSHARP / DESKTOP ACCEPTANCE\nWASD + Q/E: Fly | Mouse: Look\nLMB / RMB: Left / Right grip\nTab: Select hand | IJKL UO: Hand move\nR/F T/G Y/H: Hand rotate | P: Latch\nV / B: Left / Right trigger | Shift: Active trigger\nZ X C: Thumb / Index / Grasp\nF5: Save checkpoint | F9: Restore room')
    cls=unreal.load_asset('/VRSharp/Tests/BP_DesktopTestPawn').generated_class()
    pawn=next((a for a in ed.get_all_level_actors() if a.get_class()==cls),None)
    if pawn is None:pawn=ed.spawn_actor_from_class(cls,unreal.Vector(0,0,160),unreal.Rotator())
    pawn.set_actor_label('Desktop interaction rig')
    pawn.set_editor_property('auto_possess_player',unreal.AutoReceiveInput.PLAYER0)
    pawn.set_editor_property('DesktopCheckpointProps',props)
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('Saved room checkpoint props; MouseX/MouseY gain 0.70, vertical inversion removed')
