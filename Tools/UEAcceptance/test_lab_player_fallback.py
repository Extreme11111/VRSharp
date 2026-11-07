import unreal,json
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world();assert w
p=unreal.GameplayStatics.get_player_pawn(w,0)
cls=unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpPlayer').generated_class()
actors=unreal.GameplayStatics.get_all_actors_of_class(w,cls)
print('POSSESSED',p.get_class().get_path_name(),[(a.get_actor_label(),str(a.get_controller())) for a in actors])
cases=[]
def check(name,v):cases.append({'case':name,'passed':bool(v)})
check('existing_lab_original_player_possessed',p.get_class()==cls)
if p.get_class()==cls:
    c=p.get_editor_property('DesktopInput')
    check('existing_lab_auto_pc',p.get_editor_property('ControlMode')==unreal.VRSharpControlMode.AUTO and p.get_editor_property('IsDesktopMode'))
    check('existing_lab_component_configured',not c.call_method('GetDesktopSetupIssues') and c.call_method('IsDesktopInputBound'))
    check('existing_lab_physical_body',p.get_editor_property('BodyCapsule').is_simulating_physics())
    check('existing_lab_hands_ready',all(p.get_editor_property(s+'Hand') is not None for s in ['Left','Right']))
report={'passed':all(v['passed'] for v in cases),'cases':cases,'headset_tested':False}
(Path(unreal.Paths.project_dir()).resolve()/'Saved/Tests/Player-Lab-Fallback-20261107.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
print(json.dumps(report,indent=2))
