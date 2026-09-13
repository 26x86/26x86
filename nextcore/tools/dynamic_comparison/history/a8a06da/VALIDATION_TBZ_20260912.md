# TBZ/TBNZ runtime freeze and replay

## Current Status

Active source is an immutable `git archive` of published ISE
`a8a06dad15449b15ffb2383934f6a4239a54327f`. The 77-file freeze SHA-256 is
`4c3de3dc9fcbff28714576ff6e2fc5f44662cc06d230361c79245d77cf91c1f2`.
No working-tree bytes or generated test results were used to select hashes.

Relative to `08156f4`, production changes are limited to `jit.c` and
`preos/src/arch.rs`: native/reference TBZ/TBNZ plus allowing an aligned direct
instruction word at `UINT64_MAX-3`. Three provider test files changed and
`test_test_bit_branch_jit.c` was added. No frozen file was removed.

Independent read-only review checked bit-index concatenation, W/X width and ZR,
signed imm14 scaled displacement, x86 BT carry polarity, target/fallthrough
wrap, PSTATE/register preservation, and branch retirement before the next fetch
fault. The inclusive last-word check retains the separate buffer-length guard,
so a three-byte input still cannot execute. No actionable defect was found.

## Validation

The exact archived C JIT and Rust memory service executed all six unchanged
captured cases successfully. The mutated captured ESR expectation was rejected.
All 14 comparator regression tests passed, including missing-IL rejection.
The active comparator still checks one hardcoded freeze-file identity and every
listed source hash before compilation and after execution; no result predicate
or source gate was broadened for the new instruction family.

The complete local replay is `/tmp/nextcore-ci-dynamic-a8a06da`. Its receipt,
negative control, and native output rows are copied unchanged into
`evidence-tbz-20260912`. The previous source package was copied without evidence
recursion into `history/08156f4`; all eight copied files were byte-compared with
parent commit `d6104e70`. Prior `evidence-20260912` and its validation document
remain unchanged.

## Target State

CI replays this exact frozen runtime against the original oracle and runs the
14 comparator tests on its fresh output. Use the commands in `README.md` with
a new output directory. A future source change again requires explicit review
and replay. Native comparison does not establish original macOS execution,
physical display output, or hardware boot.
