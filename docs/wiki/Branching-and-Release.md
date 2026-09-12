# Branching and release policy

**Current Status:** PR/CI policy; current server-side protection must be inspected separately.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

## Summary

- `main` is the **only** deployable branch.
- **All** changes — code, documentation, CI, and module submodule pointers —
  must arrive through a **pull request** under the project policy.
- Every PR must pass the required status checks before merge.
- The documentation site and any release artifact deploy **only** from `main`,
  after a successful merge. A PR merge is the deploy trigger.

## Why

The seven modules own their source in separate repositories. This repository
tracks exact Git submodule commits and patches Cargo resolution to those local
checkouts. Each module change is tested and published before a parent PR records
its gitlink. PRs keep module source, dependency identities and integration checks
reviewable. See [the module workflow](Nextcore-Modules.md).

## Branch model

```text
feature/xyz ──▶ PR ──▶ main ──▶ GitHub Pages deploy (docs-pages.yml)
                        │
                        └──▶ package/release steps (future, PR-gated)
```

- Long-lived integration branches (for example `codex/mellow-mode-integration`)
  are merged into `main` through the same PR gate. They are **not** deploy
  branches.
- Feature and hotfix branches follow `codex/*`, `feature/*`, `fix/*`, `docs/*`, or
  `module/*` naming and target `main`.

## Intended baseline checks and current workflow receipts

| Check | Source | What it verifies |
| --- | --- | --- |
| `docs-build` | `.github/workflows/docs-pr.yml` | MkDocs Material site builds cleanly |
| `isolated-asset-guard` | `.github/workflows/isolated-asset-guard.yml` | No `_isolated/` path can enter the tree |
| `workspace-tests` | `.github/workflows/tests.yml` | Rust workspace compiles and tests pass |

Additional firmware, native comparator, integration and application workflows
have their own required evidence. This baseline table is not the exhaustive
current job list; inspect the selected commit's workflow and CI receipts. The
2026-09-12 `8f562` checkpoint passed 31 checks without establishing OS boot.

## Enforcement

The rules above are project policy. Their presence in this document does not
prove GitHub protection is configured. The live API reported no protection on
2026-09-08; current releases still follow PR and CI gates. Administrators can
apply the intended protection using the scripts below.

Branch protection is applied and kept up to date with:

```powershell
# Windows (PowerShell) — requires `gh` authenticated as an admin
powershell -File Tools/git/ensure-branch-protection.ps1
```

```bash
# macOS / Linux / WSL
bash Tools/git/ensure-branch-protection.sh
```

The script enforces on `main`:

- `required_pull_request_reviews` — 1 approving review
- required status checks: `docs-build`, `isolated-asset-guard`, `workspace-tests`
- `enforce_admins = true`, `allow_force_pushes = false`,
  `allow_deletions = false`
- `required_linear_history = true` — merges are squash or rebase only

## Deployment

- `.github/workflows/docs-pages.yml` runs on `push` to `main`, builds the site
  with MkDocs Material, and deploys with `actions/deploy-pages`.
- `docs-pr.yml` runs the **same build** on every pull request but never deploys.
- Site URL: <https://26x86.github.io/26x86/>

## Module release hygiene

- Commit and test changes in their owning module; do not copy crate sources into
  the parent or reinitialize a published module history.
- Publish leaf dependencies before dependents. Pin immutable commit IDs and
  verify standalone builds without the parent workspace patches.
- Merge the tested module PRs before merging the parent gitlink PR. A merge
  commit preserves the exact tested module IDs in main's reachable history.
- After merging, prove the feature commits are reachable from main, then remove
  the completed branch. Keep unmerged work and active worktrees intact.
- Never force-push, replace an existing release tag, or include original restore
  assets. A module CI pass is distinct from a successful guest OS boot.

The legacy protection helper's linear-history option must be reviewed before
applying it to module repositories: rebasing or squashing produces different
commit IDs. Do not delete the only reference to a dependency commit still used
by an integration gitlink.

## Current evidence and hardware coverage

Reviewed for documentation freshness on 2026-09-12. See the
[portal](../index.md), [progress](../progress.md),
[compatibility catalog](../compatibility.md) and
[library](../library.md) for the active evidence boundary. Historical
receipts in this guide retain their original scope and date.
