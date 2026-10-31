"""Import the modular Blender kit through the connected MCP editor endpoint."""
import json,time,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
SOURCE=ROOT/'ArtSource/VRSharpLab'
DATA=json.loads((SOURCE/'lab_manifest.json').read_text(encoding='utf-8'))
DEST='/VRSharp/Lab'
TOOLS=unreal.AssetToolsHelpers.get_asset_tools()
EDIT=unreal.MaterialEditingLibrary
MATERIALS={}
def scalar(mat,value,x,y):
 n=EDIT.create_material_expression(mat,unreal.MaterialExpressionConstant,x,y);n.set_editor_property('r',value);return n
def vector(mat,value,x,y):
 n=EDIT.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,x,y);n.set_editor_property('constant',unreal.LinearColor(*value,1));return n
with unreal.ScopedEditorTransaction('Import NEXUS laboratory materials'):
 for i in range(3):
  task=unreal.AssetImportTask();task.set_editor_property('filename',str(SOURCE/'Textures'/f'T_LabUI_{i}.png'))
  task.set_editor_property('destination_path',DEST+'/Textures');task.set_editor_property('automated',True);task.set_editor_property('replace_existing',True);task.set_editor_property('save',True)
  TOOLS.import_asset_tasks([task])
 for name,spec in DATA['materials'].items():
  path=DEST+'/Materials/M_Lab_'+name
  mat=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else TOOLS.create_asset('M_Lab_'+name,DEST+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
  # Only this generated asset family is authored here.
  EDIT.delete_all_material_expressions(mat)
  col=vector(mat,spec['color'],-500,0);EDIT.connect_material_property(col,'',unreal.MaterialProperty.MP_BASE_COLOR)
  for prop,value,y in [(unreal.MaterialProperty.MP_METALLIC,spec['metallic'],140),(unreal.MaterialProperty.MP_ROUGHNESS,spec['roughness'],220)]:
   n=scalar(mat,value,-300,y);EDIT.connect_material_property(n,'',prop)
  if name in ('Cyan','Red','White'):
   gain=7 if name!='White' else 5
   emission=vector(mat,[v*gain for v in spec['color']],-500,320);EDIT.connect_material_property(emission,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
  elif name.startswith('Screen'):
   tex=EDIT.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-550,400)
   tex.set_editor_property('texture',unreal.load_asset(DEST+'/Textures/T_LabUI_'+name[-1]))
   EDIT.connect_material_property(tex,'RGB',unreal.MaterialProperty.MP_BASE_COLOR);EDIT.connect_material_property(tex,'RGB',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
  elif name=='Glass':
   mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT);mat.set_editor_property('two_sided',False)
   opacity=scalar(mat,.07,-500,400);EDIT.connect_material_property(opacity,'',unreal.MaterialProperty.MP_OPACITY)
   mat.set_editor_property('translucency_lighting_mode',unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
  EDIT.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat);MATERIALS[name]=mat

_names=list(DATA['assets']);_index=0;_busy=False;_started=time.monotonic();_rows=[]
_status=ROOT/'Saved/Tests/Lab-Import.json'
def progress(error=None):
 _status.write_text(json.dumps({'done':_index,'total':len(_names),'complete':_index==len(_names) and error is None,'elapsed_seconds':time.monotonic()-_started,'error':error,'assets':_rows},indent=2),encoding='utf-8')
def tick(_dt):
 global _index,_busy
 if _busy:return
 _busy=True
 try:
  name=_names[_index];spec=DATA['assets'][name]
  task=unreal.AssetImportTask();task.set_editor_property('filename',str(SOURCE/'Exports'/(name+'.fbx')))
  task.set_editor_property('destination_path',DEST+'/Meshes');task.set_editor_property('automated',True);task.set_editor_property('replace_existing',True);task.set_editor_property('save',True)
  options=unreal.FbxImportUI();options.set_editor_property('automated_import_should_detect_type',False)
  options.set_editor_property('mesh_type_to_import',unreal.FBXImportType.FBXIT_STATIC_MESH);options.set_editor_property('import_materials',False);options.set_editor_property('import_textures',False)
  imp=options.get_editor_property('static_mesh_import_data');imp.set_editor_property('combine_meshes',True)
  imp.set_editor_property('generate_lightmap_u_vs',False);imp.set_editor_property('auto_generate_collision',spec['collision']=='simple')
  imp.set_editor_property('normal_import_method',unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
  task.set_editor_property('options',options);task.set_editor_property('factory',unreal.FbxFactory());TOOLS.import_asset_tasks([task])
  mesh=unreal.load_asset(DEST+'/Meshes/'+name)
  if not mesh:raise RuntimeError('FBX failed: '+name)
  for slot,entry in enumerate(mesh.get_editor_property('static_materials')):
   key=str(entry.material_slot_name)
   if key not in MATERIALS:raise RuntimeError('Unknown material slot '+key+' in '+name)
   mesh.set_material(slot,MATERIALS[key])
  if spec['collision']=='complex':
   setup=mesh.get_editor_property('body_setup')
   setup.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
  unreal.EditorAssetLibrary.set_metadata_tag(mesh,'Lab.Source','VRSharpLab_HardSurface.blend')
  unreal.EditorAssetLibrary.set_metadata_tag(mesh,'Lab.Modularity','Separate reusable part; meters authored, centimeters in UE')
  unreal.EditorAssetLibrary.save_loaded_asset(mesh)
  _rows.append({'mesh':name,'bounds':str(mesh.get_bounding_box()),'slots':len(mesh.get_editor_property('static_materials'))})
  _index+=1;progress()
  if _index==len(_names):unreal.unregister_slate_post_tick_callback(_handle);unreal.log('NEXUS laboratory import complete')
 except Exception:
  progress(traceback.format_exc());unreal.unregister_slate_post_tick_callback(_handle)
 finally:_busy=False
progress();_handle=unreal.register_slate_post_tick_callback(tick)
print('Started incremental import:',len(_names),'modular assets; progress Saved/Tests/Lab-Import.json')
