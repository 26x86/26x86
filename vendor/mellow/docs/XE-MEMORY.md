> **Historical record — preserved unedited.** Component documentation for the hand-written
> Intel Xe backend, which compiles into the kext but has no call path
> ([Mellow/RuntimeReadiness.hpp:84](../Mellow/RuntimeReadiness.hpp)). Scheduled to move to
> `docs/backends/xe/` in P1. For how these modules map onto the vendor-neutral abstraction
> see [MGAL.md](MGAL.md); for the current architecture see [ARCHITECTURE.md](ARCHITECTURE.md).

# Xe memory implementation for the 7D41 research target

This revision contains working C++ memory bookkeeping, page-entry encoders and an
IOKit system-memory DMA adapter. It has **not executed on the Galaxy Book GPU or
on macOS**. The IOKit adapter provides allocation/pinning and teardown; it does
not provide GPU `bind`, `unbind` or completion callbacks. Therefore its successful
pin cannot become `State::Bound`. A USB boot or loaded kext does not change this
capability boundary.

## Implemented code

`Mellow/XeMemory.hpp` and `Mellow/XeMemory.cpp` implement:

- A first-fit GPU virtual-address allocator using caller-owned fixed-capacity
  records. It checks the entire half-open interval before insertion, requires
  4 KiB allocation sizes, supports larger power-of-two alignments, and preserves
  permanent excluded intervals for addresses owned by another subsystem.
- Owner checks and generation-bearing handles. Reusing an address or slot cannot
  make an old handle valid. Generation exhaustion is refused rather than wrapped.
- Explicit `Reserved`, `Pinned`, `Bound`, `Retiring` and `Quarantined` states.
  `Reserved` describes address bookkeeping only. `Pinned` requires a successful
  backend receipt containing the exact number of aligned DMA pages.
- Queue resource holds through `retainUse` and `releaseUse`. Retirement refuses
  new holds, and outstanding holds prevent unbinding or freeing the allocation.
  Only a trusted scheduler may release a hold after confirmed rejection, real
  completion or verified device quiescence. A user-client free request is not
  permission to release an outstanding scheduler hold.
- An optional direct scheduler fence path through `recordUse`. It accepts one
  nonzero, strictly increasing timeline per allocation. Cross-queue dependency
  joining is deliberately left to the scheduler. Reclamation polls the backend
  for the recorded fence before unbinding.
- Conservative failure handling. A possibly partial GPU bind or invalidation
  keeps both VA and backing pages quarantined. A failed pin that leaves a receipt
  also quarantines it. There is no automatic quarantine recovery/reset shortcut.
- 4 KiB system-memory leaf PTE and non-leaf PDE encoders, and four-level VA index
  decomposition. Invalid inputs preserve the caller's output value. These
  functions create integer entries in CPU memory; they do not write GPU state.

The manager is noncopyable and performs no dynamic allocations. Its caller must
keep the allocation records alive and serialize **all** operations and backend
callbacks. Direct mutation of records, pin receipts, owner identities or handle
generations is not a supported interface.

`Mellow/XeMemoryIOKit.hpp` and `Mellow/XeMemoryIOKit.cpp` add the actual Darwin API
adapter. On an explicitly invoked pin operation, it allocates a zeroed
`IOBufferMemoryDescriptor`, pairs descriptor preparation with completion, creates
an `IODMACommand`, and collects one 4 KiB mapped DMA segment per backing page. It
uses an explicit retained `IOMapper` from the admitted PCI device and refuses a
null mapper. There is no fallback that treats a CPU physical address as a valid
IOMMU-translated GPU DMA address. Per-allocation and total-byte limits are charged
before allocation and refunded only after complete teardown. The defaults are
64 MiB per allocation and 256 MiB pinned per context; these are research resource
limits, not hardware VRAM measurements.

`synchronizeForDevice` and `synchronizeForCpu` call `IODMACommand::synchronize`
in the corresponding direction. They cover that API's intermediate-buffer
copies. They are **not** GPU engine cache flushes, GPU TLB invalidation, MMIO
publication barriers or job-completion evidence. The adapter must run in a
serialized, sleepable client context; DMA preparation can block and must not run
inside an interrupt handler or a gated work-loop action. The context and device
mapper must outlive every pin. Apple's API definitions explain these mapping,
preparation, synchronization and teardown contracts.
([Apple IODMACommand API](https://github.com/apple-oss-distributions/xnu/blob/main/iokit/IOKit/IODMACommand.h),
[Apple IODMACommand implementation](https://github.com/apple-oss-distributions/xnu/blob/main/iokit/Kernel/IODMACommand.cpp))

## Hardware format evidence and limits

The Linux Xe `mtl_desc` uses a 46-bit DMA address limit, 48-bit GPU virtual
addresses and maximum page-table level 3. Both Meteor Lake and Arrow Lake PCI
groups select that descriptor; graphics and media IP are then determined using
GMD_ID. This is the reference for `DmaLimit`, `VaLimit` and the four-level encoder.
The physical PCI ID alone does not prove the exact GT IP revision or its active
PAT configuration. Those still require identification on the actual device.
([Linux Xe device descriptors](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/xe/xe_pci.c))

For the implemented Xe-LPG PPGTT leaf format, present is bit 0, write permission
is bit 1, and PAT index bits 0/1/2/3 are encoded into entry bits 3/4/7/62.
Non-leaf table pointers support only the first two PAT bits. The address is
4 KiB aligned and this target's 46-bit DMA limit is stricter than the general
entry address field. The implementation does not set device-memory, GGTT,
scratch/null, 64 KiB, 2 MiB or 1 GiB page flags.
([Intel-authored Xe page-entry definitions](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/xe/regs/xe_gtt_defs.h))

Linux selects non-leaf PAT values according to page-table allocation caching;
leaf PAT choices are a separate concern. Representing an index is not evidence
that its cache policy was programmed. Accordingly, `Backend::verifiedPatIndices`
defaults to zero and `bind` refuses every PAT until a hardware backend supplies
an independently validated mask. The pure encoder can represent all legal
index bits for offline construction and tests without claiming that any cache
policy is active. The functions were checked against `pde_encode_pat_index`,
`pte_encode_pat_index`, `xelp_pde_encode_bo` and `xelp_pte_encode_addr`.
([Linux Xe VM entry construction](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/xe/xe_vm.c))

Sources above were inspected on 2026-09-05; their branch links may change. The
implementation uses named, documented field values and deliberately contains no
guessed MMIO register writes or command opcodes.

## Backend contract and queue integration

A minimal address-only instance can be initialized with `Backend{}`; reservation
works, while pinning returns `Unavailable`. `makeIOKitPinBackend(context)` provides
real system-memory pin/unpin functions but leaves GPU operations unavailable.
Neither construction performs an allocation or GPU write by itself.

For a future hardware backend:

1. `pin` must return stable backing pages, mapped DMA addresses and a retained
   receipt for exactly `bytes / 4096` pages. A normal failure must return an empty
   receipt after cleaning up all resources.
2. `bind` may return `Ok` only after installing the mapping in the correct GPU
   address space and completing the required publication ordering and GPU TLB
   invalidation. `Unavailable` promises that no GPU state changed. All other
   failure results are treated as possibly partial and quarantine the allocation.
3. `unbind` has the same completed-invalidation requirement. The pages remain
   pinned until it succeeds. Zeroing a CPU PTE or issuing an asynchronous
   invalidation request alone is insufficient.
4. `fenceComplete`, when using the direct fence path, must read genuine ordered
   completion for that timeline. Missing callbacks, timeout and unrelated queue
   completion cannot authorize reclamation.

`MellowXe::Resource` identifies a VM allocation with `id = handle.slot + 1`
and `mappingGeneration = handle.generation`. Its authoritative retain callback
must resolve `inspect(resource.owner, Handle{id - 1, mappingGeneration})`, verify
`Bound` and exact owner/address/size, then call `retainUse` within the same
serialization domain. The submission queue's reset generation is a different
identity from the VM allocation generation and must not be compared to it.
`Mellow/XeMemorySubmission.hpp` now implements this connection as the noncopyable
`SubmissionMemoryBridge`. It replaces the transport's retain/release callbacks
with the authoritative VM checks and forwards readiness, submission, fence
observations and quiescence to the supplied transport without changing their
results. A transport missing any of those functions remains unavailable.
The matching release callback calls `releaseUse` only after the queue's verified
completion/rejection/quiescence rules permit it. A future adapter must also
validate additional resource access permissions and the entire command stream
when commands beyond the existing read-only bootstrap policy are supported.
If a release encounters a stale mapping or an underflow, the bridge keeps the
failure status and blocks new holds; it never zeroes an unrelated counter. The
bridge, transport, allocation storage and VM must all outlive the queue.

The retain/release path avoids recording an unsubmitted provisional fence when
a job is rejected before acceptance. Do not mix it with a made-up completed
value or reset a hold counter after timeout. If both holds and a direct fence
were recorded, both conditions must be satisfied before reclaim succeeds.

## Page-table construction and remaining integration

The separate `Mellow/XePageTable.hpp` / `.cpp` builder uses these encoders for a
private four-level tree from caller-supplied DMA page buffers. Its CPU lookup and
seal operation do not bind the tree to an engine. A caller must preserve the
page-table pool and all data pins after publication until the GPU can no longer
reference them. Do not reuse a published page table through the private builder.

Still absent from this memory adapter are the actual device-specific GPU root
binding, context placement, PAT programming/verification, engine-cache and TLB
ordering, page-fault service, eviction, imported user memory/IOSurface mapping,
DSM/device-memory allocation and multi-queue dependency joining. The parent
submission subsystem owns firmware, queue, interrupt, fence and reset contracts;
those need a hardware implementation before the memory manager can advance to
`Bound` in production. IOKit pinning is a prerequisite, not that implementation.
Changing an EFI or system ROM cannot replace these kernel operations or supply
the absent Metal user-mode driver/compiler integration.

## Verification and stop criteria

The native test command, from this source root, is:

```sh
g++ -std=c++17 -Wall -Wextra -Werror -O2 tests/xe_memory_tests.cpp Mellow/XeMemory.cpp -o xe_memory_tests
./xe_memory_tests
```

The Windows MinGW build passed **79,451 assertions**. Coverage includes all
256 occupancy patterns in an eight-page address space, all request lengths and
four alignments, all 256 PAT input byte values, literal expected entry bits,
all 512 indices at every level, boundary/overflow errors, wrong/stale owners,
pin validation and failure unwinding, partial-operation quarantine, retirement,
real-callback fence gating, queue hold underflow/overflow and multiple outstanding
job lifetimes. The backend in these tests is explicitly a deterministic test
double. It neither implements IOKit nor executes GPU commands.

Both new `.cpp` files also compiled for `x86_64-apple-macos13` with kernel/kext
flags against the bundled MacKernelSDK using LLVM 20.1.8. Only the SDK's existing
TargetConditionals macro redefinition warnings were emitted. This verifies
source/API compatibility at compile time; it is not a Darwin 25 load or run test.

The integration test `tests/xe_bridge_tests.cpp` additionally passed **123
assertions** while connecting the real submission queue, real bridge and real VM.
Only hardware operations were mocked. It proves that timeout and failed reset
keep DMA ownership, a quiesced reset permits release, wrong/unordered fence
observations do not release holds, and an old generation cannot reach a reused
allocation. It also covers rejected and unknown acceptance, multiple jobs sharing
one mapping and release-contract failure handling. Build it with:

```sh
g++ -std=c++17 -Wall -Wextra -Werror -O2 tests/xe_bridge_tests.cpp Mellow/XeMemory.cpp Mellow/XeSubmission.cpp -o xe_bridge_tests
./xe_bridge_tests
```

Before enabling the hardware pin path, require a retained mapper for the exact
admitted PCI device and a macOS test of allocation, segment translation, quotas,
synchronization and balanced teardown. Stop if no mapper is available, a segment
falls outside the DMA width, a teardown fails or DMA address ownership is unclear.

Before supplying GPU bind callbacks, prove a page-table root and backing pages
belong to the correct engine/context, cache policies are valid, invalidation is
acknowledged and both normal completion and timeout/reset retain pages correctly.
Stop on the first unexpected page fault, stale translation, unverified completion
or ambiguous reset. Keep the allocation quarantined until actual quiescence and
mapping teardown are established; this revision offers no recovery API that can
assert those facts without evidence.

Only then run the real `Tools/metal-probe.swift` acceptance workflow and retain
the source/binary hashes, driver registry identity, command-buffer result,
computed output and `Tools/collect-mellow-logs.sh` diagnostics. Metal device
enumeration or successful kext loading alone is not the acceptance result.
