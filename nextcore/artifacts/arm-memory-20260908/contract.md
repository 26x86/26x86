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
