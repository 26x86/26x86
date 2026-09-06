# Verification record — 2026-09-06

Historical `platform-v0.2.0-dev` record. The later objects/JIT and diagnostic-driver snapshot is
[VERIFICATION-METAL-JIT-2026-09-06](VERIFICATION-METAL-JIT-2026-09-06.md).

This record separates executable driver-source porting, a real Windows GPU runtime path, and
QEMU guest execution. The combined result is **implemented stages verified; complete Tahoe/Metal
validation not achieved**. The user confirmed that only the current Windows PC was available.
The [machine-readable index](../validation/integration-verification.json) pins each evidence file
and records remaining gates, the kext hash/import comparison and actual encoder branch relocations.

## 1. Real Linux driver code and kext integration

Linux commit `0d9ff90a5422cc7509258aaaba1e7481df4d332a` is the source pin.
[PortedXe provenance](../Drivers/PortedXe/provenance.json) identifies four original files and
six unchanged function bodies: `xelp_ggtt_pte_flags`, `xelpg_ggtt_pte_flags`,
`pde_encode_pat_index`, `pte_encode_pat_index`, `pte_encode_ps`, `xelp_pte_encode_addr`.
Their original MIT notices and permission text are retained. This is a reviewed manual partial
port, distinct from the generic source-intake CLI.

The executable wrappers implement bounded GGTT/PPGTT/PDE encoding. The adapted system-memory
SG mapping and clear loops enforce retained DMA ownership across writes/invalidation, including
partial-write and invalidation failure. The test adapter simulates MMIO, DMA leases and TLB
visibility; no physical register or DMA operation is inferred from a successful callback.

`Mellow/XeMemory.cpp` now calls the ported encoding. Its original 46-bit DMA, 4K system-memory,
PAT and read-only contracts are preserved. `Mellow/PortedXeBindings.cpp` is compiled exactly
once in the Xcode source target. The object relocation table contains branches to the actual
`Mellow::PortedXe::encodePpgtt` and `encodePde` symbols.

- [Host port tests](../validation/ported-xe-host.json): 18,721 checks and source/fragment provenance.
- [Existing Xe regression](../validation/ported-xe-kext-regression.json): memory 79,451;
  page table 30,698; IOKit-boundary lifecycle 41; additional MMIO, Zebin, submission and GuC
  tests. The hardware boundaries in these suites are simulated.
- [Existing context/dispatch regression](../validation/ported-xe-runtime-regression.json):
  3,658,796 context checks, 88,716 dispatch checks and 224 execution checks, again with simulated
  hardware. These counts are not independent GPU workloads.

[Actual cross-build](../validation/ported-xe-kext-build.json) compiled all 31 target units using
Clang 20.1.8 and linked with cctools-port ld64. The resulting **Mellow.kext 0.4.2** is an x86_64
`MH_KEXT_BUNDLE`, not an executable relabeled as a kext. The
[Mach-O validation](../validation/ported-xe-kext-macho.json) records retained relocations,
initializers/destructors and bundle metadata. All 378 unresolved kernel/Lilu symbol names were
also present in the previous kext; resolution against an installed Tahoe kernel was not tested.

## 2. Actual native MellowRT OpenCL execution on Windows

[The integrated runtime report](../validation/native-opencl-runtime.json) belongs to a native C++
binary compiled from `PlatformRuntime.cpp`, `OpenCLProvider.cpp` and its acceptance harness.

The installed Intel Windows driver reports OpenCL GPU type, vendor 8086 and device 7D41.
The device ID comes from the advertised `cl_intel_device_attribute_query` extension. Independent
PCI ownership is not established by that API. Windows device inventory also reports an Intel
display device with VEN_8086/DEV_7D41 and the same driver version; this corroborates the reported
identity, not the private driver's actual scheduler or physical fence implementation.

The provider creates and owns a real context, in-order profiling queue, program, kernel, buffer
and event. It first runs an unadvertised bootstrap witness. Only after actual event ownership,
profiling and readback checks does it publish Compute/OrderedQueue verification for its live epoch.

The final stress run verifies **10,000 consecutive positive submissions**, each with 256 uint
elements. Every submission goes through MellowRT planning, actual enqueue, correlated completion,
readback and checked resource finalization. Sequences 2 through 10,001 share one queue/device/epoch.
Python independently regenerates all inputs and expected results and compares aggregate SHA256
against the native input/expected/readback streams. Two detailed samples plus the aggregate
record keep evidence bounded. Negative source/size/reference/session tests run separately.

This is **OpenCL C input on the installed Windows driver**, not MSL/AIR translation, Metal
compute, or execution of the new Darwin driver port. The default Metal route remains rejected.
Hardware reset, physical page-fault and private-driver fence counters are not available; their
absence from the report must not be interpreted as zero.

The adapter's review found and fixed stale identity across initialization attempts and unchecked
resource finalization before completion publication. Forty-five synthetic ICD lifecycle/error
checks pass under ASan/UBSan, with additional Windows host execution.
[Lifecycle evidence](../validation/native-opencl-regressions.json) remains explicitly synthetic.

The supervisor isolates driver calls in a bounded worker, stops on the first failure and supports
alternating progress checkpoints. Worker crash/missing report/timeout cannot become success.
[Report controls](../validation/native-opencl-report-controls.json) exercise malformed/crashed
workers and partial checkpoints without claiming those controls ran on a GPU.

## 3. Actual emulator execution

[Final QEMU report](../validation/ported-xe-qemu.json) and
[serial output](../validation/ported-xe-qemu-serial.log) record QEMU 8.2.2, q35/TCG and Ubuntu
Linux 6.8.0-139. Guest PID1 executes a static binary compiled from the actual PortedXe source
and tests. No disk or network is attached to this guest.

The guest completes all **18,721 checks**, returns process exit 0 and QEMU debug-exit status 33.
Source and kernel/test/init/initramfs hashes are checked before/after execution. The six-function
count is source/call-graph metadata, not a dynamic coverage counter.

Five [actual QEMU controls](../validation/ported-xe-qemu-controls.json) confirm that exit failure,
zero checks, a trailing failure, a false Metal claim and changed execution input are rejected.
Nineteen [parser controls](../validation/ported-xe-qemu-parser-controls.json) cover malformed,
duplicated and contradictory protocol records. Guest success output alone is insufficient.

QEMU models the CPU/RAM/platform. It does not model a Xe GPU here. GGTT writes, GPU TLB visibility,
DMA and page walks remain simulated test boundaries. This verifies execution of the ported
algorithms in a guest, not physical GuC authentication, GPU interrupts or macOS driver loading.

## 4. Reproduce

Windows native GPU path (MinGW compiler and an installed OpenCL GPU driver):

```powershell
python Tools/run-opencl-runtime.py --cxx C:/msys64/mingw64/bin/g++.exe --out build/opencl-stress --compute --iterations 10000 --timeout 180
```

Portable tests and Linux guest path (Linux/WSL):

```sh
python3 Tools/run-ported-xe-tests.py --cxx g++ --out build/ported-xe
python3 Tools/run-opencl-runtime-regressions.py --cxx g++ --out build/opencl-regressions --sanitize
python3 tests/opencl_runtime_stress_report_tests.py
python3 Tools/run-ported-xe-emulator.py --kernel /path/to/vmlinuz --out /path/to/new-guest-output --timeout 120
```

The [kernel provenance](../validation/ported-xe-qemu-kernel.json) gives the exact Ubuntu package
URL and measured hashes used here. A kernel is an explicit external input; no OS image or firmware
is silently installed. The guest output directory must be new to preserve earlier runs.

For the actual Darwin target build, use [cross-build notes](../Tools/cross-build-notes.md) with
the current repository as the source root. Native Xcode CI now builds the kext before the Mach-O
evidence tests and passes its actual binary path through `MELLOW_KEXT_BINARY`.

## 5. Remaining acceptance gates

The following are neither implemented in full nor established by these tests:

- a loaded, functioning Darwin 7D41 backend: real DMA/IOMMU, PAT/GGTT programming, GuC firmware
  authentication/submission, hardware interrupts/fences, resets and suspend/resume;
- a complete LinuxKPI/DRM/vendor port or automatic arbitrary-source driver conversion;
- MSL/AIR/metallib frontend/lowering/JIT and a Mellow-owned Objective-C Metal device;
- Metal compute, offscreen render, GPU stress through Metal, GL/CL resource sharing;
- system Metal registration, IOSurface/compositor integration, WindowServer and scanout;
- actual Galaxy Book Tahoe installation/Recovery GUI and subsequent normal boot.

The earlier QEMU Recovery run reached Apple boot.efi and kernel collection loading but not a
verified XNU start or Recovery desktop. The emulator algorithm run does not resolve that result.
The newly built kext was not loaded into the Windows host or automatically enabled in USB EFI.
