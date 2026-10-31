"""Assemble the authored kit in the user's currently open VRSharpLab map via MCP."""
import json,math,time,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();DATA=json.loads((ROOT/'ArtSource/VRSharpLab/lab_manifest.json').read_text(encoding='utf-8'))
editor=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name()=='/VRSharp/Maps/VRSharpLab.VRSharpLab', 'Refusing to edit a different map'
assert json.loads((ROOT/'Saved/Tests/Lab-Import.json').read_text())['complete'], 'Asset import is not complete'
existing=editor.get_all_level_actors()
assert not any('LabGenerated' in [str(t) for t in a.get_editor_property('tags')] for a in existing), 'Scene already assembled; use targeted edits'
with unreal.ScopedEditorTransaction('Archive old demo staging in VRSharpLab'):
 for actor in existing:
  label=actor.get_actor_label()
  if 'VRSharpPlayer' in actor.get_class().get_name() or actor.get_class()==unreal.PlayerStart.static_class():
   actor.set_actor_location_and_rotation(unreal.Vector(0,950,100),unreal.Rotator(yaw=-90),False,True)
   actor.set_folder_path('VRSharpLab/Player')
  else:
   old=actor.get_actor_location();actor.set_actor_location(unreal.Vector(old.x,old.y,old.z-100000),False,True)
   actor.set_actor_enable_collision(False);actor.set_actor_hidden_in_game(True);actor.set_is_temporarily_hidden_in_editor(True)
   actor.set_folder_path('VRSharpLab/OriginalDemo_Archived')
   for comp in actor.get_components_by_class(unreal.LightComponent):comp.set_visibility(False)

_index=0;_actors=[];_lookup={};_started=time.monotonic();_busy=False
_status=ROOT/'Saved/Tests/Lab-Assembly.json'
def status(error=None,complete=False):
 _status.write_text(json.dumps({'done':_index,'total':len(DATA['instances']),'complete':complete,'error':error,'elapsed_seconds':time.monotonic()-_started},indent=2),encoding='utf-8')
def tagged(actor,label,folder):
 actor.set_actor_label(label);actor.set_folder_path('VRSharpLab/'+folder);actor.set_editor_property('tags',[unreal.Name('LabGenerated')])
 return actor
def light(name,pos,color,power,radius=700,rect=False,shadow=False):
 cls=unreal.RectLight if rect else unreal.PointLight
 actor=tagged(editor.spawn_actor_from_class(cls,unreal.Vector(*pos),unreal.Rotator(pitch=-90)),name,'Lighting')
 comp=actor.get_component_by_class(unreal.LightComponent);comp.set_mobility(unreal.ComponentMobility.MOVABLE)
 comp.set_intensity(power);comp.set_light_color(unreal.LinearColor(*color,1));comp.set_cast_shadows(shadow)
 comp.set_attenuation_radius(radius)
 if rect:comp.set_source_width(360);comp.set_source_height(180)
 return actor
def finish():
 with unreal.ScopedEditorTransaction('Attach modular laboratory assemblies and light the scene'):
  for row,actor in _actors:
   group=row['assembly_id'];parent=None
   if row.get('parent'):parent=_lookup.get((group,row['parent']))
   if parent is None:
    parent=_lookup.get((group,'Frame'))
    if parent is None:parent=next(a for r,a in _actors if r['assembly_id']==group)
   if actor!=parent:
    ok=actor.attach_to_actor(parent,'',unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)
    if not ok:raise RuntimeError('Failed assembly attachment: '+actor.get_actor_label())
  # Local lighting carries the blue/red reference palette; most fixtures do not cast shadows.
  for x in (-1050,0,1050):
   for y in (-750,0,750):light('Lab_Ceiling_'+str(x)+'_'+str(y),(x,y,825),(.62,.78,1),16000,1100,True,x==0 and y==0)
  for y in (-700,0,700):
   for x in (-1460,1460):light('Lab_RedAccent_'+str(x)+'_'+str(y),(x,y,320),(1,.015,.035),1700,550)
  for x,y in [(-200,0),(200,0),(0,-200),(0,200)]:light('Lab_ReactorBounce_'+str(x)+'_'+str(y),(x,y,180),(.035,.38,1),1400,470)
  for x in (-800,800):light('Lab_WorkbenchFill_'+str(x),(x,-600,270),(.3,.60,1),800,550)
  pp=tagged(editor.spawn_actor_from_class(unreal.PostProcessVolume,unreal.Vector()),'Lab_PostProcess','Lighting')
  pp.set_editor_property('unbound',True);settings=pp.get_editor_property('settings')
  for key,value in {'auto_exposure_min_brightness':3.0,'auto_exposure_max_brightness':3.0,'auto_exposure_bias':0.0,
                    'motion_blur_amount':0.0,'bloom_intensity':.45,'ambient_occlusion_intensity':.7}.items():
   settings.set_editor_property('override_'+key,True);settings.set_editor_property(key,value)
  pp.set_editor_property('settings',settings)
  # Explicit preview camera does not replace or alter the VR tracking camera.
  cam=tagged(editor.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(-1080,1050,280)),'Lab_PreviewCamera','Presentation')
  rot=unreal.MathLibrary.find_look_at_rotation(cam.get_actor_location(),unreal.Vector(0,-170,320));cam.set_actor_rotation(rot,False)
  cam.get_component_by_class(unreal.CameraComponent).set_field_of_view(80)
  unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(cam.get_actor_location(),rot)
  editor.clear_actor_selection_set()
  unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
  status(complete=True)
  unreal.log('VRSharpLab modular environment assembled and saved')
def tick(_dt):
 global _index,_busy
 if _busy:return
 _busy=True
 try:
  with unreal.ScopedEditorTransaction('Place modular laboratory parts'):
   for _ in range(30):
    if _index==len(DATA['instances']):break
    row=DATA['instances'][_index];x,y,z=row['location']
    actor=editor.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x*100,-y*100,z*100),unreal.Rotator(yaw=-row['yaw']))
    group=row['assembly_id'];tagged(actor,f"Lab_A{group:04d}_{row['role']}",row['folder']+'/'+str(group).zfill(4))
    comp=actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_mobility(unreal.ComponentMobility.MOVABLE if row.get('motion','fixed')!='fixed' or row.get('parent') else unreal.ComponentMobility.STATIC)
    comp.set_static_mesh(unreal.load_asset('/VRSharp/Lab/Meshes/'+row['mesh']));actor.set_actor_scale3d(unreal.Vector(*row['scale']))
    if DATA['assets'][row['mesh']]['collision']=='none':
     comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);comp.set_cast_shadow(False)
    else:comp.set_collision_profile_name('BlockAll')
    tags=['LabGenerated','LabAssembly='+row['assembly'],'LabRole='+row['role'],'LabMotion='+row.get('motion','fixed')]
    if row.get('axis'):tags.append('LabAxis='+json.dumps([row['axis'][0],-row['axis'][1],row['axis'][2]]))
    if row.get('travel'):tags.append('LabTravel='+json.dumps(row['travel']))
    actor.set_editor_property('tags',[unreal.Name(t) for t in tags]);_actors.append((row,actor));_lookup[group,row['role']]=actor;_index+=1
  status()
  if _index==len(DATA['instances']):
   unreal.unregister_slate_post_tick_callback(_handle);finish()
 except Exception:
  status(traceback.format_exc());unreal.unregister_slate_post_tick_callback(_handle)
 finally:_busy=False
status();_handle=unreal.register_slate_post_tick_callback(tick)
print('Started assembly:',len(DATA['instances']),'independent parts; progress Saved/Tests/Lab-Assembly.json')
