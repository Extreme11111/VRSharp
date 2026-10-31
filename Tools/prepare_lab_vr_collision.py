import unreal,json
from pathlib import Path
root=Path(unreal.Paths.project_dir());data=json.loads((root/'ArtSource/VRSharpLab/lab_manifest.json').read_text());ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);tools=unreal.AssetToolsHelpers.get_asset_tools();actors=ed.get_all_level_actors();lookup={a.get_actor_label():a for a in actors}
pawn=next(a for a in actors if 'VRSharpPlayer' in a.get_class().get_name());player_channel=pawn.get_editor_property('BodyCapsule').get_collision_object_type()
with unreal.ScopedEditorTransaction('Finalize VR laboratory collision and traversable stairs'):
 for name in ['SM_Lab_VRWalkRamp','SM_Lab_GalleryCornerConnector']:
  task=unreal.AssetImportTask();task.set_editor_property('filename',str(root/'ArtSource/VRSharpLab/Collision'/(name+'.fbx')));task.set_editor_property('destination_path','/VRSharp/Lab/Collision');task.set_editor_property('automated',True);task.set_editor_property('replace_existing',True)
  options=unreal.FbxImportUI();options.set_editor_property('automated_import_should_detect_type',False);options.set_editor_property('mesh_type_to_import',unreal.FBXImportType.FBXIT_STATIC_MESH);options.set_editor_property('import_materials',False);options.set_editor_property('import_textures',False)
  imp=options.get_editor_property('static_mesh_import_data');imp.set_editor_property('combine_meshes',True);imp.set_editor_property('generate_lightmap_u_vs',False);imp.set_editor_property('auto_generate_collision',False)
  task.set_editor_property('options',options);task.set_editor_property('factory',unreal.FbxFactory());tools.import_asset_tasks([task]);mesh=unreal.load_asset('/VRSharp/Lab/Collision/'+name)
  for i,slot in enumerate(mesh.get_editor_property('static_materials')):mesh.set_material(i,unreal.load_asset('/VRSharp/Lab/Materials/M_Lab_'+str(slot.material_slot_name)))
  mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);unreal.EditorAssetLibrary.save_loaded_asset(mesh)
 # Static frames use triangle collision so their doorways, leg spaces and cabinet cavities remain open.
 fixed_frames=[]
 for name in data['assets']:
  if name in ['SM_Lab_DoorPortal','SM_Lab_WindowFrame','SM_Lab_Console','SM_Lab_ServerRack','SM_Lab_EquipmentCabinet','SM_Lab_RobotPedestal','SM_Lab_Cart','SM_Lab_Whiteboard','SM_Lab_Chair'] or name.endswith('_Shell'):
   mesh=unreal.load_asset('/VRSharp/Lab/Meshes/'+name);mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);unreal.EditorAssetLibrary.save_loaded_asset(mesh);fixed_frames.append(name)
 for x in (-1190,1190):
  label='Lab_Collision_StairRamp_'+str(x)
  a=lookup.get(label) or ed.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,750,0));a.set_actor_label(label);a.set_folder_path('VRSharpLab/Collision/Player walk ramps');a.set_editor_property('tags',[unreal.Name('LabWalkHelper')]);c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(unreal.load_asset('/VRSharp/Lab/Collision/SM_Lab_VRWalkRamp'))
  c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS);c.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE);c.set_collision_response_to_channel(player_channel,unreal.CollisionResponseType.ECR_BLOCK);c.set_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY,unreal.CollisionResponseType.ECR_BLOCK)
  a.set_actor_hidden_in_game(True);c.set_visibility(False);c.set_cast_shadow(False)
 for x in (-1450,1450):
  label='Lab_GalleryCornerConnector_'+str(x)
  if label in lookup:continue
  a=ed.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,-900,439));a.set_actor_label(label);a.set_folder_path('VRSharpLab/Architecture/Gallery');a.set_editor_property('tags',[unreal.Name('LabGenerated')]);c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(unreal.load_asset('/VRSharp/Lab/Collision/SM_Lab_GalleryCornerConnector'));c.set_collision_profile_name('BlockAll')
 # Old demo actors must not participate in the new room's physics or lighting.
 for a in actors:
  if 'OriginalDemo_Archived' in str(a.get_folder_path()):
   a.set_actor_enable_collision(False);a.set_actor_hidden_in_game(True);a.set_actor_tick_enabled(False)
 ed.clear_actor_selection_set();unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
(root/'Saved/Tests/Lab-VRCollisionSetup.json').write_text(json.dumps({'fixed_frames_preserve_openings':fixed_frames,'player_channel':str(player_channel),'walk_ramps':2,'gallery_gap_connectors':2},indent=2),encoding='utf-8')
print('VR collision saved: accurate frame openings; player-only stair ramps; rear gallery gaps filled')
