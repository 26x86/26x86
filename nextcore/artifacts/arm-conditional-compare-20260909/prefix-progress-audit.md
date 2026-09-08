# BP31 prefix progress audit

The three existing budget checkpoints support **forward progress through
variable-length executable metadata**, rather than a stationary polling spin.
This is a static comparison of saved observations; no additional guest
execution or budget increase was performed.

| Instruction budget | Retired | Native blocks | Termination |
| --- | --- | --- | --- |
| 256 | 256 | 72 | Budget |
| 1,024 | 1,024 | 327 | Budget |
| 4,096 | 4,096 | 1,205 | Budget |

All stops map to the same small loop in the original executable segment. One
visible cursor advances between every checkpoint and maps to successively
later valid command boundaries in the unchanged image. The nearby control
flow uses per-record lengths, range checks and a counter-controlled backedge.
The sampled cursor remains within the finite command table at the last stop.
The inspected window contains no MMIO polling or wait instruction.

This classification is an inference from the saved state and private static
inspection, not an identification of a particular operating-system routine.
The public Mach-O format defines a finite command count and record size field
used to advance through load commands. [Apple's public format definition](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/EXTERNAL_HEADERS/mach-o/loader.h).
No original address, instruction, operand, private asset path or disassembly
is reproduced here.

The observation does not prove completion of the traversal, correctness of
every intermediate iteration or eventual handoff. The current bridge exposes
only four general registers plus SP and PSTATE; the loop's internal counter
and base registers are not saved in these receipts. Instruction-budget
termination supplies no unsupported-instruction diagnosis.

The immediate observed limit is the approved diagnostic budget. SPTM arguments
and services remain unprovided, and the platform DeviceTree remains an
authored diagnostic input. Those are separate incomplete-handoff conditions;
none of these budget stops demonstrates a failure caused by them. A subsequent
bounded investigation must observe the next actual architectural or provider
boundary before attributing a blocker or implementing its semantics. Raising
the budget alone would not establish normal macOS boot or stable operation.

The canonical ISE, Core and EFI source hashes and original/ESP input hashes
were preserved. Detailed checkpoint coordinates, file mappings, command-table
records and the inspected instruction window remain in the private audit.
