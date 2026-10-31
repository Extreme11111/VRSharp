import unreal,json,time
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve();ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLevelLibrary.get_game_world() is None
prefix='GrabSelectionTest_';created=[]
for name in ['A','B','C','Blocker']:
 a=ed.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(10000,10000,5000),unreal.Rotator(),False);a.set_actor_label(prefix+name);created.append(a)
 c=a.static_mesh_component;c.set_mobility(unreal.ComponentMobility.MOVABLE);c.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));c.set_collision_profile_name('PhysicsActor')
 if name!='Blocker':a.call_method('AddComponentByClass',args=(unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpGrabbable').generated_class(),False,unreal.Transform(),False))
start=time.monotonic();finished=False;report={'cases':[]}
def cleanup():
 for a in ed.get_all_level_actors():
  if a.get_actor_label().startswith(prefix):ed.destroy_actor(a)
def tick(dt):
 global finished,handle
 if finished:
  if not unreal.EditorLevelLibrary.get_game_world():cleanup();unreal.unregister_slate_post_tick_callback(handle)
  return
 try:
  w=unreal.EditorLevelLibrary.get_game_world()
  if not w:
   if time.monotonic()-start>20:raise RuntimeError('PIE did not start')
   return
  pawns=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpPlayer').generated_class())
  if not pawns:return
  for p in pawns:p.set_actor_tick_enabled(False);p.get_editor_property('BodyCapsule').set_simulate_physics(False)
  targets={a.get_actor_label().replace(prefix,''):a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.StaticMeshActor) if a.get_actor_label().startswith(prefix)}
  assert len(targets)==4
  hands=[]
  for side in ['Left','Right']:
   cls=unreal.load_asset('/VRSharp/Blueprints/BP_VRSharpHand'+side).generated_class()
   h=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,cls) if a.get_class()==cls);h.set_actor_tick_enabled(False);hands.append((side,h))
  o=unreal.Vector(10000,10000,5000)
  for side,h in hands:
   body=h.get_editor_property('HandRigidbody');body.set_simulate_physics(False)
   sphere=h.get_editor_property('GrabSphere');sphere.set_relative_location(unreal.Vector(),False,False);sphere.set_relative_rotation(unreal.Rotator(),False,False);sphere.set_sphere_radius(30)
   def reset():
    h.call_method('Release')
    body.set_simulate_physics(False)
    h.set_actor_location_and_rotation(o,unreal.Rotator(),False,True)
    for a in targets.values():
     a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
     a.static_mesh_component.set_relative_location(unreal.Vector(),False,False)
     a.set_actor_scale3d(unreal.Vector(.04,.04,.04));a.set_actor_location_and_rotation(o+unreal.Vector(500,0,0),unreal.Rotator(),False,True)
   def place(name,pos,size=4,pivot=None):
    a=targets[name];a.set_actor_scale3d(unreal.Vector(size/100,size/100,size/100));a.set_actor_location_and_rotation(o+unreal.Vector(*(pivot or pos)),unreal.Rotator(),False,True)
    if pivot:a.static_mesh_component.set_world_location(o+unreal.Vector(*pos),False,True)
    a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
   def check(name,expected):
    result=h.call_method('RefreshGrabTarget');actual=result.get_owner().get_actor_label().replace(prefix,'') if result else None
    report['cases'].append({'side':side,'case':name,'expected':expected,'actual':actual,'passed':actual==expected,'sphere':str(sphere.get_world_location()),'radius':sphere.get_scaled_sphere_radius(),'up':str(sphere.get_up_vector()),'scale':str(h.get_actor_scale3d()),'A':str(targets['A'].get_actor_location()),'Aclosest':str(targets['A'].static_mesh_component.get_closest_point_on_collision(sphere.get_world_location()))})
   reset();place('A',(0,0,-22));place('B',(8,0,0));check('forward_over_closer_side','A')
   reset();place('A',(20,0,0));place('B',(8,0,0));check('nearest_surface_without_ray','B')
   reset();place('Blocker',(0,0,-8));place('B',(8,0,0));check('non_grabbable_ray_still_falls_back','B')
   reset();place('A',(100,0,0),size=196);place('B',(16,0,0));check('distant_actor_pivot_near_surface','A')
   reset();place('A',(0,0,-80));check('reject_far_forward_target',None)
   reset();place('A',(0,0,20));place('B',(9,0,0));check('rear_target_does_not_win_forward_ray','B')
   reset();place('A',(0,0,0),size=12);place('B',(9,0,0));check('inside_collision_distance_zero','A')
   reset();place('A',(8,0,0));check('highlight_before_motion','A')
   place('A',(200,0,0));place('B',(9,0,0));grabbed=h.call_method('TryGrab');result=h.call_method('RefreshGrabTarget');actual=result.get_owner().get_actor_label().replace(prefix,'') if result else None
   report['cases'].append({'side':side,'case':'grip_rechecks_after_target_moved','actual':actual,'passed':bool(grabbed) and actual=='B'})
   h.call_method('Release')
  report['passed']=all(c['passed'] for c in report['cases']);report['hardware_tested']=False
 except Exception as e:report['error']=str(e);report['passed']=False
 finally:
  if unreal.EditorLevelLibrary.get_game_world():
   finished=True;(root/'Saved/Tests/GrabSelection-20261023.json').write_text(json.dumps(report,indent=2),encoding='utf-8');level.editor_request_end_play()
handle=unreal.register_slate_post_tick_callback(tick);level.editor_request_begin_play();print('Started left/right production selection and actual grip tests')
