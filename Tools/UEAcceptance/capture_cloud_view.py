import unreal
from pathlib import Path
p=Path(unreal.Paths.project_dir()).resolve()/'Saved/Tests/Cloud-Desktop-20261107.png'
task=unreal.AutomationLibrary.take_high_res_screenshot(1280,720,str(p))
print('Screenshot requested',p)
