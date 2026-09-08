# Incremental NextCore module release — 2026-09-08

Current state: seven existing public module repositories have independent `main` history and their original `26x86-<module>-v0.1.0` tags. Each currently identifies source commit `3acb61b5c60e3519debb5a65cf47629c387e12cf`. Desired state: publish the reviewed current NextCore source as a new fixed-tag snapshot while retaining every existing commit and tag.

DECIDED: use fresh clones, a parent-selected immutable source commit, and public tracked crate bytes obtained through Git objects. The shared dirty workspace and its exporter scripts are not modified or copied as a release source. The initial-export workflow's orphan repositories are not used as replacement histories. `_isolated`, artifacts, target outputs, Apple inputs and runtime receipts are excluded from module exports.

The proposed unused tag family is `26x86-<module>-v0.1.1`. Package versions stay identical to the selected source; module snapshot tags are independently versioned. Manifests replace only sibling module paths with fixed new Git tags. Original `initial_tag` metadata is retained; the new release records `release_tag`, source commit, previous module head, dependency tags and a fresh content inventory.

Publish order is Core/GPU/HAL/ISE, then APLS/EFI, then Tool. Every module must pass its declared gate before an ordinary fast-forward push of main and its new tag. A separate post-publish clone must pass again: ordinary modules use all-target tests, Core additionally checks no_std, GPU checks its optional Vulkan build/tests, and EFI checks the x86_64 UEFI target including its features. Module checks are not macOS boot or GPU execution evidence.

DECIDED source: `dcc90013109eac694ccbf997b1e44a7018480f78`, selected by the parent after BP22-D. Export and validation use only that commit's objects, including when the shared working tree advances later.

The organization `.github` profile was first cloned read-only at `7c1a100`; its introduction describes macOS 26 on x86 with older Nextcore casing. The parent subsequently delegated its update: name NextCore consistently, state Tahoe 26 and Golden Gate 27 architecture goals, link the seven published snapshots, distinguish demonstrated boot layers from remaining ARM/Metal work, and preserve existing upstream repository links.

## Observed release corrections

The first Windows post-clone byte comparison failed because Git checked text files out with native CRLF endings. No test started during those failed attempts. The corrected verification checks canonical committed Git-blob hashes and a clean normalized worktree, then runs tests against the actual clone. Both attempts are preserved. All seven Windows clone gates subsequently passed.

GitHub's standalone Linux Tool job then found a real export defect: `bundle_cli.rs` included a fixture from a sibling Core directory. The Windows validation had been contaminated by an adjacent module clone on a case-insensitive filesystem; its pass did not establish standalone portability. The failing `v0.1.1` tag remains immutable and is not reported as a successful Linux release.

The parent fixed the source by making the authored fixture crate-local in `045065700cbd037eaaa974faf957ba15cb628370`. Tool alone advances to `v0.1.2`; its Core/APLS dependencies remain at the verified `v0.1.1` tags. Verification now uses a Linux parent directory containing exactly one Tool clone before and after publication. The first diagnostic invocation lacked Cargo in the non-login WSL PATH; that failure is preserved, and the corrected process uses the observed existing `/home/developer/.cargo/bin` path without changing global settings.

A broad PowerShell removal of the release's completed target directories was rejected by automatic approval review before execution. The narrower, package-aware `cargo clean --profile dev --manifest-path ... --target-dir ...` succeeded for all 14 owned clone manifests, reclaiming about 5 GiB while preserving source, inventories and test logs. No generated EFI executable existed in these check-only targets.

## Completed release

All seven latest module snapshots passed fresh-clone gates and GitHub CI at the exact published main/tag commit. Existing history and all earlier tags remain intact.

| Module | Latest tag | Commit | Exact-head CI |
| --- | --- | --- | --- |
| [Nextcore-Core](https://github.com/26x86/Nextcore-Core) | [26x86-Nextcore-Core-v0.1.1](https://github.com/26x86/Nextcore-Core/tree/26x86-Nextcore-Core-v0.1.1) | [66eb698](https://github.com/26x86/Nextcore-Core/commit/66eb69888a9cb8bc56d05f9b2a0bbfab5abfd54b) | [success](https://github.com/26x86/Nextcore-Core/actions/runs/34195932526) |
| [Nextcore-GPU](https://github.com/26x86/Nextcore-GPU) | [26x86-Nextcore-GPU-v0.1.1](https://github.com/26x86/Nextcore-GPU/tree/26x86-Nextcore-GPU-v0.1.1) | [8962199](https://github.com/26x86/Nextcore-GPU/commit/8962199b5a7381850ef9aa9e72e98b45a8671d46) | [success](https://github.com/26x86/Nextcore-GPU/actions/runs/34195968754) |
| [Nextcore-HAL](https://github.com/26x86/Nextcore-HAL) | [26x86-Nextcore-HAL-v0.1.1](https://github.com/26x86/Nextcore-HAL/tree/26x86-Nextcore-HAL-v0.1.1) | [9c1cd8d](https://github.com/26x86/Nextcore-HAL/commit/9c1cd8dfff33478e32668c5cd181dd094ec2881b) | [success](https://github.com/26x86/Nextcore-HAL/actions/runs/34196005275) |
| [Nextcore-ISE](https://github.com/26x86/Nextcore-ISE) | [26x86-Nextcore-ISE-v0.1.1](https://github.com/26x86/Nextcore-ISE/tree/26x86-Nextcore-ISE-v0.1.1) | [e4c318f](https://github.com/26x86/Nextcore-ISE/commit/e4c318ff707ff57eaf128ffd66cc962a210ab8e1) | [success](https://github.com/26x86/Nextcore-ISE/actions/runs/34196016446) |
| [Nextcore-APLS](https://github.com/26x86/Nextcore-APLS) | [26x86-Nextcore-APLS-v0.1.1](https://github.com/26x86/Nextcore-APLS/tree/26x86-Nextcore-APLS-v0.1.1) | [f4d640e](https://github.com/26x86/Nextcore-APLS/commit/f4d640e362fbcf160994d833b330e16506de9110) | [success](https://github.com/26x86/Nextcore-APLS/actions/runs/34196180700) |
| [Nextcore-EFI](https://github.com/26x86/Nextcore-EFI) | [26x86-Nextcore-EFI-v0.1.1](https://github.com/26x86/Nextcore-EFI/tree/26x86-Nextcore-EFI-v0.1.1) | [c00f6fe](https://github.com/26x86/Nextcore-EFI/commit/c00f6fe6d6618f574ed193547837d675e6ca2da3) | [success](https://github.com/26x86/Nextcore-EFI/actions/runs/34196192640) |
| [Nextcore-Tool](https://github.com/26x86/Nextcore-Tool) | [26x86-Nextcore-Tool-v0.1.2](https://github.com/26x86/Nextcore-Tool/tree/26x86-Nextcore-Tool-v0.1.2) | [c536456](https://github.com/26x86/Nextcore-Tool/commit/c53645672d940290ed383b348e751c0a6e4e36c6) | [success](https://github.com/26x86/Nextcore-Tool/actions/runs/34197149715) |

Core passed 180 tests and its no_std check. GPU passed 94 default tests and 97 with Vulkan enabled; HAL passed 32 and ISE 26. APLS passed 49. EFI passed its all-feature x86_64 UEFI check. Counts are suite totals for the documented invocation, not proof of guest hardware execution. Tool’s corrected standalone Linux invocation and raw logs are preserved separately; its opt-in ignored test remains ignored.

The organization profile was independently reviewed and published at [4e446a4](https://github.com/26x86/.github/commit/4e446a4b7debc714ff2ec7ac6ead069bb2860618); GitHub API content readback confirmed the new NextCore logo, release links and explicit `metal_verified=false`. Latest development links follow main while module source references remain immutable.

The [release receipt](release-receipt.json) contains source commits, old/new heads, post-clone commands, remote CI URLs and the retained failed Tool v0.1.1 history. Gate logs, the corrected Linux receipts, public-file inventories, release helper sources and Cargo cleanup records accompany it. This release changed only fresh module clones and the explicitly delegated organization profile; the parent controlled the shared source, index and source-fixture fix.
