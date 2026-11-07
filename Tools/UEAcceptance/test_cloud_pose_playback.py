"""Check actual skeletal animation evaluation, trigger blending and AnimBP restoration."""
import unreal,json,traceback
from pathlib import Path
w=unreal.EditorLevelLibrary.get_game_world();assert w
p=unreal.GameplayStatics.get_player_pawn(w,0);p.set_actor_tick_enabled(False)
hands=[p.get_editor_property(s+'Hand') for s in ['Left','Right']]
prop=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.load_asset('/VRSharp/Tests/BP_VRSharpFlashlight').generated_class())[0]
poses=[prop.get_editor_property(s+'Grip') for s in ['Left','Right']]
meshes=[h.get_editor_property('HandMesh') for h in hands]
for m in meshes:
    m.set_editor_property('visibility_based_anim_tick_option',unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
    m.set_component_tick_enabled(True)
original=[m.get_anim_instance().get_class() for m in meshes]
report={'cases':[],'hardware_tested':False}
def call(o,n,*args):return o.call_method(n,args=args)
def check(n,v,**kw):report['cases'].append(dict(case=n,passed=bool(v),**kw))
def finger(m):return m.get_socket_transform('index_03_r',unreal.RelativeTransformSpace.RTS_PARENT_BONE_SPACE).rotation
for h,pose in zip(hands,poses):check('preview_started_'+h.get_name(),call(h,'StartGrabPosePreview',pose))
frames=0;stage=0;done=False
out=Path(unreal.Paths.project_dir()).resolve()/'Saved/Tests/Cloud-Pose-Playback-20261107.json'
def tick(dt):
    global frames,stage,done,handle,base,pressed
    if done:return
    frames+=1
    if frames<5:return
    try:
        if stage==0:
            base=[finger(m) for m in meshes]
            for i,(h,m) in enumerate(zip(hands,meshes)):
                node=m.get_anim_instance()
                check('native_blendspace_playing_'+str(i),isinstance(node,unreal.AnimSingleNodeInstance) and node.get_animation_asset()==poses[i].get_editor_property('PoseBlendSpace'))
                check('native_visual_enter_complete_'+str(i),abs(call(h,'GetGrabPoseBlendWeight')-1)<.001)
                call(h,'SetGrabPosePreviewTrigger',1.)
            stage=1;frames=0;return
        if stage==1:
            pressed=[finger(m) for m in meshes]
            for i,h in enumerate(hands):
                angle=base[i].angular_distance(pressed[i])
                check('actual_index_bone_moves_'+str(i),angle>.1,rotation_radians=angle)
                call(h,'SetGrabPosePreviewTrigger',.5)
            stage=2;frames=0;return
        if stage==2:
            for i,(h,m) in enumerate(zip(hands,meshes)):
                mid=finger(m)
                a=mid.angular_distance(base[i]);b=mid.angular_distance(pressed[i]);total=base[i].angular_distance(pressed[i])
                check('actual_half_trigger_interpolates_'+str(i),a>.02 and b>.02 and abs(a+b-total)<.1,grip_distance=a,pressed_distance=b)
                call(h,'StopGrabPosePreview')
            stage=3;frames=0;return
        if stage==3:
            for i,(h,m) in enumerate(zip(hands,meshes)):
                check('original_animbp_restored_'+str(i),m.get_anim_instance().get_class()==original[i] and call(h,'GetAnimationGrabPose') is None)
            report['passed']=all(c['passed'] for c in report['cases']);done=True
    except Exception:report['passed']=False;report['error']=traceback.format_exc();done=True
    if done:
        out.write_text(json.dumps(report,indent=2),encoding='utf-8')
        unreal.unregister_slate_post_tick_callback(handle)
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
handle=unreal.register_slate_post_tick_callback(tick)
print('Started real skeletal pose evaluation test',out)
