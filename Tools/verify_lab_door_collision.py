import unreal,json
from pathlib import Path
r=Path(unreal.Paths.project_dir());ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);setup=json.loads((r/'Saved/Tests/Lab-VRCollisionSetup.json').read_text());frames=set(setup['fixed_frames_preserve_openings']);actors=ed.get_all_level_actors()
for a in actors:
 c=a.get_component_by_class(unreal.StaticMeshComponent)
 if c:
  mesh=c.get_editor_property('static_mesh')
  if mesh and mesh.get_name() in frames:c.set_static_mesh(None);c.set_static_mesh(mesh)
a=next(a for a in actors if (c:=a.get_component_by_class(unreal.StaticMeshComponent)) and c.get_editor_property('static_mesh') and c.get_editor_property('static_mesh').get_name()=='SM_Lab_DoorPortal');c=a.get_component_by_class(unreal.StaticMeshComponent)
p=a.get_actor_location()+unreal.Vector(0,0,170);right=a.get_actor_right_vector();forward=a.get_actor_forward_vector()
opening=c.line_trace_component(p-right*150,p+right*150,False,False)
pillar=p+forward*135
blocked=c.line_trace_component(pillar-right*150,pillar+right*150,False,False)
checks={'opening_clear':opening is None,'pillar_blocks':blocked is not None};print('Door-frame checks',checks)
assert all(checks.values())
(r/'Saved/Tests/Lab-DoorCollisionChecks.json').write_text(json.dumps(checks,indent=2))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
