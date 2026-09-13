# Combined multiply and reference-branch runtime replay

## Current Status

Active source is an immutable `git archive` of published ISE
`7cd9ac04016cbe436b3090fbf84e7cae67c6e8dc`, combining ordinary multiply-add
commit `0409a3d`, reference branch correction `61c42d5`, and the final inventory.
The 79-file freeze SHA-256 is
`6bb4fce61a1885b9fd099c05ab19c3c7aff5b8d27d6fdc9997ebe809c037a1db`.
No uncommitted working-tree bytes were used to select hashes.

Relative to `a8a06da`, production changes are `jit.c` and `preos/src/arch.rs`.
Three provider test files changed; `multiply_add_cases.rs` and
`test_multiply_add_jit.c` were added. No frozen file was removed.

Independent read-only review found no actionable ordinary MADD/MSUB defect:
the exact mask excludes widened/high-half neighbors; all sources are read
before destination writes; subtraction computes addend minus product; W writes
zero-extend; signed x86 IMUL's low product implements the required modular
result; ZR, aliases, SP and guest PSTATE are handled consistently. Wider test
oracles cover overflow without overflowing their own accumulator.

The reference branch correction applies W-width masking to CBZ/CBNZ, exact
fixed-bit checks to BR/BLR/RET, and target capture before BLR's link write. Its
Rn31 rejection matches the current native support profile, not a claim that
the architectural encoding is reserved. The source freeze includes those fixes;
the native six-case replay does not replace their separate reference tests.

## Validation

The archived C JIT and canonical Rust memory service passed all six unchanged
captured cases. The mutated captured ESR expectation failed as intended, and
all 14 comparator regression tests passed. No result predicate changed; the
active comparator still accepts exactly one hardcoded freeze-file identity.

The full local run is `/tmp/nextcore-ci-dynamic-7cd9ac0`. Its receipt, negative
control and native rows are copied unchanged into `evidence-madd-20260912`.
Eight prior source/freeze/documentation files are preserved in
`history/a8a06da` and byte-compared with parent commit `7aff75e0`. Existing
prior evidence and validation documents remain unchanged.

## Target State

CI replays this frozen source against the original oracle and applies the
14 comparator tests to fresh output. Future source changes require a new
explicit archive, review and replay. This proof establishes native comparison,
not original macOS execution, physical hardware boot or display output.
