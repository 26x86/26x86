# Exact ISAR2 and PAC address-selection revision replay

## Current Status

The active runtime is a Git archive of ISE
`5cd1e44413958450875392d8a431dba15bb76f2e`. All 120 runtime files match their
exact Git blobs. The source-freeze SHA-256 is
`7a7a7f0cfce5789ce3e05e7819757b78464bc9e12df59f2fcf0ebaab0b21087c`.

Thirteen runtime files changed. Exact read-only ISAR2 uses the existing EL1
and live inactive HCR/SCR gate. Signing uses bit63 to select the non-TBI APA1
address size; authentication and stripping retain bit55. Independent ISAR2
checks pass 918 native assertions, 32 actual Arm destination observations,
35 reference tests and 32 provider tests per cache mode. Six representative
unimplemented extensions are rejected. The deliberately changed ISAR0 negative
now targets unsupported ISAR4; historical expectations remain unchanged.

All six unchanged captures, fourteen comparator regressions and three negative
controls pass. The preceding freeze and an altered runtime are rejected before
compilation. All 187 previous history/evidence files remain byte-identical.
Eight selected preceding files are preserved in `history/29413d9`.

## Target State

Maintain exact source identity and unchanged captured expectations. Separate
adapted-control PAC and actual enabled M0 EFI proofs cover the new signing
behavior; these captures retain their original profile-2 contract. This replay
still stops at unsupported, nonretired HVC with ESR `0x02000000`. It does not
establish original reset ABI, normal startup or physical desktop output.
