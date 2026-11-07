"""Exercise automatic fallback on the original physical VRSharpPlayer in ordinary PIE."""
import unreal,json,traceback,math
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world();assert w
p=unreal.GameplayStatics.get_player_pawn(w,0)
assert p.get_class()==unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpPlayer').generated_class()
pc=unreal.GameplayStatics.get_player_controller(w,0)
sub=next(o for o in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if o.get_world()==w)
c=p.get_editor_property('DesktopInput');s=c.get_editor_property('Settings')
cam=p.get_editor_property('Camera');body=p.get_editor_property('BodyCapsule')
hands=[p.get_editor_property(side+'Hand') for side in ['Left','Right']]
props=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.load_asset('/VRSharp/Tests/BP_VRSharpFlashlight').generated_class())
report={'cases':[],'headset_tested':False,'physical_player':True}
def call(o,n,*args):return o.call_method(n,args=args)
def check(n,v,**data):report['cases'].append(dict(case=n,passed=bool(v),**data))
def mapped(context):return sub.has_mapping_context(context) is not None
def inject(name,x=0,y=0,z=0):sub.inject_input_vector_for_action(s.get_editor_property(name),unreal.Vector(x,y,z),[],[])
check('original_player_auto_mode',str(p.get_editor_property('ControlMode')).endswith('AUTO: 0>') and p.get_editor_property('IsDesktopMode'))
check('desktop_component_bound',call(c,'IsDesktopInputBound') and not call(c,'GetDesktopSetupIssues'))
check('desktop_mapping_only',mapped(s.get_editor_property('MappingContext')) and not mapped(unreal.load_asset('/VRSharp/Input/VRSharpInputContext')))
check('camera_hmd_lock_disabled',not cam.get_editor_property('lock_to_hmd'))
check('physical_body_retained',body.is_simulating_physics())
check('xr_targets_disabled',not p.get_editor_property('LeftController').is_component_tick_enabled() and not p.get_editor_property('RightController').is_component_tick_enabled())
check('no_duplicate_hands',len([a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpHandRight').generated_class())])==2)
p.set_actor_location(unreal.Vector(-180,0,p.get_actor_location().z),False,True)
body.set_physics_linear_velocity(unreal.Vector())
stage=0;frames=0;done=False
out=Path(unreal.Paths.project_dir()).resolve()/'Saved/Tests/Player-Desktop-Fallback-20261107.json'
def tick(dt):
    global stage,frames,done,handle,start,props_ready
    if done:return
    frames+=1
    try:
        if stage==0:
            if frames<7:return
            start=p.get_actor_location()
            check('standing_eye_height',abs(cam.get_world_location().z-170)<2,height_cm=cam.get_world_location().z)
            check('grounded_idle',(body.get_physics_linear_velocity()).length()<2)
            stage=1;frames=0;return
        if stage==1:
            inject('Move',1)
            if frames<8:return
            d=p.get_actor_location()-start
            check('wasd_forward_axis',d.x>10 and abs(d.y)<5,delta_x=d.x,delta_y=d.y)
            stage=2;frames=0;return
        if stage==2:
            if frames<8:return
            v=body.get_physics_linear_velocity()
            check('movement_completed_stops',math.hypot(v.x,v.y)<3,horizontal_speed=math.hypot(v.x,v.y))
            inject('Look',90,15)
            stage=3;frames=0;return
        if stage==3:
            if frames<10:return
            check('mouse_look_applied',abs(cam.get_world_rotation().yaw-90)<1 and abs(cam.get_world_rotation().pitch-15)<1)
            for i,h in enumerate(hands):
                offset=c.get_editor_property('LeftHandOffset' if i==0 else 'RightHandOffset')
                target=cam.get_world_location()+cam.get_forward_vector()*offset.x+cam.get_right_vector()*offset.y+cam.get_up_vector()*offset.z
                distance=(h.get_actor_location()-target).length()
                check('camera_local_hand_follows_'+str(i),distance<3,error_cm=distance)
            start=p.get_actor_location();stage=4;frames=0;return
        if stage==4:
            inject('Move',1)
            if frames<6:return
            d=p.get_actor_location()-start
            check('movement_follows_view_yaw',d.y>8 and abs(d.x)<8,delta_x=d.x,delta_y=d.y)
            stage=5;frames=0;return
        if stage==5:
            if frames<8:return
            # Isolate grip input from room furniture without replacing the physical Player.
            p.set_actor_location(unreal.Vector(-250,-250,p.get_actor_location().z),False,True)
            inject('Look',-90,-15)
            stage=6;frames=0;return
        if stage==6:
            if frames<10:return
            for h,a in zip(hands,props):
                b=a.get_editor_property('Body');b.set_enable_gravity(False)
                a.set_actor_location(h.get_editor_property('GrabSphere').get_world_location(),False,True)
                b.set_physics_linear_velocity(unreal.Vector());b.set_physics_angular_velocity_in_radians(unreal.Vector())
            inject('LeftGrip',1);inject('RightGrip',1)
            stage=7;frames=0;return
        if stage==7:
            inject('LeftGrip',1);inject('RightGrip',1)
            if frames<4:return
            check('independent_mouse_grips',all(call(h,'GetCurrentGrabComponent') is not None for h in hands))
            stage=8;frames=0;return
        if stage==8:
            inject('LeftGrip',1);inject('RightGrip',1);inject('LeftTrigger',1);inject('RightTrigger',1)
            if frames<4:return
            check('independent_tool_triggers',all(abs(call(h,'GetGrabPoseTrigger')-1)<.001 for h in hands))
            check('both_tools_activate',all(call(a.get_editor_property('Grab'),'GetIsTriggerActive') for a in props))
            inject('SwitchHand',1);stage=9;frames=0;return
        if stage==9:
            inject('RightGrip',1);inject('RightTrigger',1)
            if frames<4:return
            check('left_release_preserves_right_after_switch',call(hands[0],'GetCurrentGrabComponent') is None and call(hands[1],'GetCurrentGrabComponent') is not None)
            pc.un_possess();stage=10;frames=0;return
        if stage==10:
            if frames<4:return
            check('unpossess_unbinds_component',not call(c,'IsDesktopInputBound'))
            check('unpossess_removes_own_mapping',not mapped(s.get_editor_property('MappingContext')))
            check('unpossess_releases_input_owned_grips',all(call(h,'GetCurrentGrabComponent') is None for h in hands))
            pc.possess(p);stage=11;frames=0;return
        if stage==11:
            if frames<4:return
            check('repossess_rebinds',call(c,'IsDesktopInputBound') and mapped(s.get_editor_property('MappingContext')))
            report['passed']=all(v['passed'] for v in report['cases']);done=True
    except Exception:report['passed']=False;report['error']=traceback.format_exc();done=True
    if done:
        out.write_text(json.dumps(report,indent=2),encoding='utf-8')
        unreal.unregister_slate_post_tick_callback(handle)
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
handle=unreal.register_slate_post_tick_callback(tick)
print('Started original-player automatic PC acceptance',out)
