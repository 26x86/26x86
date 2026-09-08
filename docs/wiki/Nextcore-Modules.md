# Nextcore module repositories

Nextcore is split into **seven module repositories** under the `26x86` GitHub
organization. This repository references them as **git submodules** so module
source has a single home and is never staged twice.

## Module map

| Module (submodule path) | Repository | Crate | Responsibility |
| --- | --- | --- | --- |
| `nextcore/crates/nextcore-core` | [Nextcore-Core][core] | `nextcore-core` | Configuration, public format codecs, handoff contracts |
| `nextcore/crates/nextcore-efi` | [Nextcore-EFI][efi] | `nextcore-efi` | EFI application and controlled XNU handoff probes |
| `nextcore/crates/nextcore-tool` | [Nextcore-Tool][tool] | `nextcore-tool` | Reproducible command-line orchestration |
| `nextcore/crates/nextcore-ise` | [Nextcore-ISE][ise] | `nextcore-ise` | Instruction-set emulation and CPU feature policy |
| `nextcore/crates/nextcore-gpu` | [Nextcore-GPU][gpu] | `nextcore-gpu` | GPU compatibility policy and virtual-device contracts |
| `nextcore/crates/nextcore-hal` | [Nextcore-HAL][hal] | `nextcore-hal` | ACPI, PCI, SMBIOS and DeviceTree translation |
| `nextcore/crates/nextcore-apls` | [Nextcore-APLS][apls] | `nextcore-apls` | AArch64 VMApple recovery runner and guest ABI |

[core]: https://github.com/26x86/Nextcore-Core
[efi]: https://github.com/26x86/Nextcore-EFI
[tool]: https://github.com/26x86/Nextcore-Tool
[ise]: https://github.com/26x86/Nextcore-ISE
[gpu]: https://github.com/26x86/Nextcore-GPU
[hal]: https://github.com/26x86/Nextcore-HAL
[apls]: https://github.com/26x86/Nextcore-APLS

## Workflow

The superproject `nextcore/` remains a Cargo **workspace** root
([`nextcore/Cargo.toml`](https://github.com/26x86/26x86/blob/main/nextcore/Cargo.toml));
its members are the seven checked-out submodules.

The exported module manifests are **standalone**: cross-crate references are git
dependencies pinned to the module's initial tag (for example
`nextcore-core = { git = "…/Nextcore-Core.git", tag = "26x86-Nextcore-Core-v0.1.0" }`).
For the superproject workspace to build against the **local** submodule
checkouts instead of re-fetching GitHub, the workspace root carries `[patch]`
entries that redirect those git sources back to the checked-out paths:

```toml
[patch."https://github.com/26x86/Nextcore-Core.git"]
nextcore-core = { path = "crates/nextcore-core" }

[patch."https://github.com/26x86/Nextcore-GPU.git"]
nextcore-gpu = { path = "crates/nextcore-gpu" }

[patch."https://github.com/26x86/Nextcore-APLS.git"]
nextcore-apls = { path = "crates/nextcore-apls" }
```

```bash
# First clone
git clone --recurse-submodules https://github.com/26x86/26x86.git
cd 26x86/nextcore
cargo test --workspace

# Later sync
git pull
git submodule update --init --recursive
```

## Publishing a module

Export + publish + convert is scripted in
[`Tools/publish_nextcore_modules.sh`](https://github.com/26x86/26x86/blob/main/Tools/publish_nextcore_modules.sh),
which reuses `Tools/export_nextcore_repositories.py`. It builds each module repo
(own `main`, initial tag, git dependencies), pushes it, and — only with
`--convert-submodules` — replaces the tracked crate directories with submodules.

```bash
# 1) export and publish the seven module repositories
bash Tools/publish_nextcore_modules.sh --output /tmp/nx-modules --yes

# 2) after inventory review, convert this repository's crate dirs
bash Tools/publish_nextcore_modules.sh --output /tmp/nx-modules --yes --convert-submodules
```

The conversion stages `.gitmodules`, the gitlinks, and the `[patch]` manifest on
the current branch — never a commit on `main` directly.

## Changing module code

1. Edit inside the submodule (its own repository).
2. Commit **and push** to the module repository's `main` on its own PR review
   there — or for this repo's PR, bump the checked-out commit to the reviewed
   revision.
3. In this repository, the change is a **gitlink update** only. Stage it with
   `git add nextcore/crates/<module>` and include it in the PR description.

!!! warning "Staging hygiene"

    Module directories are submodules. Never add their *contents*
    (`git add nextcore/crates/<module>/src/...`). If `git status` ever shows
    module files as regular changes instead of a single gitlink, the submodule's
    `.git` wiring is missing — re-run `git submodule update --init` first.

## Boundary rules (unchanged)

- `_isolated/` reverse-engineering material is **not** part of any module
  repository and is excluded by `.gitignore` and the pre-commit guard.
- Every module exports an independent `main`, but widening the *module boundary*
  never widens a *boot claim*: an observation still advances only the layer it
  measures.