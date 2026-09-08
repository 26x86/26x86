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
LLD and LLVM tools (`llvm-ar`, `llvm-objcopy`). On Ubuntu install
`clang lld llvm qemu-system-x86 ovmf`. The native ARM diagnostic additionally uses `aarch64-unknown-uefi`;
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
changes there, test them, publish the module branch and merge its verified PR
into main before merging the new gitlink in the parent. Parent commits contain module SHA updates, integration
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

## Execution and graphics scope

The target is ARM64e macOS 27 code running on an x86_64 machine entered through
EFI. The macOS-focused JIT/HAL is the product runtime; an outer QEMU/OVMF x86
machine supplies reproducible development firmware. WSL is the build host.

AMD, NVIDIA and Intel integrated GPUs are implementation targets. Current host
Vulkan readback evidence comes from an AMD RX6800XT. Neither vendor enumeration
nor that host result establishes NVIDIA/Intel hardware execution, an EFI GPU
driver or guest Metal support. Original-prefix diagnostics are also separate
from a usable macOS boot. Keep these outcomes explicit in milestone receipts.

## Scalar and MMU development checks

The ISE module implements the 13 unsigned-offset integer width/sign forms. Its
reference walker preserves exact stage-1 fault levels and typed backing failures.
The native JIT still rejects SCTLR.M; this interface is preparation for a checked
memory provider, not native MMU completion. Reproduce the authored CPU checks:

```bash
cargo test --manifest-path nextcore/crates/nextcore-ise/runtime/preos/Cargo.toml
python3 nextcore/crates/nextcore-ise/tools/probe_scalar_memory.py
python3 nextcore/crates/nextcore-ise/tools/mmu_fault_levels/probe_fault_levels.py \
  --output /path/to/new-mmu-at
python3 nextcore/crates/nextcore-ise/tools/mmu_fault_levels/probe_abort_levels.py \
  --output /path/to/new-mmu-abort
python3 nextcore/crates/nextcore-ise/tools/mmu_fault_levels/compare_current_walker.py \
  --runtime-checkout nextcore/crates/nextcore-ise \
  --at-report /path/to/new-mmu-at/report.json \
  --abort-report /path/to/new-mmu-abort/report.json --output /path/to/new-comparison
```

These independent AArch64 oracle commands additionally need `qemu-system-arm`.
The actual x86 EFI scalar harness and recorded boundary checks are under
`nextcore/artifacts/arm-scalar-memory-20260909`. It executes the same native C
JIT in OVMF and keeps original-image diagnostics separate from authored fixtures.

## Checked native memory service

There are still seven repositories and seven parent workspace members. ISE also
owns the allocation-free `nextcore-memory-service` package at
`runtime/memory-service`. Both EFI ISE dependencies use the same canonical Git URL
and immutable revision; the parent patches both package names to that submodule.
The ownership check includes feature-enabled host and UEFI Cargo resolution,
rejecting an auxiliary copy, remote duplicate or conflicting owner revision.

```bash
cargo build --locked --manifest-path nextcore/Cargo.toml -p nextcore-efi --release \
  --target x86_64-unknown-uefi --features arm-jit-memory-provider --bin NXARMJIT
python3 Tools/verify_nextcore_submodules.py --cargo --require-clean
```

This diagnostic feature routes fetch and integer memory through the Rust service;
it still rejects native SCTLR.M. Add `arm-jit-tiered-trace` only for explicit bounded
256/1024/4096 diagnostics and pass `--tiered-diagnostic` to the trace tool. The
ordinary trace keeps its 64/8 limits. The current integrated firmware runner is
`nextcore/tools/verify_arm_memory_provider_ovmf.py`; it checks actual callback
counters, precise failure state and a direct-execution negative control.

Normal macOS27 entry additionally needs the target-specific live SPTM/boot-argument
and runtime-device-tree contracts described in
[the entry audit](../NEXTCORE_ARM64E_ENTRY_CONTRACT.md). These remain incomplete.


### BP33 owned guest staging

Core147f4c4 retains exclusive guest backing, bounded purpose reservations and
source-bound DeviceTree commit. EFI7e7a08b supplies the opt-in NXDT consumer,
with actual nonidentity ARM loads/stores executed as x86 code. Tool4bb09da selects
the same Core source. These remain separate Git repositories and immutable
submodule pins; no Windows tester is added. Reproduction commands live in the
EFI module's docs/ARM_DT_LEDGER_EFI_PROBE.md. The parent runs the eight-case
firmware matrix and full capture rejection alongside existing stage1 checks.
This authored connection does not establish the macOS27 target handoff or Metal.

Core selects sha2 force-soft only for firmware targets after the actual debug
NXAPFS build exposed an LLVM x86-backend failure. Debug and release code generation
are explicit CI requirements; check-only compilation is insufficient.
