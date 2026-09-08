# Native x86 EFI pair-memory milestone

Sixteen authored EFI cases passed using ISE commit
`07cd3e19f397556fa6d233c562fb245bfe528363`. The fixture executes ARM instructions
in generated x86 code inside an x86 EFI application. QEMU provides the x86 test
computer and OVMF firmware; it does not execute the ARM guest instruction set.

`authored-results.json` records all sixteen cases. `provenance.json` identifies
the immutable runtime, historical Core/EFI revisions, binary digest and runtime
source hashes verified against the commit. `original-aggregate.json` contains
only a bounded original-prefix summary; no original image is part of this bundle.

| Authored suite | Cases | Verified behavior |
| --- | ---: | --- |
| Pair memory | 6 | Both widths and offset/pre/post modes; values and SP restored; original-SP alignment faults; precise UNDEFINED syndrome for writeback overlap |
| Platform/vector | 8 | Explicit software provider state, masks, pending IRQ/FIQ levels, saved state and vector entry |
| ARM/PAC/GOP | 2 | Boot argument readback, ARM64e PAC authentication, actual GOP readback of sixteen pixels |

The successful pair path retired 48 instructions in twelve native blocks.
Store/load SP faults each retired seven instructions before status19 with exact
syndrome and no writeback. The invalid writeback fixture retired four before
status8 with ESR zero. Review found that MMU-off data uses Device memory, which
requires element alignment even when SCTLR.A is clear. The corrected runtime
adds that check. Two additional authored cases verify A=0 misaligned X-store
and W-load faults, exact read/write ESR, preserved full-width destinations and
base, unchanged SP and precise retirement.

The EFI v2 result exposes ESR, registers, SP and retirement; these are the
actual EFI assertions. It does not expose FAR or post-fault RAM bytes. FAR and
absence of partial RAM mutation are checked by the separate native C/reference
runtime proofs, not inferred from the EFI receipt. The pinned ISE
[pair-memory contract](https://github.com/26x86/Nextcore-ISE/blob/07cd3e19f397556fa6d233c562fb245bfe528363/docs/AARCH64_PAIR_MEMORY.md)
documents those host/oracle checks. Vector tests stop after committing exception entry and
do not execute a guest handler. GOP readback is not a Metal result.

## Reproduce after parent integration

Use an x86_64 Linux/WSL environment with Rust's `x86_64-unknown-uefi` target,
Clang, LLVM tools (`llvm-ar`, `llvm-nm`, `llvm-objcopy`), LLD, Python3,
`qemu-system-x86_64`, and the distribution OVMF firmware files. Initialize the
parent repository's submodules recursively. The ISE checkout must be the exact
revision above; the runner rejects changed runtime source bytes.

From the repository root, choose a new persistent output directory:

```sh
python3 nextcore/artifacts/arm-pair-memory-20260909/reproduce.py \
  --repo . --output "$HOME/nextcore-evidence/bp28-replay"
```

The default runtime source is `nextcore/crates/nextcore-ise/runtime`, passed via
the existing `NEXTCORE_PREOS_RUNTIME` build hook. The runner builds NXARMJIT with
`arm-jit-probe,arm-jit-trace`, then runs all sixteen cases. Per-suite logs,
authored images, exact local commands and fresh receipts remain in the selected
output directory. No OS image is needed or executed. Output directories must
not already exist, preserving earlier evidence.

To run just the pair fixture against a separately built EFI binary:

```sh
python3 nextcore/artifacts/arm-pair-memory-20260909/verify_pair_ovmf.py \
  --tools nextcore/tools --efi /path/to/NXARMJIT.efi \
  --output "$HOME/nextcore-evidence/bp28-pair"
```

`reproduce.py --runtime-checkout /path/to/Nextcore-ISE` permits the same immutable
source in an isolated checkout. `--efi /path/to/NXARMJIT.efi` skips compilation
only for the recorded historical binary, whose SHA256 is checked. A fresh
build can have a different digest because of paths/toolchain/metadata; its
behavior must pass the same checks and its new digest is recorded.

## Original diagnostic limits and next work

The explicitly incomplete original diagnostic progressed from 26 to **47
retired instructions in ten native blocks**, bounded by a 64-instruction budget.
Independent source matching identified the next generic boundary as an integer
unsigned-immediate 32-bit load. Original bytes and source/binary inputs were
preserved. Detailed original traces and coordinates are not distributed here.

This still lacks SPTM arguments/services, a resolved original runtime device
tree and native MMU execution. The selected platform state is software-defined,
not measured Apple reset state. Neither normal macOS boot nor stable use nor
Metal acceleration is verified. `next-boot-slice.md` describes a concrete,
independently testable address-space slice while keeping the exact M1 handoff
and macOS27 SPTM ABI unresolved.
