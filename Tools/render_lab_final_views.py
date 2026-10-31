import unreal,json
from pathlib import Path
root=Path(unreal.Paths.project_dir());folder=root/'Saved/Tests/LabScreenshots'
ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);actors=ed.get_all_level_actors();world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
cap=next(a for a in actors if a.get_actor_label()=='Lab_RenderCapture');comp=cap.get_component_by_class(unreal.SceneCaptureComponent2D)
shots=[('Lab_UE_Hero.png',[-1080,1050,280],[0,-170,320],80),
       ('Lab_UE_FrameRepair.png',[-1080,-70,410],[-985,-380,354],62),
       ('Lab_UE_ConsoleDetail.png',[145,1150,130],[0,950,112],62)]
_index=-1;_frames=0;_rt=None;_done=[]
def next_shot():
 global _index,_frames,_rt
 _index+=1;_frames=0
 if _index==len(shots):
  comp.set_editor_property('capture_every_frame',False);comp.set_editor_property('texture_target',None)
  unreal.unregister_slate_post_tick_callback(_handle)
  unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
  (root/'Saved/Tests/Lab-FinalViews.json').write_text(json.dumps({'complete':True,'files':_done},indent=2))
  return
 name,pos,target,fov=shots[_index];location=unreal.Vector(*pos)
 comp.set_editor_property('capture_every_frame',False);cap.set_actor_location_and_rotation(location,unreal.MathLibrary.find_look_at_rotation(location,unreal.Vector(*target)),False,True)
 comp.set_editor_property('fov_angle',fov)
 _rt=unreal.RenderingLibrary.create_render_target2d(world,2400,1500,unreal.TextureRenderTargetFormat.RTF_RGBA8)
 comp.set_editor_property('texture_target',_rt);comp.set_editor_property('capture_every_frame',True)
def tick(dt):
 global _frames
 _frames+=1
 if _frames<36:return
 comp.set_editor_property('capture_every_frame',False);comp.capture_scene()
 unreal.RenderingLibrary.export_render_target(world,_rt,str(folder),shots[_index][0]);_done.append(shots[_index][0]);next_shot()
_handle=unreal.register_slate_post_tick_callback(tick);next_shot()
print('Capturing final overview, repaired frame joint, and workstation close-up')
