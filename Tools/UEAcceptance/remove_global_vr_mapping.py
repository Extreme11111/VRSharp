"""Let the original Player own its XR mapping, rather than enabling it in every mode."""
import unreal
from pathlib import Path
assert unreal.EditorLevelLibrary.get_game_world() is None
settings=unreal.get_default_object(unreal.load_class(None,'/Script/EnhancedInput.EnhancedInputDeveloperSettings'))
rows=list(settings.get_editor_property('DefaultMappingContexts'))
kept=[]
for row in rows:
    print('DEFAULT_CONTEXT',row.export_text())
    if '/VRSharp/Input/VRSharpInputContext' not in row.export_text():kept.append(row)
with unreal.ScopedEditorTransaction('Use per-player VR and PC mapping contexts'):
    settings.set_editor_property('DefaultMappingContexts',kept)
root=Path(unreal.Paths.project_dir()).resolve()
ini=root/'Config/DefaultInput.ini'
text=ini.read_text(encoding='utf-8-sig')
lines=text.splitlines(keepends=True)
removed=[line for line in lines if line.lstrip().startswith('+DefaultMappingContexts=') and '/VRSharp/Input/VRSharpInputContext' in line]
assert len(removed)<=1,'Expected at most the known redundant VRSharp default context'
backup=root/'Saved/Tests/DefaultInput-BeforeDesktopFallback-20261107.ini'
if not backup.exists():backup.write_bytes(ini.read_bytes())
ini.write_text(''.join(line for line in lines if line not in removed),encoding='utf-8')
print('Removed only the redundant global VRSharp mapping; other host contexts preserved')
