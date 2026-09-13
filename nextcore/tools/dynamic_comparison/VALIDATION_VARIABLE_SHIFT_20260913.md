# Variable-register shift revision replay

## Current Status

The active runtime is a Git archive of ISE
`00243e65b934abb79c87719cd4ef06860c8489f2`. All 106 runtime files match their
exact Git blobs. The source-freeze SHA-256 is
`14980507eb5eca539512373b1e3eda5dfaea72592e42aff1b2f57f72aca8468e`.

Six runtime files changed: the native and reference shift implementation plus
four independent verification files. LSLV, LSRV, ASRV and RORV support both
widths, masked counts, ZR and aliases while preserving SP/NZCV. Separate tests
compare 1,920 actual Arm vectors against native and reference execution.

All six unchanged captured inputs, fourteen comparator regressions and three
negative controls pass. The preceding freeze identity and altered runtime copy
are rejected before compilation. Captured inputs and expectations are unchanged.
All 142 earlier history/evidence files remain byte-identical. Eight selected
preceding files are preserved in `history/fa5fe9e`; new receipts are in
`evidence-variable-shift-20260913`.

## Target State

Preserve exact source identity and captured expectations in future revisions.
This replay still stops at unsupported, nonretired HVC with ESR `0x02000000`.
It does not establish original reset ABI, normal startup or a physical desktop.
