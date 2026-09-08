# Branching and release policy

## Summary

- `main` is the **only** protected, deployable branch.
- **All** changes — code, documentation, CI, and module submodule pointers —
  must arrive through a **pull request**. Direct pushes to `main` are blocked.
- Every PR must pass the required status checks before merge.
- The documentation site and any release artifact deploy **only** from `main`,
  after a successful merge. A PR merge is the deploy trigger.

## Why

Single-source modules are now git **submodules** of this repository. A tree
("gitlink") entry records the pinned commit a PR intended. Enforcing PR-based
merges keeps those pointers reviewable, keeps `main` green, and prevents
accidental duplicate staging of module source that already lives in the module
repositories.

## Branch model

```text
feature/xyz ──▶ PR ──▶ main ──▶ GitHub Pages deploy (docs-pages.yml)
                        │
                        └──▶ package/release steps (future, PR-gated)
```

- Long-lived integration branches (for example `codex/mellow-mode-integration`)
  are merged into `main` through the same PR gate. They are **not** deploy
  branches.
- Feature and hotfix branches follow `feature/*`, `fix/*`, `docs/*`, or
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

Branch protection is applied and kept up to date with:

```powershell
# Windows (PowerShell) — requires `gh` authenticated as an admin
powershell -File tools/git/ensure-branch-protection.ps1
```

```bash
# macOS / Linux / WSL
bash tools/git/ensure-branch-protection.sh
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

## Submodule hygiene

- Never stage the *contents* of a module directory; stage the **gitlink**.
- After pulling new module commits:
  ```bash
  git submodule update --init --recursive
  ```
- Bump a module pointer by updating the submodule to the reviewed commit inside
  the PR branch — never on `main` directly.