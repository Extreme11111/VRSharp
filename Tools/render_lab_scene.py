from pathlib import Path
import json
import unreal
root=Path(unreal.Paths.project_dir()).resolve();folder=root/'Saved/Tests/LabScreenshots';folder.mkdir(parents=True,exist_ok=True)
ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors=ed.get_all_level_actors();cam=next(a for a in actors if a.get_actor_label()=='Lab_PreviewCamera')
request_path=root/'Saved/Tests/LabCaptureRequest.json'
request=json.loads(request_path.read_text()) if request_path.exists() else {}
filename=request.get('filename','Lab_UE_Hero.png')
location=unreal.Vector(*request['location']) if 'location' in request else cam.get_actor_location()
rotation=unreal.MathLibrary.find_look_at_rotation(location,unreal.Vector(*request['target'])) if 'target' in request else cam.get_actor_rotation()
cap=next((a for a in actors if a.get_actor_label()=='Lab_RenderCapture'),None)
if not cap:
 cap=ed.spawn_actor_from_class(unreal.SceneCapture2D,cam.get_actor_location(),cam.get_actor_rotation());cap.set_actor_label('Lab_RenderCapture');cap.set_folder_path('VRSharpLab/Presentation');cap.set_editor_property('tags',[unreal.Name('LabGenerated')])
comp=cap.get_component_by_class(unreal.SceneCaptureComponent2D)
cap.set_actor_location_and_rotation(location,rotation,False,True)
comp.set_editor_property('capture_every_frame',False);comp.set_editor_property('capture_on_movement',False);comp.set_editor_property('always_persist_rendering_state',True)
comp.set_editor_property('capture_source',unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR);comp.set_editor_property('fov_angle',request.get('fov',80))
rt=unreal.RenderingLibrary.create_render_target2d(world,2400,1500,unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp.set_editor_property('texture_target',rt)
settings=comp.get_editor_property('post_process_settings')
for key,value in {'dynamic_global_illumination_method':unreal.DynamicGlobalIlluminationMethod.LUMEN,
                  'reflection_method':unreal.ReflectionMethod.LUMEN,
                  'lumen_scene_lighting_quality':2.0,'lumen_reflection_quality':2.0,
                  'auto_exposure_min_brightness':3.0,'auto_exposure_max_brightness':3.0,
                  'motion_blur_amount':0.0,'bloom_intensity':.45}.items():
 settings.set_editor_property('override_'+key,True);settings.set_editor_property(key,value)
comp.set_editor_property('post_process_settings',settings);comp.set_editor_property('post_process_blend_weight',1.0)
comp.set_editor_property('capture_every_frame',True)
_frames=0
def _capture_tick(dt):
 global _frames
 _frames+=1
 if _frames<24:return
 unreal.unregister_slate_post_tick_callback(_capture_handle)
 comp.set_editor_property('capture_every_frame',False);comp.capture_scene()
 unreal.RenderingLibrary.export_render_target(world,rt,str(folder),filename)
 comp.set_editor_property('texture_target',None)
 unreal.log('Exported warm UE laboratory render')
_capture_handle=unreal.register_slate_post_tick_callback(_capture_tick)
print('Warming 24 scene capture frames, then exporting UE image')
