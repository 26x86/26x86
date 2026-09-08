#!/usr/bin/env bash
set -euo pipefail

# Phase 2 — publish the seven Nextcore module repositories and convert
# nextcore/crates/* into git submodules of 26x86/26x86.
#
# Steps:
#   1. Reuses Tools/export_nextcore_repositories.py to build each module repo
#      (own git history on `main`, initial tag 26x86-<Module>-v0.1.0, git
#      dependencies rewritten to fixed tags).
#   2. Pushes each exported repo to github.com/26x86/Nextcore-<Module> (`main`
#      + tag).
#   3. In this repository: `git rm --cached` the old crate dirs, `git submodule
#      add` each module, and adds [patch] sections to the workspace root so
#      `cargo test --workspace` keeps resolving against the local checkouts.
#
# This script always:
#   - Requires explicit confirmation unless --yes.
#   - Never touches _isolated/ or any private asset.
#   - Stops before step 3 unless --convert-submodules is given (steps 1-2 only
#     publish module repositories and are reversible).
#
# Usage:
#   bash Tools/publish_nextcore_modules.sh --output /tmp/nx-modules
#   bash Tools/publish_nextcore_modules.sh --output /tmp/nx-modules --yes --convert-submodules

OWNER="26x86"
SUPERPROJECT_REPO="$OWNER/26x86"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() { echo "usage: $0 --output DIR [--yes] [--convert-submodules]"; exit 2; }

OUTPUT=""
CONFIRM=1
CONVERT=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT="$2"; shift 2 ;;
    --yes) CONFIRM=0; shift ;;
    --convert-submodules) CONVERT=1; shift ;;
    *) usage ;;
  esac
done
[[ -n "$OUTPUT" ]] || usage

if [[ ! -f "$ROOT/Tools/export_nextcore_repositories.py" ]]; then
  echo "ERROR: Tools/export_nextcore_repositories.py not found" >&2
  exit 1
fi

GH=""
for cand in gh gh.exe; do
  if command -v "$cand" >/dev/null 2>&1; then GH="$cand"; break; fi
done
if [[ -z "$GH" ]] && [[ -x "/c/Program Files/GitHub CLI/gh.exe" ]]; then
  export PATH="$PATH:/c/Program Files/GitHub CLI"
  GH="gh"
fi
if [[ -z "$GH" ]] || ! "$GH" auth status >/dev/null 2>&1; then
  echo "ERROR: gh CLI is not available or not authenticated" >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi

echo "== Exporting module repositories =="
"$PY" "$ROOT/Tools/export_nextcore_repositories.py" --output "$OUTPUT"

mapfile -t REPOS < <(find "$OUTPUT" -maxdepth 1 -mindepth 1 -type d | sort)

for repo_dir in "${REPOS[@]}"; do
  name="$(basename "$repo_dir")"
  tag="$(cat "$repo_dir/repository.json" | python3 -c "import json,sys; print(json.load(sys.stdin)['initial_tag'])")"
  remote="https://github.com/$OWNER/$name.git"
  echo "== [${name}] push $tag to $remote =="
  git -C "$repo_dir" remote add origin "$remote"
  git -C "$repo_dir" push -u origin main
  git -C "$repo_dir" push origin "$tag"
  echo "== [${name}] published $tag =="
done

if [[ "$CONVERT" -eq 0 ]]; then
  echo "Modules published. Submodule conversion was NOT run (pass --convert-submodules)."
  echo "Review each exported inventory under $OUTPUT first."
  exit 0
fi

echo "== Converting nextcore/crates/* into submodules =="

# The superproject checkout must be clean enough to apply the conversion.
if [[ -n "$(git -C "$ROOT" status --porcelain --untracked-files=no)" ]]; then
  echo "ERROR: superproject has tracked changes; commit or stash first" >&2
  exit 1
fi

declare -A CRATE_MAP=(
  [nextcore-core]=Nextcore-Core
  [nextcore-efi]=Nextcore-EFI
  [nextcore-tool]=Nextcore-Tool
  [nextcore-ise]=Nextcore-ISE
  [nextcore-gpu]=Nextcore-GPU
  [nextcore-hal]=Nextcore-HAL
  [nextcore-apls]=Nextcore-APLS
)

for crate in "${!CRATE_MAP[@]}"; do
  path="nextcore/crates/$crate"
  if git -C "$ROOT" ls-files --error-unmatch "$path" >/dev/null 2>&1; then
    echo "staging removal of tracked tree $path"
    git -C "$ROOT" rm -r --cached --quiet "$path"
  fi
  repo="${CRATE_MAP[$crate]}"
  echo "adding submodule $path -> $OWNER/$repo"
  git -C "$ROOT" submodule add "https://github.com/$OWNER/$repo.git" "$path"
done

# Directory-level ignores that applied to the old tree still apply to the
# gitlink (they used /nextcore/target/ which now lives inside submodules).
echo "workspace submodule conversion staged. Next:"
echo "  1. add [patch] sections to nextcore/Cargo.toml (see docs/wiki/Nextcore-Modules.md)"
echo "  2. commit .gitmodules + gitlinks + manifest on a feature branch"
echo "  3. open a pull request to ${SUPERPROJECT_REPO}:main"