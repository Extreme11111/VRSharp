import unreal,json,time
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve();ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert unreal.EditorLevelLibrary.get_game_world() is None
prefix='FingerFeedbackTest_';created=[]
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
   reset();place('B',(8,0,0));assert h.call_method('TryGrab')
   # Keep the real C# grab state but detach the transient test hand so the test
   # can position a surface relative to its fingertips without moving the hand.
   h.detach_from_actor(unreal.DetachmentRule.KEEP_WORLD,unreal.DetachmentRule.KEEP_WORLD,unreal.DetachmentRule.KEEP_WORLD)
   body.set_simulate_physics(False)
   mesh=h.get_editor_property('HandMesh');socket=h.get_editor_property('ThumbName');r=h.get_editor_property('FingerRadius')
   assert mesh.does_socket_exist(socket)
   obj=targets['B'];obj.set_actor_scale3d(unreal.Vector(.02,.02,.02))
   def put(distance):
    pos=mesh.get_socket_location(socket)
    obj.set_actor_location_and_rotation(pos+unreal.Vector(1+distance,0,0),unreal.Rotator(),False,True)
    return obj.static_mesh_component.get_closest_point_on_collision(pos)[0]
   put(10*r)
   for _ in range(120):h.call_method('ReceiveTick',args=(1/90,))
   closed=h.get_editor_property('ThumbWeight');depth=put(.4*r)
   history=[]
   for _ in range(12):
    h.call_method('ReceiveTick',args=(1/90,));history.append(h.get_editor_property('ThumbWeight'))
   opened=history[-1]
   report['cases'].append({'side':side,'case':'deep_contact_opens','radius':r,'measured_distance':depth,'before':closed,'after':opened,'passed':depth<.8*r and opened<closed-.01 and all(history[i]<=history[i-1]+.00001 for i in range(1,len(history)))})
   actual=put(.9*r);before=h.get_editor_property('ThumbWeight')
   for _ in range(12):h.call_method('ReceiveTick',args=(1/90,))
   held=h.get_editor_property('ThumbWeight')
   report['cases'].append({'side':side,'case':'shallow_contact_holds','distance':actual,'before':before,'after':held,'passed':abs(held-before)<.0001})
   put(10*r)
   for _ in range(30):h.call_method('ReceiveTick',args=(1/90,))
   reclosed=h.get_editor_property('ThumbWeight')
   report['cases'].append({'side':side,'case':'separation_recloses','before':held,'after':reclosed,'passed':reclosed>held+.01})
   h.call_method('Release')
  report['passed']=all(c['passed'] for c in report['cases']);report['hardware_tested']=False
 except Exception as e:report['error']=str(e);report['passed']=False
 finally:
  if unreal.EditorLevelLibrary.get_game_world():
   finished=True;(root/'Saved/Tests/FingerFeedback-20261023.json').write_text(json.dumps(report,indent=2),encoding='utf-8');level.editor_request_end_play()
handle=unreal.register_slate_post_tick_callback(tick);level.editor_request_begin_play();print('Started left/right production selection and actual grip tests')
