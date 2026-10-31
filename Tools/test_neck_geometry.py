import unreal,time,json,math
from pathlib import Path
root=Path(unreal.Paths.project_dir());level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);start=time.monotonic()
ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
beam=ed.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(10050,10000,2282),unreal.Rotator(),False)
beam.set_actor_label('NeckTest_TemporaryBeam')
beam.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
beam.set_actor_scale3d(unreal.Vector(.1,2,.2))
beam.static_mesh_component.set_collision_profile_name('BlockAll')
def tick(dt):
 global handle
 try:
  w=unreal.EditorLevelLibrary.get_game_world()
  if not w:
   if time.monotonic()-start>20:raise RuntimeError('No PIE world')
   return
  actors=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpPlayer').generated_class())
  p=actors[0] if actors else None
  if not p:return
  p.set_actor_tick_enabled(False)
  body=p.get_editor_property('BodyCapsule');body.set_enable_gravity(False)
  cam=p.get_editor_property('Camera');neck=p.get_editor_property('Neck');head=p.get_editor_property('HeadCollision')
  rows=[]
  for height,pitch,yaw,sub,extra in [(170,0,0,0,15),(170,-60,0,0,15),(170,60,90,0,15),(100,-40,120,12,15),(170,0,45,12,25)]:
   p.set_actor_location_and_rotation(unreal.Vector(10000,10000,2200),unreal.Rotator(yaw=yaw),False,True)
   body.set_capsule_size(10,88);body.set_physics_linear_velocity(unreal.Vector(),False)
   p.get_editor_property('VROrigin').set_relative_location(unreal.Vector(0,0,-88-sub),False,False)
   p.set_editor_property('CapsuleSubHeight',float(sub));p.set_editor_property('CapsuleAdditionalHeight',float(extra))
   cam.set_relative_location(unreal.Vector(0,0,height),False,False);cam.set_relative_rotation(unreal.Rotator(pitch=pitch),False,False)
   foot=body.get_world_location().z-body.get_scaled_capsule_half_height();eye=cam.get_world_location()
   p.call_method('ReceiveTick',args=(1/90,))
   b=body.get_world_location();r=body.get_scaled_capsule_radius();hh=body.get_scaled_capsule_half_height();h=head.get_world_location();n=neck.get_world_location();eye2=cam.get_world_location()
   dist=math.sqrt((h.x-b.x)**2+(h.y-b.y)**2+(h.z-(b.z+hh-r))**2)
   row={'height':height,'pitch':pitch,'yaw':yaw,'sub':sub,'extra':extra,'foot_error':b.z-hh-foot,'eye_error':(eye2-eye).length(),'tangent_error':dist-r-head.get_scaled_sphere_radius(),'neck_xy_error':math.hypot(n.x-b.x,n.y-b.y),'half_height':hh}
   row['passed']=abs(row['foot_error'])<.001 and row['eye_error']<.001 and abs(row['tangent_error'])<.01 and row['neck_xy_error']<.001
   rows.append(row)
  # A head-height beam leaves the shortened body free, but must stop the camera sphere.
  p.set_editor_property('CapsuleSubHeight',0.);p.set_editor_property('CapsuleAdditionalHeight',15.)
  body.set_capsule_size(10,88)
  p.set_actor_location_and_rotation(unreal.Vector(10000,10000,2200),unreal.Rotator(),False,True)
  p.get_editor_property('VROrigin').set_relative_location(unreal.Vector(0,0,-88),False,False)
  cam.set_relative_location(unreal.Vector(0,0,170),False,False);cam.set_relative_rotation(unreal.Rotator(),False,False)
  p.call_method('ReceiveTick',args=(1/90,))
  cam.set_relative_location(unreal.Vector(80,0,170),False,False)
  p.call_method('ReceiveTick',args=(1/90,))
  hx=head.get_world_location().x
  beams=[a.get_actor_label() for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.StaticMeshActor) if 'NeckTest' in a.get_actor_label()]
  rows.append({'beams':beams,'head_z':head.get_world_location().z,'collision':str(head.get_collision_enabled()),'passed':bool(beams)})
  rows.append({'case':'head_beam_sweep','head_x':hx,'passed':10000<hx<10031})
  report={'passed' :all(x['passed'] for x in rows),'cases':rows,'hardware_tested':False}
  (root/'Saved/Tests/Neck-Geometry-20261023.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
  unreal.log('Neck geometry checks '+str(report))
 except Exception as e:
  (root/'Saved/Tests/Neck-Geometry-20261023.json').write_text(json.dumps({'error':str(e)}),encoding='utf-8')
 finally:
  if unreal.EditorLevelLibrary.get_game_world():
   unreal.unregister_slate_post_tick_callback(handle);level.editor_request_end_play();ed.destroy_actor(beam)
handle=unreal.register_slate_post_tick_callback(tick);level.editor_request_begin_play()
print('Started neck PIE geometry verification')
