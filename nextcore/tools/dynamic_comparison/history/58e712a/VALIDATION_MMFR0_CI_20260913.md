# MMFR0 source freeze after the canonical ASID test correction

## Current Status

The active runtime is an exact Git archive of ISE `58e712a5a93448014addd635d6fab9e9e8fcc00c`.
All 128 runtime files match their Git blobs. The source-freeze SHA-256 is
`d748bb2319dde1a07747986703931c8fa881f785477b18db84cf0f918fe65f23`.

Only `memory-service/src/stage1_tests.rs` changed from ISE `feb09b5`.
The old canonical test incorrectly expected TCR.A1 to be rejected after the
accepted fixed ASID8 implementation. It now checks A1 admission, low-eight-bit
TTBR tags, rejection of high tag bits and AS=1, and rejection of an A1 change in
an immutable request. This is a test correction; production semantics are unchanged.

All six unchanged captures, fourteen comparator regressions and three negative
controls pass. Old-freeze and changed-source controls fail before compilation.
All 217 prior history/evidence files retain their original bytes.
Eight selected source files are preserved under `history/feb09b5`.
The original MMFR0/ASID8 receipts remain historical evidence of their exact
tested revision; this replay records the new complete source identity.

## Target State

Retain precise source provenance without attributing a new guest execution to
a test-only correction. Binary equivalence is verified separately. These
profile-2 captures do not establish dynamic ASID switching, normal startup,
original reset ABI, physical boot, or macOS desktop output.
