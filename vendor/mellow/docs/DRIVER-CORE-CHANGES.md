> **Historical record — preserved unedited.** This document predates the MELLOW
> re-architecture. It is retained because the record of what was known, and when, is itself
> evidence. For the current concept and architecture see [CONCEPT.md](CONCEPT.md) and
> [ARCHITECTURE.md](ARCHITECTURE.md); for what any of it is allowed to claim, see
> [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).

# 7D41 driver core changes

These changes repair concrete access and completion defects in the inherited
Mellow core. They are source changes in the real driver path, with native tests
of shared code. They do **not** establish a working Metal accelerator or a usable
Xe-LPG memory manager. No MMIO, PCI configuration, firmware, or EFI operation was
executed on the Windows host by these tests.

## MMIO access

`Mellow/HardwareAccess.hpp` contains the OS-independent access checks used by
`MellowCore::readReg32Checked`, `readReg32`, and `writeReg32`.

- Register addresses consistently mean byte offsets.
- Every DWORD access requires a live base, four-byte alignment and a complete
  four-byte range inside BAR0. The subtraction-based range check cannot wrap at
  `UINT64_MAX`.
- Rejected accesses do not read or write the mapped array. In particular, an
  out-of-range read no longer writes BAR0 DWORD 14 and reads DWORD 15 through the
  inherited `mmPCIE_INDEX2/mmPCIE_DATA2` fallback. No Intel documentation was
  established for those supposed indirect ports on 7D41.
- Checked reads preserve the output parameter on failure and report `false`.
  Existing callers using the old value-only `readReg32` still receive zero on
  failure, with a bounded rejection log. Zero is not proof of a hardware result;
  new code that must distinguish failure uses the checked accessor.
- The unused `readReg64/writeReg64` methods were removed. They used a byte
  offset as a DWORD array index and transferred only 32 bits. Adding a generic
  pair access here would hide register-specific ordering and latching rules.
- Invalid BAR0 maps are released rather than retained. The map requests
  inhibited CPU caching and validates length, address and alignment before
  exposing the pointer. The existing display SURF=0 guard is retained.

This addresses addressability and CPU mapping correctness only. It does not add
forcewake domains, serialize engine MMIO sequences, validate arbitrary register
offsets, or prove that hardware accepted a posted write. Intel's Linux uncore
implementation treats those as additional responsibilities and explicitly
documents caveats for 64-bit register accesses:
[intel_uncore.h](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/i915/intel_uncore.h),
[intel_uncore.c](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/i915/intel_uncore.c).

## Physical PCI identity and spoof reads

The original CPU/GPU pair gate is retained: CPU model `B5` admits physical
`8086:7D41`; a property containing the Tiger Lake spoof `9A49` is not sufficient.
`kern_model.hpp` now depends only on standard integer types, allowing the same
pair predicates to run in native tests.

The config-read wrappers now require the exact admitted `IOPCIDevice`, matching
bus/device/function, conventional configuration page, a valid 16-bit injected
device ID, and a hardware read matching the admitted physical ID. They preserve
absent-device/error all-ones results. They no longer infer identity from a name
beginning with `IGPU`.

DWORD offset 0, 1, 2 or 3 all refer to the aligned vendor/device DWORD in Apple's
documented interface; a WORD offset 2 or 3 refers to device ID. The new shared
helpers preserve the vendor half and unrelated registers. Extended configuration
pages cannot be mistaken for vendor/device ID simply because the low offset is
zero. See Apple's
[IOPCIDevice.h](https://github.com/apple-oss-distributions/IOPCIFamily/blob/main/IOPCIDevice.h)
and [IOPCIDevice.cpp](https://github.com/apple-oss-distributions/IOPCIFamily/blob/main/IOPCIDevice.cpp),
and [Lilu's config accessor](https://github.com/acidanthera/Lilu/blob/master/Lilu/Sources/kern_iokit.cpp).

## DSM and BAR2 platform differences

The inherited PCI GGC decode and forced minimum of 128 MiB were replaced with a
read of Xe-LPG's MMIO GGC at `0x108040`. The strict decoder requires GGMS=3 and
admits only GMS `00..04` (0,32,64,96,128 MiB) or `F0..FE` (4..60 MiB). An invalid
register or failed read leaves `stolen_size=0`; it never invents a reservation.
This field records **total DSM**, before the reserved WOPCM and possible GSC
area are excluded. A successful decode is not permission to use all of it as a
GPU allocator.

For graphics IP >=12.70, Intel's Xe driver treats BAR2 as LMEMBAR system-stolen
memory. DSM begins 8 MiB after GSMBASE, and device-memory PTE semantics differ
from the old GGTT-mappable aperture. Consequently `setApertureIfNecessary`
reports the inherited GGTT aperture unavailable on Core Ultra: null pointer,
zero length, and an explanatory log. Existing GGTT offsets must not be used as
BAR2 CPU addresses. This patch does not implement a replacement LMEM allocator.

The register constants and decode are supported by Intel-authored Linux code:
[GGC register definition](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/i915/i915_reg.h),
[Xe stolen-memory detection](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/xe/xe_ttm_stolen_mgr.c),
[i915 MTL stolen-memory setup](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/i915/gem/i915_gem_stolen.c).

## Completion and client semantics

`wrapIGAccelDeviceStart` now forwards the actual start result.
`wrapWaitForStamp` now forwards the original return code and output stamp, even
when startup ordering caused a timeout. It never marks a fence complete itself.
`wrapSetIdMode` forwards the original mode rather than clearing the undocumented
`0xff8073c0` mask. These hooks retain diagnostic logging.

The inherited rationale for forced completion described a startup/interrupt
dependency. This patch exposes that dependency rather than declaring unfinished
work done. Real fixes require traces proving ordering, command submission,
interrupt delivery, and fence completion; the native tests cannot supply that.

## Validation performed

On the Windows development host, GCC compiled and ran both programs with
`-std=c++14 -Wall -Wextra -Werror -O2 -static`:

- `tests/HardwareAccessTests.cpp`: mapped-array reads are side-effect free;
  valid writes touch exactly one expected DWORD; misalignment, one-past-end,
  undersized mappings, null pointers and near-`UINT64_MAX` offsets do not touch
  memory. Tests cover all 256 config offsets, BDF/extended-page differences,
  malformed IDs, failed hardware reads, and all 1,024 GMS/GGMS combinations.
- `tests/modelTests.cpp`: the exact B5/7D41 decision across all 65,536 device IDs
  and all 256 CPU models, plus sibling families and rejection of injected 9A49.

Both test programs printed PASS. The programs execute shared production helper
code against ordinary arrays and synthetic PCI register values. They do not
load a kext or execute a GPU command. Whole-kext compilation and GPU execution
are separately reported by the build and Metal validation workflow.
