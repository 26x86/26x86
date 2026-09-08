# x86 EFI ARM64e JIT handoff results — 2026-09-08

The primary executable is `NXARMJIT.efi`, an x86 EFI application which stages
ARM images into separate guest RAM and executes generated x86 instructions.
WSL2 is the development environment. QEMU/OVMF models the x86 test computer;
there is no external ARM emulator in this EFI execution path.

## Verified behavior

- `ovmf-final/report.json`: all nine firmware cases passed. The authored ARM64
  payload retired 25 instructions in one native block. The ARM64e payload
  retired 45 instructions across seven native blocks, with actual QARMA5 PAC
  signing/authentication through the shared Rust primitive and native C JIT.
  Both read their staged boot arguments, wrote guest pixels, presented through
  GOP, and verified sixteen RGB pixels through GOP readback.
- The other seven cases covered production gating, ARM64e immutable staging,
  missing PAC fixture identification, missing marker, malformed image, Intel
  profile separation and corrupted guest readback. Failed conditions did not
  produce a successful handoff marker.
- `sptm-prefix-final/report.json`: all three firmware cases passed. Explicit
  cold registers reached a six-instruction authored payload in two native
  blocks and read the boot-argument header through x1. A budget of one stopped
  after exactly one retired instruction. The default binary staged the image
  without entering the feature-gated trace path.
- Eight Core parser/placement tests passed; Core also passed a no-default-
  features check. The tests include VA/PA correspondence, 16 KiB placement,
  insufficient RAM, staged-byte/readback corruption, trace ABI/budget rejection
  and preservation of the existing Intel configuration gate.
- `NXARMJIT` release builds passed with the diagnostic features enabled and
  disabled. The secondary `BOOTAA64` release build passed for
  aarch64-unknown-uefi; that secondary binary was not executed in firmware.

## Original input observation

The unchanged original macOS 27/M1 kernel collection (121,864,192 bytes,
342 members) passed host staging and full readback. An explicit diagnostic
then loaded and staged the same original image inside x86 OVMF EFI. Generated
x86 code retired four original instructions in three native blocks before
stopping on an unsupported TPIDR_EL0 system-register write. Independent private
inspection matched the saved fault to the unchanged source and confirmed that
the prefix did not dereference its argument pointers. Input and ESP-copy
SHA-256 values remained unchanged; the firmware run took 31.118 seconds.

This diagnostic used `HandoffAbi=unprovisioned-sptm-prefix`: x0 was the cold
sentinel, x1 was the staged boot-argument address, and x2/x3 were zero. No SPTM
arguments, SPTM services, authentication or runtime M1 device tree were provided.
An explicitly authored DRAM-only diagnostic tree was supplied. The original
firmware device-tree template was preserved, including unresolved template
properties. Actual original execution addresses, instruction words, input
hashes and serial logs remain under `_isolated/macos27-j274`; no Apple bytes
are included in these public artifacts.

This is an early executable entry-prefix result, **not a macOS boot result**.
GOP pixel transport is **not Metal acceleration**. Those outcome fields remain
false throughout every receipt.

## Reproduction

From the repository root, with Rust UEFI targets, clang/LLVM, QEMU and OVMF:

```sh
CARGO_TARGET_DIR=/tmp/nxc-proof cargo build --manifest-path nextcore/Cargo.toml \
  -p nextcore-efi --bin NXARMJIT --target x86_64-unknown-uefi --release \
  --features arm-jit-probe,arm-jit-trace
CARGO_TARGET_DIR=/tmp/nxc-default cargo build --manifest-path nextcore/Cargo.toml \
  -p nextcore-efi --bin NXARMJIT --target x86_64-unknown-uefi --release \
  --features arm-jit
python3 nextcore/tools/verify_arm_jit_ovmf.py \
  --efi-probe /tmp/nxc-proof/x86_64-unknown-uefi/release/NXARMJIT.efi \
  --efi-default /tmp/nxc-default/x86_64-unknown-uefi/release/NXARMJIT.efi \
  --output /tmp/nxc-nine-cases
python3 nextcore/tools/verify_arm_sptm_prefix_ovmf.py \
  --efi-trace /tmp/nxc-proof/x86_64-unknown-uefi/release/NXARMJIT.efi \
  --efi-default /tmp/nxc-default/x86_64-unknown-uefi/release/NXARMJIT.efi \
  --output /tmp/nxc-prefix-cases
```

For local original-input reproduction, the exact argument array is retained in
`_isolated/macos27-j274/trace-command.private.json`. The general tool is
`nextcore/tools/trace_arm_jit_ovmf.py`; it requires explicit guest placement,
diagnostic DT, and opt-in to the incomplete SPTM prefix. Its budget is 1..8.

Receipts preserve the tested binary hashes and original temporary paths.
They precede the subsequent result-reporting-only C fix that clears stale
`fault_instruction` on non-fault returns. HALT/BUDGET status and retirement
counts in these historical receipts remain valid. An initial feature-gate
test used an older default binary which did not yet recognize the trace
profile; rebuilding the default from the same source produced the passing
three-case result above. No negative gate was relaxed.
