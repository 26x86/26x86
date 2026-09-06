# MELLOW-UAPI — the user/kernel boundary

> **Scope and precedence:** [PLATFORM-DECISIONS](PLATFORM-DECISIONS.md),
> [PLATFORM-ARCHITECTURE](PLATFORM-ARCHITECTURE.md), and
> [IMPLEMENTATION-STATUS](IMPLEMENTATION-STATUS.md) govern conflicting draft assumptions.
> Current evidence includes policy/intake, native Windows OpenCL provider execution and portable Xe tests.
> Standalone probe results remain separate; no Metal, WindowServer or display acceptance has passed.
> Native macOS GPU execution remains unverified; see IMPLEMENTATION-STATUS for the recorded scope.

## 한글 요약

MELLOW-UAPI는 `MellowKMD.kext`가 공개하는 IOUserClient ABI다. 설계 원칙 하나가 전부를 결정한다 —
**의도적으로 Linux DRM의 ioctl 모양을 따른다.** `GEM_CREATE`, `GEM_MMAP`, `VM_BIND`, `EXEC`,
`SYNCOBJ_*`. 이유는 성능이 아니라 이식성이다. Mesa의 `amdgpu_winsys`/`nouveau_winsys`가
이름이 비슷하더라도 memory·handle·동기화·오류 의미를 각각 검증해야 한다.
[백포팅 파이프라인](BACKPORT-PIPELINE.md)의 사용자 공간 adapter도 별도 구현 대상이다.
Apple의 `IOAcceleratorFamily2` 브리지는 [전략 A](METAL-EMULATION.md)용 **선택적** 경로이지 기본이 아니다 —
125개 vtable 심볼은 찾았지만 selector 번호·vtable 슬롯·구조체 레이아웃은 전부 미확보다.
**실제 MELLOW-UAPI/IOUserClient는 미구현이다. 별도 Runtime 정책 코드는 위 상태 문서를 따른다.**

---

**Status: `PLANNED`. No IOUserClient exists in this repository.**

## The design decision

MELLOW-UAPI's shape is chosen for **portability of the user-space half**, not for elegance or
performance.

Mesa's winsys layers — `amdgpu_winsys`, `nouveau_winsys`, and the Intel equivalents — are the code
that turns a Gallium or Vulkan driver's requests into kernel calls. They are written against DRM's
ioctl surface. Similar operation names do not make memory, synchronization or lifetime semantics
equivalent. Each selected winsys/kernel UAPI pairing requires a reviewed adapter.

That matters because [libMellowGL and libMellowCL](WORKLOAD-RUNTIME.md) are Mesa-derived. The
backport pipeline handles the kernel half; the DRM-shaped UAPI is what makes the user-space half
tractable by the same logic.

## Operation groups

Inspired by DRM operations; original per-file notices and dependencies require review before
copying or generation. Similar shape is not a license or ABI compatibility decision. See [LICENSING.md](LICENSING.md).

| Group | Operations | Purpose |
| --- | --- | --- |
| Object lifetime | `GEM_CREATE`, `GEM_CLOSE`, `GEM_INFO` | Allocate and release GPU memory objects |
| Mapping | `GEM_MMAP`, `GEM_MMAP_OFFSET` | Map objects into the calling task |
| Address space | `VM_CREATE`, `VM_DESTROY`, `VM_BIND`, `VM_UNBIND` | Manage GPU virtual address spaces |
| Execution | `EXEC`, `EXEC_QUEUE_CREATE`, `EXEC_QUEUE_DESTROY` | Submit work to engines |
| Synchronization | `SYNCOBJ_CREATE`, `SYNCOBJ_DESTROY`, `SYNCOBJ_WAIT`, `SYNCOBJ_SIGNAL`, `SYNCOBJ_TIMELINE_WAIT` | Fences and timelines |
| Query | `DEVICE_QUERY`, `ENGINE_QUERY`, `MEM_REGION_QUERY` | Capability and topology discovery |
| Surface | `SURFACE_IMPORT`, `SURFACE_EXPORT` | IOSurface interop — the macOS-specific addition |

The last group has no DRM equivalent and is where the boundary necessarily diverges: DRM uses
dma-buf for cross-API sharing; IOSurface alone does not implement that lifetime/sync contract. See
[WORKLOAD-RUNTIME.md](WORKLOAD-RUNTIME.md).

## Mapping onto IOKit

A proposed IOUserClient adapter exposes selected operations. The table names candidate bindings;
selector layout, validation, task ownership, caching and reset semantics are not mechanical:

| DRM concept | MELLOW-UAPI realization |
| --- | --- |
| `/dev/dri/cardN` open | `IOServiceOpen` on the Mellow accelerator service |
| ioctl number | External method selector |
| ioctl argument struct | `IOExternalMethodArguments` structure input/output |
| `mmap` on the DRM fd | `clientMemoryForType` returning an `IOMemoryDescriptor` |
| DRM authentication / render nodes | User client type, plus entitlement checks |
| `drm_file` per-open state | Per-user-client state, owning its VMs and objects |

Every selector validates its arguments before touching hardware state, matching the bounds- and
ownership-checking discipline the `Xe*` modules already apply — see the register allow-list in
[Mellow/XeGuCTransportIOKit.cpp](../Mellow/XeGuCTransportIOKit.cpp), which permits reads only in a
12-byte window and writes only of a single value to a single register.

## Ownership and lifetime

The hard part of this boundary is not the call shape — it is proving that a client cannot outlive,
alias, or corrupt state it does not own. The existing modules already thread ownership through
their APIs (`owner`, `generation`, `epoch`, pin cookies, use references), and MELLOW-UAPI is the
place those become enforceable:

- Every object belongs to exactly one user client and one VM.
- An object cannot be freed while any submitted job references it — `XeMemory`'s use references
  and fence-based retirement are the existing model.
- A VM's page-table root cannot be released until the device has demonstrably stopped using it;
  `XePageTableIOKit` already returns `Status::Quarantined` on a failed unwind rather than freeing.
- Reset destroys one epoch. Handles from a previous epoch are rejected, not silently remapped.

## Relationship to IOAcceleratorFamily2

Apple's own GPU drivers attach through `IOAcceleratorFamily2`, and the ABI survey enumerated its
kernel class hierarchy in detail — **125 vtable symbols** in version 487.4.3, including
`IOGraphicsAccelerator2`, `IOAccelDevice2`, `IOAccelShared2`, `IOAccelContext2`,
`IOAccelGLContext2`, `IOAccelCLContext2`, `IOAccelSurfaceMTL`, `IOAccelCommandQueue`, and
`IOAccelFenceMachine`, plus user clients `IOAccelSharedUserClient2`, `IOAccelGLDrawableUserClient`,
`IOAccelMemoryInfoUserClient`, and `IOAccelDisplayPipeUserClient2`. Roughly a dozen
`externalMethod` and `getTargetAndMethodForIndex` entry points were located.
See [TAHOE-ABI.md](TAHOE-ABI.md) and
[abi-evidence/tahoe-graphics-inventory.json](../abi-evidence/tahoe-graphics-inventory.json).

**What was found is a name-and-address inventory, not an ABI.** No selector numbers, no vtable
slot indices, no struct layouts, and no calling conventions were extracted. Every relevant
artifact records `private_abi_verified: false`.

Therefore:

- **MELLOW-UAPI is primary.** It is a versioned Mellow contract requiring compatibility tests, and
  it is what the Mesa-derived providers target.
- **An `IOGraphicsAccelerator2` bridge is optional and secondary.** It is required only for
  [Strategy A](METAL-EMULATION.md), where Apple's Metal loads a Mellow driver plug-in and expects
  to find Apple's accelerator classes underneath. It cannot begin before the private ABI is
  actually recovered, per macOS build.

Building on Apple's private classes as the primary boundary would make every Mellow backend
hostage to a macOS point release. Building Mellow's own boundary first means the driver stack
keeps working even when the Metal attachment strategy has to change.

## Versioning

The boundary is versioned explicitly, because generated backends and Mesa-derived user-space
components will be built at different times:

- A `DEVICE_QUERY` returns the UAPI version and a feature bitmap.
- Selectors are append-only. A selector's argument layout never changes meaning; a new layout gets
  a new selector.
- A client requesting an unsupported operation receives a clear failure — never a partial
  operation, and never a success it did not earn. See [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).
