# Porting status

> **Scope and precedence:** [PLATFORM-DECISIONS](PLATFORM-DECISIONS.md),
> [PLATFORM-ARCHITECTURE](PLATFORM-ARCHITECTURE.md), and
> [IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md) govern conflicting draft assumptions.
> Current evidence includes portable MSL/AIR compute, MSL render objects, Windows OpenCL/OpenGL
> execution and portable Xe tests.
> Standalone probe results remain separate; Apple Metal ABI, WindowServer and display acceptance have not passed.
> Native macOS GPU execution remains unverified; see IMPLEMENTATION-STATUS for the recorded scope.

## 한글 요약

**증거를 기록하며, 야심을 기록하지 않는다.** 확대개편에 맞춰 범위를 "7D41 포팅"에서
"평면별·backend별 포팅 상태"로 재조정했다. 증거 사다리 `S/B/L/F/R`와 7개 분류는 그대로다.
IORegistry에 iGPU가 보이거나, framebuffer가 로드되거나, 데스크톱에 도달하는 것은 그 자체로
하드웨어 가속을 증명하지 않는다.
**native macOS Xe/Metal 경로의 `L`·`F`·`R` 증거는 없다.** Windows에서는 자체 C++ 객체·MSL 및
synthetic raw AIR의 제한된 compute를 각각 10,000회 검증했다. 기존 standalone 기판 시험, 이식 알고리즘의
QEMU 시험, kext 빌드는 각각 별도의 범위이며 아래처럼 기록한다.
별도의 MSL vertex/fragment 객체 경로는 1,000회 offscreen·120회 visible 렌더링에서 전체
픽셀을 대조했다. Windows swap API 결과는 물리 scanout·Apple Metal ABI·WindowServer 결과가 아니다.
[렌더링 증거 묶음](../validation/render/integration.json)은 실제 픽셀·완료·source hash 검증 범위를 기록한다.

---

Snapshot: 2026-09-06. This document tracks **evidence, not ambition**. Unless a row explicitly
cites a captured result, every hardware result is `UNVERIFIED`. Seeing an iGPU in the IORegistry,
loading a framebuffer, or reaching a desktop does not by itself prove hardware acceleration.

Evidence levels, change classifications, and the no-manufactured-success rule are defined
normatively in [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md) and summarized here.

## Evidence levels

Cumulative. A component at `F` must also satisfy `S`, `B`, and `L`.

| Level | Meaning |
| --- | --- |
| `S` | A source path exists and has been reviewed. This proves neither compilation nor execution. |
| `B` | A reproducible build completed and its artifact, commit, toolchain, and log were retained. |
| `L` | A hardware log shows that the intended path executed on the physical target. |
| `F` | A deterministic functional test produced the expected GPU result with CPU fallback excluded. |
| `R` | Repeated functional and recovery tests passed across reboot, sleep/wake, and sustained load. |

**No native macOS Xe/Metal execution path has `L`, `F`, or `R` evidence.** Windows OpenCL
provider execution through MellowRT is recorded separately from both the standalone substrate
probe and this Darwin driver stack. Its `8086:7D41` identity is driver-reported; independent
physical PCI ownership is not established by the OpenCL query.

## Classifications

| Classification | Use |
| --- | --- |
| **Diagnostic** | Adds observation or bypasses a check solely to locate a failure. |
| **Workaround** | Masks a known mismatch without implementing the underlying contract. |
| **Feature-limited implementation** | Implements a documented subset and rejects the rest. |
| **Prototype implementation** | Exercises a plausible path whose correctness and recovery are incomplete. |
| **Stabilization candidate** | Has deterministic functional evidence and is undergoing regression testing. |
| **Production-level implementation** | Has defined compatibility, recovery, regression, and performance evidence. |
| **Not implemented** | No Mellow-owned implementation exists at this layer. |

Device-ID spoofing, assertion bypasses, forced return values, and capability-bit changes are
diagnostics or workarounds. They must never be promoted merely because the system boots.

## Status by plane

### Plane 4 — MellowMTL and MellowJIT

| Layer | Current source state | Classification | Evidence | Hardware result |
| --- | --- | --- | --- | --- |
| Metal object model | Separate portable MellowMTL compute and render devices, libraries/functions, pipelines, buffers/RGBA8 texture snapshots, queues and encoders exist; Apple Objective-C `MTLDevice` conformance and registration do not. | Feature-limited implementation | Current object tests and GPU records; RENDER-IMPLEMENTATION | Windows bounded compute/render subsets passed; native macOS **UNVERIFIED** |
| Attachment — interposition | Planned. The `cs_validate_page` hook exists but its body is gated to Sonoma and is dead on Tahoe. | Not implemented | none | **UNVERIFIED** |
| Attachment — driver plug-in | Planned. The `gpu_bundle_find_trusted` discovery hook exists but is commented out at [Mellow/DYLDPatches.cpp:113](../Mellow/DYLDPatches.cpp). | Not implemented | none | **UNVERIFIED** |
| AIR ingestion | Actual LLVM raw/wrapped bitcode decoder, observed metallib container parser and exact AIR2.7 metadata admission exist. Positive AIR fixture is synthetic; general Apple artifact compatibility remains unimplemented. | Feature-limited implementation | Decoder/roundtrip/control tests and current object GPU record | Windows synthetic AIR compute passed; native macOS **UNVERIFIED** |
| Shader lowering | Typed MSL AST and AIR SSA lower the checked single-buffer uint subset to OpenCL C; driver pipelines compile once and are reused. | Feature-limited implementation | 2,269 frontend checks, 72 CPU references, 9 CL syntax fixtures; current GPU records | Windows MSL/raw AIR each passed 10,000 submissions; native macOS **UNVERIFIED** |
| MSL render lowering | Checked vertex/fragment float/vector source lowers to GLSL330; exact triangle, shared parameters, clip-depth and fragment-coordinate conversion. Render AIR and sampled textures are absent. | Feature-limited implementation | 969 frontend checks, including Linux ASan/UBSan; independent full-pixel GPU records | Windows 1,000 offscreen / 120 visible frames passed; native macOS **UNVERIFIED** |
| Offline compiler harness | Intel `ocloc` 26.27.39122.11 / IGC 2.38.2 compiled OpenCL C for `-device 0x7d41`; 6,944-byte ZEBIN with verified EU disassembly. **This is OpenCL C, not Metal.** | Feature-limited tooling | `B` | **UNVERIFIED** |
| Acceptance harnesses | [Tools/metal-probe.swift](../Tools/metal-probe.swift) and [Userspace/metal_session.py](../Userspace/metal_session.py) are careful clients with strong attribution checks. Never compiled or executed — no macOS or Metal in the build environment. | Feature-limited implementation | `S` | **UNVERIFIED** |

### Plane 3 — MellowRT

| Layer | Current source state | Classification | Evidence | Hardware result |
| --- | --- | --- | --- | --- |
| Workload router | PlatformRuntime admits explicit OpenCL C steps and tracks actual host-provider completion; default Metal steps are rejected. | Feature-limited implementation | Host tests and Windows runtime record, see IMPLEMENTATION-STATUS | Bounded Windows OpenCL execution passed; macOS unverified |
| Resource model and storage modes | Route/resource policy, uint-buffer compute and separate copied RGBA8 render snapshots exist. General Metal storage modes, sampled textures and interop remain planned. | Feature-limited implementation | Host and bounded provider/object tests, see IMPLEMENTATION-STATUS | Windows uint compute and single-target RGBA8 rendering passed |
| Host OpenCL provider | Native adapter compiles and submits OpenCL C through the installed host driver; Windows executed. Other loader paths require host tests. | Feature-limited implementation | See IMPLEMENTATION-STATUS and Runtime/OpenCLProvider.md | Driver-reported `8086:7D41`; physical PCI ownership not independently verified |
| Host OpenGL provider | Isolated Windows WGL/core3.3 worker/context, actual GLSL programs, RGBA8 FBO rendering, fences, readback and optional swap. RenderDevice selects it explicitly; GL/CL sharing is absent. | Feature-limited implementation | Provider and MSL-object GPU records; Runtime/OpenGLProvider.md | Intel Windows execution passed; physical PCI identity, scanout and native macOS **UNVERIFIED** |
| Mellow provider (Mesa-derived) | Planned. | Not implemented | none | **UNVERIFIED** |

### Plane 2 — MGAL and MELLOW-UAPI

| Layer | Current source state | Classification | Evidence | Hardware result |
| --- | --- | --- | --- | --- |
| Logic/platform separation | Portable Xe algorithms use explicit ops/callback boundaries and production sources are host-tested with `-Werror`; IOKit binding code remains a separate kernel boundary. | Feature-limited implementation | `S`, `B` | **UNVERIFIED** |
| Named MGAL interfaces | Full named interface extraction and a single GPU backend admission owner remain incomplete. | Not implemented | none | **UNVERIFIED** |
| Composition root | Complete GPU owner remains absent: MMIO, VM publication, firmware, transport, interrupt, fence and execution are not integrated. The separate diagnostic service only binds bounded administrative PCI/DMA operations. | Not implemented for GPU execution | Diagnostic source/build records, see IMPLEMENTATION-STATUS | **UNVERIFIED** |
| MELLOW-UAPI | Full GPU UAPI remains unimplemented. TahoeDiagnostic supplies a separate admin IOUserClient for query and bounded DMA preparation/release, without GPU submission. | Feature-limited diagnostic implementation | 6,328 host protocol checks and actual kext cross-link | Native service/DMA execution **UNVERIFIED** |
| Readiness ladder | 20-bit fail-closed gate with ordered stages; monotonic; `mayAdvertiseMetal` requires all bits. | Feature-limited implementation | `S` | Source-predicted stage `physical-provider`, first missing `bar0-mapped`; no physical capture |

### Plane 1 — Backends and MellowKPI

| Layer | Current source state | Classification | Evidence | Hardware result |
| --- | --- | --- | --- | --- |
| MellowKPI | No `linux/*` or `drm/*` headers exist. | Not implemented | none | **UNVERIFIED** |
| `xe` — MMIO / forcewake | Real BAR0 mapping helpers, bounds and ordering, GMD_ID read, GT/render forcewake with ACK and timeout. | Prototype implementation | `S`, `B` | **UNVERIFIED** |
| `xe` — memory and page tables | 48-bit VA, owner/generation, 46-bit DMA; XeMemory calls retained Linux PTE/PDE algorithms. Portable GGTT bind/unmap has simulated ownership/TLB tests; native table build retains rollback and seal. | Prototype implementation | `S`, `B`; 18,721 checks in a real QEMU Linux guest | **UNVERIFIED** on the GPU; guest CPU/RAM execution only |
| `xe` — firmware and GuC transport | CSS parse, WOPCM, DMA upload and authentication polling; CTB/HXG packets with credits and epochs. | Prototype implementation | `S`, `B` | **UNVERIFIED** — no device ever authenticated the blob |
| `xe` — submission and execution | **Two rival stacks.** `SubmissionQueue` and `EvidenceExecution` are unconnected; `XeMemorySubmission.hpp` and `XeInterruptDispatch.hpp` are referenced only from `tests/` and are outside the kext include closure. | Prototype implementation | `S` | **UNVERIFIED** |
| `xe` — interrupt and fence | Tile/master/identity handling, `IOFilterInterruptEventSource` and workloop, coherent GGTT qword fence reads. | Prototype implementation | `S`, `B` | **UNVERIFIED** |
| `xe` — ZEBIN loader | ELF64/IntelGT parse, staging, relocation. Hardcoded to one kernel named `.text.mellow_evidence` with exactly eight arguments. | Feature-limited implementation | `S`, `B` | **UNVERIFIED** |
| **`xe` — reachability** | XeMemory calls the portable encoder implementation; PortedXeBindings is linked once. Complete GPU device-owner construction and hardware admission remain absent. | Partial integration | `B`; kext linkage is structural evidence only | **UNVERIFIED** |
| `applecompat` — ICL | Solve/route lists against `AppleIntelICLLPGraphicsFramebuffer`, which was found in the inspected Tahoe Recovery inputs. | Prototype / workaround | `S` | **UNVERIFIED** |
| `applecompat` — TGL | **`DEPRECATED`.** TGL kext absent from inspected Recovery inputs; full installed-system inventory and provenance unverified. See [LEGACY-DISPOSITION.md](LEGACY-DISPOSITION.md). | Workaround | `S` | **UNVERIFIED** |
| `amdgpu`, selected NVIDIA adapter | Source-intake targets exist; executable GPU backends do not. | Not implemented | none | **UNVERIFIED** |
| Display | `DisplayMergeNub` has a backing IOKit class in source; runtime attach is unverified. Link training, modeset, hotplug, and scanout have no recorded target evidence. | Prototype plus device-specific workaround | `S` | **UNVERIFIED** |

### Plane 0 — `mellow-port`

| Layer | Current source state | Classification | Evidence | Hardware result |
| --- | --- | --- | --- | --- |
| Source intake/report and bounded generation | `Tools/mellow-port.py inspect/plan/generate` exist. Reviewed PortedXe integration is a separate manual source port; the intake tool does not perform semantic driver translation or XNU binding. | Feature-limited analysis tooling | Tests, see IMPLEMENTATION-STATUS | — |
| Firmware fetch and verify | [tests/xe_submission_fetch_firmware.py](../tests/xe_submission_fetch_firmware.py) checks size and SHA-256, opens exclusive-create, refuses to write on mismatch. Intel GuC only. | Feature-limited implementation | `B` | — |
| Cross-build | [Tools/cross-build.py](../Tools/cross-build.py) built 0.4.3 from 33 target units as Darwin `MH_KEXT_BUNDLE`; portable encoders and diagnostic service included, inputs hashed before/after. | Feature-limited implementation | `B` | No kernel load or GPU execution |
| ABI validation | [Tools/tahoe-abi.py](../Tools/tahoe-abi.py) resolves imports against inspected KPI/Lilu export sets; current diagnostic build resolves 426/426 imports. Parser regressions remain separate from native linker/load acceptance. | Feature-limited implementation | `B` | — |

## Current ceiling

**Prototype / workaround.** Nothing in this repository is a stabilization candidate or a
production-level implementation.

The portable encoder integration is now callable inside the kext, while the complete native GPU
device owner remains unimplemented. Windows host OpenCL execution does not supply that missing
Darwin ownership or Metal path.

## Phase gates

Full sequencing in [ROADMAP.md](ROADMAP.md). The hardware bring-up order is unchanged:

1. **Environment** — pin macOS and build versions, retain a CI artifact, record a Mellow-disabled
   baseline, prove a known-good recovery boot.
2. **Identification and mapping** — prove physical identity, expected driver selection, and
   positive BAR0 mapping evidence, without interpreting a missing error as success.
3. **Execution primitive** — submit one bounded NOP or copy; correlate ring head/tail, interrupt
   count, fence completion, and output bytes.
4. **Compute** — deterministic buffer kernel; verify every output byte with CPU fallback excluded.
5. **Render** — offscreen first, then scanout, with capture and corruption checks.
6. **Metal** — device, queue, library, pipeline, execution, result correctness, in that order.
   Update [METAL_FEATURE_MATRIX.md](METAL_FEATURE_MATRIX.md) per test.
7. **Stability and optimization** — only after functional evidence exists.

## Safety and recovery rules

- Test only with an OpenCore picker entry that can disable Mellow, and with a separately preserved
  known-good EFI. Confirm that recovery path before the first Mellow boot.
- Keep physical access or an independently tested remote/serial path. Do not perform the first
  experiment on the only bootable installation.
- One change per commit, one hypothesis per experiment. Record the exact commit, artifact hash,
  macOS build, EFI hash, and boot arguments.
- Do not combine Mellow and WhateverGreen during isolation testing.
- Treat `mellow-dmc=skip` as "skip Mellow compatibility writes and pass through Apple's
  initializer", not as a guarantee of zero MMIO writes.
- Never use arbitrary `/dev/mem` access, blind MMIO writes, voltage or clock changes, or firmware
  flashing. A register write requires a cited definition, a target-generation review, a rollback
  plan, and a bounded test.
- Stop immediately on a panic, GPU hang, display corruption, input loss, or repeated timeout. Boot
  the known-good entry, preserve evidence, classify the experiment as failed, and do not stack
  another workaround on it.
- Diagnostic bundles can contain serial numbers, paths, and other private metadata. Review and
  redact before sharing.

## Updating this file

Every status promotion must link to an experiment record containing raw logs, expected and actual
results, a fallback check, and an artifact/commit identity.

Source comments such as `V###`, "fixed", "working", or "loaded" are historical labels only and do
not count as evidence.

## Separate Windows substrate observation

[opencl-windows-substrate.json](../validation/opencl-windows-substrate.json) records
`PASS_OPENCL_GPU_SUBSTRATE_ONLY`: the installed Windows Intel OpenCL driver executed the probe.
`mellow_runtime_used=false`, `mellow_jit_used=false`, `metal_tested=false`,
`macos_driver_tested=false`, `mellow_gpu_acceleration_pass=false`.
The OpenCL-reported GPU identity was not correlated to physical PCI (`physical_pci_identity_verified=false`).
This demonstrates a Windows substrate only; it does not promote a Mellow/backend/family capability.

## Current native provider, portable port and build evidence

The newer [OpenCLProvider](../Runtime/OpenCLProvider.md) runs bounded OpenCL C compute through
MellowRT on Windows. It checks planning, queue/event ownership, readback, profiling and completion,
and rejects unsupported Metal input. This result must not be described as the older standalone
probe, which has `mellow_runtime_used=false`.

The portable C++ [MetalObjects](../Runtime/MetalObjects.md) now translate the supported MSL/AIR
subset before calling that provider. MSL and synthetic raw AIR each passed 10,000 GPU submissions
and independent readbacks through one compiled pipeline, plus ordered encoder checks. The
[current verification](VERIFICATION-METAL-JIT-2026-09-06.md) records this additional scope. It does
not provide Apple Metal ABI conformance, rendering, native Tahoe GPU ownership or system registration.

[Drivers/PortedXe](../Drivers/PortedXe) contains six retained Linux source functions and separately
adapted GGTT bind/unmap loops. The [QEMU runner](../Tools/run-ported-xe-emulator.py) executed the
actual portable source in a diskless Linux guest: 18,721 checks passed. Five guest negative controls
and 19 parser controls verified failure handling. The simulated MMIO/DMA/TLB boundary does not
authenticate firmware, access a real Xe GPU or load the Darwin kext.

Version 0.4.3 links 33 target translation units as `MH_KEXT_BUNDLE`; XeMemory uses the ported
encoder through one binding unit, and the new PCI/IOUserClient service supports bounded DMA
diagnostics only. Exact records and limits are maintained in
[IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md). No sustained-load or reset/reboot acceptance
is inferred from these bounded runs.
