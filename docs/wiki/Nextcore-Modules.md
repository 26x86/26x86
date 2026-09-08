# NextCore module repositories

NextCore uses seven Git submodules. Each module owns its source and history;
the integration repository records exact commits and the workspace build.

| Submodule | Repository | Responsibility |
| --- | --- | --- |
| nextcore-core | [Core](https://github.com/26x86/Nextcore-Core) | Public formats, boot configuration, kernel placement |
| nextcore-efi | [EFI](https://github.com/26x86/Nextcore-EFI) | Firmware picker and architecture-specific handoff |
| nextcore-tool | [Tool](https://github.com/26x86/Nextcore-Tool) | Command-line orchestration |
| nextcore-ise | [ISE](https://github.com/26x86/Nextcore-ISE) | ARM64e-to-x86 JIT, PAC, freestanding runtime and instruction policy |
| nextcore-gpu | [GPU](https://github.com/26x86/Nextcore-GPU) | GPU command dispatch, rendering and Vulkan compute |
| nextcore-hal | [HAL](https://github.com/26x86/Nextcore-HAL) | Platform table and device translation |
| nextcore-apls | [APLS](https://github.com/26x86/Nextcore-APLS) | ARM recovery execution and guest ABI |

## Clone and build

```bash
git clone --recurse-submodules https://github.com/26x86/26x86.git
cd 26x86
# Also run after switching integration branches or pulling new gitlinks:
git submodule sync --recursive
git submodule update --init --recursive
python3 Tools/verify_nextcore_submodules.py
cargo test --manifest-path nextcore/Cargo.toml --workspace
python3 Tools/verify_nextcore_submodules.py --cargo --require-clean
```

Run these commands inside WSL2 on Windows. Keep build directories on its Linux
filesystem. The product build needs Rust's `x86_64-unknown-uefi` target, Clang
and LLD. The native ARM diagnostic additionally uses `aarch64-unknown-uefi`;
it is not the product execution path. QEMU/OVMF runs the development firmware
checks on an x86 machine.

```bash
rustup target add x86_64-unknown-uefi
cargo build --manifest-path nextcore/Cargo.toml -p nextcore-efi --release \
  --target x86_64-unknown-uefi --features arm-jit --bin NXARMJIT
python3 nextcore/tools/verify_arm_jit_ovmf.py --help
```

`NXARMJIT.efi` contains the ARM64e JIT and PAC provider. Default execution stages
validated inputs and reports missing providers. The `arm-jit-probe` build opts
into authored execution fixtures; it does not enable original macOS boot.

## Develop and integrate

Create a development branch inside the module before editing. Commit module
changes there, test them, and publish the module branch before recording its new
gitlink in the parent. Parent commits contain module SHA updates, integration
tools and documentation; they do not contain copied crate sources.

```bash
git -C nextcore/crates/nextcore-core switch -c codex/my-change
# Edit, validate, and commit inside that module.
git -C nextcore/crates/nextcore-core push -u origin codex/my-change
git add nextcore/crates/nextcore-core
python3 Tools/verify_nextcore_submodules.py --cargo --require-clean
# Commit the integration change, then publish its branch.
git push --recurse-submodules=check origin HEAD
```

A gitlink is the source of truth. Do not use `git submodule update --remote` in
reproducible builds. It substitutes branch tips for the reviewed commits.

Standalone module manifests pin remote dependencies to immutable commits.
The parent Cargo workspace has explicit patches for every module URL, so tests
and firmware builds use the seven local checkouts without duplicate remote
NextCore packages. Update a dependent module's remote revision when its required
API changes; standalone builds must pass without the parent workspace patches.

## Validation and publication

CI initializes submodules recursively, checks gitlink ownership and Cargo
resolution, runs workspace tests, and checks firmware targets. Validate a new
integration commit from a fresh recursive clone before delivery.

The former exporter is retained for separate source exports, not for module
publication. Do not reinitialize published module histories or recreate existing
release tags. The publication helper checks submodule cleanliness and remote
reachability before allowing the parent branch push.

Only public source belongs in modules. Original restore inputs and runtime
material remain under the parent's ignored `_isolated/` directory. Synthetic
firmware and host GPU tests establish their own layers; original XNU, userspace
and guest Metal each require actual execution evidence.
