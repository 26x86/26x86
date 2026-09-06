> **Historical record — preserved unedited.** This document predates the MELLOW
> re-architecture. It is retained because the record of what was known, and when, is itself
> evidence. For the current concept and architecture see [CONCEPT.md](CONCEPT.md) and
> [ARCHITECTURE.md](ARCHITECTURE.md); for what any of it is allowed to claim, see
> [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).

# 7D41 compiler backend, IOAccelerator ABI, and Metal evidence

The package now contains a **real Intel offline compiler output for device
0x7D41**, a read-only ABI inventory, and a native Metal compute/render probe.
It does **not** contain a functioning new macOS Metal driver for this GPU.
Neither the generated EU program nor the native Swift probe has executed on
the Galaxy Book GPU in this session. These limits are explicit in the JSON
reports and are enforced by the diagnostic gates.

## Work that actually executed

`Tools/metal-offline-compile.py` invokes Intel's official ocloc and IGC packages
in the existing Ubuntu 24.04 WSL environment. It downloads only when requested,
verifies pinned SHA256 and size, and uses `dpkg-deb -x` into a local directory.
It does not install packages, load a Linux GPU driver, or require a GPU.
The selected [compute-runtime 26.27.39122.11 release](https://github.com/intel/compute-runtime/releases/tag/26.27.39122.11)
documents Ubuntu 24.04 and IGC 2.38.2. The exact package URLs, hashes, sizes,
extracted tool/library hashes, and command logs are in
`compiler-evidence/compiler-report.json`.

The real compiler reported:

```
Auto-detected target based on 0x7d41 device id: mtl-u-a0
Build succeeded.
```

The program takes random-input-compatible `uint` data, a nonce, and a count,
then computes a wrapping integer multiply/add/xor expression. The front end
is **OpenCL C 2.0**, with embedded SPIR-V. Intel describes
[IGC as its LLVM-based OpenCL graphics compiler](https://github.com/intel/intel-graphics-compiler).
This invocation does not accept Metal Shading Language or Apple's AIR.

Actual retained outputs:

- `mellow_evidence_mtl.bin`: 6,944 bytes, SHA256
  `fea5095ddad2a328b6216263a1ab0571778f6277058720b09318399196185a90`.
- `mellow_evidence_mtl.spv`: 1,636 bytes, SHA256
  `97d420c607b73abdf9b9d5101e72d96ef8dd1258267b38e8aea82562492ecc62`.
- `disassembly/.text.mellow_evidence.asm`: actual Intel EU assembly, 7,159
  bytes, SHA256 `0b57df5a73c37df65a853c5009cfab3dfda38ed2675db90835dcd28914d89ed4`.
- `.ze_info`, symbol/relocation tables, compatibility notes, build options,
  and the source kernel are retained beside the compiler report.

Intel's `ocloc validate` returned zero and reported the binary valid/decoded
with one kernel. It also warned that `.note.intelgt.metrics` is not handled
by that validator; the warning is preserved, not suppressed. Validation here
means that the offline container decodes. It is not instruction execution,
a physical stepping measurement, or a hardware correctness result.

## The exact binary-to-submission boundary

The emitted file is little-endian ELF64, IntelGT machine 205, ELF type 1
(`ET_REL`), with Zebin sections. Its compatibility note records compiler
product configuration `0x03118000`, corresponding to the compiler-selected
`mtl-u-a0` configuration. The package does not infer actual silicon stepping
from that compiler choice. The parser follows the
[Intel Zebin ELF definitions](https://github.com/intel/compute-runtime/blob/26.27.39122.11/shared/source/device_binary_format/zebin/zebin_elf.h)
and checks header/section/string/symbol/relocation bounds and the expected
compatibility note. It is intentionally an inventory, not a runtime loader.

The `.text.mellow_evidence` section is 1,216 bytes including padding; the
function symbol records 1,040 bytes. The actual code has two `R_SYM_ADDR_32`
relocations at offsets 76 and 236 referring to the unresolved compiler symbol
`__INTEL_PATCH_CROSS_THREAD_OFFSET_OFF_R0`. No relocation has been applied.
The runtime would also have to construct the kernel's actual execution state:

- SIMD width 32, 128 GRFs, and the declared preemption/execution requirements.
- 64 bytes of cross-thread data and 192 bytes of per-thread local-ID data.
- Global-ID offset at byte 0; enqueued local size at byte 12.
- Input/output stateless pointer arguments at bytes 24 and 32; nonce/count at
  bytes 40 and 44; bindless input/output fields at bytes 48 and 52.
- Valid GPU addresses, surface descriptors, residency, cache/coherency state,
  launch packets, and completion handling for the selected engine.

Those values come from this specific compiled kernel. They are not a general
ABI for all IGC outputs. Copying this ELF, SPIR-V, or bare instruction section
into a ring does not perform that work. The Xe submission component therefore
does not accept this file as a GPU batch; its current bootstrap contract
accepts only its own validated NOOP/BBE stream and has no device submission
backend. The private page-table and lifetime components are separate kernel
development work, not evidence that this kernel has executed.

## Why this does not register a Metal device

Apple's public [MTLDevice API](https://developer.apple.com/documentation/metal/mtldevice)
lets an application obtain a device and create Metal resources. It does not
provide a public third-party Intel hardware-driver registration mechanism.
The existing Mellow route depends on external TGL framebuffer/accelerator
drivers and their user-space plug-ins. Those binaries are not present in the
inspected integration/USB roots. A file name, substituted PCI identity, or a
manually returned capability cannot establish their private ABI on Tahoe.

The following implementation and validation work still prevents a complete
Metal route:

1. A target-compatible accelerator/provider and user-client interface,
   including exact external-method layouts, object lifetime rules, and memory
   mappings expected by the **specific** Tahoe IOAccelerator family.
2. Metal user-space driver objects and resource/pipeline/queue contracts that
   match the target Metal framework. This includes resource handles, GPU VA,
   IOSurface/coherency, notifications, fences, residency, and error/reset
   propagation. No private selector numbers or vtable offsets are fabricated.
3. A Metal Shading Language/AIR compiler path with the correct Metal resource
   and execution semantics. ocloc's public
   [compiler API](https://github.com/intel/compute-runtime/blob/26.27.39122.11/shared/offline_compiler/source/ocloc_api.h)
   does not implement this interface. The real IGC output above proves a useful
   Intel code-generation backend, but no Metal-to-IGC front end was built.
4. Hardware command submission, relocations, context/engine state, interrupts,
   fences, and reset handling connected to the physical GPU, followed by real
   result validation. Host-side contract tests do not replace these steps.
5. Presentation, display timing, power transitions, and broader conformance.
   A successful small offscreen probe would still leave these unverified.

[Mesa's documented drivers and API layers](https://docs.mesa3d.org/systems.html)
and [Rusticl](https://docs.mesa3d.org/rusticl.html) supply useful graphics/OpenCL
components, but do not by themselves supply this missing Apple Metal driver
ABI. Treating a Vulkan-on-Metal implementation as a Metal-on-Intel driver
would reverse its direction. A complete replacement stack is still a larger
driver implementation, not an EFI or ROM patch.

## Read-only ABI gate

`Tools/abi-inventory.py` reads explicitly supplied roots. It inventories thin
or universal x86_64 Mach-O bundles, identifiers/versions, load commands,
dylib dependencies, rpaths, UUIDs, raw build versions, imports/exports, and
ObjC class symbols when symbol tables exist. It checks bundle executable
paths, malformed binary bounds, role-specific file types, missing/ambiguous
components, and observed bundle minimum-version dependencies. Stripped or
dyld-cache-only binaries are recorded as incomplete evidence.

The current report is `tests/metal-abi-inventory.json`. Required TGL and Tahoe
executables were unavailable in the explicitly inspected roots. Target kernel
KPI exports and Lilu exports have not been checked against exact target
binaries. Even a complete inventory always retains `gate: BLOCKED`, because
symbol names and versions cannot validate private object layouts or runtime
semantics. It never authorizes loading or changes a system file.

On a Mac, or against an already available matching OS snapshot:

```sh
python3 Tools/abi-inventory.py --search-root / --search-root /path/to/TGL-snapshot --output /tmp/mellow-abi.json
```

The program returns 2 for an inventory that cannot authorize activation;
this is intentional. Supply real local paths to existing snapshots. No
proprietary Apple driver binaries are downloaded or included by these tools.

## Native Metal result probe

`Tools/metal-probe.swift` uses the real Metal framework. Default behavior only
enumerates devices. `--compute` requires an exact registry ID, and traverses
the device's IORegistry ancestry using Apple's
[MTLDevice.registryID](https://developer.apple.com/documentation/metal/mtldevice/registryid).
It requires Intel PCI identity plus the Mellow diagnostic properties captured
from physical configuration before spoofing: vendor 8086, device 7D41, BDF
00:02.0 (`0x1000`), and source `pci-config-before-spoof`.
These are driver-reported correlation data, **not cryptographic attestation**.

The probe compiles actual MSL with `makeLibrary`, allocates GPU resources,
submits compute, and compares all 4,096 returned UInt32 values with a CPU
reference. Input and nonce are random; output initially contains `0xA5`.
The CPU never writes the expected values into the output buffer. A second
command renders a full-screen red triangle over a blue clear into a private
4x4 RGBA8 texture, blits it into shared memory, and checks all 16 pixels.
It emits ordered JSON Lines with registry correlation, input/output SHA256,
nonce, actual sample values/pixel, GPU timestamps, and errors. The approach
uses the actual command flow described in
[Apple's compute example](https://developer.apple.com/documentation/metal/performing-calculations-on-a-gpu).

Each submitted command has a ten-second completion deadline. The Python
wrapper also enforces a process deadline covering compilation and execution;
terminating a process does not guarantee cancellation of an in-flight GPU
command. Missing, duplicated, reordered, mismatched-target, unchanged-output,
failed, or partial evidence cannot pass the host evaluator. Success is scoped
to this small compute/offscreen-render probe, never full Metal conformance or
WindowServer presentation. The report is diagnostic data, not tamperproof
hardware attestation.

Run on macOS from the package directory:

```sh
python3 Tools/metal-run.py --output /tmp/mellow-enumeration.json
# Use the exact registry_id emitted by enumeration for the intended device:
python3 Tools/metal-run.py --compute 0xACTUAL_REGISTRY_ID --timeout 45 --output /tmp/mellow-compute.json
```

`0xACTUAL_REGISTRY_ID` is a placeholder to replace, not a valid device ID.
Enumeration does not submit GPU work and returns the non-acceleration result.
The wrapper writes `.jsonl` and structured `.json` reports and returns zero
only after both real result checks and normal process completion. This Swift
source has **not been compiled on macOS or run in this Windows session**;
`tests/metal-native-not-run.json` records that exact limitation.

## Reproduce and test the offline work

From the Windows workspace directory, use a new output directory:

```powershell
python outputs/Mellow-7D41-integration/Tools/metal-offline-compile.py --toolchain-root work/mellow-build --prepare --output work/mellow-build/ocloc-reproduction
python outputs/Mellow-7D41-integration/tests/metal_evidence_tests.py --report outputs/Mellow-7D41-integration/tests/metal-evidence-result.json
```

The compiler tool refuses an existing output directory, so a failed new build
cannot be confused with retained older artifacts. Official package copyright
text is retained in `compiler-evidence/licenses`; full compiler libraries
remain in local scratch, not in the deliverable. Intel's upstream
[IGC license notice](https://github.com/intel/intel-graphics-compiler/blob/v2.38.2/LICENSE.md)
identifies MIT; component-specific third-party notices remain with the
downloaded packages. The generated test source and small binaries are included
as development evidence, not redistributable Apple Metal driver components.

Host tests exercise corrupt Mach-O/ELF, wrong target notes, invalid relocation
bounds, malicious bundle paths, absent dependencies, and false-success event
sequences. They use labeled synthetic fixtures only to test rejection logic;
fixture acceptance is never exported as a native GPU result.
