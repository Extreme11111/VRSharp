import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];data=json.loads((root/'ArtSource/VRSharpLab/lab_manifest.json').read_text())
rows=[]
for name in data['assets']:
 mesh=bpy.data.objects[name].data;known=set();duplicates=0
 for face in mesh.polygons:
  key=tuple(sorted(tuple(round(c,7) for c in mesh.vertices[v].co) for v in face.vertices))
  if key in known:duplicates+=1
  known.add(key)
 # Each primitive has its own vertex set, so signed volume also catches inward shells.
 linked=[[] for v in mesh.vertices]
 for face in mesh.polygons:
  for v in face.vertices:linked[v].append(face.index)
 remaining=set(range(len(mesh.polygons)));negative=0;components=0
 while remaining:
  stack=[remaining.pop()];faces=[]
  while stack:
   i=stack.pop();faces.append(mesh.polygons[i])
   for v in mesh.polygons[i].vertices:
    for j in linked[v]:
     if j in remaining:remaining.remove(j);stack.append(j)
  volume=0.0
  origin=mesh.vertices[faces[0].vertices[0]].co
  for face in faces:
   vs=[mesh.vertices[v].co-origin for v in face.vertices]
   for j in range(1,len(vs)-1):volume+=vs[0].dot(vs[j].cross(vs[j+1]))/6
  negative+=volume < -1e-9;components+=1
 rows.append({'mesh':name,'components':components,'inward_components':negative,'identical_faces':duplicates})
report={'assets':rows,'passed':all(not r['inward_components'] and not r['identical_faces'] for r in rows)}
(root/'Saved/Tests/Lab-Geometry.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('GEOMETRY CHECK',report['passed'],[r for r in rows if r['inward_components'] or r['identical_faces']])
