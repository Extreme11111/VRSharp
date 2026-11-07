"""Exercise the integrated native UE paths in the desktop acceptance map via MCP."""
import unreal,json,time,traceback,math
from pathlib import Path

w=unreal.EditorLevelLibrary.get_game_world();assert w
p=unreal.GameplayStatics.get_player_pawn(w,0)
assert 'DesktopTestPawn' in p.get_class().get_name()
pc=unreal.GameplayStatics.get_player_controller(w,0)
sub=next(o for o in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if o.get_world()==w)
print('INJECT_VECTOR',sub.inject_input_vector_for_action.__doc__)
report={'cases':[],'hardware_tested':False,'full_animation_clip_graph_tested':False}
def check(name,condition,**values):
    report['cases'].append(dict(case=name,passed=bool(condition),**values))
    if not condition:print('FAILED',name,values)
def call(o,n,*args):return o.call_method(n,args=args)
left=p.get_editor_property('LeftHand');right=p.get_editor_property('RightHand')
props=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.load_asset('/VRSharp/Tests/BP_VRSharpFlashlight').generated_class())
check('desktop_setup',not call(p,'GetDesktopSetupIssues'))
check('native_input_bound',call(p,'IsDesktopInputBound'))
check('camera_not_hmd_locked',not p.get_editor_property('Camera').get_editor_property('lock_to_hmd'))
check('both_hands_spawned',left is not None and right is not None and left!=right)
check('tool_configuration',all(not call(a.get_editor_property('Grab'),'GetGrabSetupIssues') for a in props))
start=p.get_actor_location();frames=0;stage=0;finished=False
action=p.get_editor_property('DesktopMove')
root=Path(unreal.Paths.project_dir()).resolve()
out=root/'Saved/Tests/Cloud-Native-20261107.json'

def controlled_checks():
    p.set_actor_tick_enabled(False)
    for h in [left,right]:
        call(h,'Release');h.set_actor_tick_enabled(False)
        h.get_editor_property('HandRigidbody').set_enable_gravity(False)
    a=props[0];body=a.get_editor_property('Body');body.set_enable_gravity(False)
    grab=a.get_editor_property('Grab');lp=a.get_editor_property('LeftGrip');rp=a.get_editor_property('RightGrip')
    # Far from the room: isolate grab queries from unrelated scene collision.
    def reset_hand(h,xyz):
        call(h,'Release')
        h.set_actor_location_and_rotation(unreal.Vector(*xyz),unreal.Rotator(),False,True)
        b=h.get_editor_property('HandRigidbody');b.set_physics_linear_velocity(unreal.Vector());b.set_physics_angular_velocity_in_radians(unreal.Vector())
    def near(h):
        body.set_physics_linear_velocity(unreal.Vector());body.set_physics_angular_velocity_in_radians(unreal.Vector())
        a.set_actor_location_and_rotation(h.get_editor_property('GrabSphere').get_world_location(),unreal.Rotator(),False,True)
    for side,h,pose in [('left',left,lp),('right',right,rp)]:
        reset_hand(h,(3000,3000,1000));near(h)
        check(side+'_preset_applied',pose.get_editor_property('UseFingerWeights') and abs(pose.get_editor_property('IndexWeight')-.25)<.001)
        ok=call(h,'TryGrabAtPose',grab,pose)
        check(side+'_authored_grab',ok and call(h,'GetActiveGrabPose')==pose and call(grab,'GetGrabCount')==1)
        check(side+'_held_component',call(h,'GetCurrentGrabComponent')==body and call(grab,'GetPrimaryGrabComponent')==body)
        palm=h.get_editor_property('Palm')
        distance=(palm.get_world_location()-pose.get_world_location()).length()
        delta=palm.get_world_rotation().quaternion().angular_distance(pose.get_world_rotation().quaternion())
        check(side+'_palm_alignment',distance<.02 and delta<.002,distance_cm=distance,rotation_error_radians=delta)
        call(h,'SetGrabTrigger',.8)
        check(side+'_trigger_lights_tool',call(grab,'GetIsTriggerActive') and a.get_editor_property('Lamp').is_visible())
        call(h,'SetGrabTrigger',.65);check(side+'_trigger_hysteresis',call(grab,'GetIsTriggerActive'))
        call(h,'SetGrabTrigger',.55);check(side+'_trigger_release_threshold',not call(grab,'GetIsTriggerActive'))
        call(h,'SetGrabTrigger',1.)
        for _ in range(40):call(h,'ReceiveTick',1/90)
        check(side+'_pressed_finger_weights',abs(h.get_editor_property('IndexWeight')-.9)<.005 and abs(h.get_editor_property('GraspWeight')-.85)<.005)
        call(h,'Release')
        check(side+'_release_state',call(h,'GetActiveGrabPose') is None and call(h,'GetCurrentGrabComponent') is None and call(grab,'GetGrabCount')==0 and not call(grab,'GetIsTriggerActive'))
        check(side+'_release_visual_trigger',call(h,'IsGrabPoseExiting') and abs(call(h,'GetGrabAnimationTrigger')-1)<.001)
        for _ in range(30):call(h,'ReceiveTick',1/90)
        check(side+'_visual_exit_complete',call(h,'GetAnimationGrabPose') is None)
        check(side+'_preview_isolated',call(h,'StartGrabPosePreview',pose) and call(grab,'GetGrabCount')==0)
        call(h,'SetGrabPosePreviewTrigger',.5)
        check(side+'_preview_trigger',abs(call(h,'GetGrabAnimationTrigger')-.5)<.001 and not call(grab,'GetIsTriggerActive'))
        call(h,'StopGrabPosePreview')
        for _ in range(30):call(h,'ReceiveTick',1/90)
        check(side+'_wrong_hand_pose_rejected',not call(h,'TryGrabAtPose',grab,rp if side=='left' else lp))
        near(h);grab.set_editor_property('DisableGrabbing',True,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
        check(side+'_disabled_grab_rejected',not call(h,'TryGrabAtPose',grab,pose))
        grab.set_editor_property('DisableGrabbing',False,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
        a.set_actor_location(unreal.Vector(6000,6000,1000),False,True)
        check(side+'_distant_grab_rejected',not call(h,'TryGrabAtPose',grab,pose))
    reset_hand(left,(3000,3000,1000));near(left)
    check('two_hand_first_grab',call(left,'TryGrabAtPose',grab,lp))
    reset_hand(right,(3000,3000,1000));right.set_actor_location(left.get_actor_location(),False,True)
    # Bring the right query sphere onto the existing body without relocating the held tool.
    right.set_actor_location(right.get_actor_location()+body.get_world_location()-right.get_editor_property('GrabSphere').get_world_location(),False,True)
    grab.set_editor_property('SingleHandOnly',True,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
    check('single_hand_admission',not call(right,'TryGrabAtPose',grab,rp) and call(grab,'GetGrabCount')==1)
    grab.set_editor_property('SingleHandOnly',False,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
    check('two_hand_second_grab',call(right,'TryGrabAtPose',grab,rp) and call(grab,'GetGrabCount')==2)
    check('first_holder_primary',call(grab,'GetPrimaryGrabbingHand')==left)
    call(left,'Release')
    check('primary_handoff',call(grab,'GetPrimaryGrabbingHand')==right and call(right,'GetCurrentGrabComponent')==body and call(grab,'GetGrabCount')==1)
    call(right,'Release');check('two_hand_final_release',call(grab,'GetGrabCount')==0)
    reset_hand(left,(3000,3000,1000));near(left);call(left,'TryGrabAtPose',grab,lp)
    a.destroy_actor();call(left,'Release')
    check('destroyed_grabbable_release_recovers',call(left,'GetActiveGrabPose') is None and call(left,'GetCurrentGrabComponent') is None)
    other=props[1];other.get_editor_property('Body').set_enable_gravity(False)
    other.set_actor_location(left.get_editor_property('GrabSphere').get_world_location(),False,True)
    check('regrab_after_destroyed_release',call(left,'TryGrabAtPose',other.get_editor_property('Grab'),other.get_editor_property('LeftGrip')))
    call(left,'Release')

def tick(dt):
    global frames,stage,finished,handle,stopped
    if finished:return
    frames+=1
    try:
        if stage==0:
            sub.inject_input_vector_for_action(action,unreal.Vector(1,0,0),[],[])
            if frames<12:return
            current=p.get_actor_location()
            check('enhanced_input_movement',current.x>start.x+1,distance_cm=(current-start).length())
            stage=1;frames=0
            sub.inject_input_vector_for_action(action,unreal.Vector(),[],[])
            return
        if stage==1:
            if frames==2:stopped=p.get_actor_location()
            if frames<8:return
            check('enhanced_input_completed_stops', (p.get_actor_location()-stopped).length()<.01)
            controlled_checks()
            report['passed']=all(c['passed'] for c in report['cases'])
            finished=True
    except Exception:
        report['error']=traceback.format_exc();report['passed']=False;finished=True
    if finished:
        out.write_text(json.dumps(report,indent=2),encoding='utf-8')
        unreal.unregister_slate_post_tick_callback(handle)
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()

handle=unreal.register_slate_post_tick_callback(tick)
print('Started native integration acceptance',out)
