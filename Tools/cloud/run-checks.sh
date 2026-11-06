#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
dotnet run --project Tools/SpringMathChecks/SpringMathChecks.csproj --configuration Release
dotnet run --project Tools/FingerContactChecks/FingerContactChecks.csproj --configuration Release

python3 Tools/test_host_collision.py
