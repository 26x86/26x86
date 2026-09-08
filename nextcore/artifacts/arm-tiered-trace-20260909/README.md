# Explicit tiered EFI diagnostic budget

The default parser still permits at most 64 instructions with an explicit
platform profile, or 8 without one. A separate Core entry accepts a caller's
explicit ceiling of 64, 256, 1024 or 4096. Budgets above 64 must themselves be
one of the 256/1024/4096 tiers. EFI selects the larger ceiling only with the
`arm-jit-tiered-trace` build feature. The host tool additionally requires
`--tiered-diagnostic` and verifies the firmware's extended-diagnostic marker.

Twenty-four Core configuration tests passed, including four new tests covering
ceilings, unsupported tiers, the unchanged absent-provider limit and retained
handoff/platform/memory validation. The authored harness checks six CLI
rejections and two actual x86 OVMF cases. The extended EFI runs an independent
ARM loop for exactly 256 retired instructions and reads back its expected
register state; the default EFI rejects that same budget before guest entry.
QEMU supplies an x86 computer and OVMF. The EFI application executes translated
ARM instructions as generated native x86 code.

`authored-results.json` contains the runnable harness's final results.
`provenance.json` records the base Core/EFI revisions, changed source digests,
patch digests and both historical EFI binary hashes. Those binaries include
the recorded uncommitted source changes; they are not represented as binaries
of the unchanged base revisions. Final module pins belong to the integrator.
The ISE execution runtime was immutable commit
`8b09f8764f13838baf71c1676575cb829bcd7902` throughout this diagnostic.

## Reproduce after integration

Use an x86_64 Linux/WSL environment with Rust's `x86_64-unknown-uefi` target,
Clang, LLVM tools, LLD, Python 3, `qemu-system-x86_64` and OVMF. Initialize the
parent's submodules recursively. Integrate the Core/EFI changes and the small
`trace-tool.patch` first. The complete proposed trace tool is also supplied
for review; it contains no original image, bytes or coordinates.

Set `RUNTIME` to a clean local Nextcore-ISE checkout at the immutable revision
above. Run from the parent repository root, with a fresh output directory:

```sh
OUT="$HOME/nextcore-evidence/bp30-tiered"
RUNTIME=/path/to/Nextcore-ISE
test "$(git -C "$RUNTIME" rev-parse HEAD)" = \
  8b09f8764f13838baf71c1676575cb829bcd7902
mkdir -p "$OUT/bin"
export CARGO_TARGET_DIR="$OUT/target"
export NEXTCORE_PREOS_RUNTIME="$RUNTIME/runtime"
cargo build --locked --release --manifest-path nextcore/Cargo.toml \
  -p nextcore-efi --bin NXARMJIT --target x86_64-unknown-uefi \
  --features arm-jit-tiered-trace
cp "$OUT/target/x86_64-unknown-uefi/release/NXARMJIT.efi" \
  "$OUT/bin/NXARMJIT-tiered.efi"
cargo build --locked --release --manifest-path nextcore/Cargo.toml \
  -p nextcore-efi --bin NXARMJIT --target x86_64-unknown-uefi \
  --features arm-jit-probe,arm-jit-trace
cp "$OUT/target/x86_64-unknown-uefi/release/NXARMJIT.efi" \
  "$OUT/bin/NXARMJIT-default.efi"
python3 nextcore/artifacts/arm-tiered-trace-20260909/verify_tiered_budget_ovmf.py \
  --tools nextcore/tools --efi "$OUT/bin/NXARMJIT-tiered.efi" \
  --default-efi "$OUT/bin/NXARMJIT-default.efi" --output "$OUT/authored"
```

The final harness rejects an existing output directory and records fresh
binary/source hashes. Path, toolchain and integration metadata can change
binary hashes; newly built artifacts must pass the same behavior checks.
The fixture contains three independent instructions and uses no OS asset.

## Original diagnostic result and limits

The previous original-input checkpoint reached its 64-instruction budget.
After the authored test passed, the unchanged original input was run with an
explicit budget of 256. It stopped at a standard 64-bit conditional-compare
register instruction after **98 retired instructions in 14 native blocks**.
The runtime returned status 8 with an actual saved instruction. Because this
was not a budget result, the 1024 and 4096 tiers were not executed.
`original-aggregate.json` publishes counters, method and limits only.

Exact original commands, coordinates, bytes, detailed traces and independent
source matching remain private. Original input hashes, ESP copies and compiled
source/binary hashes were unchanged across the run. The software interrupt
profile uses explicitly defined compatibility state, not a measured Apple
reset. The diagnostic still lacks complete SPTM arguments/services and a
resolved original runtime device tree; it does not establish native MMU
integration, normal macOS boot or Metal acceleration. A larger instruction
budget does not supply any of those prerequisites.

Publication correction: the reproduction command now names the actual parent
artifact directory. Only this README and its file-index digest changed; the
historical source, provenance and execution receipts are unchanged.
