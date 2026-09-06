# Repository layout

> **Scope and precedence:** [PLATFORM-DECISIONS](PLATFORM-DECISIONS.md),
> [PLATFORM-ARCHITECTURE](PLATFORM-ARCHITECTURE.md), and
> [IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md) govern conflicting draft assumptions.
> Current evidence includes portable MSL/AIR objects, Windows OpenCL execution and portable Xe tests.
> Standalone probe results remain separate; Apple Metal ABI, WindowServer and display acceptance have not passed.
> Native macOS GPU execution remains unverified; see IMPLEMENTATION-STATUS for the recorded scope.

## 한글 요약

목표 디렉터리 구조와 현재→목표 이관 대응표다. **이 문서는 서술이며, P0에서는 실행하지 않는다.**
기존 source의 디렉터리 이관은 아직 실행하지 않았다. Runtime/의 자체 C++ compute 객체·MSL/AIR
frontend·LLVM decoder·OpenCL provider, Drivers/PortedXe/의 Linux 함수 이식과 Tools/mellow_port/는 현재 존재한다.
XeMemory의 encoder 연결은 실제 kext에 포함됐으며, 아래 목표 kernel/userspace/tools 구조와 구별한다.
핵심 원칙은 **평면별 분리** — `kernel/`(Plane 1–2), `userspace/`(Plane 3–4), `tools/`(Plane 0) —
와 **backend별 격리**다. 기존 증거 자료(`validation/`, `abi-evidence/`, `compiler-evidence/`,
`tests/*.json`)는 **전량 그대로 보존**한다.

---

**Status: current tree plus a proposed migration. Portable compute objects/JIT, Runtime policy/OpenCL,
reviewed PortedXe integration, opt-in Tahoe diagnostics and Tools/intake files exist. Directory migration is not performed; target
directories and future bundles below are proposals.**

## Current layout

```
Mellow/
├─ Mellow/                 plug-in/Xe modules, PortedXeBindings.cpp and opt-in TahoeDiagnostic service
├─ Drivers/PortedXe/       six retained Linux functions, GGTT bind/unmap, notices and provenance
├─ Runtime/                MetalObjects, ShaderJit/AirDecoder, PlatformRuntime and OpenCLProvider
├─ Tools/                  build, ABI, Metal, test orchestration
│  ├─ mellow-port.py        current inspect/plan/generate entry point
│  ├─ mellow_port/          source analysis/report and bounded generation
│  ├─ run-platform-tests.py policy contract host-test runner
│  ├─ run-opencl-runtime.py native OpenCL provider build/acceptance
│  ├─ run-metal-objects.py  MSL/AIR portable object build and supervised GPU acceptance
│  ├─ run-shader-jit-tests.py typed frontend, CPU references and optional LLVM roundtrip
│  ├─ mellow-shader.py      supervised bitcode decoding and restricted lowering CLI
│  ├─ mellow_air.py         observed metallib/raw/wrapped bitcode decoder
│  └─ run-ported-xe-*.py   portable host tests and real QEMU Linux guest execution
├─ Examples/               opt-in portable MSL compute client
├─ Userspace/              metal_session.py, mellow_acceptance.py, tahoe_diag_client.c
├─ tests/                  host tests, fixture provenance and result JSON; fixtures/air retains origins
├─ validation/             evidence JSON
├─ abi-evidence/           macOS ABI survey artifacts
├─ compiler-evidence/      Intel ocloc output
├─ docs/                   flat document set
├─ Lilu.kext/  MacKernelSDK/
└─ Mellow.xcodeproj/       33-unit 0.4.3 kext includes PortedXe/diagnostics; Runtime remains userspace
```

`Mellow/` still contains Apple compatibility patching, experimental Xe modules and display code.
The portable source now has its own `Drivers/PortedXe` boundary. Its six retained function bodies
and adapted GGTT loops preserve their source notices; this separation does not relicense the rest
of the tree. XeMemory calls PTE/PDE wrappers through one binding translation unit, retaining its
46-bit DMA and read-only contracts. The 0.4.3 `MH_KEXT_BUNDLE` adds a bounded administrative
PCI/DMA diagnostic IOUserClient. Its build and 426-import resolution are structural evidence;
native GPU execution and the complete device owner remain unverified or unimplemented.

Windows translated MSL/synthetic AIR compute uses `Runtime/MetalObjects`, `ShaderJit`, `AirDecoder`
and the reusable `OpenCLProvider`, independently of that kext. This is an explicit C++ subset,
not Apple's Objective-C Metal ABI or system device registration. Portable Xe
tests executed 18,721 checks in a Linux QEMU guest, with simulated MMIO/DMA/TLB boundaries and no
Xe GPU model. Current source-bound evidence is indexed by
[IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md).

## Proposed target layout — not the current filesystem

```
Mellow/
├─ README.md
├─ docs/
│  ├─ PLATFORM-ARCHITECTURE.md    reviewed architecture
│  ├─ PLATFORM-DECISIONS.md       reviewed contract decisions
│  ├─ IMPLEMENTATION-STATUS.md    current runnable code and evidence
│  ├─ CONCEPT.md                 concept draft
│  ├─ ARCHITECTURE.md            the five planes
│  ├─ EVIDENCE-POLICY.md         normative; everything references this
│  ├─ ROADMAP.md
│  ├─ REPO-LAYOUT.md             this file
│  ├─ LICENSING.md
│  ├─ LEGACY-DISPOSITION.md
│  ├─ GPU-SUPPORT-MATRIX.md
│  ├─ METAL-EMULATION.md         Plane 4
│  ├─ SHADER-JIT.md              Plane 4
│  ├─ AIR-ABI.md                 Plane 4
│  ├─ WORKLOAD-RUNTIME.md        Plane 3
│  ├─ MGAL.md                    Plane 2
│  ├─ MELLOW-UAPI.md             Plane 2
│  ├─ MELLOWKPI.md               Plane 1
│  ├─ BACKPORT-PIPELINE.md       Plane 0
│  ├─ ADDING-A-GPU.md            Plane 0 tutorial
│  ├─ METAL_FEATURE_MATRIX.md
│  ├─ PORTING_STATUS.md
│  ├─ backends/xe/               XE-*.md moved here
│  └─ history/                   superseded records, bodies unedited
├─ kernel/
│  ├─ MellowKMD/                 composition root, registry, UAPI, policy
│  ├─ mgal/                      the nine interfaces + pure logic
│  ├─ kpi/                       MellowKPI: linux/*, drm/*, ttm/*
│  ├─ backends/
│  │  ├─ xe/                     current Xe* refactored onto MGAL
│  │  ├─ applecompat/            ICL path only; TGL removed
│  │  ├─ amdgpu/                 generated + patches/
│  │  └─ nvidia-selected/        future reviewed RM or Nouveau adapter; not interchangeable
│  └─ display/                   DisplayMergeNub, HDMI, IntelDPLinkTraining
├─ userspace/
│  ├─ MellowMTL/                 core + interposition + plug-in adapters
│  ├─ MellowJIT/                 AIR → MIR → gated CL C / GLSL / IL / native adapters
│  ├─ MellowRT/                  router, resource model, IOSurface interop
│  ├─ MellowGL/  MellowCL/       Mesa-derived providers
│  └─ tools/                     metal_session.py, mellow_acceptance.py
├─ tools/
│  ├─ mellow-port/               the backport pipeline
│  └─ ...                        existing Tools/ scripts
├─ tests/                        host tests + conformance suites
├─ validation/                   evidence JSON — preserved in full
├─ abi-evidence/  compiler-evidence/
└─ Lilu.kext/  MacKernelSDK/  Mellow.xcodeproj/
```

Two organizing principles: **separation by plane**, and **isolation by backend** so that adding a
family-scoped changes are reviewable. Shared compiler, runtime, UAPI and firmware contracts may
still require changes; one directory does not guarantee isolation of semantics or licensing.

## Migration map

| Current | Proposed target, not performed | Notes |
| --- | --- | --- |
| `Mellow/kern_start.cpp`, `kern_mellow.*`, `kern_patcherplus.*`, `StartupPolicy.hpp`, `RuntimeReadiness.hpp`, `PatternMatch.hpp` | `kernel/MellowKMD/` | Entry, policy, readiness. Gains the composition root |
| `Mellow/HardwareAccess.hpp` | `kernel/mgal/` | Already OS-independent — the model for the rest |
| `Mellow/kern_model.hpp` | `kernel/mgal/` | Becomes the device descriptor table for `IMellowDevice` |
| `Mellow/Xe*.cpp/.hpp` (20 + 24 files) | `kernel/backends/xe/` | Refactored onto MGAL interfaces per [MGAL.md](MGAL.md) |
| `Mellow/kern_genx.*`, ICL routes from `kern_gen11.*` | `kernel/backends/applecompat/` | See [LEGACY-DISPOSITION.md](LEGACY-DISPOSITION.md) |
| `Mellow/AppleIntelParams.hpp`, TGL routes, `MellowDriverProfiles.TGL` | Quarantined legacy research | No deletion in this redesign; review later changes separately |
| `Mellow/DisplayMergeNub.*`, `HDMI.*`, `IntelDPLinkTraining.*` | `kernel/display/` | Kept and promoted |
| `Mellow/DYLDPatches.*` | `userspace/MellowMTL/` (attachment) | Minus ~210 lines of unreferenced AMD VCN tables; any future hook activation requires a version-pinned ABI experiment |
| `Mellow/Info.plist` | `kernel/MellowKMD/Info.plist` | Personalities revised; profiles generalized per backend |
| `Userspace/*.py` | `userspace/tools/` | Unchanged content |
| `Tools/*` | `tools/` | Future migration only; update imports/entry points and tests first |
| `Runtime/PlatformRuntime.*`, `OpenCLProvider.*`, `OpenCLAbi.hpp` | `userspace/MellowRT/` | Existing policy and bounded native OpenCL execution; destination proposed |
| `Runtime/MetalObjects.*`, `ShaderJit.*`, `AirDecoder.*` | `userspace/MellowMTL/` and `userspace/MellowJIT/` | Existing portable C++ compute objects and restricted MSL/AIR translation; Apple ABI/general shaders remain unimplemented |
| `Mellow/TahoeDiagnostic*`, `Userspace/tahoe_diag_client.c` | Future diagnostic kernel/userspace split | Existing opt-in query/bounded DMA protocol; native execution unverified, not the full GPU owner |
| `Drivers/PortedXe/*`, `Mellow/PortedXeBindings.cpp` | Reviewed portable subsystem under the future Xe backend | Existing integration; preserve notices/provenance and exactly one compiled implementation |
| `docs/XE-*.md` | `docs/backends/xe/` | Bodies unedited |
| `docs/IOACCEL-METAL.md`, `METAL-IMPLEMENTATION-PLAN.md`, `METAL-USERSPACE.md`, `METAL-PATH-CHANGES.md`, `USERLAND-METAL-EVIDENCE-AUDIT-*.md`, `NATIVE-XE-BACKEND-AUDIT.md`, `DRIVER-CORE-CHANGES.md`, `STARTUP-PATCHER-CHANGES.md`, `ACCEPTANCE-0.4.1.ko.md`, `BUILD-VALIDATION.md`, `EXPERIMENTS.md`, `UPSTREAM-README.md` | `docs/history/` | **Bodies unedited.** Banners added in P0 |
| `validation/`, `abi-evidence/`, `compiler-evidence/`, `tests/*.json` | unchanged | **Preserved in full** |

## Preservation rules

1. **No evidence artifact is deleted or edited.** Every JSON in `validation/`, `abi-evidence/`,
   `compiler-evidence/`, and `tests/` stays exactly as it is. Their negative-claim fields are the
   machine-readable form of this project's honesty and they are not rewritten to match new
   ambitions.
2. **Historical documents keep their bodies.** A superseded document gets a banner and a move,
   never an edit. Rewriting an old assessment to agree with a new plan destroys the record of what
   was actually known when.
3. **Provenance manifests are append-only.** Existing entries are corrected only for the pinning
   defect described in [LICENSING.md](LICENSING.md).

## Build implications

Two facts make the reorganization safer than it looks:

- [Tools/cross-build.py](../Tools/cross-build.py) **parses `PBXSourcesBuildPhase` out of the
  pbxproj** and resolves each name against a search path, so the Xcode and command-line builds
  cannot silently diverge. Adding directories means updating the resolver's search paths, not
  duplicating a file list.
- The project already hashes every input before and after a build and refuses the artifact if
  anything changed, which makes a before-and-after comparison across the move meaningful.

The Xcode project keeps one kext target during P1. Splitting into `MellowKMD` plus per-backend
kexts — linked through `OSBundleLibraries` on `com.NiSeullent.MellowKMD` — happens in P2, when
there is a composition root for them to attach to.

## Existing and proposed bundle identifiers

| Bundle | Identifier | Phase |
| --- | --- | --- |
| Legacy plug-in | `com.NiSeullent.Mellow` | exists |
| Core kext | `com.NiSeullent.MellowKMD` | P2 |
| Backend modules | `com.NiSeullent.MellowKMD.<backend>` | P3+ |
| Metal driver bundle | `com.NiSeullent.MellowMTLDriver` | P5+ |
