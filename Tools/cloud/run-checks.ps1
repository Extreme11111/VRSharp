$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:DOTNET_CLI_UI_LANGUAGE = 'en'
Push-Location (Join-Path $PSScriptRoot '../..')
try {
    foreach ($name in @('SpringMathChecks', 'FingerContactChecks', 'GrabAdmissionChecks', 'FingerInputChecks')) {
        dotnet run --project "Tools/$name/$name.csproj" --configuration Release
        if ($LASTEXITCODE -ne 0) { throw "$name failed with exit code $LASTEXITCODE" }
    }
    foreach ($name in @('check_desktop_grip', 'check_grab_state', 'check_pose_selection', 'check_finger_input_state',
                         'check_flashlight_demo', 'check_grab_setup', 'check_pose_preset', 'test_host_collision', 'check_player_mode')) {
        python "Tools/$name.py"
        if ($LASTEXITCODE -ne 0) { throw "$name failed with exit code $LASTEXITCODE" }
    }
} finally {
    Pop-Location
}
