# Exact MMFR0 and fixed ASID8 revision replay

## Current Status

The active runtime is an immutable Git archive of ISE
`feb09b5f1ef5eecce60120ba39e624bb020bd071`. All 128 runtime files match their
exact Git blobs. The source-freeze SHA-256 is
`9366c7d87e2150bf1e6978fc38522c7ad682082697603a6a1c693221d4567cc9`.

Sixteen runtime files changed. Exact MMFR0 reads use the explicit non-secure
EL1 diagnostic model, with live HCR/SCR checks. Immutable profiles admit fixed
eight-bit ASIDs and A1 selection; generic model control synchronization uses
the selected tag. Dynamic profile 2 explicitly retains its previous admission.

All six unchanged captures, fourteen comparator regressions and three negative
controls pass. An old freeze and an altered runtime are rejected before
compilation. All 202 preceding history/evidence files remain byte-identical;
eight selected files are preserved under `history/5cd1e44`.

Independent MMFR0 checks pass 964 native assertions, 31 provider cases per
cache mode and 34 reference tests. Its 32 actual Arm observations validate
encoding/access, not equality with the different software feature value.
Independent ASID checks directly exercise both immutable profiles, 35 provider
tests per mode, 102 reference tests, three compiled bad-selector controls and
the old source rejection. Actual EFI separately checks 64 tagged contexts,
control readbacks and alias transfers.

## Target State

Preserve captured inputs and exact source identity. These original profile-2
captures do not establish dynamic ASID switching or the full guest CPU model.
The terminal HVC remains unsupported and nonretired, with ESR `0x02000000`.
Normal startup, original reset ABI and physical macOS output remain unverified.
