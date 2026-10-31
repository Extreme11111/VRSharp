"""Editable, metrically scaled hard-surface kit; Blender 4 background authoring."""
import bpy, bmesh, math, json, random, sys
from pathlib import Path
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parents[1]/'ArtSource/VRSharpLab'
OUT=ROOT/'Exports'; OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'
random.seed(17)
specs={
 'Ivory':((.32,.38,.42),.15,.42), 'Floor':((.13,.17,.21),.78,.24), 'Dark':((.025,.037,.049),.7,.32),
 'Steel':((.20,.26,.30),.85,.23), 'Rubber':((.012,.018,.022),.05,.72),
 'Brass':((.57,.30,.075),.72,.29), 'Cyan':((.03,.45,.8),.25,.22),
 'Red':((.65,.015,.035),.25,.3), 'White':((.62,.83,1),.1,.25),
 'Glass':((.08,.22,.29),.05,.12),
 'Screen0':((.015,.08,.14),.1,.35), 'Screen1':((.015,.08,.14),.1,.35),
 'Screen2':((.015,.08,.14),.1,.35), 'RimSteel':((.20,.26,.30),.65,.42)}
mats=[]
for name,(col,metal,rough) in specs.items():
 m=bpy.data.materials.new(name);m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if name in ('Cyan','Red','White'):
  p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=5 if name!='White' else 3
 if name=='Glass':
  p.inputs['Transmission Weight'].default_value=.25;p.inputs['Alpha'].default_value=.10;m.diffuse_color=(*col,.10);m.blend_method='BLEND';m.use_screen_refraction=True;m.show_transparent_back=False
 if name.startswith('Screen'):
  tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'Textures'/f'T_LabUI_{name[-1]}.png'))
  m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);m.node_tree.links.new(tex.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=2
 mats.append(m)
MI={m.name:i for i,m in enumerate(mats)}
assets={}; instances=[];assemblies={}

class Mesh:
 def __init__(self,name,bevel=.004):
  self.name=name;self.v=[];self.f=[];self.ids=[];self.smooth=[];self.bevel=bevel
  self.current_part='Frame';self.face_parts=[];self.parts={'Frame':{'pivot':[0,0,0],'motion':'fixed','parent':None}}
 def part(self,name,pivot=(0,0,0),motion='fixed',parent=None,axis=None,travel=None):
  self.current_part=name;self.parts[name]={'pivot':list(pivot),'motion':motion,'parent':parent,'axis':axis,'travel':travel}
 def poly(self,verts,faces,mat='Ivory',smooth=False):
  n=len(self.v);self.v.extend(verts);self.f.extend([tuple(n+i for i in f) for f in faces]);self.ids.extend([MI[mat]]*len(faces));self.smooth.extend([smooth]*len(faces));self.face_parts.extend([self.current_part]*len(faces))
 def box(self,c,s,mat='Ivory',rot=0):
  x,y,z=c;a,b,d=[v/2 for v in s];co,si=math.cos(rot),math.sin(rot)
  vs=[(x+u*co-v*si,y+u*si+v*co,z+w) for u,v,w in [(-a,-b,-d),(-a,-b,d),(-a,b,-d),(-a,b,d),(a,-b,-d),(a,-b,d),(a,b,-d),(a,b,d)]]
  self.poly(vs,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],mat)
 def cyl(self,a,b,r,mat='Steel',n=16,r2=None):
  a,b=Vector(a),Vector(b);w=(b-a).normalized();u=w.cross(Vector((0,0,1)))
  if u.length<.01:u=w.cross(Vector((0,1,0)))
  u.normalize();v=w.cross(u);vs=[]
  for c,rr in [(a,r),(b,r if r2 is None else r2)]:
   vs += [tuple(c+rr*(math.cos(i*math.tau/n)*u+math.sin(i*math.tau/n)*v)) for i in range(n)]
  fs=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  self.poly(vs,fs,mat)
 def ring(self,r,z,width,height,mat='Steel',n=96,start=0,end=math.tau):
  # A real annulus, never a capped cylinder masquerading as an empty vessel.
  vs=[];closed=abs(end-start-math.tau)<1e-7;count=n if closed else n+1
  for i in range(count):
   a=start+(end-start)*i/n
   for rr,zz in [(r-width/2,z-height/2),(r+width/2,z-height/2),(r+width/2,z+height/2),(r-width/2,z+height/2)]:vs.append((rr*math.cos(a),rr*math.sin(a),zz))
  fs=[]
  for i in range(n):
   ni=(i+1)%count
   for j in range(4):fs.append((i*4+j,i*4+(j+1)%4,ni*4+(j+1)%4,ni*4+j))
  if not closed:fs += [(3,2,1,0),(n*4,n*4+1,n*4+2,n*4+3)]
  self.poly(vs,fs,mat)
 def pipe(self,pts,r=.025,mat='Rubber',n=10):
  for a,b in zip(pts,pts[1:]):self.cyl(a,b,r,mat,n)
 def lathe(self,profile,materials,n=128):
  # One watertight shell; adjacent material bands share edges rather than overlap.
  count=len(profile);vs=[];fs=[];ids=[]
  for i in range(n):
   a=i*math.tau/n
   vs.extend((r*math.cos(a),r*math.sin(a),z) for r,z in profile)
  for i in range(n):
   for j in range(count):
    ni=(i+1)%n;nj=(j+1)%count
    fs.append((i*count+j,ni*count+j,ni*count+nj,i*count+nj));ids.append(MI[materials[j]])
  self.poly(vs,fs,materials[0]);self.ids[-len(ids):]=ids
 def bolt(self,p,axis=(0,0,1),r=.012):
  v=Vector(axis);a=Vector(p);self.cyl(a-v*.004,a+v*.004,r*1.35,'Dark',12);self.cyl(a,a+v*.012,r,'Steel',6)
  # Recess is raised black geometry smaller than the metal head, visible at arm's length.
  self.cyl(a+v*.012,a+v*.0125,r*.48,'Rubber',6)
 def text(self,text,p,size=.06,rot=(math.pi/2,0,0),mat='Dark'):
  curve=bpy.data.curves.new('engraving','FONT');curve.body=text;curve.size=size;curve.extrude=.0004;curve.align_x='CENTER'
  ob=bpy.data.objects.new('engraving',curve);bpy.context.collection.objects.link(ob);ob.location=p;ob.rotation_euler=rot
  deps=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(deps);me=ev.to_mesh()
  vs=[tuple(ob.matrix_world@v.co) for v in me.vertices];fs=[tuple(poly.vertices) for poly in me.polygons];self.poly(vs,fs,mat)
  ev.to_mesh_clear();bpy.data.objects.remove(ob,do_unlink=True)
 def screen(self,c,w,h,variant=0):
  previous=self.current_part;screen_name='Display_'+str(sum(1 for k in self.parts if k.startswith('Display_'))).zfill(2)
  self.part(screen_name,c,'tilt',parent=previous if previous!='Frame' else None,axis=[1,0,0],travel=[-25,25])
  x,y,z=c;self.box((x,y,z),(w+.065,.055,h+.065),'Dark');self.box((x,y-.032,z),(w,.006,h),'Screen'+str(variant))
  self.box((x+w*.41,y-.04,z-h*.54),(.025,.009,.006),'Cyan')
  self.current_part=previous
 def finish(self,collision='simple'):
  used=list(dict.fromkeys(self.face_parts))
  if len(used)>1:
   entries=[]
   for part in used:
    name=self.name if part=='Frame' else self.name+'__'+part
    sub=Mesh(name,self.bevel);indices=[i for i,p in enumerate(self.face_parts) if p==part]
    old_vertices=sorted({v for i in indices for v in self.f[i]});remap={v:i for i,v in enumerate(old_vertices)}
    pivot=Vector(self.parts[part]['pivot']);sub.v=[tuple(Vector(self.v[v])-pivot) for v in old_vertices]
    sub.f=[tuple(remap[v] for v in self.f[i]) for i in indices];sub.ids=[self.ids[i] for i in indices];sub.smooth=[self.smooth[i] for i in indices]
    sub.finish(collision);entries.append({'mesh':name,'role':part,**self.parts[part]})
   assemblies[self.name]=entries
   return assets[entries[0]['mesh']]['object']
  me=bpy.data.meshes.new(self.name);me.from_pydata(self.v,[],self.f);me.update()
  ob=bpy.data.objects.new(self.name,me);bpy.context.collection.objects.link(ob)
  for m in mats:me.materials.append(m)
  for p,mi,sm in zip(me.polygons,self.ids,self.smooth):p.material_index=mi;p.use_smooth=sm
  # All primitives are closed shells: recalculate outward winding before UVs and weighted normals.
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update();me.use_auto_smooth=True
  uv=me.uv_layers.new(name='UVMap')
  for p in me.polygons:
   if specs and mats[p.material_index].name.startswith('Screen'):
    # Map vertical display front in local X/Z coordinates; other thin faces are harmless.
    xs=[me.vertices[me.loops[i].vertex_index].co.x for i in p.loop_indices];zs=[me.vertices[me.loops[i].vertex_index].co.z for i in p.loop_indices]
    for li in p.loop_indices:
     co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=((co.x-min(xs))/max(max(xs)-min(xs),.0001),(co.z-min(zs))/max(max(zs)-min(zs),.0001))
   else:
    for j,li in enumerate(p.loop_indices):uv.data[li].uv=((j==1 or j==2),j>=2)
  bpy.context.view_layer.objects.active=ob;ob.select_set(True)
  if self.bevel:
   mod=ob.modifiers.new('Machined edge radii','BEVEL');mod.width=self.bevel;mod.segments=2;mod.limit_method='ANGLE'
   mod=ob.modifiers.new('Face weighted normals','WEIGHTED_NORMAL');mod.keep_sharp=True
  assets[self.name]={'object':ob,'collision':collision};ob.select_set(False)
  return ob

def place(name,x=0,y=0,z=0,yaw=0,scale=(1,1,1),folder='Architecture'):
 instances.append(dict(mesh=name,location=[x,y,z],yaw=yaw,scale=list(scale),folder=folder))

# The hero reactor: separate opaque structure, glass and lighting for controllable UE materials.
m=Mesh('SM_Lab_ReactorStructure',.008)
for z in (.28,.48,.69,6.35,6.58,6.85):
 m.part('Collar_'+str(z).replace('.','_'),(0,0,z),'removable');m.ring(2.35,z,.42,.16,'Ivory')
for z in (.38,.78,6.22,6.72):
 m.part('Gasket_'+str(z).replace('.','_'),(0,0,z),'removable');m.ring(2.35,z,.48,.05,'Dark')
for z in (.87,6.12):
 m.part('RetainingRing_'+str(z).replace('.','_'),(0,0,z),'removable');m.ring(2.12,z,.14,.08,'Steel')
for j in range(16):
 a=j*math.tau/16
 for z in (.56,6.52):
  m.part(('Lower' if z<1 else 'Upper')+'Armor_'+str(j).zfill(2),(2.43*math.cos(a),2.43*math.sin(a),z),'removable')
  m.box((2.43*math.cos(a),2.43*math.sin(a),z),(.46,.30,.48),'Ivory',a)
  for dz in (-.15,.15):m.bolt((2.60*math.cos(a),2.60*math.sin(a),z+dz),(math.cos(a),math.sin(a),0),.025)
  for dz in (-.075,-.025,.025,.075):m.box((2.66*math.cos(a),2.66*math.sin(a),z+dz),(.01,.14,.012),'Rubber',a)
 m.part('Frame')
 for r in (2.13,2.48):
  for z in (.81,6.20):m.bolt((r*math.cos(a),r*math.sin(a),z),r=.018)
 if j%2==0:
  m.part('SupportStrut_'+str(j),(2.12*math.cos(a),2.12*math.sin(a),.82),'removable')
  x,y=2.12*math.cos(a),2.12*math.sin(a);m.cyl((x,y,.82),(x,y,6.20),.038,'Steel',12)
  for z in (1.03,5.95):m.cyl((x,y,z-.07),(x,y,z+.07),.07,'Dark',12)
m.part('Frame');m.ring(1.95,.87,.65,.06,'Dark');m.ring(1.95,6.11,.65,.06,'Dark')
m.text('N E X U S   /   C - 0 7',(0,-2.687,6.5),.14,mat='Dark')
m.finish('complex');place(m.name,folder='Hero/Containment')
m=Mesh('SM_Lab_ReactorGlass',0)
# 12 individual curved panels, narrow gaps and open middle; real interior visible.
for j in range(12):
 a=(j+.5)*math.tau/12;m.part('Glass_'+str(j).zfill(2),(2.08*math.cos(a),2.08*math.sin(a),3.5),'removable')
 m.ring(2.08,3.5,.012,5.23,'Glass',12,j*math.tau/12+.008,(j+1)*math.tau/12-.008)
m.finish('none');place(m.name,folder='Hero/Containment')
m=Mesh('SM_Lab_ReactorLight',.001)
for z in (.94,1.04,6.0):m.ring(1.98,z,.048,.035,'Cyan')
m.ring(1.88,.91,.02,.025,'White');m.ring(1.88,6.04,.02,.025,'White')
for j in range(8):
 a=j*math.tau/8;x,y=2.15*math.cos(a),2.15*math.sin(a)
 for z in (1.5,2.3,3.1,3.9,4.7,5.5):m.cyl((x,y,z),(x,y,z+.07),.012,'Cyan',6)
m.finish('none');place(m.name,folder='Hero/Containment')
m=Mesh('SM_Lab_ReactorHarness',.002)
for j in range(8):
 a=j*math.tau/8
 for side in (-1,1):
  m.part('Cable_'+str(j)+'_'+('A' if side<0 else 'B'),(2.5*math.cos(a),2.5*math.sin(a),6.55),'removable')
  pts=[]
  for k in range(25):
   t=k/24;r=2.50+.40*math.sin(math.pi*t);ang=a+side*.035
   pts.append((r*math.cos(ang),r*math.sin(ang),6.55-2.2*t))
  m.pipe(pts,.027,'Rubber')
  for z,r in [(6.53,2.5),(4.35,2.5)]:m.cyl((r*math.cos(a),r*math.sin(a),z-.07),(r*math.cos(a),r*math.sin(a),z+.07),.065,'Brass',12)
m.finish('none');place(m.name,folder='Hero/Containment')
m=Mesh('SM_Lab_Dais',.007)
m.lathe([(2.1,.01),(4.65,.01),(4.65,.35),(4.4,.35),(2.1,.35)],['Dark','RimSteel','RimSteel','Dark','Dark'])
m.ring(4.47,.37,.07,.035,'Brass')
for j in range(48):
 a=j*math.tau/48
 if j%4==0:m.box((4.47*math.cos(a),4.47*math.sin(a),.40),(.18,.14,.018),'Brass',a)
m.finish('complex');place(m.name,folder='Hero/Platform')
m=Mesh('SM_Lab_RailQuarter',.003)
for j in range(9):
 a=.12+j*(math.pi/2-.24)/8;x,y=4.25*math.cos(a),4.25*math.sin(a)
 m.box((x,y,.94),(.045,.045,1.12),'Dark');m.box((x,y,.43),(.15,.14,.06),'Ivory')
 for dx in (-.04,.04):m.bolt((x+dx,y,.47),r=.007)
for z in (.75,1.46):m.ring(4.25,z,.033,.033,'Steel',36,.12,math.pi/2-.12)
m.finish('complex')
for yaw in (0,90,180,270):place(m.name,z=-.0175,yaw=yaw,folder='Hero/Platform')

# Architectural kit: panel seams, exposed fasteners, recessed ventilation and independent fixtures.
m=Mesh('SM_Lab_FloorTile',.006)
m.box((0,0,-.065),(1.985,1.985,.13),'Steel');m.box((0,0,.007),(1.87,1.87,.015),'Floor')
for x in (-.89,.89):
 for y in (-.89,.89):m.bolt((x,y,.017),r=.009)
m.box((0,-.976,.006),(.8,.014,.008),'Dark');m.finish('simple')
for x in range(-15,16,2):
 for y in range(-11,12,2):place(m.name,x,y,folder='Architecture/Floor')
m=Mesh('SM_Lab_FloorLight',.002);m.box((0,0,.016),(1.96,.07,.024),'Dark');m.box((0,0,.031),(1.86,.022,.008),'Cyan');m.finish('none')
for x in range(-15,16,2):
 for y in (-7,7):place(m.name,x,y,folder='Architecture/Wayfinding')
m=Mesh('SM_Lab_WallBay',.008)
m.box((0,.08,2.2),(1.985,.24,4.4),'Dark')
for z,h in [(1.0,1.78),(2.85,1.72),(4.1,.45)]:
 m.part('Panel_'+str(z).replace('.','_'),(0,-.06,z),'removable')
 m.box((0,-.06,z),(1.84,.07,h),'Ivory')
 for x in (-.84,.84):
  for zz in (z-h/2+.07,z+h/2-.07):m.bolt((x,-.104,zz),(0,-1,0),.012)
m.part('Frame')
for x in (-.96,.96):m.box((x,-.08,2.2),(.05,.11,4.4),'Steel')
for i in range(9):m.box((0,-.105,.45+i*.045),(1.35,.016,.020),'Rubber')
m.box((.74,-.11,2.95),(.08,.025,.65),'Dark');m.box((.74,-.127,2.95),(.025,.01,.57),'Red')
m.box((-.62,-.10,1.75),(.22,.025,.28),'Dark');m.text('07',(-.62,-.12,1.72),.1,mat='Ivory')
m.finish('simple')
for x in range(-15,16,2):
 for z in (0,4.4):place(m.name,x,12,z,folder='Architecture/Walls')
for y in range(-11,12,2):
 for z in (0,4.4):
  place(m.name,-16,y,z,90,folder='Architecture/Walls');place(m.name,16,y,z,-90,folder='Architecture/Walls')
# Front wall left and right wings leave a broad entrance, useful for the hero view.
for x in (-15,-13,-11,-9,9,11,13,15):place(m.name,x,-12,0,180,folder='Architecture/Entrance')
m=Mesh('SM_Lab_Column',.012)
m.box((0,0,4.5),(.42,.48,9),'Dark')
for x in (-.28,.28):m.box((x,-.02,4.5),(.12,.57,9),'Steel')
for z in (.25,4.4,8.7):m.box((0,-.07,z),(.8,.72,.24),'Ivory')
for z in [i*.6+.7 for i in range(14)]:m.bolt((.24,-.32,z),(0,-1,0),.019)
m.finish('simple')
for x in (-15.5,15.5):
 for y in (-10,-4,2,8):place(m.name,x,y,folder='Architecture/Columns')
m=Mesh('SM_Lab_CeilingBeam',.008);m.box((0,0,0),(.18,23.5,.30),'Dark')
for y in range(-11,12):m.box((0,y,0),(.27,.10,.44),'Steel')
m.finish('simple')
for x in range(-14,15,4):place(m.name,x,0,8.9,folder='Architecture/Ceiling')
m=Mesh('SM_Lab_CeilingPanel',.003);m.box((0,0,0),(1.8,1.8,.10),'Dark')
for y in (-.70,0,.70):m.box((0,y,-.056),(1.65,.025,.025),'Steel')
m.finish('simple')
for x in range(-15,16,2):
 for y in range(-11,12,2):place(m.name,x,y,9.25,folder='Architecture/Ceiling')
m=Mesh('SM_Lab_Luminaire',.004);m.box((0,0,0),(2.8,.17,.10),'Dark');m.box((0,0,-.06),(2.65,.09,.028),'White')
for x in (-1.24,1.24):m.box((x,0,-.075),(.02,.12,.03),'Steel')
m.finish('none')
for x in (-12,-6,0,6,12):
 for y in (-9,-3,3,9):place(m.name,x,y,8.9,folder='Architecture/Lighting')
# Gallery around the rear and side walls, supported and reachable by real stairs.
m=Mesh('SM_Lab_GalleryTile',.005);m.box((0,0,-.12),(1.98,2.48,.24),'Dark')
for x in [i*.09-.9 for i in range(21)]:m.box((x,0,.015),(.024,2.40,.04),'Steel')
for y in (-1.16,1.16):m.box((0,y,-.1),(1.95,.08,.24),'Ivory')
m.finish('complex')
for x in range(-15,16,2):place(m.name,x,10.5,4.4,folder='Architecture/Gallery')
for y in (-7.5,-5,-2.5,0,2.5,5,7.5):
 for x in (-14.5,14.5):place(m.name,x,y,4.4,90,scale=(1.25,1,1),folder='Architecture/Gallery')
m=Mesh('SM_Lab_RailStraight',.004)
for x in (-.94,0,.94):
 m.box((x,0,.55),(.045,.06,1.1),'Dark');m.box((x,0,.035),(.15,.14,.07),'Ivory')
 for dx in (-.05,.05):m.bolt((x+dx,0,.08),r=.008)
for z in (.4,1.1):m.cyl((-.98,0,z),(.98,0,z),.026,'Steel',10)
m.finish('complex')
for x in range(-15,16,2):place(m.name,x,9.2,4.4,folder='Architecture/Gallery')
for y in range(-7,9,2):
 for x in (-13.2,13.2):
  place(m.name,x,y,4.4,90,folder='Architecture/Gallery')
  if y==-1:instances[-1]['enabled']=False
m=Mesh('SM_Lab_StairFlight',.004)
for i in range(22):
 y=i*.28;z=(i+1)*.2
 m.box((0,y,z-.035),(1.8,.29,.07),'Steel');m.box((0,y-.12,z+.006),(1.78,.03,.01),'Brass')
 for j in range(10):m.box((-.8+j*.175,y,z+.008),(.016,.19,.012),'Dark')
 for x in (-.92,.92):
  m.box((x,y,z-.12),(.08,.3,.25),'Dark')
  if i%3==0:m.cyl((x,y,z),(x,y,z+1.05),.024,'Steel',10)
for x in (-.92,.92):m.cyl((x,0,1.24),(x,5.88,5.44),.03,'Steel',12)
m.finish('complex')
place(m.name,-11.9,-7.5,folder='Architecture/Stairs');place(m.name,11.9,-7.5,folder='Architecture/Stairs')

# Workstation, peripherals, cabinets and layered instrumentation.
def drawers(m,x,y,z,w=.48,h=.66):
 previous=m.current_part;prefix='Cabinet_'+str(sum(1 for k in m.parts if k.startswith('Cabinet_') and k.endswith('_Shell')))
 m.part(prefix+'_Shell',(x,y,z),'fixed')
 for xx in (x-w/2,x+w/2):m.box((xx,y,z+h/2),(.018,.68,h),'Dark')
 m.box((x,y+.33,z+h/2),(w,.02,h),'Dark');m.box((x,y,z+.015),(w,.68,.03),'Dark')
 for i in range(3):
  zz=z+.11+i*.22;drawer=prefix+'_Drawer_'+str(i);pivot=(x,y-.354,zz)
  m.part(drawer,pivot,'slide',axis=[0,-1,0],travel=[0,.48])
  m.box((x,y-.354,zz),(w-.025,.028,.198),'Ivory')
  m.box((x,y-.02,zz-.085),(w-.05,.62,.016),'Steel')
  for xx in (x-w/2+.025,x+w/2-.025):m.box((xx,y-.02,zz),(.014,.62,.17),'Steel')
  m.box((x,y+.28,zz),(w-.05,.016,.17),'Steel')
  m.part(drawer+'_Handle',(x,y-.375,zz+.045),'fixed',parent=drawer)
  m.box((x,y-.375,zz+.045),(.20,.022,.022),'Steel')
  m.bolt((x+w*.32,y-.373,zz+.05),(0,-1,0),.006)
 m.current_part=previous
def keyboard(m,x,y,z):
 previous=m.current_part;m.part('Keyboard',(x,y,z),'pickup')
 m.box((x,y,z),(.45,.17,.025),'Dark')
 for j in range(5):
  for k in range(15):m.box((x-.205+k*.029,y-.065+j*.029,z+.017),(.023,.022,.01),'Ivory' if j!=0 else 'Steel')
 m.current_part=previous
m=Mesh('SM_Lab_Console',.005)
m.box((0,0,.77),(2.5,.9,.065),'Ivory');m.box((0,.40,.72),(2.42,.06,.08),'Dark')
drawers(m,-.94,0,.06);drawers(m,.94,0,.06)
for x in (-.94,.94):
 for y in (-.27,.27):m.cyl((x,y,0),(x,y,.08),.045,'Rubber',12)
for i,x in enumerate((-.76,0,.76)):
 m.box((x,.15,.825),(.25,.20,.025),'Dark');m.cyl((x,.21,.83),(x,.21,1.14),.022,'Steel',12);m.screen((x,.18,1.30),.66,.37,i)
keyboard(m,0,-.23,.82);m.part('Mouse',(.40,-.24,.835),'pickup');m.box((.40,-.24,.835),(.065,.10,.035),'Dark');m.part('Frame')
for x in (-1.1,1.1):m.pipe([(x,.35,.77),(x,.40,.55),(x+.1,.4,.2)],.012)
m.text('NEXUS SYSTEMS  /  OPERATOR TERMINAL',(0,-.457,.75),.036,mat='Dark')
m.finish('simple')
for x in (-11,-8,-5):place(m.name,x,5.6,folder='Equipment/Control room')
for x in (-6,0,6):place(m.name,x,-9.5,folder='Equipment/Foreground desks')
for x in (7,10):place(m.name,x,7.3,folder='Equipment/Robotics')
m=Mesh('SM_Lab_Chair',.004)
m.cyl((0,0,.12),(0,0,.45),.035,'Steel',12)
m.part('Seat',(0,0,.44),'swivel',axis=[0,0,1],travel=[-180,180]);m.box((0,0,.47),(.47,.45,.09),'Rubber')
m.part('Backrest',(0,.20,.50),'hinge',parent='Seat',axis=[1,0,0],travel=[-20,5]);m.box((0,.20,.76),(.45,.08,.50),'Rubber');m.box((0,.251,.77),(.27,.025,.36),'Dark')
for side in (-1,1):
 m.part('Armrest_'+str(side),(side*.27,.10,.35),'fixed',parent='Seat');m.cyl((side*.27,.10,.35),(side*.27,.10,.65),.018,'Steel',10);m.box((side*.27,-.02,.67),(.07,.31,.045),'Rubber')
m.part('Frame')
for i in range(5):
 m.part('Caster_'+str(i),motion='roll')
 a=i*math.tau/5;x,y=.28*math.cos(a),.28*math.sin(a);m.cyl((0,0,.15),(x,y,.085),.025,'Dark',10);m.cyl((x-.025,y,.05),(x+.025,y,.05),.045,'Rubber',12)
m.finish('simple')
for x,y in [(-11,4.4),(-8,4.5),(-5,4.4),(-6,-10.7),(0,-10.7),(6,-10.7),(7,6.1),(10,6.1)]:place(m.name,x,y,yaw=180,folder='Equipment/Chairs')
m=Mesh('SM_Lab_ServerRack',.004)
for x in (-.37,.37):m.box((x,0,1.05),(.04,.85,2.1),'Dark')
for z in (.035,2.065):m.box((0,0,z),(.78,.85,.07),'Dark')
m.box((0,.41,1.05),(.78,.03,2.1),'Dark')
for x in (-.39,.39):m.box((x,-.445,1.05),(.065,.05,2.10),'Ivory')
for i in range(16):
 z=.15+i*.116;m.part('ServerBlade_'+str(i).zfill(2),(0,-.44,z),'slide',axis=[0,-1,0],travel=[0,.65]);m.box((0,-.44,z),(.66,.035,.094),'Steel')
 m.box((0,-.02,z),(.59,.78,.07),'Dark')
 for j in range(9):m.box((-.24+j*.055,-.465,z),(.035,.012,.042),'Rubber')
 for x in (.22,.28):m.box((x,-.47,z+.018),(.012,.008,.012),'Cyan')
 for x in (-.32,.32):m.bolt((x,-.47,z),(0,-1,0),.006)
m.part('Frame')
for z in (.08,2.03):m.box((0,-.47,z),(.70,.05,.05),'Ivory')
m.text('COMPUTE  //  07',(0,-.49,2.03),.045,mat='Dark');m.finish('simple')
for i in range(7):place(m.name,-10.5+i*.88,10.8,folder='Equipment/Servers')
m=Mesh('SM_Lab_InstrumentBench',.004)
m.box((0,0,.84),(1.65,.75,.06),'Ivory');drawers(m,-.53,0,.08,w=.48,h=.7)
for x in (.55,.72):m.box((x,.22,.42),(.04,.04,.8),'Steel')
m.box((.48,0,.18),(.6,.66,.035),'Steel');m.box((.48,.22,1.16),(.60,.38,.50),'Ivory')
m.screen((.48,.006,1.20),.40,.24,2)
for x in (-.55,-.25):
 m.part('Instrument_'+str(x).replace('.','_').replace('-','N'),(x,.20,.88),'pickup')
 m.box((x,.20,1.03),(.25,.26,.31),'Ivory')
 m.cyl((x,-.02,1.04),(x,-.06,1.04),.048,'Dark',20)
 for k in range(3):m.box((x-.06+k*.06,.062,1.14),(.016,.01,.016),'Cyan')
m.part('Frame')
for x in (-.15,.10):m.cyl((x,-.18,.88),(x,-.18,1.05),.032,'Steel',18)
m.finish('simple')
for x,y,yaw in [(7,3,90),(10,3,90),(-11,1,0),(-7,1,0),(10,-3,90)]:place(m.name,x,y,yaw=yaw,folder='Equipment/Benches')
m=Mesh('SM_Lab_EquipmentCabinet',.005)
for x in (-.39,.39):m.box((x,0,1.05),(.02,.72,2.1),'Dark')
for z in (.02,.73,1.43,2.08):m.box((0,0,z),(.80,.72,.035),'Dark')
m.box((0,.35,1.05),(.80,.02,2.1),'Dark')
for z in (.40,1.1,1.8):
 door='Door_'+str(round(z,1)).replace('.','_');m.part(door,(-.37,-.38,z),'hinge',axis=[0,0,1],travel=[0,110])
 m.box((0,-.38,z),(.74,.055,.65),'Ivory');m.part(door+'_Handle',(.24,-.42,z),'fixed',parent=door);m.box((.24,-.42,z),(.04,.025,.22),'Steel');m.current_part=door
 for x in (-.32,.32):
  for dz in (-.25,.25):m.bolt((x,-.414,z+dz),(0,-1,0),.009)
m.screen((-.10,-.422,1.85),.25,.18,2);m.part('Frame')
for k in range(6):m.box((-.12,-.415,.25+k*.045),(.40,.02,.018),'Rubber')
m.finish('simple')
for x in (5,6,7,8,9,10,11,12):place(m.name,x,10.8,folder='Equipment/Cabinets')
m=Mesh('SM_Lab_Cart',.003)
for z in (.20,.55,.91):m.box((0,0,z),(.65,.46,.035),'Ivory')
for x in (-.29,.29):
 for y in (-.19,.19):m.cyl((x,y,.13),(x,y,1.0),.018,'Steel',10);m.cyl((x-.02,y,.08),(x+.02,y,.08),.055,'Rubber',12)
m.pipe([(-.30,.20,.98),(-.30,.20,1.12),(.30,.20,1.12),(.30,.20,.98)],.018,'Steel')
m.box((0,0,1.04),(.28,.27,.21),'Dark');m.screen((0,-.145,1.05),.20,.12,2);m.finish('simple')
for x,y in [(-6,3),(-10,-3),(6,-4),(4,6),(11,5)]:place(m.name,x,y,folder='Equipment/Carts')

# Industrial manipulator with bearings, hoses, ribs, actuators and a three-finger gripper.
m=Mesh('SM_Lab_RobotArm',.004)
m.box((0,0,.08),(.65,.65,.16),'Ivory')
for x in (-.25,.25):
 for y in (-.25,.25):m.bolt((x,y,.17),r=.021)
m.cyl((0,0,.15),(0,0,.44),.22,'Dark',32);m.cyl((0,0,.42),(0,0,.53),.25,'Ivory',32)
points=[(0,0,.53),(.06,0,1.28),(.58,0,1.82),(.96,0,1.64)]
for i,(a,b) in enumerate(zip(points,points[1:])):
 m.part('Link_'+str(i),a,'hinge',parent='Link_'+str(i-1) if i else None,axis=[0,1,0],travel=[-90,90])
 m.cyl(a,b,.105 if i<2 else .075,'Ivory',12)
 aa,bb=Vector(a),Vector(b);off=Vector((0,.115,0));m.cyl(aa+off,bb+off,.024,'Steel',12)
 m.cyl((aa.x,-.14,aa.z),(aa.x,.14,aa.z),.14 if i<2 else .10,'Dark',24)
 for sy in (-1,1):
  m.cyl((aa.x,sy*.14,aa.z),(aa.x,sy*.16,aa.z),.11 if i<2 else .08,'Ivory',24)
  for j in range(6):
   ang=j*math.tau/6;m.bolt((aa.x+.075*math.cos(ang),sy*.165,aa.z+.075*math.sin(ang)),(0,sy,0),.008)
m.part('CableHarness',(0,.18,.44),'flexible');m.pipe([(0,.18,.44),(-.12,.18,.78),(-.08,.18,1.3),(.35,.18,1.75),(.7,.13,1.8),(.96,.10,1.64)],.022)
m.part('Wrist',points[-1],'swivel',parent='Link_2',axis=[0,0,1],travel=[-180,180])
for dx in (-.04,.04):m.cyl((.96,dx,1.64),(.98,dx,1.43),.018,'Steel',10)
for j in range(3):
 a=j*math.tau/3;m.part('GripperFinger_'+str(j),(.98,0,1.44),'hinge',parent='Wrist',axis=[-math.sin(a),math.cos(a),0],travel=[0,45]);m.pipe([(.98,0,1.44),(.98+.11*math.cos(a),.11*math.sin(a),1.38),(.98+.08*math.cos(a),.08*math.sin(a),1.28)],.025,'Dark')
m.part('Frame');m.text('NEXUS / R-07',(0,-.335,.06),.044,mat='Dark');m.finish('complex')
for x,y,ang in [(8.2,1,0),(11.5,1,180),(8.5,-3,90)]:place(m.name,x,y,.88,ang,folder='Equipment/Robotics')

m=Mesh('SM_Lab_WallDisplay',.004);m.screen((0,0,0),3.8,2.1,1)
for x in (-1.97,1.97):m.box((x,0,0),(.06,.09,2.25),'Steel')
m.text('NEURAL TOPOLOGY / LIVE FIELD', (0,-.041,-1.12),.07,mat='Ivory');m.finish('simple')
place(m.name,-8,7.8,2.6,folder='Equipment/Control room')
place(m.name,2,11.78,2.7,folder='Equipment/Control room')
m=Mesh('SM_Lab_Whiteboard',.004);m.box((0,0,1.3),(1.45,.055,1.0),'Ivory')
for x in (-.75,.75):
 m.box((x,0,.9),(.035,.045,1.8),'Steel');m.box((x,0,.1),(.06,.60,.05),'Dark')
 for y in (-.25,.25):m.cyl((x-.02,y,.06),(x+.02,y,.06),.04,'Rubber',12)
for k in range(8):
 m.pipe([(-.55,-.031,1.62-k*.07),(-.40,-.031,1.62-k*.07),(-.15,-.031,1.59-k*.07),(.4,-.031,1.60-k*.07)],.002,'Steel',4)
m.finish('simple');place(m.name,-3.5,7,folder='Equipment/Whiteboard')

# Glass partitions frame rooms without blocking the main sight line.
m=Mesh('SM_Lab_WindowFrame',.005)
for x in (-2.65,2.65):m.box((x,0,1.9),(.14,.25,3.8),'Steel')
for z in (.12,3.68):m.box((0,0,z),(5.4,.25,.24),'Ivory')
for x in (-1.3,0,1.3):m.box((x,0,1.9),(.035,.10,3.55),'Dark')
for x in (-2.55,2.55):
 for z in (.4,1.5,2.5,3.4):m.bolt((x,-.135,z),(0,-1,0),.012)
m.finish('simple')
m=Mesh('SM_Lab_WindowGlass',0);m.box((0,0,1.9),(5.15,.015,3.4),'Glass');m.finish('none')
for mesh in ('SM_Lab_WindowFrame','SM_Lab_WindowGlass'):
 place(mesh,-8,3.8,folder='Architecture/Observation glass');place(mesh,11,4.8,yaw=90,folder='Architecture/Robotics glass')

m=Mesh('SM_Lab_DoorPortal',.008)
for x in (-1.35,1.35):
 m.box((x,0,1.65),(.30,.48,3.3),'Ivory');m.box((x,-.25,1.65),(.04,.025,2.9),'Red')
 for z in (.25,1,2,3):m.bolt((x,-.26,z),(0,-1,0),.017)
m.box((0,0,3.35),(3,.48,.3),'Dark');m.box((0,-.25,3.36),(2.5,.035,.06),'White')
m.text('ROBOTICS  /  03',(0,-.26,3.18),.14,mat='Ivory');m.finish('simple')
place(m.name,11.5,7.5,yaw=90,folder='Architecture/Doors');place(m.name,0,11.8,folder='Architecture/Doors')
m=Mesh('SM_Lab_Conduit',.002)
for x in (-.12,0,.12):
 m.cyl((x,0,0),(x,0,4.2),.035,'Steel',12)
 for z in (.20,1.2,2.2,3.2,4.0):m.cyl((x,0,z-.025),(x,0,z+.025),.048,'Dark',12)
for z in (.7,1.9,3.1):m.box((0,0,z),(.44,.12,.045),'Dark')
m.finish('none')
for x in (-14,-2,14):place(m.name,x,11.65,folder='Architecture/Conduits')
for y in (-8,-2,4):
 place(m.name,-15.65,y,yaw=90,folder='Architecture/Conduits');place(m.name,15.65,y,yaw=90,folder='Architecture/Conduits')
m=Mesh('SM_Lab_CableTray',.003)
for x in (-.18,.18):m.box((x,0,0),(.03,4,.13),'Steel')
for y in [i*.17-1.9 for i in range(23)]:m.box((0,y,-.05),(.35,.025,.025),'Steel')
for x in (-.1,-.04,.04,.1):m.cyl((x,-1.98,.02),(x,1.98,.02),.015,'Rubber',8)
m.finish('none')
for x in (-10,-4,4,10):
 for y in (-8,-4,0,4,8):place(m.name,x,y,8.65,folder='Architecture/Cable trays')

# Small props: faceted scanner, sample canister, case, mug, fire bottle and portable terminal.
m=Mesh('SM_Lab_SampleCanister',.002)
m.cyl((0,0,.03),(0,0,.23),.055,'Steel',24)
for z in (.025,.24):
 m.part('Base' if z<.1 else 'Cap',(0,0,z),'fixed' if z<.1 else 'twist',axis=[0,0,1],travel=[0,180]);m.cyl((0,0,z-.018),(0,0,z+.018),.065,'Dark',24)
m.part('Sleeve',(0,0,.08),'removable');m.cyl((0,0,.08),(0,0,.19),.057,'Glass',24)
m.part('Sample',(0,0,.10),'pickup');m.cyl((0,0,.10),(0,0,.17),.02,'Cyan',12)
m.part('Frame')
for j in range(6):a=j*math.tau/6;m.cyl((.059*math.cos(a),.059*math.sin(a),.05),(.059*math.cos(a),.059*math.sin(a),.22),.004,'Brass',8)
m.finish('simple')
m=Mesh('SM_Lab_ToolCase',.003)
for x in (-.20,.20):m.box((x,0,.10),(.02,.28,.20),'Dark')
for y in (-.13,.13):m.box((0,y,.10),(.42,.02,.20),'Dark')
m.box((0,0,.01),(.42,.28,.02),'Dark')
m.part('Lid',(0,.14,.205),'hinge',axis=[1,0,0],travel=[0,110]);m.box((0,0,.205),(.42,.28,.025),'Ivory');m.part('Frame')
for x in (-.16,.16):
 m.box((x,0,.105),(.035,.29,.22),'Steel');m.part('Latch_'+str(x).replace('.','_').replace('-','N'),(x,-.155,.16),'hinge',axis=[1,0,0],travel=[0,85]);m.box((x,-.155,.16),(.04,.035,.06),'Brass');m.part('Frame')
m.part('Handle',(-.06,-.15,.11),'hinge',axis=[1,0,0],travel=[0,90]);m.pipe([(-.06,-.15,.11),(-.06,-.18,.11),(.06,-.18,.11),(.06,-.15,.11)],.012,'Rubber');m.finish('simple')
m=Mesh('SM_Lab_Mug',.001);m.ring(.045,.055,.006,.10,'Ivory',32);m.cyl((0,0,.002),(0,0,.009),.045,'Ivory',24)
m.pipe([(.04,0,.03),(.075,0,.03),(.075,0,.09),(.04,0,.09)],.009,'Ivory');m.finish('simple')
m=Mesh('SM_Lab_FireBottle',.002);m.cyl((0,0,.08),(0,0,.52),.09,'Red',24,r2=.085)
m.cyl((0,0,.52),(0,0,.59),.035,'Steel',16);m.box((0,-.025,.61),(.12,.05,.025),'Dark')
m.pipe([(.04,0,.58),(.13,0,.55),(.14,0,.30),(.11,0,.19)],.015,'Rubber');m.box((0,-.087,.34),(.09,.008,.14),'Ivory');m.finish('simple')
for x,y in [(-14,10),(14,10),(-14,-9),(14,-9)]:place(m.name,x,y,folder='Props/Safety')
for i,(x,y) in enumerate([(-6,-9.5),(0,-9.5),(6,-9.5),(-8,5.6),(-11,5.6),(7,7.3),(10,7.3),(-7,1)]):
 place('SM_Lab_Mug',x-1.05,y-.2,.82,folder='Props/Desktop')
 place('SM_Lab_ToolCase',x+.55,y,.82,folder='Props/Desktop')
 for k in range(3):place('SM_Lab_SampleCanister',x-.85+k*.15,y-.22,.82,folder='Props/Samples')

m=Mesh('SM_Lab_ReactorTerminal',.004)
m.box((0,0,.10),(.48,.48,.20),'Dark');m.box((0,.10,.70),(.23,.20,1.10),'Ivory')
m.box((0,-.06,.96),(.52,.35,.08),'Steel');m.screen((0,.02,1.25),.48,.30,0)
for i in range(5):
 m.part('Button_'+str(i),(-.18+i*.09,-.22,1.01),'press',axis=[0,0,-1],travel=[0,.007]);m.box((-.18+i*.09,-.22,1.01),(.035,.035,.018),'Red' if i==4 else 'Cyan')
m.part('Frame')
for z in (.35,.60):
 for j in range(4):m.box((0,-.008,z+j*.028),(.14,.018,.012),'Dark')
m.pipe([(.10,.17,1.14),(.20,.24,.9),(.18,.23,.3),(0,.3,.05)],.014,'Rubber')
m.text('C-07', (0,-.013,.79),.055,mat='Dark');m.finish('simple')
for j in range(6):
 a=j*math.tau/6
 place(m.name,3.25*math.sin(a),-3.25*math.cos(a),.40,j*60,folder='Hero/Terminals')
m=Mesh('SM_Lab_AccessRamp',.004)
m.poly([(-.8,-1.8,0),(.8,-1.8,0),(-.8,0,0),(.8,0,0),(-.8,0,.4),(.8,0,.4)],[(0,1,5,4),(0,4,2),(1,3,5),(2,4,5,3),(0,2,3,1)],'Dark')
for x in (-.75,.75):
 for i in range(16):m.box((x,-1.75+i*.11,.4*(.05+i*.11)/1.8+.005),(.055,.045,.015),'Brass')
m.finish('complex');place(m.name,0,-4.45,folder='Hero/Platform')

# Enclosed observation suite and robotics bay perimeter, with broad glazed fronts.
for x in (-12,-10,-8,-6):place('SM_Lab_WallBay',x,8.4,folder='Architecture/Observation room')
for mesh in ('SM_Lab_WindowFrame','SM_Lab_WindowGlass'):
 place(mesh,-12,6.1,yaw=90,folder='Architecture/Observation room')
 place(mesh,-4,6.1,yaw=90,folder='Architecture/Observation room')
# Ceiling suspension feed to the reactor crown.
m=Mesh('SM_Lab_ReactorSuspension',.007)
for j in range(8):
 a=j*math.tau/8;x,y=2.25*math.cos(a),2.25*math.sin(a)
 m.cyl((x,y,6.88),(x,y,9.14),.065,'Dark',16)
 for z in (7,8.9):m.cyl((x,y,z-.06),(x,y,z+.06),.10,'Steel',16)
m.ring(2.4,8.95,.38,.18,'Ivory');m.finish('none');place(m.name,folder='Hero/Containment')

m=Mesh('SM_Lab_StairLanding',.006)
m.box((0,0,-.12),(3.9,1.45,.24),'Dark');m.box((0,0,.005),(3.85,1.40,.01),'Steel')
for x in (-1.88,1.88):m.box((x,0,.025),(.04,1.35,.02),'Brass')
for x in (-1.72,-1,0,1,1.72):
 for y in (-.62,.62):m.bolt((x,y,.02),r=.012)
m.finish('simple')
for x in (-13,13):place(m.name,x,-1.25,4.4,folder='Architecture/Stair landings')

m=Mesh('SM_Lab_RobotPedestal',.004)
m.box((0,0,.04),(1.0,.90,.08),'Dark');m.box((0,0,.86),(.85,.75,.04),'Steel')
for x in (-.28,.28):m.box((x,0,.46),(.04,.54,.76),'Ivory')
m.box((0,.25,.46),(.56,.04,.76),'Ivory')
for x in (-.40,.40):
 for y in (-.34,.34):m.bolt((x,y,.085),r=.02)
m.part('ServiceDoor',(-.27,-.28,.46),'hinge',axis=[0,0,1],travel=[0,110])
m.box((0,-.28,.46),(.54,.025,.72),'Ivory')
for i in range(8):m.box((0,-.296,.25+i*.035),(.34,.009,.014),'Dark')
m.box((.18,-.308,.66),(.025,.025,.12),'Steel');m.text('R-07',(0,-.30,.73),.07,mat='Dark');m.finish('simple')
for x,y,ang in [(8.2,1,0),(11.5,1,180),(8.5,-3,90)]:place(m.name,x,y,yaw=ang,folder='Equipment/Robotics')
m=Mesh('SM_Lab_Subfloor',.002);m.box((0,0,-.18),(31.98,23.98,.30),'Dark');m.finish('simple');place(m.name,folder='Architecture/Subfloor')
m=Mesh('SM_Lab_DaisDeckPanel',.004);m.box((0,0,0),(1.50,.33,.045),'Steel')
for x in (-.65,.63):m.bolt((x,0,.03),r=.012)
m.finish('simple')
for j in range(48):
 a=j*math.tau/48;place(m.name,3.6*math.cos(a),3.6*math.sin(a),.36,j*360/48,folder='Hero/Platform/Removable panels');instances[-1]['motion']='removable'

# Expand assemblies into individually selectable, correctly pivoted parts.
assembly_instances=instances;instances=[]
for index,row in enumerate(assembly_instances):
 entries=assemblies.get(row['mesh'],[{'mesh':row['mesh'],'role':'Frame','pivot':[0,0,0],'motion':row.get('motion','fixed'),'parent':None}])
 angle=math.radians(row['yaw']);rotation=Matrix.Rotation(angle,3,'Z')
 for entry in entries:
  pivot=Vector([v*s for v,s in zip(entry['pivot'],row['scale'])]);position=Vector(row['location'])+rotation@pivot
  instances.append({**row,**entry,'location':list(position),'assembly':row['mesh'],'assembly_id':index})

# Export each reusable asset with material slots, and a complete editable source scene.
for name,asset in assets.items():
 ob=asset['object'];bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 if '--dais-only' not in sys.argv or name in ('SM_Lab_Dais','SM_Lab_DaisDeckPanel'):
  bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,
   global_scale=1,apply_scale_options='FBX_SCALE_NONE',axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False)
 asset['triangles']=sum(len(p.vertices)-2 for p in ob.data.polygons)
 ob.hide_render=True;ob.hide_viewport=True
for i,row in enumerate(instances):
 src=assets[row['mesh']]['object'];ob=src.copy();ob.data=src.data;bpy.context.collection.objects.link(ob)
 ob.name=row['mesh']+f'_{i:04d}';ob.location=row['location'];ob.rotation_euler.z=math.radians(row['yaw']);ob.scale=row['scale'];ob.hide_render=not row.get('enabled',True);ob.hide_viewport=not row.get('enabled',True)
# Render uses the same geometry and materials, with physically proportioned room lighting.
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.eevee.use_gtao=True;scene.eevee.gtao_distance=3;scene.eevee.use_ssr=True;scene.eevee.use_bloom=True
scene.world.color=(.025,.035,.05)
def area(name,pos,power,color,size=5):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos
for x in (-10,0,10):
 for y in (-7,2,9):area('Ceiling softbox',(x,y,8.4),2200,(.60,.77,1),6)
for x in (-3,3):area('Reactor bounce',(x,0,5.7),1100,(.12,.48,1),4)
camd=bpy.data.cameras.new('LabHero');cam=bpy.data.objects.new('LabHero',camd);bpy.context.collection.objects.link(cam)
cam.location=(-10.8,-10.5,2.8);direction=Vector((0,1.7,3.2))-cam.location;cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();camd.lens=25;scene.camera=cam
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'LabHero.png')
manifest={'units':'meters','materials':{k:{'color':v[0],'metallic':v[1],'roughness':v[2]} for k,v in specs.items()},
 'assets':{name:{k:v for k,v in a.items() if k!='object'} for name,a in assets.items()},'assemblies':assemblies,'assembly_instances':assembly_instances,'instances':instances}
(ROOT/'lab_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'VRSharpLab_HardSurface.blend'))
if '--no-render' not in sys.argv:bpy.ops.render.render(write_still=True)
print('LAB_COMPLETE',len(assets),'assets',len(instances),'instances')
