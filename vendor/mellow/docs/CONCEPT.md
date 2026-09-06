# The MELLOW concept

> **Design draft; implementation status is separate.**
> [PLATFORM-DECISIONS](PLATFORM-DECISIONS.md) and [PLATFORM-ARCHITECTURE](PLATFORM-ARCHITECTURE.md)
> take precedence over conflicting assumptions below. [IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md)
> records policy/intake, the native Windows OpenCL provider, portable Xe tests and kext build evidence.
> Standalone OpenCL probes and MellowRT provider execution have separate records; no Metal, WindowServer
> or display acceptance has passed. Native macOS GPU execution remains unverified.

## 한글 요약

**MELLOW = Metal Emulation Layer Logic for OpenGL/OpenCL Workloads.**
Mellow는 Apple의 Intel 드라이버를 빌려 쓰는 호환 패치에서, **Metal을 직접 에뮬레이션하는 레이어**로
정체성을 바꾼다. 검증된 GL/CL 제공자에서 Metal 워크로드 부분집합을 실행하고,
드라이버가 없는 GPU는 검토된 Linux family recipe와 Darwin adapter를 구현해 확장한다.
전체 Metal 2/3 동등성이나 임의 Linux driver의 자동 완성은 보장하지 않는다.
MSL 입력은 버전이 고정된 SDK AIR adapter 또는 별도 frontend가 필요하다.
GPUCompiler 심볼 발견만으로 독립적인 public compiler 호출 경로가 입증되지는 않는다.

---

## The name

**M**etal **E**mulation **L**ayer **L**ogic for **O**pen**G**L/**O**pen**CL** **W**orkloads.

The name states the whole thesis: Mellow *emulates* Metal, and it expresses the resulting work as
OpenGL and OpenCL **workloads**. Where those workloads can be executed by an existing accelerated
substrate, Mellow needs no kernel driver at all. Where they cannot, Mellow supplies the substrate
too.

## What changed

The legacy Mellow Lilu plug-in attempted to adapt Apple's graphics stack to an Intel
Core Ultra iGPU. This was not a validated acceleration path. The strategy was **impersonation**: present a TGL-compatible identity, patch
Apple's framebuffer and accelerator kexts, and let Apple's binaries do the real work.

That strategy has run out of road, for reasons that are documented rather than assumed:

- **The inspected Recovery inventory is limited.** The inspected Tahoe 25G83 Recovery collections contain `IOAcceleratorFamily2`,
  `AppleGraphicsControl`, `AppleGraphicsDeviceControl`, `AppleGraphicsDevicePolicy`,
  `AppleVirtualGraphics`, and the CFL/ICL/KBL framebuffers — no Intel acceleration kext or
  `AppleIntelTGLGraphics` was found in these inputs. This does not inventory every installed Tahoe
  system or optional component. See [TAHOE-ABI.md](TAHOE-ABI.md).
- **The user-space driver was never obtained.** The declared main executable of
  `AppleIntelICLGraphicsMTLDriver.bundle` lives inside a RIDIFF10 cryptex that was not
  reconstructed; only the `libigdmd.dylib` telemetry helper was extracted. See
  [abi-evidence/intel-umd-partial.json](../abi-evidence/intel-umd-partial.json).
- **The provenance is unverified.** The TGL bundles that
  [Mellow/Info.plist](../Mellow/Info.plist) names are an external community prerequisite whose
  existence, origin, and redistribution rights were all unresolved. See
  [USERLAND-METAL-EVIDENCE-AUDIT-2026-09-05.md](USERLAND-METAL-EVIDENCE-AUDIT-2026-09-05.md).
- **Impersonation does not generalize.** It is Intel-only by construction. It says nothing about
  how to support a GPU that Apple never shipped a driver for.

So the strategy inverts. Instead of borrowing Apple's driver, Mellow supplies the implementation
behind Metal. That is a much larger project, and this document set exists to make it a tractable
one.

## The thesis, in two halves

### Half one — Metal on top of an accelerated substrate

> *"OpenGL과 OpenCL을 지원하고 가속이 되는 상태라면, Metal 2/3 가속을 JIT로 진행해준다."*

Working accelerated GL/CL can execute a verified subset of Metal workloads through translation.
Resource, shader and synchronization semantics require individual validation; GL/CL availability
does not establish full Metal 2/3 equivalence.

What is missing is the *translation*, and translation is what a layer does. The prior art runs the
other direction — MoltenVK maps Vulkan onto Metal, ANGLE maps OpenGL onto D3D/Vulkan/Metal, Zink
maps OpenGL onto Vulkan. These projects illustrate translation techniques; they do not establish
Mellow's feasibility or a claim that no reverse-direction project exists.

On this half of the thesis, Mellow needs **no kernel code whatsoever**. It is a user-space layer
sitting on `OpenGL.framework` and `OpenCL.framework`.

### Half two — supplying the substrate that isn't there

> *"RTX 3080, RTX 3090, RX 9070 등 완전 미지원 그래픽카드인 경우에도 '리눅스 타겟으로 공개된
> 드라이버'를 기준으로 드라이버 백포팅을 진행해놓는다."*

For an RTX 3080 (GA102), an RTX 3090 (GA102), or an RX 9070 (Navi 48, RDNA4), macOS has no Metal
driver — and no OpenGL or OpenCL driver either. Half one has nothing to stand on.

Linux provides candidate driver sources; this list is not a dependency-closure license approval:

| GPU | Kernel driver | License |
| --- | --- | --- |
| RX 9070 (Navi 48) | `drivers/gpu/drm/amd` | Per-file notices and DRM/Linux dependency closure require review |
| RTX 3080 / 3090 (GA102) | NVIDIA `open-gpu-kernel-modules` | dual MIT / GPL-2.0 |
| Arc, Xe-LPG, Xe2 | `drivers/gpu/drm/xe` | Per-file notices and DRM/Linux dependency closure require review |

So the substrate gets built by **backporting those drivers**, and Mellow's own Mesa-derived
OpenGL and OpenCL providers run on top of the result. Once that substrate exists, half one applies
unchanged.

The requirement attached to this is explicit and is the hardest engineering constraint in the
project:

> *"드라이버는 만들기 쉬워야 하며, 백포팅의 과정이 쉬워야 한다. 리눅스 드라이버 파일만 넣어도
> 바로 백포팅되는 수준이여야 한다."*

Backporting must be a **pipeline**, not a transcription project. See
[BACKPORT-PIPELINE.md](BACKPORT-PIPELINE.md) for how that is made credible, and
[MELLOWKPI.md](MELLOWKPI.md) for the proposed semantic adapter contracts; minimizing source changes depends on implementing
and validating those contracts first.

## Compiler evidence and unresolved frontend work

The macOS ABI survey supplies version-specific compiler clues; it does not establish a usable
frontend or determine the engineering effort:

`Metal.framework` links `GPUCompiler.framework/Versions/32023/libllvm-flatbuffers.dylib` and
`libGPUCompilerUtils.dylib`, and defines the classes `MTLCompiler`, `MTLAirEntry`, `MTLBinaryKey`,
`MTLBufferRelocation`, and `MTLConstantRelocation`
([abi-evidence/tahoe-graphics-inventory.json](../abi-evidence/tahoe-graphics-inventory.json)).

Apple documents SDK tools that produce AIR. Framework symbols do not establish a public standalone
compiler ABI or a compiler usable without an existing Metal device.

That reframes the problem. The previous plan identified the absence of a Metal front end as the
blocking obstacle:

> *"no Metal-to-IGC front end was built"* — [IOACCEL-METAL.md](IOACCEL-METAL.md)

The first input is a known SDK-generated AIR corpus through a versioned adapter. Unknown dialects
fail compilation; runtime MSL requires a verified SDK adapter or separately implemented frontend. See [SHADER-JIT.md](SHADER-JIT.md) and [AIR-ABI.md](AIR-ABI.md).

## Where Metal stops being Apple's and starts being Mellow's

> *"어느정도 레이어 이상으로는 Metal이 아닌 Mellow를 통하여 Metal를 돌아가게 만들면 된다."*

This sentence sets the architectural seam, and it is the right seam. Mellow does not replace
`Metal.framework` — it replaces what sits *behind* the Metal API for a given device. Two
attachment points exist, at different heights:

- **Interposition (higher, portable).** `libMellowMTL.dylib` provides Objective-C classes
  conforming to `MTLDevice` and its collaborators, and interposes `MTLCreateSystemDefaultDevice`
  and `MTLCopyAllDevices`. This is limited to opted-in test processes. Binary consumers, signing
  restrictions and OS updates require separate tests; system-wide replacement is not promised.
- **Driver plug-in (lower, system-wide).** A bundle named by the accelerator's
  `MetalPluginClassName` property, whose principal class subclasses the private
  `MTLIOAccelDevice`. These names are ABI investigation leads; WindowServer/CoreAnimation support
  needs a complete build-pinned contract and separate runtime evidence.

Both are described in [METAL-EMULATION.md](METAL-EMULATION.md). Interposition comes first because
it is achievable and independently testable; the plug-in path follows as the ABI record is built up.

## What this concept does not claim

Consistent with [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md), the execution paths above are not implemented; the policy/intake code is tracked separately.
Specifically, as of this document:

- No Metal emulation layer exists in this repository.
- No shader JIT exists.
- No vendor-neutral abstraction layer exists; the `Xe*` modules are Intel-specific and, as
  recorded at [Mellow/RuntimeReadiness.hpp:84](../Mellow/RuntimeReadiness.hpp), have no IOKit
  owner and therefore no call path.
- Source intake/report generation and platform policy code now exist; complete driver translation,
  platform bindings and GPU execution do not. See [IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md).
- No executable AMD or NVIDIA GPU backend exists. Source-intake targets are not driver support.

This document describes a target. [ROADMAP.md](ROADMAP.md) describes the order of approach, and
[GPU-SUPPORT-MATRIX.md](GPU-SUPPORT-MATRIX.md) records how far each GPU has actually come — which
is, at present, no distance at all.
