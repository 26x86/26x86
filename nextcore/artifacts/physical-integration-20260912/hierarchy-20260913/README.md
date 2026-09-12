# Authored hierarchy validation — 2026-09-13

This package records authored stage-1 hierarchical permission tests. It contains no original macOS input, downloaded Apple material, firmware images, compiled executables, or firmware variable stores. Actual Arm execution below means QEMU TCG emulating Arm, not physical Arm hardware. Physical startup, macOS startup, and desktop output remain unverified by this package. MMFR1 feature advertisement is not implemented or established here.

## Evidence layers

- Linux x86 native execution through the canonical immutable memory provider: 34 tests in each cached, uncached, and small-slot mode; Rust reference: 104 tests. Two compiled semantic mutants are rejected. Exposed native results and ordered data requests agree across modes; expected RAM is asserted exactly. This is not a full private CPU/reply snapshot claim.
- QEMU TCG Arm r10: 306 authored page-permission cases. The canonical service's recorded replies directly agree with 258 AP/XN/ancestor cases on success and precise fault ESR. The remaining split-ancestor/fault-priority cases are separately covered, not claimed to be directly joined. Different CPU models, guest addresses, physical memory layouts, and feature registers are not equated.
- OVMF x86 EFI: 961 ordered authored native fetch/load/store cases. A separately built old runtime rejects the first admitted hierarchy case. This is firmware execution evidence, not physical hardware or macOS boot.
- Nearest stage-1 and ASID regressions, old native runtime rejection, and paired EFI build source/binary hashes are preserved separately.

## Original r6 failure and separate qualification

The original native r6 process exited 1 at its broad source-preservation assertion and emitted **no receipt.json**. Its original logs and semantic-mutant results are retained. `native/r6/failure-observation.json` is an explicitly authored observation of that terminal failure, not a fabricated original receipt or a replacement PASS.

The exact subsequent source audit found one changed file: `tests/hierarchy_oracle/run.py`, the standalone Arm host runner. The native runner copied that file with the runtime directory but did not compile, import, or execute it. All consumed native production/test sources remained byte-identical. `native/qualification/receipt.json` therefore separately qualifies the completed native checks and joins them to the final source-bound Arm r10 result. The r6 failure is not erased or relabeled. The same final test fixtures also reject the pre-change native runtime, recorded under `native/old-r5/`.

## Reviewable payload

`native/r6/canonical-replies.csv` contains recorded service replies. Columns are granule, ancestor level, leaf AP, parent AP, XN selector, EL, operation, result, fault, ESR. Operations use the actual service ABI: fetch=1, load=2, store=3. XN bits are leaf PXN=1, leaf UXN=2, table PXN=4, table UXN=8. Duplicate rows retain cold/warm and cross-EL observations; values must agree. Final direct comparison rows and exact source audit are under `native/qualification/`.

Original receipts, serial output and logs are copied byte-for-byte. Absolute scratch paths inside receipts are historical provenance, not portable dependencies. Binary snapshots/executables and complete copied runtimes are omitted; their hashes remain in original qualification/build receipts. `summary.json` inventories every payload file except itself, with source paths where copied. Its own hash must be provided by the parent artifact inventory.
