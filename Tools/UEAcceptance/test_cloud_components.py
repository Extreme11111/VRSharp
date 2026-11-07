"""Native multi-collider and two-hand tool policy acceptance in ordinary PIE."""
import unreal,json,traceback
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world();assert w
p=unreal.GameplayStatics.get_player_pawn(w,0);p.set_actor_tick_enabled(False)
hands=[p.get_editor_property(s+'Hand') for s in ['Left','Right']]
report={'cases':[],'hardware_tested':False}
def call(o,n,*args):return o.call_method(n,args=args)
def cfg(o,n,v):o.set_editor_property(n,v,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
def check(n,v):report['cases'].append(dict(case=n,passed=bool(v)))
def place_hand(h,point):
    call(h,'Release');h.set_actor_tick_enabled(False)
    h.set_actor_location_and_rotation(point,unreal.Rotator(),False,True)
    h.get_editor_property('HandRigidbody').set_enable_gravity(False)
def sphere(h):return h.get_editor_property('GrabSphere').get_world_location()
try:
    a=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.load_asset('/VRSharp/Tests/BP_VRSharpFlashlight').generated_class())[0]
    grab=a.get_editor_property('Grab');body=a.get_editor_property('Body')
    body.set_enable_gravity(False)
    for i,h in enumerate(hands):place_hand(h,unreal.Vector(3000,3000+i*100,1000))
    a.set_actor_location_and_rotation(sphere(hands[0]),unreal.Rotator(),False,True)
    second=call(a,'AddComponentByClass',unreal.StaticMeshComponent,False,unreal.Transform(),False)
    second.set_mobility(unreal.ComponentMobility.MOVABLE);second.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    second.set_world_scale3d(unreal.Vector(.06,.06,.06));second.set_world_location(sphere(hands[1]),False,True)
    second.set_collision_profile_name('PhysicsActor');second.set_simulate_physics(True);second.set_enable_gravity(False)
    lp=a.get_editor_property('LeftGrip');rp=a.get_editor_property('RightGrip')
    cfg(rp,'TargetComponent',second)
    check('different_colliders_left_grab',call(hands[0],'TryGrabAtPose',grab,lp))
    check('different_colliders_right_grab',call(hands[1],'TryGrabAtPose',grab,rp))
    check('per_hand_native_component_queries',call(hands[0],'GetCurrentGrabComponent')==body and call(hands[1],'GetCurrentGrabComponent')==second)
    check('first_primary_component',call(grab,'GetPrimaryGrabComponent')==body)
    call(hands[0],'Release')
    check('per_hand_query_after_primary_release',call(hands[1],'GetCurrentGrabComponent')==second and call(grab,'GetPrimaryGrabComponent')==second)
    call(hands[1],'Release')
    # Restore the existing single rigid-body tool and exercise both interlocks.
    cfg(rp,'TargetComponent',body);second.destroy_component(second)
    def both_grab():
        for i,h in enumerate(hands):place_hand(h,unreal.Vector(3000,3000+i*100,1000))
        a.set_actor_location_and_rotation(sphere(hands[0]),unreal.Rotator(),False,True)
        if not call(hands[0],'TryGrabAtPose',grab,lp):return False
        hands[1].set_actor_location(hands[1].get_actor_location()+body.get_world_location()-sphere(hands[1]),False,True)
        return call(hands[1],'TryGrabAtPose',grab,rp)
    cfg(grab,'RequireTwoTriggerHands',True)
    check('two_trigger_rule_grabs',both_grab())
    call(hands[0],'SetGrabTrigger',1.);check('two_trigger_one_is_off',not call(grab,'GetIsTriggerActive'))
    call(hands[1],'SetGrabTrigger',1.);check('two_trigger_both_is_on',call(grab,'GetIsTriggerActive'))
    call(hands[0],'Release');check('two_trigger_release_is_off',not call(grab,'GetIsTriggerActive'))
    call(hands[1],'Release')
    cfg(grab,'RequireTwoTriggerHands',False);cfg(grab,'RequireSupportHandForPrimaryTrigger',True);cfg(lp,'SupportGripOnly',True)
    check('support_role_rule_grabs',both_grab())
    check('support_first_primary_trigger_is_right',call(grab,'GetPrimaryTriggerHand')==hands[1])
    call(hands[0],'SetGrabTrigger',1.);check('support_trigger_cannot_activate',not call(grab,'GetIsTriggerActive'))
    call(hands[1],'SetGrabTrigger',1.);check('primary_trigger_with_support_activates',call(grab,'GetIsTriggerActive'))
    call(hands[0],'Release');check('support_release_deactivates',not call(grab,'GetIsTriggerActive'))
    call(hands[1],'Release')
    report['passed']=all(c['passed'] for c in report['cases'])
except Exception:report['passed']=False;report['error']=traceback.format_exc()
out=Path(unreal.Paths.project_dir()).resolve()/'Saved/Tests/Cloud-Components-20261107.json'
out.write_text(json.dumps(report,indent=2),encoding='utf-8')
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
print(json.dumps(report,indent=2))
