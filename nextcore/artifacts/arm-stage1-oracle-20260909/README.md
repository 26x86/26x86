# BP32 independent stage1 operation oracle

The default suite passes 428 authored actual AArch64 execution cases in QEMU, covering 4 KiB/16 KiB granules and EL0/EL1. Scalar64 and 32/64-bit pairs check A=1 alignment against translation, AF and AP faults. Pair cross-page cases use nonadjacent physical backing; failing second elements report the second VA. Fetch cases include valid, translation/AF/XN failures and the complete 64-case AP/PXN/UXN matrix. Exact ESR/FAR/ELR and saved origin mode/PAN/UAO/DAIF are checked. TTBR/TCR/SCTLR/MAIR readbacks and descriptor inputs are retained.

An actual compiled negative variant clears SCTLR.A for one valid misaligned load. That load completes instead of faulting; the verifier detects the changed exception behavior, not only the changed control marker. All other default cases remain matched. Original BP29 framework files are unchanged.

The separate optional 440-case run contains 12 PC-misalignment plus mapping-fault overlaps. QEMU 8.2.2 reports instruction abort first; the Arm manual specifies PC alignment first. Its report stays passed=false and its command returns 1. The other 428 cases still pass. These 12 comparisons are an explicit model limitation, not newly accepted architecture behavior.

## Reproduce

Use Linux/WSL with clang, ld.lld, qemu-system-aarch64 and Python 3. The script creates a new output directory and copies its exact inputs before compilation; use fresh output paths.

```sh
python3 probe_operations.py --output /tmp/stage1-accepted-new
# Expected exit 1: 12 known QEMU contradictions are kept as failures.
python3 probe_operations.py --include-known-qemu-pc-priority --output /tmp/stage1-pc-priority-new
```

`run4-accepted/report.json` records 428 passes and the actual negative control. `run5-pc-model-limit/report.json` records all 440 comparisons with 12 failures. Each result directory retains exact assembly/C/Python/linker inputs, generated expectations, original console logs, commands and ELF hashes. ELF/object outputs are generated locally and are not required in the public bundle.

## Source-backed findings

[Arm DDI0487B.a](https://cs140e.sergio.bz/docs/ARMv8-Reference-Manual.pdf) Table D4-34 (D4-2077/2078) and the actual fetch matrix agree: AP01 imposes privileged execute-never even with PXN0/WXN0; at EL0, UXN0 allows execution with AP00/AP10 despite no data-read permission. The reviewed canonical walker lacked both distinctions. CPU/root were notified to update its one permission implementation and cached metadata. No production source was edited by this review. [Arm's own staff explanation](https://community.arm.com/forums/f/architectures-and-processors-forum/53584/cortex-a-permission-fault-due-to-code-region-mapped-as-read-write/178834) independently identifies the privileged rule and newer specification statement IDs.

The same Arm manual D1.13.3 (D1-1827) gives PC alignment priority over instruction abort, and D4.7.3 (D4-2110/2111) gives non-memory-type alignment priority over translation/AF/permission. The 40 MB manual was read from a public university mirror and hashed; it is not redistributed in this bundle. Exact references and provenance are in contract.md and review-receipt.json.

This is an implementation oracle with synthetic inputs, not physical Arm, x86 EFI/native JIT, original macOS or Metal proof. Pair fault RAM/destination atomicity is a separate host/provider test; this oracle checks architectural fault metadata.
