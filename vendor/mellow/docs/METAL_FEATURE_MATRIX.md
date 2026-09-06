# Metal feature matrix

> **Scope and precedence:** [PLATFORM-DECISIONS](PLATFORM-DECISIONS.md),
> [PLATFORM-ARCHITECTURE](PLATFORM-ARCHITECTURE.md), and
> [IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md) govern conflicting draft assumptions.
> Current evidence includes portable MSL/AIR compute, MSL render objects, Windows OpenCL/OpenGL
> execution and portable Xe tests.
> Standalone probe results remain separate; Apple Metal ABI, WindowServer and display acceptance have not passed.
> Native macOS GPU execution remains unverified; see IMPLEMENTATION-STATUS for the recorded scope.

## 한글 요약

이 표는 **시험 계약**이다. 번들 이름, 기능 플래그, 부팅 성공, 화면 출력으로 지원을 추론하지 않는다.
아래 Apple Metal 호환성 기능 행은 **모두 하드웨어 `UNVERIFIED`**다. 별도로 Windows 자체 C++
객체의 제한된 MSL/raw AIR compute 변환·GPU 실행은 각각 10,000회 검증했다. 시스템 Metal 가속 시험은 아니다.
별도의 MSL vertex/fragment 객체 경로도 1,000회 offscreen·120회 visible 실행과 전체 픽셀
대조를 통과했다. 이 결과는 portable 렌더 부분집합이며 Apple ABI·WindowServer 결과와 분리한다.
기존 standalone OpenCL 기판 시험과 새 provider 실행 기록도 구분한다.
확대개편에 맞춰 두 가지가 바뀌었다 — 능력별로 **어느 경로(`cl`/`gl`/`native`)가 그것을 제공하는지**
명시하고, backend별 열을 추가했다. 능력 비트는 `F` 등급 시험 통과 후에만 켠다.

---

This matrix is a test contract. It does not infer support from a bundle name, a feature flag, a
successful boot, or a visible framebuffer. Apple Metal ABI conformance rows below remain hardware
`UNVERIFIED`. The explicitly labelled portable C++ subset has separate Windows GPU evidence.

Status vocabulary and evidence levels are defined in [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md):

- `SOURCE PATH` — related matching, routing, or patch code exists.
- `PLANNED` — described in a design document; no implementation exists.
- `UNKNOWN` — the responsible platform or hardware contract has not been established.
- `NOT IMPLEMENTED` — no Mellow-owned or validated compatible implementation exists.
- `BLOCKED` — a prerequisite test has not passed.
- `VERIFIED` — reserved for a linked, deterministic experiment that excludes CPU fallback.
  **No Apple Metal ABI conformance row currently qualifies.**

## Backend columns

Per-backend readiness is tracked in [GPU-SUPPORT-MATRIX.md](GPU-SUPPORT-MATRIX.md). Summarized:

| Backend | Target | Overall |
| --- | --- | --- |
| `xe` | Intel Xe-LPG / Xe2 | Portable encoding and an opt-in DMA diagnostic service linked in 0.4.3; full GPU IOKit owner absent |
| `applecompat` | Intel ICL via Apple's framebuffer | `SOURCE PATH`; TGL half `DEPRECATED` |
| `amdgpu` | RX 9070 (Navi 48) | `NOT IMPLEMENTED` |
| Selected NVIDIA adapter, TBD | RTX 3080 / 3090 (GA102) | `NOT IMPLEMENTED` |

Because no native macOS backend has reached `Execution` on the readiness ladder, **no Metal capability row differs by
backend yet**. Windows OpenCL and OpenGL providers are separate host API/runtime domains. Per-backend columns are added when the first backend produces a
result that another does not.

## Capability rows

The `Route` column names which [Plane 3](WORKLOAD-RUNTIME.md) route is intended to provide the
capability — this is new, and it is what makes the matrix actionable under the MELLOW architecture.

### Implemented portable compute subset — separate from Apple ABI conformance

The explicit `MellowMTL` C++ API has Device/Buffer/Library/Function/Pipeline/Queue/CommandBuffer/
ComputeEncoder objects, one immutable-size uint buffer, exact 1D dispatch, synchronous completion,
and reusable driver compilation. Typed MSL and actual LLVM-decoded AIR2.7 lower to OpenCL C.
Windows MSL and synthetic raw AIR each passed 10,000 submissions and independent readbacks,
including two ordered encoder dispatches. These results validate the documented portable subset,
not Objective-C Metal protocols, storage-mode equivalence, arbitrary AIR, rendering or macOS GPU
registration. See [MetalObjects](../Runtime/MetalObjects.md), [shader contract](SHADER-JIT-IMPLEMENTATION.md)
and [current verification](VERIFICATION-METAL-JIT-2026-09-06.md).

### Implemented portable render subset — separate from Apple ABI conformance

The explicit RenderDevice API owns render libraries/functions, a retained native program,
RGBA8 texture snapshots, queues, command buffers and encoders. Typed MSL vertex/fragment
source lowers to GLSL330. One triangle, one clearing draw per pass, shared float4 parameters
and fragment position are supported. Clip depth, top-left fragment coordinates and readback
rows are converted explicitly. Normal completion requires a real GL fence, readback and checked
cleanup without receiving a pixel oracle.

Windows tests passed 1,000 offscreen frames with independent checks of all 3,072,000 pixels,
plus 120 visible frames with 368,640 checked pixels and window swap API acceptance. Subpixel
boundary pixels permit only transparent clear or the valid gradient color. These results
do not establish general texture layouts/storage, sampled textures, user varyings, render AIR,
GL/CL interop, Apple Metal ABI or physical scanout. See [RENDER-IMPLEMENTATION](RENDER-IMPLEMENTATION.md).
Actual [offscreen](../validation/render/objects-offscreen.json),
[visible](../validation/render/objects-visible.json) and
[source consistency](../validation/render/integration.json) records retain those separate scopes.

### Device and submission

| Capability | Route | Status | Current evidence or limitation | Hardware result | Next decisive test |
| --- | --- | --- | --- | --- | --- |
| `MTLDevice` creation | any | `NOT IMPLEMENTED` | No Mellow-owned `MTLDevice` exists. `Info.plist` names unverified Apple bundles not found in the inspected Recovery inputs. | **UNVERIFIED** | Enumerate a Mellow device; correlate its registry ID with a physical PCI device. |
| Truthful family/feature exposure | any | `NOT IMPLEMENTED` | PlatformRuntime validates live OpenCL provider contracts; Metal family queries and Metal provider evidence are absent. | **UNVERIFIED** | Record all capability queries; keep each bit disabled until its conformance test passes. |
| Command queue creation | any | Apple ABI `NOT IMPLEMENTED` | Portable C++ compute/render queues execute on Windows; Apple MTLCommandQueue protocol and callback compatibility remain absent. | Apple ABI **UNVERIFIED** | Create one Apple-compatible queue, submit a command buffer, correlate submission and completion. |
| Command-buffer ordering and callbacks | any | `NOT IMPLEMENTED` | — | **UNVERIFIED** | Submit ordered writes; verify callback order with forced-success diagnostics disabled. |
| Error propagation | any | `NOT IMPLEMENTED` | — | **UNVERIFIED** | Force a failure; confirm `MTLCommandBufferStatusError` with a populated `error`. |

### Resources

| Capability | Route | Status | Current evidence or limitation | Hardware result | Next decisive test |
| --- | --- | --- | --- | --- | --- |
| Buffer allocation, `Shared` / `Private` | `cl`, `gl` | `NOT IMPLEMENTED` | — | **UNVERIFIED** | Fill with sentinels, execute a GPU copy, synchronize, compare all bytes. |
| `Managed` storage mode | `cl`, `gl` | `NOT IMPLEMENTED` | The most error-prone mode to emulate — fails as stale data, not as an error. | **UNVERIFIED** | Differential test against the `cpu` reference across `didModifyRange` boundaries. |
| `Memoryless` storage mode | — | `NOT IMPLEMENTED` | Meaningful only for tile-based rendering. | **UNVERIFIED** | Keep unexposed on desktop backends. |
| GPU virtual addressing / residency | `native` | `SOURCE PATH` | XeMemory calls ported PTE/PDE algorithms; host/QEMU tests simulate DMA/TLB boundaries. The full native GPU VM owner remains absent. | **UNVERIFIED** | Trace VA-to-PTE mappings and controlled fault/unmap behavior for one buffer. |
| Texture allocation and layouts | `gl` | Portable RGBA8 target subset implemented; Apple layouts incomplete | Per-pass FBO texture allocation and top-left copied readback tested; persistent VRAM, tiling/compression and Metal storage modes absent. | Windows subset passed; Apple ABI **UNVERIFIED** | Add explicit storage/layout and blit contracts with per-pixel tests. |
| Pixel and texture formats | `gl`, `cl` | RGBA8 render target only | Full RGBA readback checked; upload/sampling and other formats are not exposed. | Windows RGBA8 subset passed; Apple ABI **UNVERIFIED** | Table-driven upload/sample/render/readback for each additional exposed format. |
| Resource heaps and aliasing | `native` | `UNKNOWN` | — | **UNVERIFIED** | Allocate aliased heap resources; verify hazard and lifetime behavior. |
| IOSurface interop | `gl` | `NOT IMPLEMENTED` | Import/export, format, lifetime and sync contracts remain unimplemented. | **UNVERIFIED** | Write from one provider, read from another, compare bytes. |

### Shaders

| Capability | Route | Status | Current evidence or limitation | Hardware result | Next decisive test |
| --- | --- | --- | --- | --- | --- |
| AIR ingestion | any | Portable subset implemented; general Metal ingestion incomplete | Actual LLVM decoding and exact AIR2.7 uint ABI checks; synthetic positive fixture, actual SDL render inputs rejected. | Windows subset passed; Apple ABI/macOS **UNVERIFIED** | Validate a supported Apple-compiler-produced compute fixture and target macOS execution. |
| AIR/MIR → OpenCL C; optional supported IL, compute (J1) | `cl` | Restricted AIR SSA → OpenCL C implemented | Typed single-buffer uint lowering and reusable OpenCL driver compilation; MIR/general IL remains planned. | Windows subset passed; macOS **UNVERIFIED** | Expand shader coverage and compare a supported Apple-produced fixture on macOS. |
| Threadgroup memory and barriers (J2) | `cl` | `PLANNED` | SIMD width, SLM layout, barrier encoding all unresolved. | **UNVERIFIED** | Multi-threadgroup reduction with adversarial scheduling, repeated. |
| Atomics | `cl` | `PLANNED` | Width, scope, and ordering mapping unverified. | **UNVERIFIED** | Contended counters for every exposed type and scope, with exact totals. |
| MSL source → GLSL, graphics | `gl` | Checked vertex/fragment subset implemented | Typed float/vector source, exact three-vertex arrays, shared parameter binding and fragment-position conversion; GLSL330 driver compilation. | Windows full-pixel subset passed; Apple ABI/macOS **UNVERIFIED** | Expand validated stages/resources and execute on a native macOS provider. |
| AIR → GLSL, graphics (J3) | `gl` | `PLANNED` | Source MSL rendering does not implement AIR render lowering; macOS provider is absent. | **UNVERIFIED** | Decode and lower a supported render AIR fixture, then compare pixels. |
| Native ISA via backported Mesa | `native` | `NOT IMPLEMENTED` | Requires a working backend and a ported compiler. | **UNVERIFIED** | — |
| ZEBIN loading (Intel) | `native` | `SOURCE PATH` | [Mellow/XeZebin.cpp](../Mellow/XeZebin.cpp) is well-built but hardcoded to one kernel: exactly one text section named `.text.mellow_evidence`, exactly eight arguments. | **UNVERIFIED** | Generalize, then load an arbitrary compiled kernel. |
| Pipeline cache and serialization | any | `PLANNED` | Key must include AIR hash, backend ID, driver version, JIT version. | **UNVERIFIED** | Cold and warm cache across process restart and reboot, with version invalidation. |

### Rendering

| Capability | Route | Status | Current evidence or limitation | Hardware result | Next decisive test |
| --- | --- | --- | --- | --- | --- |
| Blit encoder | `gl`, `native` | `NOT IMPLEMENTED` | First execution primitive. | **UNVERIFIED** | GPU copy patterned buffers; prove engine progress, fence completion, byte equality. |
| Compute pipeline and dispatch | `cl` | Portable C++ subset implemented; Apple ABI incomplete | One retained driver pipeline, exact 1D uint-buffer dispatch and synchronous checked completion. | Windows subset passed; Apple ABI/macOS **UNVERIFIED** | Extend resource shapes and validate the separate Apple ABI path. |
| Render pipeline creation | `gl` | Portable C++ subset implemented; Apple ABI incomplete | Actual MSL vertex/fragment translation and native program linking; one program reused for each repeated test. | Windows subset passed; Apple ABI/macOS **UNVERIFIED** | Extend pipeline state and validate separate Apple ABI behavior. |
| Rasterization and render targets | `gl` | One-triangle RGBA8 subset implemented | 1,000 MSL offscreen frames; all coverage/gradient pixels checked, including restricted subpixel edge outcomes. | Windows subset passed; Apple ABI/macOS **UNVERIFIED** | Expand primitive/state coverage and verify native macOS execution. |
| Vertex/fragment interpolation | `gl` | User varyings `NOT IMPLEMENTED` | Built-in fragment position, clip-depth conversion and top-left readback tested; custom varying and interpolation contracts absent. | Position-only Windows subset passed; general interpolation **UNVERIFIED** | Vertex-color triangle with explicit perspective/flat interpolation tests. |
| Texture sampling and samplers | `gl` | `NOT IMPLEMENTED` | — | **UNVERIFIED** | Nearest and linear sampling with edge and address-mode cases. |
| Blending and write masks | `gl` | `NOT IMPLEMENTED` | — | **UNVERIFIED** | Layer known colors; compare per format. |
| Depth and stencil | `gl` | `NOT IMPLEMENTED` | — | **UNVERIFIED** | Overlapping geometry across all compare modes and stencil transitions. |
| MSAA and resolves | `gl` | `UNKNOWN` | — | **UNVERIFIED** | Render edges at each exposed sample count; validate resolve output. |

### Synchronization and binding

| Capability | Route | Status | Current evidence or limitation | Hardware result | Next decisive test |
| --- | --- | --- | --- | --- | --- |
| `MTLFence` — intra-buffer | any | `NOT IMPLEMENTED` | — | **UNVERIFIED** | Cross-encoder producer/consumer with timeout and negative ordering cases. |
| `MTLEvent` — cross-buffer | any | `NOT IMPLEMENTED` | — | **UNVERIFIED** | Ordered cross-buffer dependency with a deliberate deadlock case. |
| `MTLSharedEvent` — cross-process | any | `UNKNOWN` | Needs a shared primitive on both provider kinds. | **UNVERIFIED** | Two processes signalling and waiting on one event. |
| Mixed-route command buffers | multiple | `NOT IMPLEMENTED` | Initially **rejected** rather than emitted with unguaranteed ordering. | **UNVERIFIED** | Compute on `cl` then render on `gl`, ordering asserted. |
| Argument buffers Tier 1 | any | `UNKNOWN` | Encoding in AIR not yet surveyed. | **UNVERIFIED** | Bind multiple buffers, textures, and samplers through the tier. |
| Argument buffers Tier 2 | any | `NOT IMPLEMENTED` | Metal 3 gated. | **UNVERIFIED** | — |
| Indirect command buffers | `native` | `UNKNOWN` | — | **UNVERIFIED** | Enable only after direct paths pass; compare direct and indirect output. |

### Metal 3 and beyond

All gated. Metal 3 family support remains unexposed; the project has no implemented Apple
`supportsFamily` protocol endpoint. Portable compute/render success does not enable that family.

| Capability | Status | Note |
| --- | --- | --- |
| Mesh shaders | `NOT IMPLEMENTED` | — |
| MetalFX upscaling | `NOT IMPLEMENTED` | — |
| Fast resource loading | `NOT IMPLEMENTED` | — |
| Ray tracing / acceleration structures | `NOT IMPLEMENTED` | — |
| Tessellation | `UNKNOWN` | Keep unexposed until a conformance sample passes. |
| Sparse resources | `UNKNOWN` | Keep unexposed until map/unmap/fault tests pass. |
| `MTL4*` surface | **out of scope** | See [METAL-EMULATION.md](METAL-EMULATION.md). |

### System integration

| Capability | Status | Current evidence or limitation | Hardware result | Next decisive test |
| --- | --- | --- | --- | --- |
| Windows owned-window swap | Portable API implemented | Offscreen FBO blit and SwapBuffers API acceptance tested for 120 MSL frames; no monitor frame-count or scanout assertion. | Windows swap API passed; physical scanout **UNVERIFIED** | Independently capture displayed frames and pacing. |
| Native macOS display presentation | `SOURCE PATH` | `DisplayMergeNub` has a backing display class; the diagnostic PCI personality does not implement presentation. Hardware-backed display remains unproven. | **UNVERIFIED** | Present a known surface, capture scanout, correlate engine activity. |
| WindowServer acceleration | `BLOCKED` | Requires [Strategy A](METAL-EMULATION.md), which requires a private ABI that has not been recovered. | **UNVERIFIED** | Correlate WindowServer's Metal device, GPU counters, frame timing, CPU-fallback checks. |
| Fault reporting and recovery | `UNKNOWN` | — | **UNVERIFIED** | Inject a bounded invalid command on a disposable setup; verify recovery. |
| Sleep/wake and long-duration load | `BLOCKED` | Functional milestones have not passed. | **UNVERIFIED** | Only after correctness: repeated sleep/wake and one-hour mixed load. |

## Promotion rule

A row becomes `VERIFIED` only when its experiment records inputs, expected and actual outputs,
physical GPU execution evidence, CPU-fallback exclusion, exact software versions, and reproducible
commands.

Any capability that fails must be disabled or reported unsupported. It must not remain exposed
behind a forced feature flag.

**A result produced through the `cpu` route never promotes a row.** That route exists to generate
reference values for differential testing, and using it as evidence of acceleration is precisely
the failure mode this matrix exists to prevent. See [WORKLOAD-RUNTIME.md](WORKLOAD-RUNTIME.md).

## Separate Windows substrate observation

[opencl-windows-substrate.json](../validation/opencl-windows-substrate.json) records
`PASS_OPENCL_GPU_SUBSTRATE_ONLY`: the installed Windows Intel OpenCL driver executed the probe.
`mellow_runtime_used=false`, `mellow_jit_used=false`, `metal_tested=false`,
`macos_driver_tested=false`, `mellow_gpu_acceleration_pass=false`.
The OpenCL-reported GPU identity was not correlated to physical PCI (`physical_pci_identity_verified=false`).
This demonstrates a Windows substrate only; it does not promote a Mellow/backend/family capability.

## Native Windows OpenCL execution through MellowRT

The newer [OpenCLProvider](../Runtime/OpenCLProvider.md) is an implemented native C++ adapter.
It executed bounded OpenCL C compute on the installed Windows Intel GPU driver through MellowRT
planning and completion tracking. The driver reports `8086:7D41`; independent physical PCI ownership
is not established by that query. Queue/event ownership, readback and ordered profiling are checked.
See [IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md) for the current source-bound records.

The provider directly accepts OpenCL C. The newly implemented object/frontend layer translates
the supported MSL/AIR subset before invoking it; that evidence is recorded separately above.
Neither path promotes Apple Metal ABI conformance. The portable Xe QEMU tests and 33-unit 0.4.3
diagnostic kext build do not prove native GPU execution or Metal support on Tahoe.
