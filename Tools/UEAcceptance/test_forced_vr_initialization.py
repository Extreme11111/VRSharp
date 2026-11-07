import unreal,json
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world();assert w
p=unreal.GameplayStatics.get_player_pawn(w,0)
c=p.get_editor_property('DesktopInput')
sub=next(o for o in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if o.get_world()==w)
cases=[]
def check(name,v):cases.append({'case':name,'passed':bool(v)})
check('forced_vr_uses_original_player',p.get_class()==unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpPlayer').generated_class())
check('forced_vr_not_desktop',not p.get_editor_property('IsDesktopMode'))
check('desktop_adapter_not_bound',not c.call_method('IsDesktopInputBound'))
check('xr_mapping_added_by_player',sub.has_mapping_context(unreal.load_asset('/VRSharp/Input/VRSharpInputContext')) is not None)
check('desktop_mapping_absent',sub.has_mapping_context(c.get_editor_property('Settings').get_editor_property('MappingContext')) is None)
check('hmd_camera_lock_preserved',p.get_editor_property('Camera').get_editor_property('lock_to_hmd'))
check('motion_controller_ticks_preserved',p.get_editor_property('LeftController').is_component_tick_enabled() and p.get_editor_property('RightController').is_component_tick_enabled())
report={'passed':all(x['passed'] for x in cases),'cases':cases,'headset_tested':False,'scope':'forced initialization branch only'}
(Path(unreal.Paths.project_dir()).resolve()/'Saved/Tests/Player-VR-Initialization-20261107.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
unreal.get_default_object(p.get_class()).set_editor_property('ControlMode',unreal.VRSharpControlMode.AUTO,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
print(json.dumps(report,indent=2))
