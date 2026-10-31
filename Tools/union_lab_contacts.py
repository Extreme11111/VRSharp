"""Boolean only intersecting shells INSIDE a rigid part; retain all separate VR parts."""
import bpy,bmesh,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];data=json.loads((root/'ArtSource/VRSharpLab/lab_manifest.json').read_text())
report=json.loads((root/'Saved/Tests/Lab-Coplanar.json').read_text())
fixes=[]
def component_object(source,faces,name):
 mesh=source.data;verts=sorted({v for f in faces for v in mesh.polygons[f].vertices});remap={v:i for i,v in enumerate(verts)}
 new=bpy.data.meshes.new(name);new.from_pydata([tuple(mesh.vertices[v].co) for v in verts],[],[tuple(remap[v] for v in mesh.polygons[f].vertices) for f in faces]);new.update()
 for mat in mesh.materials:new.materials.append(mat)
 for p,f in zip(new.polygons,faces):p.material_index=mesh.polygons[f].material_index
 for old_uv in mesh.uv_layers:
  uv=new.uv_layers.new(name=old_uv.name)
  for p,f in zip(new.polygons,faces):
   for li,old_li in zip(p.loop_indices,mesh.polygons[f].loop_indices):uv.data[li].uv=old_uv.data[old_li].uv
 ob=bpy.data.objects.new(name,new);bpy.context.scene.collection.objects.link(ob);return ob
for row in report['results']:
 name=row['mesh']
 if '--window-only' in sys.argv and name!='SM_Lab_WindowFrame':continue
 ob=bpy.data.objects[name];mesh=ob.data
 linked=[[] for v in mesh.vertices]
 for face in mesh.polygons:
  for v in face.vertices:linked[v].append(face.index)
 remaining=set(range(len(mesh.polygons)));components=[];mapping={}
 while remaining:
  stack=[remaining.pop()];fs=[];idx=len(components)
  while stack:
   f=stack.pop();fs.append(f);mapping[f]=idx
   for v in mesh.polygons[f].vertices:
    for other in linked[v]:
     if other in remaining:remaining.remove(other);stack.append(other)
  components.append(fs)
 graph={}
 for overlap in row['overlaps']:
  a,b=[mapping[f] for f in overlap['faces']]
  if a==b:continue
  graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
 groups=[];unvisited=set(graph)
 while unvisited:
  stack=[unvisited.pop()];group=[]
  while stack:
   i=stack.pop();group.append(i)
   for j in graph[i]:
    if j in unvisited:unvisited.remove(j);stack.append(j)
  groups.append(group)
 used=set(graph);leftover=[f for i,fs in enumerate(components) if i not in used for f in fs]
 if not groups:continue
 results=[]
 for group in groups:
  objects=[component_object(ob,components[i],'UnionShell') for i in group]
  base=objects[0];collection=bpy.data.collections.new('Boolean operands');bpy.context.scene.collection.children.link(collection)
  for piece in objects[1:]:
   for c in list(piece.users_collection):c.objects.unlink(piece)
   collection.objects.link(piece)
  bpy.context.view_layer.objects.active=base;base.hide_set(False);base.select_set(True)
  mod=base.modifiers.new('Exact rigid-part union','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.operand_type='COLLECTION';mod.collection=collection;mod.use_self=True
  bpy.ops.object.modifier_apply(modifier=mod.name)
  if len(base.data.polygons)==0:raise RuntimeError('Union returned empty mesh: '+name)
  for piece in objects[1:]:bpy.data.objects.remove(piece,do_unlink=True)
  bpy.data.collections.remove(collection);results.append(base)
 if leftover:results.append(component_object(ob,leftover,'Untouched detail'))
 bpy.ops.object.select_all(action='DESELECT')
 for piece in results:piece.select_set(True)
 bpy.context.view_layer.objects.active=results[0];bpy.ops.object.join();result=results[0]
 old=ob.data;new=result.data.copy();new.name=name+'_Clean'
 bm=bmesh.new();bm.from_mesh(new);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(new);bm.free();new.use_auto_smooth=True
 for other in bpy.data.objects:
  if other.type=='MESH' and other.data==old:other.data=new
 bpy.data.objects.remove(result,do_unlink=True)
 bpy.ops.object.select_all(action='DESELECT');ob.hide_set(False);ob.hide_viewport=False;ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.fbx(filepath=str(root/'ArtSource/VRSharpLab/Exports'/(name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,global_scale=1,apply_scale_options='FBX_SCALE_NONE',axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False)
 ob.hide_viewport=True;ob.select_set(False)
 fixes.append({'mesh':name,'union_groups':len(groups),'intersecting_shells':len(used),'faces_after':len(new.polygons)})
 print('CONTACTS_FIXED',fixes[-1],flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'ArtSource/VRSharpLab/VRSharpLab_HardSurface.blend'))
(root/'Saved/Tests/Lab-ContactRepairs.json').write_text(json.dumps(fixes,indent=2),encoding='utf-8')
