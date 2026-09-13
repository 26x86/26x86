# Hierarchy source-freeze validation

## Current Status

Exact immutable ISE `778473fd9c43d7ba3a4721852f838be996fed45d` provides 136 runtime files,
each matched independently to its Git blob. Source-freeze SHA-256:
`96111a63902c7db61a65a44921187dfa3b4c2ba400884cba8b3a8a6be080fffa`.

The shared walker now accumulates baseline APTable/PXNTable/UXNTable permissions
for EL0/EL1 and separates cached regime classes from legacy EL2/EL3 behavior.
Eight new test/oracle files accompany that one production-file change. Existing
dynamic profile-2 control admission remains unchanged.

Six unchanged captured-Arm cases, fourteen comparator regressions and three
negative controls pass. Old-freeze and modified-source controls reject before
compilation. All 247 prior history/evidence files retain their bytes;
eight selected comparator sources are archived under `history/50b3da2`.

## Target State

Retain exact source identity across future edits. These are shared-runtime
regressions against the original dynamic captures, separate from the new
hierarchy native/Arm/EFI proofs. They do not prove mutable guest mappings,
original entry ABI, physical macOS startup, or desktop display.
