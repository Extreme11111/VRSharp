"""Find positive-area, same-facing coplanar overlap; edge contacts are allowed."""
import bpy,json,math
from mathutils import Vector,geometry
from pathlib import Path
from collections import defaultdict
root=Path(__file__).resolve().parents[1];data=json.loads((root/'ArtSource/VRSharpLab/lab_manifest.json').read_text())
def area(poly):return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])))*.5
def clip(subject,cutter):
 signed=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(cutter,cutter[1:]+cutter[:1]));sgn=1 if signed>=0 else -1
 for a,b in zip(cutter,cutter[1:]+cutter[:1]):
  old=subject;subject=[]
  if not old:break
  def dist(p):return sgn*((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]))
  for p,q in zip(old,old[1:]+old[:1]):
   dp,dq=dist(p),dist(q)
   if dp>=-1e-10:subject.append(p)
   if (dp>=0)!=(dq>=0):
    t=dp/(dp-dq);subject.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
 return subject
results=[]
for name in data['assets']:
 mesh=bpy.data.objects[name].data;planes=defaultdict(list);overlaps=[]
 for f in mesh.polygons:
  if f.area<1e-9:continue
  n=f.normal;d=n.dot(mesh.vertices[f.vertices[0]].co);key=tuple(round(float(v),5) for v in n)+(round(float(d),5),)
  drop=max(range(3),key=lambda i:abs(key[i]));axes=[i for i in range(3) if i!=drop]
  poly=[tuple(float(mesh.vertices[v].co[i]) for i in axes) for v in f.vertices]
  bounds=(min(p[0] for p in poly),min(p[1] for p in poly),max(p[0] for p in poly),max(p[1] for p in poly))
  for of,op,ob in planes[key]:
   if min(bounds[2],ob[2])-max(bounds[0],ob[0])<1e-7 or min(bounds[3],ob[3])-max(bounds[1],ob[1])<1e-7:continue
   intersection=clip(poly,op)
   overlap=area(intersection) if len(intersection)>2 else 0
   if overlap>1e-7:
    # Boolean cuts and font caps can be concave: validate against their tessellation.
    triangles_a=geometry.tessellate_polygon([[Vector((p[0],p[1],0)) for p in poly]])
    triangles_b=geometry.tessellate_polygon([[Vector((p[0],p[1],0)) for p in op]])
    actual=0.0
    for ta in triangles_a:
     for tb in triangles_b:
      intersection=clip([poly[v] if isinstance(v,int) else (v.x,v.y) for v in ta],[op[v] if isinstance(v,int) else (v.x,v.y) for v in tb])
      if len(intersection)>2:actual+=area(intersection)
    overlap=actual
   if overlap>1e-7:
    overlaps.append({'faces':[of,f.index],'area_m2':overlap,'plane':key,'materials':[mesh.materials[mesh.polygons[of].material_index].name,mesh.materials[f.material_index].name]})
  planes[key].append((f.index,poly,bounds))
 if overlaps:results.append({'mesh':name,'overlaps':overlaps})
(root/'Saved/Tests/Lab-Coplanar.json').write_text(json.dumps({'results':results,'total_pairs':sum(len(r['overlaps']) for r in results)},indent=2),encoding='utf-8')
print('COPLANAR',[(r['mesh'],len(r['overlaps'])) for r in results])
