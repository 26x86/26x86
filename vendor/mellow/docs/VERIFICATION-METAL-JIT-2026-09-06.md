# Mellow objects, compute JIT and Tahoe diagnostic verification

This is the 2026-09-06 KST development snapshot for `platform-v0.3.0-dev`, including
Mellow.kext **0.4.3**. It supersedes the current implementation summary in the earlier
[platform-v0.2.0 verification](VERIFICATION-2026-09-06.md), without rewriting that historical
evidence. UTC timestamps in individual reports may read 2026-09-05.

The implemented user-space path executed on the available Windows Intel GPU:

```text
Explicit MellowMTL C++ objects
  -> typed MSL AST or LLVM-decoded AIR SSA (documented uint compute subset)
  -> generated OpenCL C
  -> one retained driver-compiled pipeline
  -> installed Intel Windows OpenCL GPU driver
  -> correlated event completion, readback, independent result comparison
```

The kernel path is separate: an opt-in Darwin 25 PCI/IOUserClient diagnostic service
has been cross-compiled and linked into the actual kext. It is not the driver used by
the Windows GPU tests. Full Apple Metal ABI compatibility and a working Tahoe GPU
execution backend are **not implemented** by this release.

## Physical GPU results: user-space compute subset

- [MSL object run](../validation/msl-object-gpu.json): **10,000 verified submissions**, each
  with 256 uint values; **2,560,000 readback values** compared with an independent reference.
- [Raw AIR object run](../validation/air-object-gpu.json): the same **10,000 submissions**
  and **2,560,000 readback values**, through actual LLVM C API decoding and module verification.
  The input is hand-authored synthetic AIR assembled with real LLVM18, not authenticated
  Apple compiler output. Accepted AIR semantics are intentionally narrow.
- Each run retained **one compiled pipeline**, used epoch 1 and consecutive sequences
  2 through 10,001 after bootstrap, and verified two additional ordered encoder dispatches.
  Each recorded 160,049 assertions and 13 negative API checks. Worker exit was zero;
  source/input hashes remained unchanged and report-validation errors were empty.
- The installed driver was Intel Windows **32.0.101.6737**, exposing `Intel(R) Graphics`.
  Its advertised Intel query extension reported `8086:7D41`. This is driver-reported identity,
  not an independent physical PCI ownership measurement by Mellow.
- [Standalone source example](../Examples/compute-msl.cpp) also executed through the same
  public Mellow C++ API. Input `[1, 2, 3, 4]` produced `[10, 17, 24, 31]` on the GPU;
  [captured result](../validation/compute-msl-example.json). The runtime does not receive
  those expected values as an execution oracle.

These results establish actual GPU execution of the supported MSL/AIR compute subset.
They do not establish Objective-C Metal protocol conformance, native macOS execution,
general metallib compatibility, rendering or WindowServer acceleration.

## Compiler and lifetime checks

[Windows](../validation/shader-frontend-windows.json) and
[Linux](../validation/shader-frontend-linux.json) each passed **2,269 frontend checks**
and **72 independent CPU comparisons**. Windows additionally checked nine generated
OpenCL C fixtures with real clang. Linux used ASan/UBSan and actual LLVM18 assembly and
disassembly round trips. Linux also [compiled the complete object API](../validation/metal-objects-linux-build.json);
that compile-only record correctly has no GPU execution claim.

The [actual LLVM-C native test](../validation/air-decoder-native.json) passed **256**
concurrent parse/lifetime checks. Selecting Windows `kernel32.dll` instead of LLVM correctly
made the [negative control](../validation/air-decoder-negative.json) fail; its `FAIL` is the
expected control result, not a successful shader decode. An independent
[13-case real decoder corpus](../validation/air-decoder-corpus.json) accepted raw/wrapped
synthetic compute AIR and rejected malformed, unsupported, missing-entry and wrong-library
cases. The real upstream SDL vertex/fragment metallibs decode as containers/modules but
their shaders are not supported or executed.

Actual testing exposed a Windows process-exit access violation after LLVM-C unloading.
A separate load/unload experiment reproduced it even without parsing. Keeping the selected
DLL mapped until process exit corrected both positive and negative exits. The runtime now
pins that DLL with `GetModuleHandleExW`; the precise internal crashing callback remains
unidentified. [Experiment](../validation/air-dll-lifetime-experiment.json),
[implementation and dependency contract](AIR-DECODER.md).

[Reusable provider tests](../validation/reusable-pipeline-regressions.json) passed **70**
ASan/UBSan lifecycle and cleanup checks with a simulated ICD. These check failure behavior
and ownership, not hardware execution. [Process/report controls](../validation/shader-control-tests.json)
passed 17 container/process tests, nine shader report tests and six object-report tests.
They cover malformed reports, extra false evidence fields, timeout, output limits, file-write
failure and output/report aliasing. No failure may be relabeled as successful GPU execution.

## Kernel IOKit path and actual build

`Mellow/TahoeDiagnostic*` adds a real IOPCIDevice service and admin-only IOUserClient for
Darwin 25, raw `8086:7D41`, bus 0/device 2/function 0, admitted only with `-mellowdiag`.
It checks device state and BAR0 identity through existing IOKit access and offers a bounded
query/allocate/release protocol. It admits prepared DMA only through an already attached
device IOMapper. Without that mapper it remains query-only. Cleanup failures quarantine
the bounded allocation; they are not reported as released. The client never receives physical
DMA addresses. GPU execution capability remains zero.

The [Windows](../validation/tahoe-diagnostic-protocol-windows.json) and
[Linux sanitizer](../validation/tahoe-diagnostic-protocol-linux.json) tests each passed
**6,328** production protocol checks using simulated memory callbacks. Actual PCI matching,
MMIO, IOMMU/DMA preparation and user-client calls have not been observed on a Tahoe host.

The [final cross build](../validation/tahoe-diagnostic-kext-build.json) compiled all **33**
translation units and linked an actual x86_64 Darwin `MH_KEXT_BUNDLE` using Darwin ld64.
The [Mach-O audit](../validation/tahoe-diagnostic-kext-macho.json) recorded version **0.4.3**,
size **474,472 bytes**, 851 defined symbols and 426 imports. Executable SHA256:

```text
6932453a484ac62fb46f19b78f4a6424cef8ba907a3abe655b051bf03daed3c7
```

All **426/426 imports** have statically eligible declared providers in the inspected Tahoe
**25G83 Recovery** and Lilu inputs, including dependency version ranges;
[resolution report](../validation/tahoe-diagnostic-import-resolution.json).
This checks exports and declarations, not execution of the kernel linker or private ABI behavior.
The [host policy regression](../validation/metal-jit-host-policy.json) also passed; existing
kernel GPU paths are not promoted to runtime support by a successful build.

`Userspace/tahoe_diag_client.c` is provided as source. This Windows environment lacks the full
macOS userspace SDK, so native compilation of that client is not claimed. A genuine macOS/Xcode
workflow step was added. GitHub Actions was externally blocked by the account billing lock
at publication time; local cross-build evidence is not substituted for an unexecuted native CI job.

## Remaining implementation and verification

- Apple Objective-C `MTLDevice`/resource/encoder protocols and system Metal registration;
  current objects are an explicit portable C++ API.
- General MSL/AIR semantics, Apple-compiler-produced positive compute coverage, textures,
  render/blit, barriers/atomics, graphics pipelines and persistent/shared GPU resources.
- The integrated Tahoe GPU owner: physical GGTT/PPGTT publication, authenticated GuC loading,
  context execution, physical interrupt/fence completion and reset recovery. Existing experimental
  modules plus the new diagnostic service do not complete this execution path.
- Native Tahoe kext loading, installed-system Metal compute/render/stress, Recovery/installation,
  WindowServer and sleep/wake. No macOS test host was available.
- Executable NVIDIA/AMD backends and automatic whole-Linux-driver conversion remain absent.

This release does not resolve the earlier physical Tahoe `EXITBS:START` boot failure or provide
a verified installation USB. No EFI, USB contents or firmware were modified in this phase.
The earlier QEMU Linux algorithm tests remain useful historical evidence, but do not emulate
this Intel GPU or prove Tahoe installation or Metal acceleration.

## Reproduction and artifact identity

Use the commands and contracts in [MetalObjects](../Runtime/MetalObjects.md),
[SHADER-JIT-IMPLEMENTATION](SHADER-JIT-IMPLEMENTATION.md), [AIR-DECODER](AIR-DECODER.md)
and [TAHOE-DRIVER-IMPLEMENTATION](TAHOE-DRIVER-IMPLEMENTATION.md).
The source and kext development packages retain licenses and provenance. LLVM-C is an explicit,
separately supplied dependency; no LLVM DLL, Apple OS image or Apple compiler is bundled.

[The integration index](../validation/metal-jit-integration.json) binds this snapshot's reports,
source hashes and final kext. It is an artifact consistency audit, not another hardware test.
Historical v0.2.0 reports are preserved separately and must not be relabeled as runs of this source.
