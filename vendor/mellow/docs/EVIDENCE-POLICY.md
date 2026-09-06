# Evidence policy

> **Scope and precedence:** [PLATFORM-DECISIONS](PLATFORM-DECISIONS.md),
> [PLATFORM-ARCHITECTURE](PLATFORM-ARCHITECTURE.md), and
> [IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md) govern conflicting draft assumptions.
> Current evidence includes policy/intake, native Windows OpenCL provider execution and portable Xe tests.
> Standalone probe results remain separate; no Metal, WindowServer or display acceptance has passed.
> Native macOS GPU execution remains unverified; see IMPLEMENTATION-STATUS for the recorded scope.

## 한글 요약

이 문서는 Mellow의 모든 주장에 적용되는 **규범**이다. 다른 모든 문서가 여기를 참조한다.
증거는 `S → B → L → F → R` 5단계 누적 사다리로 분류하며, 변경은 7개 분류 중 하나를 달아야 한다.
핵심 규칙은 **"성공을 만들어내지 않는다"** — 미구현 경로는 조용히 통과하지 않고 큰 소리로 실패한다.
Mellow 실행 경로의 `L`·`F`·`R` 증거는 **0건**이다. 별도의 Windows OpenCL 기판 시험은
아래처럼 구분하며 Mellow 기능이나 macOS 지원 증거로 승격하지 않는다.
이 정책은 확대개편 이후에도 완화되지 않는다.

---

## Why this document exists

Mellow is a driver project whose most likely failure mode is not a crash — it is a **false
positive**. A kext that loads, a service that appears in the IORegistry, a `MTLDevice` that
enumerates, and a desktop that draws are each easy to reach without any GPU ever executing a
single instruction of the caller's work.

This policy exists so that "it works" is a claim with a defined meaning, and so that no
component can be promoted by accident. It is normative: where another document conflicts with
this one, the no-manufactured-success rule applies; the reviewed PLATFORM documents define
architecture scope and IMPLEMENTATION-STATUS defines current code, without weakening that rule.

## The evidence ladder

Levels are **cumulative**. A component at level `F` must also satisfy `S`, `B`, and `L`.

| Level | Meaning |
| --- | --- |
| `S` | A source path exists and has been reviewed. This proves neither compilation nor execution. |
| `B` | A reproducible build completed and its artifact, commit, toolchain, and log were retained. |
| `L` | A hardware log shows that the intended path executed on the physical target. |
| `F` | A deterministic functional test produced the expected GPU result with CPU fallback excluded. |
| `R` | Repeated functional and recovery tests passed across reboot, sleep/wake, and sustained load. |

### Current repository state

**No Mellow execution path has recorded `L`, `F`, or `R` evidence.** Host policy tests and a
separate Windows OpenCL substrate probe exist. Evidence must name its execution path; an
installed-vendor-driver result cannot promote a Mellow component.

The path-specific negative-claim fields in result JSON under [validation/](../validation) and
[tests/](../tests) — `hardware_executed`, `gpu_executed`, `metal_tested`,
`iokit_adapter_runtime_tested`, `guc_authentication_tested`,
`cpu_fallback_excluded_by_hardware_evidence` — are the machine-readable form of this statement.
They must remain present and must remain accurate.

## Change classifications

Every change carries exactly one classification:

| Classification | Use |
| --- | --- |
| **Diagnostic** | Adds observation, or bypasses a check solely to locate a failure. |
| **Workaround** | Masks a known mismatch without implementing the underlying contract. |
| **Feature-limited implementation** | Implements a documented subset and rejects the rest. |
| **Prototype implementation** | Exercises a plausible path whose correctness and recovery are incomplete. |
| **Stabilization candidate** | Has deterministic functional evidence and is undergoing regression testing. |
| **Production-level implementation** | Has defined compatibility, recovery, regression, and performance evidence. |
| **Not implemented** | No Mellow-owned implementation exists at this layer. |

Device-ID spoofing, assertion bypasses, forced return values, and capability-bit changes are
**Diagnostic** or **Workaround**. They are never promoted merely because the system boots.

## The no-manufactured-success rule

A code path that cannot do its job must fail loudly. It must not:

- return a success status it did not earn,
- substitute a plausible-looking value for a measurement it did not take,
- treat the absence of an error as the presence of a result,
- or silently fall back to a slower correct path in a way the caller cannot observe.

This rule already shaped the existing tree, and those decisions are load-bearing precedent:

- `Gen11::loadGuCBinary` returns failure rather than a fake success
  ([docs/METAL-PATH-CHANGES.md](METAL-PATH-CHANGES.md)).
- `Gen11::barrierSubmission` no longer defaults to a bypassed successful barrier; it forwards the
  underlying result.
- `XeSubmission::unavailableSubmissionBackend()` returns an empty ops struct on purpose
  ([Mellow/XeSubmission.hpp](../Mellow/XeSubmission.hpp)), so an unbacked queue cannot appear to work.
- `XeZebin::resolveEvidencePointers` returns `Error::Unavailable` when no surface backend is
  supplied, instead of defaulting to a zero handle ([Mellow/XeZebin.cpp](../Mellow/XeZebin.cpp)).
- `MellowRuntime::BackendOwnerIntegrated = false` at
  [Mellow/RuntimeReadiness.hpp:84](../Mellow/RuntimeReadiness.hpp), with the comment
  *"A boot argument must never substitute for that missing owner."*

### Application to the new architecture

The MELLOW planes introduce two new places where this rule is easy to violate, and both are
called out in their own documents:

1. **The workload router** ([WORKLOAD-RUNTIME.md](WORKLOAD-RUNTIME.md)) can express any Metal
   workload on the CPU. A CPU result is a *reference value for tests*, never a service to the
   caller. The `cpu` route must be unreachable without an explicit opt-in, and any command buffer
   completed through it must be observably marked.
2. **Generated backends** ([BACKPORT-PIPELINE.md](BACKPORT-PIPELINE.md)) will contain stubs for
   Linux kernel APIs that MellowKPI does not yet implement. Every such stub fails loudly and is
   counted in the `mellow-port doctor` coverage report. A stub that returns a neutral success
   value is a bug, not a placeholder.

## Capability exposure

A capability bit — a Metal feature flag, a `MTLGPUFamily` claim, a supported-format entry, a
`supportsFamily(.metal3)` response — may be exposed **only after the corresponding path has
produced a correct result at level `F`**.

The readiness ladder in [Mellow/RuntimeReadiness.hpp](../Mellow/RuntimeReadiness.hpp) is the
existing mechanism for this. It is a 20-bit fail-closed gate in seven stages
(`Configuration → PhysicalProvider → AddressSpace → Firmware → Execution → KernelProvider →
Userspace → Ready`), where each stage requires the previous one. `mayAdvertiseMetal` requires all
twenty bits. That structure is retained and extended per backend in the MELLOW architecture; see
[MGAL.md](MGAL.md).

## Status vocabulary for matrices

Feature and support matrices use one vocabulary:

- `SOURCE PATH` — related matching, routing, or patch code exists.
- `PLANNED` — described in a design document; no implementation exists.
- `UNKNOWN` — the responsible platform or hardware contract has not been established.
- `NOT IMPLEMENTED` — no Mellow-owned or validated compatible implementation exists.
- `BLOCKED` — a prerequisite test has not passed.
- `VERIFIED` — reserved for a linked, deterministic experiment that excludes CPU fallback.

`VERIFIED` currently applies to **no row in any matrix in this repository**.

## Citation discipline

Every factual claim in Mellow documentation carries a reference:

- Claims about this repository cite `file:line`.
- Claims about upstream Linux, Mesa, or vendor sources cite a **pinned commit SHA**, never a
  moving branch. [docs/DRIVER-CORE-CHANGES.md](DRIVER-CORE-CHANGES.md) contains `master` links
  that predate this rule; new documents do not repeat that.
- Claims about macOS internals cite the extracted artifact and its hash, as
  [docs/TAHOE-ABI.md](TAHOE-ABI.md) does.

A statement with no citation is an assumption and must be written as one.

## Separate Windows substrate observation

[opencl-windows-substrate.json](../validation/opencl-windows-substrate.json) records
`PASS_OPENCL_GPU_SUBSTRATE_ONLY`: the installed Windows Intel OpenCL driver executed the probe.
`mellow_runtime_used=false`, `mellow_jit_used=false`, `metal_tested=false`,
`macos_driver_tested=false`, `mellow_gpu_acceleration_pass=false`.
The OpenCL-reported GPU identity was not correlated to physical PCI (`physical_pci_identity_verified=false`).
This demonstrates a Windows substrate only; it does not promote a Mellow/backend/family capability.
