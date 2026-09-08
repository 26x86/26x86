#!/usr/bin/env bash
# Publish an already committed integration branch after its module branches.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$#" -ne 1 || "$1" != "--push-integration" ]]; then
  echo "Usage: $0 --push-integration"
  echo "Commit, test and push changed module branches first."
  exit 2
fi
cd "$ROOT"
python3 Tools/verify_nextcore_submodules.py --cargo --require-clean
if [[ -n "$(git status --porcelain --untracked-files=normal)" ]]; then
  echo "ERROR: commit the integration changes first" >&2
  exit 1
fi
branch="$(git symbolic-ref --quiet --short HEAD)"
if [[ "$branch" == main || "$branch" == master ]]; then
  echo "ERROR: publish an integration feature branch and use a pull request" >&2
  exit 1
fi
git push --recurse-submodules=check --set-upstream origin "HEAD:refs/heads/$branch"
