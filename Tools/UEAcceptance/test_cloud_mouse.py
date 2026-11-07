import unreal,json,traceback
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world();assert w
p=unreal.GameplayStatics.get_player_pawn(w,0);p.set_actor_tick_enabled(False)
sub=next(o for o in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if o.get_world()==w)
imc=p.get_editor_property('DesktopMappingContext');look=p.get_editor_property('DesktopLook')
rows=[r for r in imc.get_editor_property('default_key_mappings').get_editor_property('mappings') if r.get_editor_property('action')==look]
by_key={r.get_editor_property('key').export_text():r for r in rows}
print('LOOK_KEYS',list(by_key))
report={'cases':[],'hardware_tested':False}
def check(n,v,**kw):report['cases'].append(dict(case=n,passed=bool(v),**kw))
check('single_possessed_desktop_rig',len(unreal.GameplayStatics.get_all_actors_of_class(w,p.get_class()))==1)
check('scene_checkpoint_props_configured',len(p.get_editor_property('DesktopCheckpointProps'))==2)
for key,row in by_key.items():
    mods=row.get_editor_property('modifiers')
    scalar=next(m for m in mods if isinstance(m,unreal.InputModifierScalar))
    check('fivefold_mouse_gain_'+key,abs(scalar.get_editor_property('scalar').x-.7)<.0001)
    check('mouse_mapping_not_inverted_'+key,not any(isinstance(m,unreal.InputModifierNegate) for m in mods))
start_yaw=p.get_actor_rotation().yaw
camera=p.get_editor_property('Camera');start_pitch=camera.get_editor_property('relative_rotation').pitch
frames=0;stage=0;done=False
def inject(key):sub.inject_input_vector_for_action(look,unreal.Vector(1,0,0),list(by_key[key].get_editor_property('modifiers')),[])
inject('MouseX')
out=Path(unreal.Paths.project_dir()).resolve()/'Saved/Tests/Cloud-Mouse-20261107.json'
def tick(dt):
    global frames,stage,done,handle
    if done:return
    frames+=1
    if frames<3:return
    try:
        if stage==0:
            delta=p.get_actor_rotation().yaw-start_yaw
            check('native_mouse_right_yaw',abs(delta-.7)<.01,yaw_degrees=delta)
            inject('MouseY');stage=1;frames=0;return
        delta=camera.get_editor_property('relative_rotation').pitch-start_pitch
        check('native_mouse_up_pitch',abs(delta-.7)<.01,pitch_degrees=delta)
        report['passed']=all(c['passed'] for c in report['cases']);done=True
    except Exception:report['error']=traceback.format_exc();report['passed']=False;done=True
    if done:
        out.write_text(json.dumps(report,indent=2),encoding='utf-8')
        unreal.unregister_slate_post_tick_callback(handle)
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
handle=unreal.register_slate_post_tick_callback(tick)
print('Started native mouse mapping checks',out)
