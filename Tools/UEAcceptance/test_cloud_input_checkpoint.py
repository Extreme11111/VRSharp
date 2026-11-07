"""Validate real Enhanced Input dispatch, independent holds and native checkpoint restoration."""
import unreal,json,traceback
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world();assert w
p=unreal.GameplayStatics.get_player_pawn(w,0)
sub=next(o for o in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if o.get_world()==w)
hands=[p.get_editor_property(s+'Hand') for s in ['Left','Right']]
props=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.load_asset('/VRSharp/Tests/BP_VRSharpFlashlight').generated_class())
report={'cases':[],'hardware_tested':False}
def call(o,n,*args):return o.call_method(n,args=args)
def check(n,v,**kw):report['cases'].append(dict(case=n,passed=bool(v),**kw))
def config(o,n,v):o.set_editor_property(n,v,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
def inject(n,v):sub.inject_input_vector_for_action(p.get_editor_property('Desktop'+n),unreal.Vector(v,0,0),[],[])
p.set_actor_tick_enabled(False)
for i,(h,a) in enumerate(zip(hands,props)):
    call(h,'Release')
    h.set_actor_location_and_rotation(unreal.Vector(3000,3000+i*100,1000),unreal.Rotator(),False,True)
    h.set_actor_tick_enabled(False)
    b=h.get_editor_property('HandRigidbody');b.set_enable_gravity(False)
    a.get_editor_property('Body').set_enable_gravity(False)
    a.set_actor_location_and_rotation(h.get_editor_property('GrabSphere').get_world_location(),unreal.Rotator(),False,True)
    t=p.get_editor_property(('Left' if i==0 else 'Right')+'Target')
    t.set_world_location(h.get_actor_location(),False,True);t.set_world_rotation(h.get_actor_rotation(),False,True)
config(p,'DesktopCheckpointProps',props)
check('checkpoint_capture',call(p,'CaptureDesktopCheckpoint'))
saved=[a.get_actor_transform() for a in props];origin=p.get_actor_location()
stage=0;frames=0;done=False
out=Path(unreal.Paths.project_dir()).resolve()/'Saved/Tests/Cloud-Input-Checkpoint-20261107.json'
def tick(dt):
    global stage,frames,done,handle
    if done:return
    frames+=1
    try:
        if stage==0:
            inject('LeftGrip',1);inject('RightGrip',1)
            if frames<4:return
            check('input_left_and_right_grip',all(call(h,'GetCurrentGrabComponent') is not None for h in hands))
            stage=1;frames=0;return
        if stage==1:
            inject('LeftGrip',1);inject('RightGrip',1);inject('LeftTrigger',1);inject('RightTrigger',1)
            call(p,'ReceiveTick',1/90)
            if frames<4:return
            call(p,'ReceiveTick',1/90)
            check('input_independent_triggers',all(abs(call(h,'GetGrabPoseTrigger')-1)<.001 for h in hands))
            check('both_tools_lit',all(call(a.get_editor_property('Grab'),'GetIsTriggerActive') for a in props))
            inject('SwitchHand',1)
            stage=2;frames=0;return
        if stage==2:
            inject('RightGrip',1);inject('RightTrigger',1)
            call(p,'ReceiveTick',1/90)
            if frames<4:return
            check('input_release_isolated_after_switch',call(hands[0],'GetCurrentGrabComponent') is None and call(hands[1],'GetCurrentGrabComponent') is not None)
            check('input_left_trigger_completed_zero',call(hands[0],'GetGrabPoseTrigger')==0)
            check('input_right_trigger_retained',abs(call(hands[1],'GetGrabPoseTrigger')-1)<.001)
            check('tool_release_lights_isolated',not call(props[0].get_editor_property('Grab'),'GetIsTriggerActive') and call(props[1].get_editor_property('Grab'),'GetIsTriggerActive'))
            stage=3;frames=0;return
        if stage==3:
            # End input holds, then displace the registered physics props.
            if frames<4:return
            for i,a in enumerate(props):
                call(hands[i],'Release')
                a.set_actor_location(unreal.Vector(3600,3200+i*100,1100),False,True)
                a.get_editor_property('Body').set_physics_linear_velocity(unreal.Vector(5,10,0))
            p.set_actor_location(origin+unreal.Vector(50,20,10),False,True)
            inject('RestoreCheckpoint',1)
            stage=4;frames=0;return
        if stage==4:
            if frames<3:return
            check('input_checkpoint_key_restores_pawn',(p.get_actor_location()-origin).length()<.01)
            check('checkpoint_restores_props',all((a.get_actor_location()-t.translation).length()<.1 for a,t in zip(props,saved)))
            check('checkpoint_clears_velocity',all(a.get_editor_property('Body').get_physics_linear_velocity().length()<.01 for a in props))
            check('checkpoint_releases_both',all(call(h,'GetCurrentGrabComponent') is None for h in hands))
            report['passed']=all(c['passed'] for c in report['cases']);done=True
    except Exception:report['error']=traceback.format_exc();report['passed']=False;done=True
    if done:
        out.write_text(json.dumps(report,indent=2),encoding='utf-8')
        unreal.unregister_slate_post_tick_callback(handle)
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
handle=unreal.register_slate_post_tick_callback(tick)
print('Started input/checkpoint native tests',out)
