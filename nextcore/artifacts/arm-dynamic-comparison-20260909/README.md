# Captured Arm enable transitions through the native dynamic memory provider

Six recorded Arm cases pass against the frozen BP34 native C JIT and canonical Rust dynamic memory service on Linux x86_64. The two normal transitions reproduce the guaranteed post-ISB control, instruction-address, load, store and readback effects before the original terminal HVC. The four missing-page cases reproduce the actual Arm translation fault ESR/FAR/ELR/SPSR. Thirteen comparator regression tests pass, including a changed expected ESR negative control.

This is a comparison with the existing six-case QEMU AArch64 capture, not a new physical Arm execution. The original oracle bundle is an immutable external input: manifest SHA256 29ccd46ff85dd9da2f8ee8023f86362bfb469e461b04a26d4a07bb7ae0b990cc. Runtime freeze SHA256 is 72f5e7e58ad42c1428cbced6c261d37783061c13b45639a465faada7d51dc7d3; all 69 runtime files are checked before and after execution.

## Compared boundaries

| Case, for both 4 KiB and 16 KiB | Comparison | Native retired / fetch / data / completed |
| --- | --- | --- |
| Successful enable | SCTLR, post-ISB PC, loaded seed, stored readback, marker, RAM effect, A/E state | 12 / 13 / 3 / 3 |
| Absent next code page | ESR 0x86000007; FAR and ELR at the immediate post-ISB code VA | 2 / 3 / 0 / 0 |
| Absent data page | ESR 0x96000007; FAR 0x60000000; ELR code VA + 8 | 4 / 5 / 1 / 0 |

The exact original HVC #0x34 word remains at code VA + 40. Arm executes this instruction to return to the EL2 test controller. The native runtime does not implement that dispatch: it stops at status 8, undefined instruction, without retiring HVC. Its ELR at HVC and SPSR 0x3c5 are separately checked as native diagnostic bookkeeping. They are not claimed to match the Arm HVC-to-EL2 completion state or to implement architectural HVC behavior.

The preserved initial run1 guessed that this unsupported boundary would be status 13 with empty native ELR/SPSR. That adapter assumption failed in the two normal cases; every post-ISB effect and all four faults already matched. Canonical C classification and execution establish status 8 and its exception-bank bookkeeping. The final comparison qualifies those fields separately. No runtime, original capture, mapping, expected Arm effect or opcode was changed. History files retain the unsuccessful initial receipt and the exact adapter/source used for it.

## Inputs and adaptations

All used table-page physical addresses and nonzero descriptors come directly from the capture. The rest of the 512 KiB table allocation is reconstructed as zero because the authored controller explicitly zeroes the entire allocation. Transition/target/decoy instruction bytes come from the bound original ELF and are copied to their original guest physical locations. The 64 KiB transition, target and data backing is reconstructed using the original controller's explicit zero initialization and captured seed/canary. Full native RAM is checked against those source-based expectations; only the two data words were directly sampled by the Arm controller.

The initial EL1 SCTLR, TTBR0, TTBR1, TCR and MAIR values are retained. Captured HCR must be exactly RW-only 0x80000000 before it can be adapted to the service's inactive EL2 value zero. VM, TGE and every other HCR bit must already be zero. Uncaptured SCR is explicitly inactive zero. Consequently the complete service control record is an adapted profile, not a byte-exact copy of a captured original 80-byte record.

PSTATE 0x3c5 is retained without masking. The original ERET entry establishes it; the payload does not alter flags or PSTATE and the saved state agrees. The original ELF SP_EL1 symbol is used; the payload never accesses the stack. The native run starts at the authored EL1 transition rather than executing the EL2 setup or handlers. Initial x0-x3 are reconstructed from the entry source; x10-x14 start at zero and are the captured result witnesses. Other unobserved caller registers are reset to zero without equality claims.

The external C observer only initializes state, calls the actual vf_run_memory_provider_dynamic entry, and records final CPU state. The Rust adapter constructs the canonical exclusive RAM/table owner and forwards callbacks to its actual exports. Real generated x86 code executes from a separately allocated buffer using write/execute protection changes. This exercises the direct native dynamic entry; the EFI boot wrapper and Win64 callback ABI are outside this comparison.

## Reproduce

Requirements: Linux x86_64, Python 3, Clang, and Rust supporting edition 2021. The recorded run used Rust 1.98.1 and Clang 18. Keep this bundle's top-level source files together, provide the original Arm oracle bundle and a runtime matching all 69 frozen hashes, and choose a fresh output directory:

    python3 -B /path/to/comparison/compare.py --oracle /path/to/arm-enable-oracle --runtime /path/to/ISE/runtime --output /path/to/fresh-comparison --rustc /path/to/rustc
    python3 -B /path/to/comparison/test_compare.py --oracle /path/to/arm-enable-oracle --evidence /path/to/fresh-comparison

The script fails on any source/input identity mismatch, compiler/execution error, missing or duplicate native result, different result boundary, changed observation, or undetected syndrome negative. Output contains the generated inputs, compiler commands, actual native output, callback events, source hashes, reconstructed RAM/tables and final receipt. Compiled object files, Rust library and native executable are retained by each execution but excluded from this public bundle; the executable hash and exact compile commands are retained.

The recorded evidence directory contains final run2 outputs. Historical command paths are provenance, not paths required by the portable top-level replay. Use the arguments above after relocation; do not execute a historical expanded adapter or generated cases.rs directly.

The mapping-omission and enable-omission negatives belonging to the Arm oracle remain in that separate immutable bundle. This comparison uses its six ordinary captures and independently detects a changed expected syndrome. The 13 local tests mutate copies only and also reject false success/status13, retiring HVC, changed PC/opcode/witness/backing, missing callbacks/compiled blocks, and missing native unsupported bookkeeping.

The comparison does not assert deterministic visibility before the first ISB. Immutable-table hardware observations do not establish actual hardware TLB eviction or refill. Service table-read counts and invalidation counts are separate software evidence. This bundle does not verify EFI execution, physical Arm hardware, an original OS image, stable macOS boot or guest Metal.
