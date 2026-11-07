import unreal,json
from pathlib import Path
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert world.get_path_name()=='/VRSharp/Maps/VRSharpVRInteractionTest.VRSharpVRInteractionTest'
desktop=unreal.load_asset('/VRSharp/Tests/BP_DesktopTestPawn').generated_class()
mode=unreal.load_asset('/VRSharp/Tests/BP_VRInteractionTestGameMode')
vr=unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpPlayer').generated_class()
assert not any(a.get_class()==desktop for a in ed.get_all_level_actors())
assert world.get_world_settings().get_editor_property('default_game_mode')==mode.generated_class()
assert unreal.get_default_object(mode.generated_class()).get_editor_property('default_pawn_class')==vr
assert len([a for a in ed.get_all_level_actors() if a.get_class()==unreal.load_asset('/VRSharp/Tests/BP_VRSharpFlashlight').generated_class()])==2
print('VR map has the original VR Pawn GameMode, two tools and no desktop rig')
for side in ['Left','Right']:
    bp=unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpHand'+side)
    action=unreal.get_default_object(bp.generated_class()).get_editor_property('AnalogTriggerAction')
    assert action and action.get_editor_property('value_type')==unreal.InputActionValueType.AXIS3D
    print('XR_ANALOG',side,action.get_path_name())
print('Native acceptance assets loaded successfully after editor recovery')
