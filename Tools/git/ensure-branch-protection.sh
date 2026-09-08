#!/usr/bin/env bash
set -euo pipefail

# Enforces the 26x86/26x86 pull-request-only branch strategy on `main`.
# Requires: gh authenticated with a token that has admin permission on the repo.
#
# Usage:
#   bash tools/git/ensure-branch-protection.sh
#   REPO=26x86/26x86 BRANCH=main bash tools/git/ensure-branch-protection.sh

REPO="${REPO:-26x86/26x86}"
BRANCH="${BRANCH:-main}"
CONTEXTS=("docs-build" "isolated-asset-guard" "workspace-tests")

protect() {
  python3 - "$1" <<'PY'
import json, os, subprocess, sys
body = {
  "enforce_admins": True,
  "required_linear_history": True,
  "require_conversation_resolution": True,
  "allow_force_pushes": False,
  "allow_deletions": False,
  "lock_branch": False,
  "allow_fork_pushes": False,
  "restrictions": None,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": True,
    "require_code_owner_reviews": False,
  },
}
mode = sys.argv[1]
if mode == "checks":
    body["required_status_checks"] = {
        "strict": True,
        "contexts": os.environ["REPO_CTX"].split(","),
    }
else:
    body["required_status_checks"] = None
proc = subprocess.run(
    ["gh", "api", "-X", "PUT",
     f"repos/{os.environ['REPO']}/branches/{os.environ['BRANCH']}/protection",
     "--input", "-"],
    input=json.dumps(body), capture_output=True, text=True,
)
if proc.returncode != 0:
    sys.stderr.write(proc.stderr)
    sys.exit(proc.returncode)
print("ok")
PY
}

export REPO BRANCH
export REPO_CTX="$(IFS=,; echo "${CONTEXTS[*]}")"

echo "Applying branch protection on $REPO/$BRANCH with checks: ${CONTEXTS[*]}"
if protect checks; then
  echo "OK: protection set with ${#CONTEXTS[@]} required checks."
else
  echo "WARN: context apply failed; applying reviews-only protection first."
  protect reviews-only
  sleep 3
  if protect checks; then
    echo "OK: protection set with ${#CONTEXTS[@]} required checks."
  else
    echo "WARN: contexts still rejected. Re-run after the three checks have completed once on a PR."
  fi
fi

echo
echo "Current protection summary:"
gh api "repos/$REPO/branches/$BRANCH/protection" \
  --jq '{enforce_admins, required_linear_history, allow_force_pushes, allow_deletions,
         required_pr_reviews: .required_pull_request_reviews.required_approving_review_count,
         contexts: [.required_status_checks.contexts[]]}'