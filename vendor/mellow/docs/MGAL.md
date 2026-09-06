# Plane 2 — MGAL, the Mellow GPU Abstraction Layer

> **Scope and precedence:** [PLATFORM-DECISIONS](PLATFORM-DECISIONS.md),
> [PLATFORM-ARCHITECTURE](PLATFORM-ARCHITECTURE.md), and
> [IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md) govern conflicting draft assumptions.
> Current evidence includes policy/intake, native Windows OpenCL provider execution and portable Xe tests.
> Standalone probe results remain separate; no Metal, WindowServer or display acceptance has passed.
> Native macOS GPU execution remains unverified; see IMPLEMENTATION-STATUS for the recorded scope.

## 한글 요약

MGAL은 벤더 중립 GPU 계약이다. **새로 발명하는 것이 아니라 이미 있는 이음매를 승격하는 것**이다 —
모든 `Xe*` 모듈은 이미 순수 C++17 로직과 POD 함수포인터 ops 구조체로 분리되어 있고, `*IOKit` 파일은
플랫폼 바인딩이다. composition root뿐 아니라 memory·concurrency·firmware·reset 계약의
구현과 실기 검증이 필요하다.
MGAL은 인터페이스 9종을 정의하고, 기존 `Xe*` ops 구조체가 각각 어디에 대응하는지 아래 표로 고정한다.
현 트리의 가장 큰 문제 둘 — 소유자 부재(`BackendOwnerIntegrated = false`)와 장치 식별 39곳 중복 —
을 해소하는 것이 P1의 과제다.

---

**Status: `PLANNED` as a named interface set. The underlying separation already exists in source
(`S`); the interfaces themselves do not.**

## The seam already exists

Every `Xe*` module in this tree follows one pattern, uniformly, across six module pairs:

- **`XeFoo.hpp` / `.cpp`** — freestanding C++17. Includes only `<stdint.h>` and `<stddef.h>`. No
  IOKit, no allocation, fixed-size arrays, deleted copy constructors, explicit `enum class Status`.
  Platform effects arrive through a **POD struct of C function pointers plus a `void *opaque`**.
- **`XeFooIOKit.hpp` / `.cpp`** — a binding class holding IOKit objects, exposing static
  trampolines and a factory that returns the POD struct.

This is why [Tools/run-xe-tests.py](../Tools/run-xe-tests.py) can compile the *production* sources
against host mocks with `-Wall -Wextra -Werror -pedantic` and exercise them with emulated MMIO and
ownership callbacks.

**MGAL is the promotion of those ops structs into named, documented interfaces.** Existing ops structs are starting points; cross-vendor memory, ownership, concurrency and reset
semantics still require design, implementation and validation.

## What is actually missing

A composition root and verified semantic platform/backend contracts are both missing.

Nothing in the tree constructs `IOKitMmio`, `IOKitPageTable`, `XeGuCFirmware::Loader`,
`XeGuC::Transport`, `MellowXeInterrupt`, `XeFence::IOKitSlot`, or `EvidenceExecution`. Nothing
supplies the `*Proofs` structs those bindings require. There is no workloop, no reset epoch, and
no PCI owner. `#include "Xe` appears nowhere outside `Mellow/Xe*`.

This is recorded in source, not inferred:

```c
// This build has no IOKit owner that constructs and retains the MMIO, GGTT,
// GuC, IRQ, fence, context and IOAccelerator objects as one reset epoch.
// A boot argument must never substitute for that missing owner.
constexpr bool BackendOwnerIntegrated = false;
```
— [Mellow/RuntimeReadiness.hpp:84](../Mellow/RuntimeReadiness.hpp)

The intended landing site exists but is unfinished. [Mellow/Info.plist](../Mellow/Info.plist)
declares an `IOResources` personality whose `IOClass` is `Mellow`, but the `IOService` subclass at
[Mellow/kern_start.cpp:52](../Mellow/kern_start.cpp) is commented out and
`LILU_CUSTOM_IOKIT_INIT` is not defined — so nothing can match it.

## Interfaces

| Interface | Responsibility |
| --- | --- |
| `IMellowDevice` | Identity, IP/generation version, capability descriptor, PCI configuration |
| `IMellowMmio` | BAR mapping, bounded register access, forcewake domains |
| `IMellowMemory` | Allocation, DMA mapping, pinning, residency, storage domains |
| `IMellowVm` | Page tables, GPU virtual addresses, bind/unbind, TLB invalidation |
| `IMellowQueue` | Engine classes, rings and doorbells, context images, submission |
| `IMellowFence` | Fences, timelines, interrupt-driven completion observation |
| `IMellowFirmware` | Blob location, version and integrity checks, load and authentication |
| `IMellowDisplay` | Planes, modeset, timing, hotplug — optional per backend |
| `IMellowCompiler` | Native ISA code generation entry point (user space) |

The proposed style uses freestanding declarations and POD ops; changed ownership or execution
semantics require updated contract tests, even when existing host tests still compile.

## Mapping from the existing Xe modules

This is a candidate responsibility map, not proof of a one-to-one or semantics-preserving port.

| Existing module | Existing ops struct | MGAL interface | Linux analogue |
| --- | --- | --- | --- |
| [XeMmioAccess](../Mellow/XeMmioAccess.hpp) | `MellowXe::MmioAccess` | `IMellowMmio` | `xe_mmio.c`, `intel_uncore` forcewake |
| [XeMmioIOKit](../Mellow/XeMmioIOKit.hpp) | — (binding) | `IMellowMmio` binding | — |
| [XeMemory](../Mellow/XeMemory.hpp) | `XeMemory::Backend` | `IMellowMemory` | `xe_vm.c`, GEM VMA, PTE encoding |
| [XeMemoryIOKit](../Mellow/XeMemoryIOKit.hpp) | — (binding) | `IMellowMemory` binding | TTM / dma-buf pinning |
| [XePageTable](../Mellow/XePageTable.hpp) | — | `IMellowVm` | `xe_pt.c`, 4-level PPGTT |
| [XePageTableIOKit](../Mellow/XePageTableIOKit.hpp) | `RootRetirement` | `IMellowVm` binding | — |
| [XeSubmission](../Mellow/XeSubmission.hpp) | `MellowXe::SubmissionBackend` | `IMellowQueue` | `xe_exec_queue`, `i915_request` |
| [XeMemorySubmission](../Mellow/XeMemorySubmission.hpp) | — | `IMellowQueue` ↔ `IMellowMemory` bridge | — |
| [XeContext](../Mellow/XeContext.hpp) | — | `IMellowQueue` (context images) | `xe_lrc.c` |
| [XeContextExecution](../Mellow/XeContextExecution.hpp) | `XeContext::ExecutionBackend` | `IMellowQueue` (execution) | GuC context register/enable/submit |
| [XeDispatch](../Mellow/XeDispatch.hpp) | — | `IMellowQueue` (command encoding) | `intel_cmd_parser`, NEO walker encode |
| [XeFence](../Mellow/XeFence.hpp) | `XeFence::Ops` | `IMellowFence` | GGTT post-sync seqno |
| [XeFenceIOKit](../Mellow/XeFenceIOKit.hpp) | `MappingProofs` | `IMellowFence` binding | — |
| [XeInterrupt](../Mellow/XeInterrupt.hpp) | `XeInterrupt::Ops` | `IMellowFence` (delivery) | `xe_irq.c` |
| [XeInterruptDispatch](../Mellow/XeInterruptDispatch.hpp) | `DispatchOps` | `IMellowFence` (demux) | G2H + engine user interrupt |
| [XeInterruptIOKit](../Mellow/XeInterruptIOKit.hpp) | — (binding) | `IMellowFence` binding | — |
| [XeFirmware](../Mellow/XeFirmware.hpp) | — | `IMellowFirmware` | `xe_uc_fw.c` CSS parse |
| [XeGuCFirmware](../Mellow/XeGuCFirmware.hpp) | `XeGuCFirmware::Backend` | `IMellowFirmware` | `xe_guc.c` WOPCM, DMA, auth |
| [XeGuCFirmwareIOKit](../Mellow/XeGuCFirmwareIOKit.hpp) | `IOKitProofs` | `IMellowFirmware` binding | — |
| [XeGuCTransport](../Mellow/XeGuCTransport.hpp) | `XeGuC::Ops`, `MmioOps` | `IMellowFirmware` (transport) | `xe_guc_ct.c` |
| [XeGuCTransportIOKit](../Mellow/XeGuCTransportIOKit.hpp) | `DriverProofs` | `IMellowFirmware` binding | — |
| [XeZebin](../Mellow/XeZebin.hpp) | `XeZebin::SurfaceBackend` | `IMellowCompiler` | Intel NEO ZEBIN loader |

### Two submission stacks must be reconciled

`XeSubmission::SubmissionQueue` and `XeContextExecution::EvidenceExecution` are independent and
unconnected — `XeContextExecution.hpp` does not include `XeSubmission.hpp`. Furthermore
`XeMemorySubmission.hpp` and `XeInterruptDispatch.hpp` are header-only and referenced **only from
[tests/](../tests)**, placing them outside the kext's include closure entirely.

`IMellowQueue` must be a single contract. Deciding which of the two designs it follows — and
deleting or subsuming the other — is a P1 task, not a documentation decision, because it needs the
composition root to exist before either can be exercised.

## Device identity must come from one table

The current tree duplicates device identity badly. `7D41` appears **39 times across 26 files**, and
admission logic is repeated in at least four binding files:

- [Mellow/XeMmioIOKit.cpp](../Mellow/XeMmioIOKit.cpp) — BDF and `8086:7D41` check
- [Mellow/XeInterruptIOKit.cpp](../Mellow/XeInterruptIOKit.cpp) — vendor and device check
- [Mellow/XeGuCFirmwareIOKit.cpp](../Mellow/XeGuCFirmwareIOKit.cpp) — config-space read check
- [Mellow/XeFirmware.hpp:24](../Mellow/XeFirmware.hpp) — `constexpr uint16_t targetDeviceId = 0x7D41;`

It is also baked into places where it cannot be parameterized later without care: the GuC boot
parameter block in [Mellow/XeGuCFirmware.cpp](../Mellow/XeGuCFirmware.cpp) embeds the device ID
directly, and the readiness ladder names an evidence bit `PhysicalIdentity7D41` with the string
`"physical-8086-7d41"` ([Mellow/RuntimeReadiness.hpp](../Mellow/RuntimeReadiness.hpp)).

Meanwhile [Mellow/kern_model.hpp](../Mellow/kern_model.hpp) already contains a proper table —
seven Intel devices with names and topology, plus `isSupportedUltraPair()` binding each device to a
CPU model.

**P1 consolidates all of it into one device descriptor table per backend**, consumed through
`IMellowDevice`. Nothing below that interface may contain a literal device ID.

## Readiness, per backend

[Mellow/RuntimeReadiness.hpp](../Mellow/RuntimeReadiness.hpp) is a 20-bit fail-closed evidence
ladder with ordered stages — `Configuration → PhysicalProvider → AddressSpace → Firmware → Execution →
KernelProvider → Userspace → Ready` — where each stage requires the previous one, and
`mayAdvertiseMetal` requires all twenty bits.

That structure is retained and made **per backend**. Each `Evidence` bit maps to exactly one MGAL
interface obligation, which makes the ladder a checklist for bringing up a new GPU:

| Stage | Interfaces that must be satisfied |
| --- | --- |
| `PhysicalProvider` | `IMellowDevice`, `IMellowMmio` |
| `AddressSpace` | `IMellowMemory`, `IMellowVm` |
| `Firmware` | `IMellowFirmware` |
| `Execution` | `IMellowQueue`, `IMellowFence` |
| `KernelProvider` | Composition root owning one reset epoch |
| `Userspace` | [MELLOW-UAPI](MELLOW-UAPI.md) reachable, `IMellowCompiler` connected |

`BackendOwnerIntegrated` may reflect an implemented owner, but flipping it is not hardware
completion evidence. Firmware, execution, reset and userspace acceptance remain separate gates.

## Composition root

The missing piece. A `MellowKMD` provider that, per device:

1. Matches the PCI device and claims it.
2. Constructs the MMIO binding and acquires forcewake.
3. Builds the memory manager and page tables.
4. Loads and authenticates firmware, where the backend needs it.
5. Creates the workloop, attaches the interrupt source, and binds the fence timeline.
6. Creates queues and contexts.
7. Publishes the MELLOW-UAPI user client.
8. Tears all of it down as **one reset epoch**, in reverse order, with ownership proven at each step.

Step 8 is why the `*Proofs` structs exist throughout the current bindings and why nothing
implements them yet: the existing code was written to require an owner that was never built. The
ownership, generation, and epoch parameters threaded through `XeMemory`, `XeGuCFirmware`, and
`XeFence` are the contract that root must satisfy.

See [MELLOW-UAPI.md](MELLOW-UAPI.md) for the boundary it publishes, and
[MELLOWKPI.md](MELLOWKPI.md) for how generated backends plug into these interfaces.
