import unreal,json
from pathlib import Path
ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);actors=ed.get_all_level_actors();w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();ignore=[a for a in actors if 'VRSharpPlayer' in a.get_class().get_name() or a.get_class()==unreal.PlayerStart.static_class()]
checks=[]
for name,x,y,z,expected in [('spawn',0,780,350,-3),('west_stair_mid',-1190,470,600,220),('east_stair_mid',1190,470,600,220),('west_landing',-1300,125,600,443),('west_gallery_gap',-1450,-900,600,441),('east_gallery_gap',1450,-900,600,441),('reactor_access',0,540,150,19)]:
 h=unreal.SystemLibrary.line_trace_single(w,unreal.Vector(x,y,z),unreal.Vector(x,y,-100),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignore,unreal.DrawDebugTrace.NONE)
 p=h.to_tuple()[5] if h else None;checks.append({'case':name,'height_cm':p.z if p else None,'passed':p is not None and abs(p.z-expected)<10})
h=unreal.SystemLibrary.line_trace_single(w,unreal.Vector(50,350,350),unreal.Vector(50,0,350),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignore,unreal.DrawDebugTrace.NONE)
checks.append({'case':'reactor_glass_blocks','passed':bool(h) and 'Glass_' in h.to_tuple()[9].get_actor_label()})
for a in actors:
 if a.get_actor_label().startswith('Lab_Collision_StairRamp_'):
  c=a.get_component_by_class(unreal.StaticMeshComponent);checks.append({'case':a.get_actor_label()+'_hands_ignore','passed':c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_VR_HAND)==unreal.CollisionResponseType.ECR_IGNORE and c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_VR_PLAYER)==unreal.CollisionResponseType.ECR_BLOCK})
report={'passed':all(c['passed'] for c in checks),'checks':checks,'vr_hardware_tested':False}
(root:=Path(unreal.Paths.project_dir())/'Saved/Tests/Lab-VRCollisionChecks.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
c=next(a for a in actors if a.get_actor_label()=='Lab_A0000_Frame').get_component_by_class(unreal.StaticMeshComponent)
print('ComponentTrace',getattr(c,'line_trace_component',None).__doc__ if hasattr(c,'line_trace_component') else 'not exposed')
