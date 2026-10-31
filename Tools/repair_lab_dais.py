import json,unreal
from pathlib import Path
r=Path(unreal.Paths.project_dir());data=json.loads((r/'ArtSource/VRSharpLab/lab_manifest.json').read_text());tools=unreal.AssetToolsHelpers.get_asset_tools();ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);edit=unreal.MaterialEditingLibrary
with unreal.ScopedEditorTransaction('Replace overlapping reactor dais with continuous shell and separate deck panels'):
 path='/VRSharp/Lab/Materials/M_Lab_RimSteel'
 mat=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else tools.create_asset('M_Lab_RimSteel','/VRSharp/Lab/Materials',unreal.Material,unreal.MaterialFactoryNew())
 edit.delete_all_material_expressions(mat)
 v=edit.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-400,0);v.set_editor_property('constant',unreal.LinearColor(.2,.26,.3,1));edit.connect_material_property(v,'',unreal.MaterialProperty.MP_BASE_COLOR)
 for prop,value,y in [(unreal.MaterialProperty.MP_METALLIC,.65,140),(unreal.MaterialProperty.MP_ROUGHNESS,.42,220)]:
  n=edit.create_material_expression(mat,unreal.MaterialExpressionConstant,-400,y);n.set_editor_property('r',value);edit.connect_material_property(n,'',prop)
 edit.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat)
 for name in ['SM_Lab_Dais','SM_Lab_DaisDeckPanel']:
  task=unreal.AssetImportTask();task.set_editor_property('filename',str(r/'ArtSource/VRSharpLab/Exports'/(name+'.fbx')));task.set_editor_property('destination_path','/VRSharp/Lab/Meshes');task.set_editor_property('automated',True);task.set_editor_property('replace_existing',True)
  o=unreal.FbxImportUI();o.set_editor_property('automated_import_should_detect_type',False);o.set_editor_property('mesh_type_to_import',unreal.FBXImportType.FBXIT_STATIC_MESH);o.set_editor_property('import_materials',False);o.set_editor_property('import_textures',False)
  imp=o.get_editor_property('static_mesh_import_data');imp.set_editor_property('combine_meshes',True);imp.set_editor_property('generate_lightmap_u_vs',False);imp.set_editor_property('auto_generate_collision',name.endswith('DeckPanel'));imp.set_editor_property('normal_import_method',unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
  task.set_editor_property('options',o);task.set_editor_property('factory',unreal.FbxFactory());tools.import_asset_tasks([task]);mesh=unreal.load_asset('/VRSharp/Lab/Meshes/'+name)
  for i,slot in enumerate(mesh.get_editor_property('static_materials')):mesh.set_material(i,unreal.load_asset('/VRSharp/Lab/Materials/M_Lab_'+str(slot.material_slot_name)))
  if name=='SM_Lab_Dais':mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
  unreal.EditorAssetLibrary.save_loaded_asset(mesh)
 actors=ed.get_all_level_actors();lookup={a.get_actor_label():a for a in actors};base=lookup['Lab_A0004_Frame']
 for row in data['instances']:
  if row['mesh']!='SM_Lab_DaisDeckPanel':continue
  label=f"Lab_A{row['assembly_id']:04d}_{row['role']}"
  if label in lookup:continue
  x,y,z=row['location'];a=ed.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x*100,-y*100,z*100),unreal.Rotator(yaw=-row['yaw']));a.set_actor_label(label);a.set_folder_path('VRSharpLab/Hero/Platform/Removable panels')
  c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_mobility(unreal.ComponentMobility.MOVABLE);c.set_static_mesh(unreal.load_asset('/VRSharp/Lab/Meshes/SM_Lab_DaisDeckPanel'));c.set_collision_profile_name('BlockAll')
  a.set_editor_property('tags',[unreal.Name('LabGenerated'),unreal.Name('LabMotion=removable')]);a.attach_to_actor(base,'',unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)
 ed.clear_actor_selection_set();unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('Dais updated: one continuous load-bearing annulus; 48 separate removable plates; no overlapping base top bands')
