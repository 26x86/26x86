# Active BP34 captured Arm to dynamic native comparison

## Current Status

This maintained copy preserves the original six captured cases and rejects
the historical missing-IL undefined syndrome. Native unsupported A64 HVC uses
exact ESR `0x02000000`; all other state and effect comparisons stay exact.
Historical source and evidence remain under the original artifact directory.

The admitted cache revision changes only the v1 physical-memory provider's
native-entry reuse and adds independent cache acceptance tests. This comparator
executes the dynamic provider, whose dispatch and service sources are unchanged.
Its captured-Arm replay is a regression gate, not a cache-performance test.

## Target State

Replay the original captured transitions against the admitted exact runtime
source freeze. A runtime update requires explicit archive-based freeze review
and a fresh native execution receipt; source mismatch remains a hard failure.

Root delegates a bounded external six-case replay using immutable BP34 public captured ELFs/logs/controls/table descriptors. No production edits or opcode substitution. Import actual canonical dynamic Rust service and compile actual C JIT/runtime, with a test-only observer around vf_run_memory_provider_dynamic to expose original x10-x14 and full fault/control state. This observer initializes the authored entry state and copies final CPU fields; it does not calculate guest results. HVC remains its exact ELF opcode and is compared as unsupported, nonretired native boundary after guaranteed post-ISB effects.

Reconstruct explicit zeroed table allocation plus directly captured nonzero descriptors. Reconstruct transition/target arrays from exact authored ELF payload bytes and data seed/canary from capture/source; distinguish these reconstructed bytes from directly printed state. Use exact guest physical symbols and original instruction VAs. Preserve actual original EL1 control fields and PSTATE; HCR.RW-only may be adapted to inactive0 after checking every other HCR bit zero, and uncaptured SCR is explicitly inactive0. EL2 entry/return/handler execution is outside native scope. No PSTATE masking, original OS input or full boot/Metal claims.

Snapshot all runtime/tool/input hashes and coordinate final freeze with CPU. Any unsupported earlier ISA boundary is evidence, not an excuse to replace instructions. Compare actual CPU load/store readback, post-ISB PC/SCTLR witnesses, real ESR/FAR/ELR/SPSR and operation failure boundaries, preserving original oracle captures. A changed expected syndrome/value must make the comparator fail. Root owns integration and publication.

Boundary qualification after preserved run1: actual canonical C classifies terminal HVC as unsupported status8/undefined, not the adapter's initial guessed status13. It records native ELR=the unchanged HVC PC and SPSR=3c5. These fields are separately tested as native diagnostic bookkeeping; successful Arm HVC executes to EL2, so its completion exception fields are not compared for architectural equality. The four actual Arm translation faults still require exact ESR/FAR/ELR/SPSR. No HVC retirement or HVC implementation is claimed.
