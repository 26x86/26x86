# 26x86 native EFI translation engine

This is a freestanding x86-64 EFI application and an original AArch64 subset
JIT. It emits executable x86 machine instructions directly. The installed boot
path starts neither Linux nor a QEMU process. QEMU/OVMF is used only as a test
fixture for the actual EFI executable.

**It does not yet boot macOS, iBoot, or an Apple Silicon machine.** An OpenCore
iBoot/AIC handoff is validated and returns `EFI_UNSUPPORTED`, rather than passing
a CPU demonstration off as a macOS launch. macOS 26/27 are accepted target
identifiers, not verified guest compatibility claims.

## Build and verification

On a system with Python 3, clang, lld, and a POSIX native compiler runtime:

```sh
python3 sandbox/efi/build.py
python3 sandbox/efi/verify_ovmf.py
```

The second command also requires `qemu-system-x86_64` and Ubuntu's OVMF paths.
`build/BOOTX64.EFI` is the production application. `build/TESTX64.EFI` includes
test-only debug-console output and a QEMU exit port; it is never staged as the
production engine. JSON reports identify both hashes and keep macOS/physical
Mac acceptance false. The Nehalem test has no AVX, and the Conroe negative test
must reject its missing SSE4 before JIT execution.

For standalone own-code diagnostics, place `BOOTX64.EFI` at the removable-media
fallback path `EFI/BOOT/BOOTX64.EFI`. An optional `EFI/26x86/guest.a64` contains
4..65536 bytes of little-endian A64 instructions. Its initial PC and X registers
are zero, RAM is a separate zeroed 64 KiB buffer, and execution is limited to
100000 retired instructions. `HLT #0` is a diagnostic monitor exit convention,
not a simulated architectural exception. No Apple binaries are included.

## Current architecture

- Host minimum is x86-64 with both SSE4.1 and SSE4.2 (Nehalem/Mac Pro 2009 CPU
  baseline). AVX/AVX2 are disabled at compilation. Real Mac firmware remains
  untested; non-Apple operation is not guaranteed and is outside issue support.
- Supported A64 operations: 32/64-bit MOVZ/MOVK, ADD/SUB immediate without flags,
  ADD/SUB unshifted register without flags, CBZ/CBNZ, B, NOP, and unsigned-offset
  64-bit LDR/STR. SP versus ZR and W-register zero extension are explicit.
- Generated functions use Microsoft x64 ABI and modify only volatile registers.
  Guest RAM bounds and address overflow are checked before every load/store.
  Fetch/data/unsupported faults preserve the faulting PC and retired count.
- Generated pages alternate RW+NX and RO+X. The UEFI Memory Attribute Protocol
  is preferred. Older firmware can use the PI CPU Architectural Protocol;
  effective page permissions, CR0.WP and EFER.NXE are checked independently.
  No page tables are modified directly. Unsupported protection capabilities
  stop execution. CPUID serializes generated code before entry.
- Blocks contain at most 32 guest instructions and are rebuilt in one reusable
  code buffer. There is no persistent translation cache or self-modifying guest
  code support yet. Guest instruction storage is distinct from guest data RAM.
- The virtual platform contract is **AIC only and iBoot only**. GIC, Windows ARM,
  and ARM UEFI guest boot are outside this ABI. Apple hardware device properties
  and `SandboxSMBIOS` come from OpenCore's config through `handoff.h`.

## OpenCore handoff

OpenCore loads `\EFI\26x86\Sandbox.efi` from its own ESP with `LoadImage`, sets
the loaded image's `LoadOptions` to the 64-byte `vf_handoff` in `handoff.h`, and
calls `StartImage`. Pointers remain valid until it returns. The v1 input has
4096..1048576 MiB RAM in whole MiB, 1..64 CPUs, target major 26 or 27, zero flags,
an absolute iBoot path of at most 191 UTF-16 code units plus NUL, and SMBIOS/device
property XML dictionaries of at most 1 MiB each including the terminating NUL.
Device properties use OpenCore-normalized base64 `<data>` values. Root
`SandboxSMBIOS` supplies the four string identity keys. These are a transport
contract; this milestone does not dereference and execute the iBoot image.

Remaining macOS-critical work is full privileged A64 translation and MMU/TLB,
exceptions/EL transitions/PAC, coherent SMP and atomics, AIC interrupt delivery,
Apple timer/device MMIO, immutable iBoot loading and authentic restore/policy,
storage, display, and hardware acceptance. Existing GIC/vmapple research cannot
serve as evidence for the AIC-based platform.

## Sources and license

This new emitter is specification-based original code under the repository's
BSD-4-Clause/OCLP-derived license. No QEMU or Linux driver code is incorporated;
using QEMU as a test harness does not relicense it. Any future source import
must retain its original license and compatible distribution obligations.

- [UEFI 2.11 memory protection protocol](https://uefi.org/specs/UEFI/2.11/37_Secure_Technologies.html#memory-protection)
- [PI 1.9 CPU architectural protocol](https://uefi.org/specs/PI/1.9/V2_DXE_Architectural_Protocols.html)
- [Arm A-profile Architecture reference manuals](https://developer.arm.com/documentation/ddi0487/latest/)
- [Intel software developer manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
