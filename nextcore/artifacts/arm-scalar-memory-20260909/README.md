# Scalar integer memory in x86 EFI

Frozen ISE `8b09f8764f13838baf71c1676575cb829bcd7902` executed all11 authored
cases in x86 OVMF. Four readback cases cover13 integer width/sign forms, W-write
upper-bit clearing, nonzero scaled offsets, SP bases, ZR and base/destination
overlap. Device A=0 load/store faults report ESR0x96000021/0x96000061; SP load/
store faults report0x9a000000. SIMD, reserved and PRFM forms stop as unsupported
without retiring the faulting instruction. See authored-results.json and serial/.

The deliberate sign control changes only LDRSB X1 to LDRB W1. Its actual EFI
execution returns129 instead of-127 in X1, and only the x1_value check fails
(exit1). negative-control.json preserves this expected failure. The positive
cases execute128 instructions across21 native x86 blocks; see each receipt for
individual counts. Original results retain absolute paths as historical context.

QEMU models the x86 computer and OVMF; ARM instructions run in the EFI binary's
native x86 JIT. This is not a physical-machine EFI or macOS boot test. The
existing diagnostic exposes X0-X3, SP, status, PC, retirement, blocks and ESR.
It does not expose FAR or post-fault RAM; their correctness remains a separate
native/reference proof. No Apple image or original-image prefix is involved.

## Reproduce

Provide an isolated ISE checkout of the recorded revision; for example use
`git -C /path/to/26x86/nextcore/crates/nextcore-ise worktree add --detach
/path/to/scalar-runtime 8b09f8764f13838baf71c1676575cb829bcd7902`.
Install a Rust toolchain with x86_64-unknown-uefi std, Clang/LLVM tools,
qemu-system-x86 and OVMF. The recorded compiler versions are in provenance.json.

```sh
python3 reproduce.py --repo /path/to/26x86 \
  --runtime-checkout /path/to/scalar-runtime --output /path/to/new-proof
```

This builds the existing root EFI with an explicit NEXTCORE_PREOS_RUNTIME
source override and a fresh persistent CARGO_TARGET_DIR. It does not edit the
root or ISE pins. `--offline` uses the local Cargo dependency cache. `--efi`
can instead reuse the historical EFI after checking its recorded SHA256.
The rebuild reports its own binary hash; paths/toolchain/source updates may
produce a different hash, which is not silently represented as the old binary.
The runtime revision and complete tracked runtime file hashes must match.

The source assembly, expected values, per-case commands, LLVM disassembly and
serial/JSON evidence are regenerated. The wrapper requires all11 positives and
exactly the intended X1 negative rejection. Runtime source hashes are checked
before and after. Generated ESPs and firmware copies stay in the output folder
and are excluded from this public source/evidence bundle.

The public reproduce.py was itself executed with the recorded EFI: all11
positives passed again and the sign control was rejected. replay-results.json
records that run. combined-linked-source-equivalence.json independently checks
the12 linked runtime C/header/PAUTH/platform inputs against later combined ISE
33fea9f; every input is identical. This is source equivalence, not a new
combined-revision EFI binary execution claim.
