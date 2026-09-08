# NextCore module repositories

NextCore has seven tracked Cargo workspace crates and seven independent release
repositories in the `26x86` organization. The workspace is the source of reviewed
exports. These directories are regular tracked source, not Git submodules.

## Module map

| Workspace crate | Repository | Responsibility |
| --- | --- | --- |
| `nextcore-core` | [NextCore Core](https://github.com/26x86/Nextcore-Core) | Configuration, picker view, public formats and kernel preparation |
| `nextcore-efi` | [NextCore EFI](https://github.com/26x86/Nextcore-EFI) | Firmware picker, providers and controlled handoff probes |
| `nextcore-tool` | [NextCore Tool](https://github.com/26x86/Nextcore-Tool) | Command-line orchestration |
| `nextcore-ise` | [NextCore ISE](https://github.com/26x86/Nextcore-ISE) | Instruction emulation and CPU feature policy |
| `nextcore-gpu` | [NextCore GPU](https://github.com/26x86/Nextcore-GPU) | GPU contracts, software rendering and optional Vulkan compute |
| `nextcore-hal` | [NextCore HAL](https://github.com/26x86/Nextcore-HAL) | ACPI, PCI, SMBIOS and device-tree translation |
| `nextcore-apls` | [NextCore APLS](https://github.com/26x86/Nextcore-APLS) | ARM VMApple recovery runner and guest ABI |

Repository URLs preserve their existing spelling. Product branding is NextCore.

## Develop in the workspace

```bash
git clone https://github.com/26x86/26x86.git
cd 26x86/nextcore
cargo test --workspace
```

The workspace manifests use local path dependencies. Commit changes to the
relevant files under `nextcore/crates/` and include their validation in a PR.
No submodule update or gitlink operation is needed for this layout.

## Independent releases

An export records its exact source commit in `repository.json` and its public
file hashes in `repository-files.json`. Cross-crate dependencies are rewritten
to immutable release tags. Core, GPU, HAL and ISE are leaves; APLS follows GPU,
EFI follows Core, and Tool follows Core and APLS.

For an existing repository, prepare a fresh clone of its current `main`, copy
only the selected commit's public crate files, update the release metadata and
dependency tags, then create a normal descendant commit and a previously unused
tag. Validate and publish leaves before dependents. Verify the remote identities
and repeat each gate from a separate fresh clone:

- Ordinary modules: `cargo test --all-targets`.
- Core: also check `--no-default-features`.
- GPU's optional backend: also check the `vulkan` feature.
- EFI: install `x86_64-unknown-uefi` and run
  `cargo check --target x86_64-unknown-uefi`.

The original exporter initializes new repository histories and fixed v0.1.0
tags. It is for first exports; it must not overwrite existing module history or
tags during incremental updates. Optional submodule-conversion tooling describes
a possible future layout and has not been applied to this workspace.

## Evidence boundary

Only public crate source belongs in module exports. `_isolated/`, runtime
artifacts, target directories, firmware and operating-system images are excluded.
Passing a module gate proves its tested layer. It does not establish original
kernel execution, a complete native HAL or guest Metal acceleration. See
[current validation](https://github.com/26x86/26x86/blob/main/nextcore/VALIDATION.md).
