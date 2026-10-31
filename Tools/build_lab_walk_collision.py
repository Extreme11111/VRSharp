from pathlib import Path
source=Path(__file__).with_name('build_lab_models.py')
exec(compile(source.read_text(encoding='utf-8').split('# The hero reactor:')[0],str(source),'exec'))
COL=ROOT/'Collision';COL.mkdir(exist_ok=True)
m=Mesh('SM_Lab_VRWalkRamp',0)
m.poly([(-.88,-.28,-.05),(.88,-.28,-.05),(-.88,5.88,-.05),(.88,5.88,-.05),(-.88,-.28,0),(.88,-.28,0),(-.88,5.88,4.4),(.88,5.88,4.4)],[(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3),(4,6,7,5),(0,1,3,2)],'Dark')
m.finish('complex')
m=Mesh('SM_Lab_GalleryCornerConnector',.004);m.box((0,0,-.06),(2.46,.62,.12),'Steel')
for x in (-1.12,1.12):
 for y in (-.22,.22):m.bolt((x,y,.005),r=.010)
m.finish('simple')
for name,a in assets.items():
 bpy.ops.object.select_all(action='DESELECT');a['object'].select_set(True);bpy.context.view_layer.objects.active=a['object']
 bpy.ops.export_scene.fbx(filepath=str(COL/(name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,global_scale=1,apply_scale_options='FBX_SCALE_NONE',axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,bake_anim=False)
bpy.ops.wm.save_as_mainfile(filepath=str(COL/'VRSharpLab_WalkCollision.blend'))
