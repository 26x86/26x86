# APFS module release preparation — 2026-09-08

Current state: read-only preparation complete. Final source commit is **not assigned**. No module tag, commit, clone, push, workflow or organization profile was changed during this task. Root owns the final source selection and workspace index; the dirty workspace exporter/main files were not read or edited.

Desired state after the root's final-source message: incrementally publish only changed public modules, keep existing history/tags and package versions, verify each changed release from independent Linux clones before and after publishing, check exact-head GitHub CI, and update the organization profile against those completed results.

## Observed remote state

`remote-observation.json` contains the complete remote refs, immutable-head Cargo manifests, repository metadata and workflow bytes/hashes. `ci-profile-observation.json` records exact-head Actions results and the current profile text. Every latest release tag resolves to its corresponding main head; all returned exact-head CI runs completed successfully.

| Module | Current release | Main commit | Next unused candidate | Proposed action |
| --- | --- | --- | --- | --- |
| [Core](https://github.com/26x86/Nextcore-Core) | v0.1.1 | `66eb69888a9cb8bc56d05f9b2a0bbfab5abfd54b` | v0.1.2 | Release the approved APFS parser snapshot |
| [GPU](https://github.com/26x86/Nextcore-GPU) | v0.1.1 | `8962199b5a7381850ef9aa9e72e98b45a8671d46` | v0.1.2 | Retain v0.1.1 if final source is unchanged |
| [HAL](https://github.com/26x86/Nextcore-HAL) | v0.1.1 | `9c1cd8dfff33478e32668c5cd181dd094ec2881b` | v0.1.2 | Retain v0.1.1 if final source is unchanged |
| [ISE](https://github.com/26x86/Nextcore-ISE) | v0.1.1 | `e4c318ff707ff57eaf128ffd66cc962a210ab8e1` | v0.1.2 | Retain v0.1.1 if final source is unchanged |
| [APLS](https://github.com/26x86/Nextcore-APLS) | v0.1.1 | `f4d640e362fbcf160994d833b330e16506de9110` | v0.1.2 | Retain unless its own source/dependency graph changes |
| [EFI](https://github.com/26x86/Nextcore-EFI) | v0.1.1 | `c00f6fe6d6618f574ed193547837d675e6ca2da3` | v0.1.2 | Release approved NXAPFS source with Core v0.1.2 |
| [Tool](https://github.com/26x86/Nextcore-Tool) | v0.1.2 | `c53645672d940290ed383b348e751c0a6e4e36c6` | v0.1.3 | Increment from the fixed v0.1.2 history; pin Core v0.1.2 |

All full tag names use `26x86-Nextcore-<Module>-v0.1.x`. Candidate absence is an observation, not a reservation; recheck immediately before the eventual atomic push. Six current modules identify source `dcc90013109eac694ccbf997b1e44a7018480f78`; Tool v0.1.2 identifies its fixture fix source `045065700cbd037eaaa974faf957ba15cb628370`. Their Cargo package versions remain `0.1.0` as previously agreed; repository snapshot tags have a separate version.

## Dependency decision

The actual remote manifest graph is:

```text
Core (leaf) ──> EFI
            └> Tool <── APLS <── GPU (leaf)
HAL, ISE (independent leaves)
```

APLS currently depends only on GPU v0.1.1; it does **not** pin Core. Therefore the expected minimal release set is Core v0.1.2, followed by EFI v0.1.2 and Tool v0.1.3. Tool can keep APLS v0.1.1. If the approved final source adds APLS changes or a Core dependency, include APLS v0.1.2 after its dependencies and update Tool to that tag. This must be decided from the final immutable source, not inferred from the anticipated change list. No dependency on an unpublished tag may be used for a release gate.

## CI and independent Linux gates

The current EFI workflow runs `cargo check --target x86_64-unknown-uefi --all-features`. Cargo's [official target-selection contract](https://doc.rust-lang.org/cargo/commands/cargo-check.html#target-selection) checks all library and binary targets by default and skips a binary only when required features are absent. With `--all-features`, a properly declared NXAPFS binary is included. The current remote snapshot does not contain NXAPFS yet, so this is workflow coverage analysis, not a completed NXAPFS check.

After final source selection, verify Cargo metadata includes NXAPFS with the intended path/features, retain the all-feature UEFI check, and add explicit `cargo build --target x86_64-unknown-uefi --all-features --bin NXAPFS` to the release gate/workflow. Unlike check, build performs code generation/linking. Record the resulting PE architecture and subsystem separately from any execution evidence. Do not add host `--all-targets` tests to the UEFI package as a substitute for its UEFI build.

Core gates: `cargo test --all-targets`, `cargo test --no-default-features --test apfs_jumpstart`, and `cargo check --no-default-features --lib --target x86_64-unknown-uefi`. Install that Rust target in the CI job. Tool and APLS, if released, retain `cargo test --all-targets`. Unchanged modules keep their existing published tags and successful CI; a final source diff must substantiate that classification.

Each changed module gets a separate fresh Linux parent containing only `module/`; other NextCore crates cannot be siblings. The prepared source clone and post-push remote clone both must execute their gates with actual Linux Cargo. Use a process-local `/home/developer/.cargo/bin` PATH prefix when necessary. Preserve argv, exit status, source/HEAD/tag identity, Git blob and checkout hashes, Cargo.lock hash and compiler version. No global configuration/package changes are needed. This directly guards against the previous Tool sibling-fixture bug, whose immutable v0.1.1 remains preserved and whose v0.1.2 fix must remain in v0.1.3.

## Frozen helper review and required adaptation

The prior helpers under the retained `nextcore-modules-v011-20260908-153614` temporary directory were inspected, not executed or modified: `prepare_incremental.py`, `publish_module.py`, `validate_module-r1.py`, `prepare_tool_fix.py`, `verify_tool_linux-r1.py`.

- Retain fixed `git show`/`git ls-tree` blob export, checked public crate paths, regular-file modes, inventory hashes, current-head comparison, direct-child history validation, unused-tag check and atomic main+new-tag push. No working-tree bytes, `_isolated`, artifacts, targets, Apple inputs, symlinks or submodules enter export.
- Do not reuse the hardcoded v0.1.1 tag/source or all-seven release loop. Use a reviewed per-module version/dependency map and compare each final source crate with its previously recorded source commit. Preserve managed deletion handling and unmanaged repository files; detect collisions between source-owned files and generated README/license/workflow files instead of silently changing declared source bytes.
- Generate separate new helpers in the next fresh release directory after source authorization. The shared legacy exporter is deliberately excluded: its initial orphan/fixed-tag behavior cannot update existing histories. This follows the skill's boundary/gate requirements using the root-approved incremental adaptation, without force-push.
- Prepare and inventory a local commit before the pre-publish Linux clone, since uncommitted work is not a clone source. The clone must match that exact prepared head. Tag/push only after its gate passes and the root-approved final source is recorded. Resolve Core first so dependent gates use the new real remote tag. Recheck unchanged old tags after publishing.
- Prefer native Linux checkout and committed Git-blob inventory validation plus a clean worktree check; do not let Windows CRLF conversion or case-insensitive sibling paths hide source/fixture problems. All transient lockfiles/build caches remain outside export, with their hashes retained in gate receipts.

## Organization update plan

Current `26x86/.github` main is `4e446a4b7debc714ff2ec7ac6ead069bb2860618`. Keep the NextCore logo, seven-module map, upstream attribution, canonical main documentation links and explicit `metal_verified=false` boundary. Once releases and exact-head CI succeed, update only the affected tag/head links and their fixed final source commit. APFS extraction, EFI driver start/controller connection, installed filesystem discovery, XNU/userspace and guest Metal remain separate evidence. No statement about the still-running original APFS experiment is added during preparation.

## Pending owner input

The remaining required input is the root's full final source commit and completed-runtime evidence references suitable for public release notes. Existing user push authorization is recorded, but the root explicitly prohibited remote mutation before that source message. Until it arrives, this task performs no release mutation.

Audit reproduction: Python 3.11+ is required for `tomllib`; on this Windows host use `py -3.12 read_remote.py` followed by `py -3.12 read_ci_profile.py`. The initial `python` command selected Python 3.10 and exited before network access because `tomllib` was absent; using the already-installed Python 3.12 resolved it without installation or global changes.
