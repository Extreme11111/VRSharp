"""Organize the .blend as an editable part library plus hierarchical scene assemblies."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
root=Path(__file__).resolve().parents[1]/'ArtSource/VRSharpLab'
data=json.loads((root/'lab_manifest.json').read_text(encoding='utf-8'))
def collection(path):
 parent=bpy.context.scene.collection
 for name in path.split('/'):
  key=parent.name+'/'+name
  child=bpy.data.collections.get(key)
  if child is None:child=bpy.data.collections.new(key);parent.children.link(child)
  parent=child
 return parent
def move(ob,target):
 for old in list(ob.users_collection):old.objects.unlink(ob)
 target.objects.link(ob)
library=collection('01 - Modular Part Library')
for name in data['assets']:
 ob=bpy.data.objects.get(name)
 if ob:move(ob,library)
roots={};objects={}
for index,row in enumerate(data['instances']):
 ob=bpy.data.objects.get(row['mesh']+f'_{index:04d}')
 if ob is None:continue
 target=collection('02 - Scene/'+row['folder']);group=row['assembly_id']
 if group not in roots:
  name='Assembly_'+str(group).zfill(4)+'_'+row['assembly'];empty=bpy.data.objects.get(name)
  if empty is None:empty=bpy.data.objects.new(name,None);target.objects.link(empty)
  original=data['assembly_instances'][group];empty.location=original['location'];empty.rotation_euler.z=math.radians(original['yaw'])
  empty.empty_display_type='PLAIN_AXES';empty.empty_display_size=.15;roots[group]=empty
 ob.parent=None
 ob.matrix_world=Matrix.Translation(Vector(row['location']))@Matrix.Rotation(math.radians(row['yaw']),4,'Z')@Matrix.Diagonal([*row['scale'],1])
 move(ob,target);objects[group,row['role']]=ob
 ob['PartRole']=row['role'];ob['MotionPreparation']=row.get('motion','fixed')
 ob['AxisBlender']=json.dumps(row.get('axis'));ob['Travel']=json.dumps(row.get('travel'))
 ob.hide_render=not row.get('enabled',True);ob.hide_viewport=not row.get('enabled',True)
bpy.context.view_layer.update()
for row in data['instances']:
 ob=objects.get((row['assembly_id'],row['role']))
 if ob is None:continue
 parent=objects.get((row['assembly_id'],row.get('parent')),roots[row['assembly_id']])
 matrix=ob.matrix_world.copy();ob.parent=parent;ob.matrix_world=matrix
bpy.ops.wm.save_as_mainfile(filepath=str(root/'VRSharpLab_HardSurface.blend'))
print('BLEND organized:',len(roots),'assemblies;',len(objects),'separate parts')
