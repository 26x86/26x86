# Branching and release policy

## Summary

- `main` is the **only** deployable branch.
- **All** changes — code, documentation, CI, and module submodule pointers —
  must arrive through a **pull request** under the project policy.
- Every PR must pass the required status checks before merge.
- The documentation site and any release artifact deploy **only** from `main`,
  after a successful merge. A PR merge is the deploy trigger.

## Why

The seven modules are tracked Cargo workspace crates in this repository.
Independent module repositories receive reviewed exports from an exact source
commit. PRs keep source changes, release identities and validation reviewable.
The optional submodule-conversion tooling has not been applied; do not describe
ordinary tracked source files as gitlinks.

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

## Required status checks (branch protection on `main`)

| Check | Source | What it verifies |
| --- | --- | --- |
| `docs-build` | `.github/workflows/docs-pr.yml` | MkDocs Material site builds cleanly |
| `isolated-asset-guard` | `.github/workflows/isolated-asset-guard.yml` | No `_isolated/` path can enter the tree |
| `workspace-tests` | `.github/workflows/tests.yml` | Rust workspace compiles and tests pass |

Existing non-doc workflows (`cross-platform`, `sandbox`, `venfire-contract`,
`boot-runtime-contract`, `windows-exe`) continue to run as informational gates.

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

- Commit the intended workspace source and export only that commit's public
  crate files. Exclude uncommitted work, private inputs, artifacts and targets.
- Update existing module history with a normal commit and a fresh immutable
  release tag. Never force-push or replace an existing tag.
- Publish leaf dependencies before dependents, pin the new dependency tags,
  and verify every release from a fresh clone using its declared build gate.
