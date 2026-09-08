# BP26-A ARM stage-1 memory configuration

Current: the reference walker compares TG0 and TG1 raw bits even though Arm gives
these fields different encodings. As a result it rejects a valid 16 KiB split
address regime and accepts reserved TG1=00 in its synthetic 4 KiB upper test.
It also does not preserve the EPD0 walk-disable condition.

The root agent owns the walker file only. Correct the encoding and configuration
checks, preserve state on rejected configuration, and distinguish a canonical
address's disabled walk (translation fault) from an invalid VA (address-size
fault). Keep unsupported mixed granules explicit rather than silently select a
wrong granule. Neither this change nor unit tests enable the native JIT MMU.

References:
- https://documentation-service.arm.com/static/5e7b6c837158f500bd5c03fc (TCR_EL1)
- https://developer.arm.com/-/media/Arm%20Developer%20Community/PDF/Learn%20the%20Architecture/LearnTheArchitecture-MemoryManagement-101811_0100_00_en.pdf

Verification: independently authored page descriptors, both VA halves, each
supported granule, disabled walk without descriptor reads, invalid granule,
unaligned roots and preserved previous valid translation on rejected configure.


Root also owns the two independent oracle files under ISE/tools. The authored
AArch64 fixture installs translation tables, enables stage-1 translation, executes
AT S1E1R and compares the physical address reported by PAR_EL1 for each granule.
It runs in QEMU's architectural CPU model only, without any Apple payload. Both
4 KiB TG1=10 and 16 KiB TG1=01 cases passed. This corroborates the configuration
and expected addresses; it does not verify native-JIT translated memory accesses.


BP26-B review reproduced a shortened initial-table index bug: canonical
extension bits selected entries outside the configured upper VA range. The
walker now removes bits above VA[63-TxSZ] before indexing. One regression covers
24 mappings across both ends of both canonical ranges, all supported starting
levels, and both granules; it failed on the old code and passes after the fix.
The total reference suite is now 65 tests, including 13 MMU tests. The expanded
independent oracle preserves the earlier cases and adds 4 KiB T1SZ=26 and
16 KiB T1SZ=29. All four produce the expected PAR_EL1 address. A temporary
negative control changes the output descriptor PA and exits with FAIL/status1.
The EFI agent owned the oracle expansion; root owned the walker and Rust test.
These checks continue to exclude native JIT MMU enablement and XNU startup.
