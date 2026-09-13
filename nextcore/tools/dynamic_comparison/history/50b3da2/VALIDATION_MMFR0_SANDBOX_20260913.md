# MMFR0 source freeze after the legacy native-test correction

## Current Status

The active runtime is an exact Git archive of ISE `50b3da2f172f67b4661336799e36bd19002ce816`.
All 128 runtime files match their Git blobs. The source-freeze SHA-256 is
`1d2f274f822371eb8f175002e8cd46f5199e2316dd6225ffa02fd22b0f8c96e5`.

Only `test_jit.c` changed from ISE `58e712a`. The legacy test initialized
EL1 with inactive HCR/SCR but still expected the previous MMFR0 value
`0x00101122`. Its expected value now matches the accepted model `0x0f100005`.
No production code changed. The native tests and independent review verify
the corrected expectation; read-access restrictions remain unchanged.

All six unchanged captures, fourteen comparator regressions and three negative
controls pass. Old-freeze and changed-source controls fail before compilation.
All 232 prior history/evidence files retain their original bytes.
Eight selected source files are preserved under `history/58e712a`.
Historical MMFR0, ASID and first CI-correction receipts retain their exact
tested source identities. This replay records the final complete source freeze.

## Target State

Preserve source identity and verify release binary equivalence separately.
The actual original r29 execution remains attributed to source f2256f1;
this test-only correction does not represent another original-kernel run.
Normal startup, original reset ABI, physical boot and desktop remain unverified.
