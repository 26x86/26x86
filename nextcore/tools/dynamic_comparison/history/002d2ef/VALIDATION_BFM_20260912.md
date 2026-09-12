# Bitfield runtime replay

## Current Status

The active source is an immutable `git archive` of published ISE
`002d2eff8b262e728224b9b039b9ffe168ed4586`. Its 81-file freeze SHA-256 is
`4b6cd21ac043d8b94d2368185c588993ee1b8ef0b78dd7f0534438494c86eea8`.
Relative to the previous freeze, BFM destination-preserving execution and
independent reference execution were added. Provider and direct tests cover
BFI/BFXIL/BFC, wrap/extract forms, register aliases, zero registers, W-width
zero-extension, unchanged flags, and invalid encodings. Old UBFM negative
cases that encoded newly supported valid BFM were replaced with invalid-N BFM.
SBFM remains unsupported. Native extraction/merge and reference rotation/masks
use different formulations; an independent bit-origin oracle checks results.

All six unchanged captured-Arm comparisons and 14 comparator regressions pass.
The captured ESR mutation is detected. The prior freeze is rejected before
compilation with `owner runtime freeze identity`; no acceptance predicate was
relaxed. Receipts are in `evidence-bfm-20260912`. Eight selected historical
files are preserved from parent `8f562ac1` under `history/7cd9ac0`; previous
evidence remains unchanged and is not recursively duplicated.

## Target State

CI must replay the exact admitted source against the original captured oracle.
This demonstrates authored native behavior, not physical or macOS boot.
