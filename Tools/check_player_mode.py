"""Compile and exercise the production startup-mode selection without Unreal dependencies."""
from pathlib import Path
import subprocess
import tempfile

root=Path(__file__).resolve().parents[1]
source=root/'Script/ManagedVRSharp/Core/VRSharpControlMode.cs'
with tempfile.TemporaryDirectory(prefix='vrsharp-control-mode-') as directory:
    path=Path(directory)
    (path/'Check.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings></PropertyGroup></Project>',encoding='utf-8')
    (path/'Mode.cs').write_text(source.read_text(encoding='utf-8-sig'),encoding='utf-8')
    (path/'Attribute.cs').write_text('namespace UnrealSharp.Attributes { public class UEnumAttribute : System.Attribute {} }',encoding='utf-8')
    (path/'Program.cs').write_text('''using VRSharp.Core;
foreach(bool connected in new[]{false,true}) foreach(bool enabled in new[]{false,true}) {
 var expected=connected&&enabled?EVRSharpControlMode.VirtualReality:EVRSharpControlMode.Desktop;
 if(VRSharpControlModeSelection.Resolve(EVRSharpControlMode.Auto,connected,enabled)!=expected)throw new Exception("Auto mode");
 foreach(var explicitMode in new[]{EVRSharpControlMode.VirtualReality,EVRSharpControlMode.Desktop})
  if(VRSharpControlModeSelection.Resolve(explicitMode,connected,enabled)!=explicitMode)throw new Exception("Explicit override");
}
Console.WriteLine("Player startup mode: 12 production selection cases passed.");
''',encoding='utf-8')
    subprocess.run(['dotnet','run','--project',str(path/'Check.csproj'),'--configuration','Release'],check=True)
