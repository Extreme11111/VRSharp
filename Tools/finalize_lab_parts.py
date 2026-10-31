import unreal,json
from pathlib import Path
r=Path(unreal.Paths.project_dir());data=json.loads((r/'ArtSource/VRSharpLab/lab_manifest.json').read_text());library=unreal.EditorAssetLibrary
ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);actors=ed.get_all_level_actors();lookup={a.get_actor_label():a for a in actors}
roles={};checks=[]
with unreal.ScopedEditorTransaction('Record laboratory part pivots and interaction preparation'):
 for row in data['instances']:
  a=lookup[f"Lab_A{row['assembly_id']:04d}_{row['role']}"];axis=row.get('axis');motion=row.get('motion','fixed');tags=[str(t) for t in a.get_editor_property('tags') if not any(str(t).startswith(k) for k in ('LabAxis=','LabAssembly=','LabRole=','LabMotion='))];tags+=['LabAssembly='+row['assembly'],'LabRole='+row['role'],'LabMotion='+motion]
  ue_axis=None
  if axis:
   ue_axis=[-axis[0],axis[1],-axis[2]] if motion in ('hinge','swivel','tilt','twist','roll') else [axis[0],-axis[1],axis[2]]
   tags.append('LabAxis='+json.dumps(ue_axis))
  a.set_editor_property('tags',[unreal.Name(t) for t in tags])
  roles[row['mesh']]={'asset':'/VRSharp/Lab/Meshes/'+row['mesh'],'motion':motion,'axis':ue_axis,'travel':([v*100 for v in row['travel']] if motion in ('slide','press') else row.get('travel')),'travel_units':'cm' if motion in ('slide','press') else 'degrees','parent_role':row.get('parent')}
 # Test a real independent drawer and the attached handle, then restore exactly.
 drawer=next(a for a in actors if a.get_actor_label().endswith('_Cabinet_0_Drawer_0'))
 handle=next(a for a in actors if a.get_attach_parent_actor()==drawer)
 p=drawer.get_actor_location();hp=handle.get_actor_location()
 try:
  drawer.set_actor_location(unreal.Vector(p.x,p.y+20,p.z),False,True)
  delta=handle.get_actor_location()-hp
  assert abs(delta.y-20)<.001 and abs(delta.x)<.001 and abs(delta.z)<.001
  checks.append({'case':'drawer_handle_follows_slide','passed':True})
 finally:drawer.set_actor_location(p,False,True)
 for mesh,spec in roles.items():
  asset=unreal.load_asset(spec['asset']);library.set_metadata_tag(asset,'Lab.InteractionPreparation',json.dumps(spec));library.save_loaded_asset(asset,only_if_is_dirty=True)
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
(r/'ArtSource/VRSharpLab/lab_unreal_parts.json').write_text(json.dumps({'length_units':'cm','angular_units':'degrees','parts':roles},indent=2),encoding='utf-8')
(r/'Saved/Tests/Lab-PartChecks.json').write_text(json.dumps({'checks':checks,'mesh_count':len(roles),'interaction_implemented':False},indent=2),encoding='utf-8')
print('Part metadata saved:',len(roles),'parts; hierarchy checks',checks)
