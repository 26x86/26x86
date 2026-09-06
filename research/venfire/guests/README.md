# AArch64 conformance guests

These are self-authored bare-metal programs, assembled from `conformance.S`.
They contain no Apple firmware, kernel, restore image, credentials, or operating
system code. `virt.elf` boots at `0x40080000`. `vmapple.bin` enters a ROM trampoline
at `0x00100000`, copies its own payload to RAM at `0x70000000`, and enters EL1.
The vmapple variant requires the project's explicit headless research machine.

The same 12 tests run on both boards:

- CurrentEL must be EL1.
- Integer multiply/add, condition flags, 32-bit zero extension, RAM write/read.
- PACIA must change the pointer, AUTIA with the correct modifier must restore it;
  the guest requires the architectural QARMA5 feature field, not implementation-
  defined PAC. This does not assert Apple's PAC algorithm or key compatibility.
- Sixteen different incorrect PAC modifiers must each raise FPAC or create a
  pointer whose use raises an address/data abort. A changed bit pattern alone
  never qualifies as successful rejection.
- SVC must enter the synchronous vector and expose the expected EC/immediate.
- The actual EL1 MMU must allow reading a RAM alias and reject writing to it,
  while preserving the original RAM word. ESR EC/FSC/WnR and FAR are checked.
- An unmapped read must fault with the exact translation level and address.
- Both MMU checks run with 4 KiB granules (L1 blocks), then 16 KiB granules
  (L2 blocks). These are translation-granule tests, not L3 page allocation tests.
- CNTP must count forward and assert its expired deadline status.
- GICv3 must deliver virtual-timer PPI27 through the IRQ vector. The handler
  checks IAR, disables the timer, writes EOIR, returns, and the test verifies
  that the redistributor no longer marks PPI27 active.
- Generated instructions return 42, then return 84 after modification and
  `DC CVAU / DSB ISH / IC IVAU / DSB ISH / ISB` synchronization.

UART reports are emitted only after the corresponding comparisons and exception
checks pass. `DONE` is necessary but not sufficient: the Python harness also
requires every expected case in order and a zero QEMU exit code. Unsupported,
missing, duplicated or contradictory cases fail the overall result. The guest
uses Arm semihosting only to exit; all evidence is written to PL011 UART.

From the project root in Linux/WSL with GNU AArch64 binutils installed:

```sh
python3 -c 'from venfire.conformance import build_guests; build_guests()'
VENFIRE_TEST_QEMU=qemu-system-aarch64 python3 -m unittest discover -s tests -p test_conformance.py -v
```

The build writes `manifest.json` with source and artifact SHA-256 hashes.
Execution rejects changed sources or binaries until explicitly rebuilt. The
harness never accepts a guest firmware path from a caller. It requires a fresh
output directory and uses only fresh blank, read-only pflash devices for the
vmapple model. Run Python and QEMU inside the same OS filesystem namespace.

These checks establish a small amount of actual TCG/EL1/device execution.
They do not establish macOS boot, XNU compatibility, Apple hardware fidelity,
real Intel Mac boot, GPU/Metal, SMP, DMA, or storage-driver operation.

Primary implementation references:

- [QEMU CPU feature controls](https://www.qemu.org/docs/master/system/arm/cpu-features.html)
  document architectural QARMA5 versus the non-cryptographic implementation-
  defined default in recent QEMU versions.
- [QEMU virt model](https://github.com/qemu/qemu/blob/master/hw/arm/virt.c) and
  [VMApple model](https://github.com/qemu/qemu/blob/master/hw/vmapple/vmapple.c)
  define the MMIO layout and timer-to-GIC wiring. The actual build is pinned by
  the enclosing project's backend source lock.
- [Arm memory management](https://developer.arm.com/-/media/Arm%20Developer%20Community/PDF/Learn%20the%20Architecture/LearnTheArchitecture-MemoryManagement-101811_0100_00_en.pdf?revision=01a01804-ca64-4e19-a55e-2af56afea5a5)
  specifies the granule-dependent block sizes.
- [Arm GICv3/v4 software overview](https://developer.arm.com/-/media/Arm%20Developer%20Community/PDF/Learn%20the%20Architecture/GICv3_v4_overview.pdf?revision=65f91645-cd52-4795-952b-f01095ff5ef8)
  describes redistributor and system-register CPU-interface operation.
- [Arm cache maintenance guidance](https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/caches-self-modifying-code-implementing-clear-cache)
  specifies the single-line synchronization sequence.
- [Arm semihosting ABI](https://github.com/ARM-software/abi-aa/blob/main/semihosting/semihosting.rst)
  specifies the exit request and AArch64 trap.
