#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
missing=0
for tool in git dotnet; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'Missing required tool: %s. Provision it in the cloud environment before running checks.\n' "$tool" >&2
    missing=1
  fi
done
[[ "$missing" == 0 ]] || exit 1
git lfs version
dotnet --list-sdks | grep -Eq '^9\.' || { echo 'A .NET 9 SDK is required.' >&2; exit 1; }
git remote get-url origin
git lfs install --local
git lfs pull origin
git lfs fsck
printf '%s\n' 'Local cloud-checkout prerequisites and LFS download passed. Write authorization is not implied by this check.'
