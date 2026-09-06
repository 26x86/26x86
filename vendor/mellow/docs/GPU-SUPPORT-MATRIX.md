# GPU support matrix

> **Scope and precedence:** native macOS backend evidence and Windows host execution remain separate.
> [PLATFORM-DECISIONS](PLATFORM-DECISIONS.md) and [PLATFORM-ARCHITECTURE](PLATFORM-ARCHITECTURE.md)
> take precedence over conflicting assumptions below. [IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md)
> records portable MSL/AIR compute, bounded MSL render objects, Windows OpenCL/OpenGL providers,
> portable Xe tests and kext evidence.
> Standalone probes, translated compute and native driver records remain separate. Apple Metal ABI,
> WindowServer and display acceptance have not passed. Native macOS GPU execution remains unverified.

## 한글 요약

**Windows에서는 자체 C++ 객체를 통한 제한된 GPU compute와 MSL 렌더링이 실행됐다.**
MSL과 synthetic raw AIR 각각 10,000회 제출·독립 readback을 확인했다. Apple Metal ABI 구현은 아니다.
MSL vertex/fragment 렌더링은 1,000회 offscreen·120회 visible 실행에서 전체 픽셀을 검증했다.
visible 결과는 창의 swap API 성공이며 물리 scanout·WindowServer 성공으로 취급하지 않는다.
드라이버가 보고한 대상은 `8086:7D41`이며, 독립적인 physical PCI 소유권 확인은 아니다.
macOS native Xe/Metal 경로에는 `L`·`F`·`R` 기록이 없다. XeMemory는 이식한 PTE/PDE 함수를
호출하며 실제 kext에 링크되지만, 하드웨어 GPU owner와 실행 경로는 아직 검증되지 않았다.
AMD·NVIDIA GPU 실행 backend는 미구현이다. source-intake target은 driver 지원이 아니다.
이 표는 계획이 아니라 **실적**을 기록한다. 계획은 [ROADMAP.md](ROADMAP.md)에 있다.

---

Status vocabulary and evidence levels are defined in [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).
This document records **what has been achieved**, not what is intended. Intent lives in
[ROADMAP.md](ROADMAP.md).

## Summary

| | |
| --- | --- |
| Native macOS/Metal GPU acceleration results | **0** |
| Windows host OpenCL providers executed through MellowRT | **1 bounded Intel GPU provider path**; driver-reported `8086:7D41` |
| Portable C++ objects and translated MSL/AIR compute | **Windows subset executed**; 10,000 submissions each, synthetic AIR positive input |
| Portable C++ render objects and translated MSL vertex/fragment | **Windows subset executed**; 1,000 offscreen / 120 visible frames, independent full RGBA checks |
| Windows host OpenGL provider | **Intel WGL/core3.3 execution observed**; physical PCI identity and scanout remain unverified |
| Native XNU GPU backends with an integrated device owner | **0** |
| Native macOS rows at evidence level `L`, `F`, or `R` | **0** |
| Executable non-Intel native macOS GPU backends | **none**; generic Windows WGL code has no AMD/NVIDIA execution record |

## Per-GPU status

### Windows host OpenCL provider — separate execution domain

[Runtime/OpenCLProvider](../Runtime/OpenCLProvider.md) implements the native adapter used by
MellowRT for bounded OpenCL C compute. Windows execution used the installed Intel OpenCL driver,
with GPU-only selection, queue/event ownership, readback, profiling and completion checks.
The driver-reported identity is `8086:7D41`; independent physical PCI ownership is not established.
This is distinct from the older standalone substrate probe, which bypassed MellowRT.
The current records and exact acceptance scope are in [IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md).
Those direct OpenCL records do not themselves validate translation, the Darwin Xe driver or display output.

### Portable C++ objects and MSL/AIR compute — Windows subset

`Runtime/MetalObjects.*`, `ShaderJit.*` and `AirDecoder.*` implement an explicit C++ object API,
typed MSL lowering, actual LLVM bitcode decoding and checked AIR2.7 SSA lowering. MSL and raw AIR
each passed 10,000 submissions and independent readbacks through one reusable OpenCL pipeline.
The positive AIR fixture is synthetic. The API binds one uint buffer with exact 1D dispatch; it
does not implement Apple's Objective-C Metal protocols, arbitrary AIR/metallib or a
native macOS provider. See [current verification](VERIFICATION-METAL-JIT-2026-09-06.md).

### Portable render objects and Windows OpenGL — separate graphics domain

`RenderShaderJit` lowers the checked MSL vertex/fragment subset to GLSL330, and
`RenderObjects` owns explicit render libraries, functions, pipelines, RGBA8 texture snapshots,
queues and encoders. The native `OpenGLProvider` owns an isolated worker/context/window and
reuses the linked program. The integrated MSL test passed 1,000 offscreen frames and checked
all 3,072,000 pixels against independent triangle coverage and fragment-position gradients.
A separate 120-frame visible test checked 368,640 pixels and swap API acceptance. The fixture
is original MSL source. This is not AIR graphics lowering or Apple Metal ABI conformance.

The actual GL driver reported Intel(R) Graphics / core3.3 / GLSL3.30 / 32.0.101.6737.
GL renderer strings do not establish a PCI ID; the OpenCL-reported 7D41 observation above
is a separate query. Sampled textures, general storage modes, GL/CL sharing, physical scanout
and WindowServer remain unimplemented or unverified. See the
[render contract](RENDER-IMPLEMENTATION.md) and [implementation status](IMPLEMENTATION-STATUS.md).
The [integration audit](../validation/render/integration.json) binds the
[offscreen](../validation/render/objects-offscreen.json) and
[visible](../validation/render/objects-visible.json) results to the tested sources.

### Intel — Xe-LPG / Xe2

The only family with any source path. Device table at
[Mellow/kern_model.hpp](../Mellow/kern_model.hpp).

| Device | Name | Backend | Evidence | Status |
| --- | --- | --- | --- | --- |
| `8086:7D40` | Intel Graphics (Meteor Lake) | `xe` | `S` | `SOURCE PATH` — recognized in the device table only |
| `8086:7D45` | Intel Graphics (Meteor Lake) | `xe` | `S` | `SOURCE PATH` |
| `8086:7D55` | Intel Arc Graphics (Meteor Lake) | `xe` | `S` | `SOURCE PATH` |
| `8086:7DD5` | Intel Graphics (Meteor Lake) | `xe` | `S` | `SOURCE PATH` |
| `8086:7D41` | Intel Graphics 4-Core (Arrow Lake-U) | `xe` | `S`, `B` | Portable Xe encoding integrated into the built kext; native GPU execution unverified |
| `8086:7D51` | Intel Graphics (Arrow Lake-H) | `xe` | `S` | `SOURCE PATH` |
| `8086:7D67` | Intel Graphics (Arrow Lake-S) | `xe` | `S` | `SOURCE PATH` |

For `7D41`, `XeMemory` now calls the portable PTE/PDE encoders through the single
`PortedXeBindings.cpp` translation unit. Version 0.4.3 also adds an opt-in PCI/IOUserClient DMA
diagnostic service; it is not the complete native GPU owner, as gated by
[Mellow/RuntimeReadiness.hpp](../Mellow/RuntimeReadiness.hpp).
[NATIVE-XE-BACKEND-AUDIT.md](NATIVE-XE-BACKEND-AUDIT.md) records the earlier source snapshot.
Source readiness evaluation predicts
stage `physical-provider`, first missing bit `bar0-mapped`; no physical capture establishes this state.

Recognition in a device table does not imply support of any kind.

### Intel — Gen9 through Gen12 (legacy path)

| Family | Backend | Evidence | Status |
| --- | --- | --- | --- |
| Ice Lake (ICL) | `applecompat` | `S` | `SOURCE PATH` — `AppleIntelICLLPGraphicsFramebuffer` found in inspected Tahoe Recovery inputs |
| Tiger Lake (TGL) | `applecompat` | — | **`DEPRECATED`** — no Apple TGL kext found in inspected Recovery inputs; installed-system inventory remains separate; see [LEGACY-DISPOSITION.md](LEGACY-DISPOSITION.md) |

### AMD

| Target | ASIC | Backend | Evidence | Status |
| --- | --- | --- | --- | --- |
| RX 9070 | Navi 48 (RDNA 4, gfx12) | `amdgpu` | — | `NOT IMPLEMENTED` |
| RDNA 2 / 3 generally | — | `amdgpu` | — | `NOT IMPLEMENTED` |

**No executable AMD native macOS GPU backend exists in this tree.** The generic Windows WGL
provider has not been tested on AMD. Source-intake targets, constants and
historical tables do not implement an amdgpu runtime adapter.

Upstream source is available; per-file notices and the full DRM/Linux dependency closure require
review before integration. See [LICENSING.md](LICENSING.md).

### NVIDIA

| Target | ASIC | Backend | Evidence | Status |
| --- | --- | --- | --- | --- |
| RTX 3080 | GA102 (Ampere) | NVIDIA adapter undecided | — | `NOT IMPLEMENTED` |
| RTX 3090 | GA102 (Ampere) | NVIDIA adapter undecided | — | `NOT IMPLEMENTED` |
| Turing through Ada generally | — | NVIDIA adapter undecided | — | `NOT IMPLEMENTED` |

**No executable NVIDIA native macOS GPU backend exists.** The generic Windows WGL provider
has not been tested on NVIDIA. Source-intake support is not runtime driver support.

Upstream source is available: NVIDIA's `open-gpu-kernel-modules`, dual MIT/GPL-2.0, supporting
Turing and later — which covers GA102. This RM/UAPI path requires matching GSP and userspace
components; it is not interchangeable with Mesa NVK/Nouveau. Select and validate the adapter
contract first. The project currently fetches firmware rather than redistributing it; see RFC D09.

## Per-plane readiness, all backends

| Plane | Component | Status |
| --- | --- | --- |
| 4 | MellowMTL — Metal object model | Separate portable C++ compute and render objects executed on Windows; Apple Objective-C Metal ABI remains unimplemented |
| 4 | MellowJIT — shader translation | Typed MSL compute/render and narrow AIR2.7 compute decoding/lowering executed; positive AIR fixture is synthetic, render AIR/general compatibility unimplemented |
| 3 | MellowRT — router and resource model | Policy contracts plus live bounded OpenCL C compute through the native host adapter; general Metal resources remain unimplemented |
| 3 | Host OpenCL provider | Implemented and executed on Windows; macOS/Linux loader paths are not execution evidence |
| 3 | Host OpenGL provider | Windows WGL/core3.3 shader compilation, FBO rendering, fences, readback and optional swap executed; macOS/Linux contexts unimplemented |
| 3 | Mellow provider (`libMellowGL` / `libMellowCL`) | `NOT IMPLEMENTED` |
| 2 | MGAL interfaces | `NOT IMPLEMENTED` — the underlying separation exists in `Xe*` at `S` |
| 2 | MELLOW-UAPI | Full GPU UAPI unimplemented; separate opt-in administrative query/bounded DMA diagnostic IOUserClient exists |
| 2 | Composition root | `NOT IMPLEMENTED` — this is the central gap |
| 1 | MellowKPI | `NOT IMPLEMENTED` |
| 1 | `xe` backend | Six retained Linux functions plus source-derived GGTT bind/unmap; XeMemory encoder calls linked in kext; no native hardware execution |
| 1 | `applecompat` backend | `SOURCE PATH` at `S`; TGL half deprecated |
| 1 | `amdgpu`, selected NVIDIA adapter | `NOT IMPLEMENTED` |
| 0 | `mellow-port` | Intake/report generation exists; complete semantic driver port remains unimplemented |

## What has actually been executed

To be precise about where the project genuinely stands, these things did run:

| Artifact | What ran | What it does not show |
| --- | --- | --- |
| [compiler-evidence/](../compiler-evidence) | Intel `ocloc` 26.27.39122.11 / IGC 2.38.2 compiled OpenCL C for `-device 0x7d41`, producing a 6,944-byte ZEBIN and 1,636-byte SPIR-V with verified EU disassembly | Nothing about Metal. This is OpenCL C, not MSL, and the two use unrelated test vectors |
| [validation/xe-tests.json](../validation/xe-tests.json) | Production `Xe*` sources compiled and executed on a host against emulated MMIO and ownership callbacks | Nothing about hardware. The OS and GPU boundaries are explicit test backends |
| [abi-evidence/](../abi-evidence) | Real Apple binaries from macOS 26.6.2 build 25G83 parsed; 378/378 kext imports resolved against KPI export sets | Symbol names and addresses only — no selector numbers, vtable slots, or struct layouts |
| [tests/xe_guc_firmware_results.json](../tests/xe_guc_firmware_results.json) | The pinned 320,320-byte Intel GuC blob parsed by production code; hash, length, and version verified | No device ever authenticated it |
| [Runtime/OpenCLProvider](../Runtime/OpenCLProvider.md), [current records](IMPLEMENTATION-STATUS.md) | Native Windows OpenCL C compute through MellowRT, using the installed Intel driver | No Metal/JIT, Darwin backend or independently verified physical PCI ownership |
| [Runtime/MetalObjects](../Runtime/MetalObjects.md), [current verification](VERIFICATION-METAL-JIT-2026-09-06.md) | MSL and synthetic raw AIR each translated, driver-compiled once, and executed for 10,000 verified GPU submissions | Portable compute subset; no Apple Metal ABI, rendering, arbitrary AIR compatibility or native Tahoe execution |
| [MSL render objects](RENDER-IMPLEMENTATION.md) | Both MSL stages translated and one GL program reused for 1,000 offscreen / 120 visible frames; independent coverage, gradient and complete raw RGBA verification | Portable source-render subset; no render AIR, sampled textures, Apple Metal ABI, physical scanout or native Tahoe execution |
| [Drivers/PortedXe](../Drivers/PortedXe), [QEMU runner](../Tools/run-ported-xe-emulator.py) | Six retained source functions and GGTT lifetime loops tested in a real Linux QEMU guest: 18,721 checks; five guest negative controls and 19 parser controls | Emulated CPU/RAM and simulated MMIO/DMA/TLB boundaries; QEMU has no Xe GPU model here |
| [kext build](IMPLEMENTATION-STATUS.md) | Version 0.4.3, 33 target translation units linked as Darwin `MH_KEXT_BUNDLE`, including portable encoders and the opt-in diagnostic service; 426 imports statically resolved | Structural build evidence; no kext load or GPU execution |

These records preserve separate scopes. Windows host execution does not promote a native macOS
row, and portable/QEMU/build results do not raise native hardware evidence above `S` or `B`.

## How a row moves

A native macOS backend row advances through the readiness ladder in
[Mellow/RuntimeReadiness.hpp](../Mellow/RuntimeReadiness.hpp), stage by stage, each requiring the
previous:

`Configuration → PhysicalProvider → AddressSpace → Firmware → Execution → KernelProvider →
Userspace → Ready`

The bring-up sequence per GPU is in [ADDING-A-GPU.md](ADDING-A-GPU.md). Capability bits are exposed
only after an `F`-level test, per [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).
