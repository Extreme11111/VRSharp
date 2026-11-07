#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
dotnet run --project Tools/SpringMathChecks/SpringMathChecks.csproj --configuration Release
dotnet run --project Tools/FingerContactChecks/FingerContactChecks.csproj --configuration Release

python3 Tools/check_desktop_grip.py

python3 Tools/check_grab_state.py

dotnet run --project Tools/GrabAdmissionChecks/GrabAdmissionChecks.csproj --configuration Release

python3 Tools/check_pose_selection.py
dotnet run --project Tools/FingerInputChecks/FingerInputChecks.csproj --configuration Release

python3 Tools/check_finger_input_state.py

python3 Tools/check_flashlight_demo.py

python3 Tools/check_grab_setup.py
