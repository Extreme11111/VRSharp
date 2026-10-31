#!/usr/bin/env bash
# Exercise the GitHub Actions identity, never a developer's personal credential.
set -euo pipefail
[[ "${GITHUB_ACTIONS:-}" == true && "${GITHUB_REF:-}" == refs/heads/main ]] || { echo 'Run only in trusted main-branch GitHub Actions.' >&2; exit 1; }
branch="cloud-access-probe-${GITHUB_RUN_ID:?}-${GITHUB_RUN_ATTEMPT:?}"
created=0
cleanup() {
  if [[ "$created" == 1 ]]; then git push origin --delete "$branch"; fi
}
trap cleanup EXIT
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git switch -c "$branch"
mkdir -p .cloud-permission-probe
printf 'VRSharp cloud LFS access check: %s/%s\n' "$GITHUB_RUN_ID" "$GITHUB_RUN_ATTEMPT" > .cloud-permission-probe/roundtrip.lfsprobe
git lfs track '*.lfsprobe'
git add .gitattributes .cloud-permission-probe/roundtrip.lfsprobe
git commit -m 'Verify cloud branch and Git LFS write access'
git push origin "HEAD:refs/heads/$branch"
created=1
probe_dir="$(mktemp -d "${RUNNER_TEMP:?}/vrsharp-lfs-roundtrip-XXXXXX")"
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 --branch "$branch" "https://github.com/${GITHUB_REPOSITORY:?}.git" "$probe_dir"
git -C "$probe_dir" lfs pull --include='*.lfsprobe' --exclude=''
cmp .cloud-permission-probe/roundtrip.lfsprobe "$probe_dir/.cloud-permission-probe/roundtrip.lfsprobe"
printf '%s\n' 'GitHub Actions branch push, LFS upload, independent LFS download and byte-for-byte comparison passed.'
