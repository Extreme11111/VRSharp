#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
command -v git >/dev/null
command -v dotnet >/dev/null
git lfs version
dotnet --list-sdks | grep -Eq '^9\.' || { echo 'A .NET 9 SDK is required.' >&2; exit 1; }
git remote get-url origin
git lfs install --local
git lfs pull origin
git lfs fsck
printf '%s\n' 'Local cloud-checkout prerequisites and LFS download passed. Write authorization is not implied by this check.'
