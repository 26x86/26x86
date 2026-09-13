# Optional TCR source-freeze validation

## Current Status

Exact immutable ISE `3a0ed3dd39f78fc3c55415f898d7faa8f34699c2` provides 139 runtime
files, matched independently to its Git archive. Source-freeze SHA-256:
`75dc4b1d2e18b7272cfd818ae49a22659db3f16c86aab509e0059e1d76d19576`.

Three production files reject unimplemented TCR HA/HD/HPD0/HPD1 before register
or translation state changes. Three new independent test files exercise that
policy. The existing dynamic profile-2 admission policy remains unchanged.

Six unchanged captured-Arm cases, fourteen comparator regressions and three
negative controls pass. Old-freeze and modified-source controls reject before
compilation. All 262 prior history/evidence files retain their bytes; eight
selected comparator sources are archived under `history/778473f`.

## Target State

Keep exact source identity across future edits. These six shared-runtime
regressions do not replace the separate optional-control API tests, establish
a complete MMFR1 feature policy, or prove original entry ABI, physical macOS
startup or display. The latest original execution remains r29.
