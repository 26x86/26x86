# Exact ZFR0 revision replay

## Current Status

The active runtime is a Git archive of ISE
`401619acb1232a366af776bc1ecbfd04eb01631f`. All 110 runtime files match their
exact Git blobs. The source-freeze SHA-256 is
`a029ec66cfc3ea8b254b0609678ea70d2533369f11a2ab9a4e00e4e7f02e2e21`.

Seven runtime files changed: native JIT, C register API, Rust reference and
four independent verification files. The exact read-only ZFR0 instruction
returns zero only in the bounded scalar profile at EL1 with inactive HCR/SCR.
Live control checks, XZR and rejected accesses preserve the existing boundary.
Independent tests pass 912 native assertions, 32 actual Cortex-A72 destination
vectors against C and Rust, and 31 canonical provider tests in each cache mode.

All six unchanged captured inputs, fourteen comparator regressions and three
negative controls pass. The preceding freeze identity and altered runtime copy
are rejected before compilation. Captured inputs and expectations are unchanged.
All 157 earlier history/evidence files remain byte-identical. Eight selected
preceding files are preserved in `history/00243e6`; new receipts are in
`evidence-zfr0-20260913`.

## Target State

Preserve exact source identity and captured expectations in future revisions.
This replay still stops at unsupported, nonretired HVC with ESR `0x02000000`.
It does not establish original reset ABI, normal startup or a physical desktop.
