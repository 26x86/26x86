> **Historical record — preserved unedited.** Component documentation for the hand-written
> Intel Xe backend, which compiles into the kext but has no call path
> ([Mellow/RuntimeReadiness.hpp:84](../Mellow/RuntimeReadiness.hpp)). Scheduled to move to
> `docs/backends/xe/` in P1. For how these modules map onto the vendor-neutral abstraction
> see [MGAL.md](MGAL.md); for the current architecture see [ARCHITECTURE.md](ARCHITECTURE.md).

# Meteor Lake IRQ delivery and coherent fence observation

This revision adds actual register-driven interrupt handling and an IOKit
delivery adapter for the main GT of the physical Intel 8086:7D41 PF. It also
adds an ordered reader for a real GPU-written GGTT completion slot. The code
has compiled for the Darwin kernel and passed host fault/lifecycle tests.
**No physical IRQ, GPU DMA write, completed batch, or Metal operation has been
observed on this Windows host.** These components remain behind the driver
owner's real device, mapping, power and reset admission checks.

## New components

- `XeInterrupt.cpp/.hpp`: allocation-free tile/GT interrupt state machine.
- `XeInterruptIOKit.cpp/.hpp`: real `IOFilterInterruptEventSource` and
  `IOWorkLoop` adapter, exposed as `MellowXeInterrupt`.
- `XeInterruptDispatch.hpp`: bounded draining of actual `XeGuC::Transport`
  G2H messages and separate `XeFence::Timeline` observations.
- `XeFence.cpp/.hpp`: immutable context/epoch fence binding and coherent
  qword observation; no fabricated completion callback or sequence advancement.
- `XeFenceIOKit.cpp/.hpp`: actual IOMemoryDescriptor retain/prepare/map and
  completion/release lifecycle, coupled to authoritative GGTT ownership.

The four `.cpp` files must be members of the actual Xcode Sources phase.
Headers and host shims do not replace any kernel implementation at link time.

## Interrupt path

The primary filter performs bounded reads, atomics and a tile-master mask
write. It allocates nothing, does not acquire forcewake, and does not call the
GuC protocol handler. For tile0 it transitions the controller to masked state
and schedules the workloop action. A shared-line interrupt without tile0
indication is ignored without acknowledging another source.

The workloop follows the measured platform's Xe interrupt hierarchy:

1. Read and acknowledge tile master `0x190008` with delivery disabled.
2. Read/ack graphics master `0x190010`.
3. Read each indicated GT interrupt bank at `0x190018 + 4*bank`.
4. Select each indicated bit through `0x190070 + 4*bank`, poll identity at
   `0x190060 + 4*bank`, and require its valid bit before acknowledging it.
5. Acknowledge the bank summary after capturing all selected valid identities.
6. Dispatch bounded workloop events, then restore tile-master delivery.

The identity wait is bounded by 100 microseconds and an independent 10,000
iteration cap. Invalid identity, a stopped/regressing clock, inaccessible
all-ones status, admission revocation or failed MMIO leaves delivery masked.
The same identity is not silently converted to a completion. A tested rearm
race fix restores the mask if the primary filter ran between the software
state change and the hardware enable write.

The implementation preserves unrelated bits while enabling the selected
render/copy/CCS0 MI_USER and FLUSH_COMPLETE sources. Main GuC-to-host is bit15
of its identity vector and bit31 of the shared GuC enable/mask registers.
The main/media mask halves are preserved independently. These definitions and
the ordering come from Intel's MIT-licensed
[Xe IRQ implementation](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_irq.c),
[IRQ registers](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/regs/xe_irq_regs.h),
and [GuC IRQ enable logic](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_guc.c).

The router must exclusively own the complete tile0 master interrupt path.
Display, media, GSC and error sources require the supplied `otherMaster` or
identity handler to acknowledge and drain their actual hardware. An unhandled
source fails closed and is retained as a fault; this module does not silently
steal the master interrupt from an existing Apple graphics driver. IRQ
installation does not claim to implement display IRQ handlers.

Hardware IRQ class numbers are render=0, copy=3, other=4 and compute=5.
They are different from GuC registration class numbers. Main GuC is other
instance0; media GuC instance16 is not dispatched to the main transport.
The [engine class definitions](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_hw_engine_types.h)
are the source for this distinction.

## GuC messages and GPU completion remain separate

`Dispatcher` consumes up to 64 real decoded CT messages per workloop action.
If more remain, it requests another action while keeping the master masked.
The current pending callback is preserved across actions, so draining does
not re-ack a captured identity or duplicate already consumed messages.
Unexpected vectors, epochs, classes or CT failures return an error.

An engine interrupt invokes the fence reader; it does not advance a software
seqno. The fence slot can still contain zero or a previous completed sequence
after an interrupt. Only the actual observed qword is reported to the owner.
The tests explicitly verify that a GuC notification produces no fence event
and that an engine interrupt before the memory update reports sequence zero.

`Timeline::bind` accepts an aligned 8-byte coherent GGTT slot below 4 GiB,
with immutable allocation, owner, context, epoch and physical engine identity.
Authoritative callbacks must prove the exact CPU/GGTT mapping, prepared
direct coherent SMEM and GPU write ownership. The slot is initialized to zero
only after context quiescence is established. The mapping is pinned before
the first CPU write. Thereafter only the GPU command stream may update it.

The command emitter must issue the engine-appropriate cache flush/stall and
GGTT qword post-sync write `{sequence32, 0}`, then MI_USER_INTERRUPT.
`published(epoch, sequence)` records strictly contiguous issued sequences,
serialized with ring publication and before the workloop can observe them.
Publication is not a completion. The emitter owns acceptance-unknown and
submission-failure handling; a timeout cannot roll back a possibly published
slot or reuse its address. Intel's
[ring emission](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_ring_ops.c)
and [hardware-fence reader](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_hw_fence.c)
provide the underlying completion model.

The reader uses an aligned volatile 64-bit x86_64 load with CPU ordering
barriers and validates mapping ownership before and after it. A nonzero high
dword, sequence beyond publication, regression, stale epoch or revoked mapping
invalidates the observation. CPU fences order direct coherent DMA observation;
they do not stand in for GPU cache flush commands. The sequence cannot wrap,
and a Timeline object cannot be rebound to a reused allocation.

`invalidate()` retains memory and marks no work successful. `close()` releases
the GGTT pin only after hardware quiescence is confirmed. The IOKit adapter
likewise retains the descriptor/map on a busy close; a failure of
`IOMemoryDescriptor::complete` preserves the prepared descriptor for retry.

## IOKit lifetime and integration contract

Create and initialize `MellowXeInterrupt` as an OSObject, and call attach,
start and detach while holding the supplied workloop gate. The provider IRQ
index must come from actual provider enumeration; no global IRQ or MSI vector
is guessed. Attach checks physical PCI 8086:7D41 / 00:02.0 before spoof hooks,
and adapter admission requires the measured 12.70 IP and a held GT forcewake
reference. The owner's hard-IRQ-safe admission callback must maintain real
PF/D0/reset-epoch/exclusive-router proof throughout the attachment.

The adapter retains its PCI provider and workloop, and holds an internal
reference to itself until successful detach. The caller must keep the plain
`IOKitMmio` object, its mapping, forcewake reference and handler objects alive
for the same period. Hard IRQ admission must not sleep or call arbitrary IOKit
APIs. All CT/fence callbacks execute on the serialized workloop.

Detach first disables the event source, then confirms tile-master masking
with a posting read. If that fails, it preserves the disabled event source,
workloop, provider, MMIO binding and internal owner reference for a gated retry.
A partial attach with uncertain MMIO has the same retained-ownership rule.
The caller cannot treat a failed detach as permission to destroy MMIO or
reset-related state. An irreversibly revoked epoch needs the enclosing owner
to perform and prove hardware shutdown before cleanup can be authorized.

Successful removal detaches the source from the workloop before dropping its
references. Apple's
[IOInterruptEventSource implementation](https://github.com/apple-oss-distributions/xnu/blob/main/iokit/Kernel/IOInterruptEventSource.cpp)
unregisters the provider interrupt on workloop removal. Its provider disable
and unregister flow uses the platform interrupt controller; Apple's
[IOInterruptController implementation](https://github.com/apple-oss-distributions/xnu/blob/main/iokit/Kernel/IOInterruptController.cpp)
waits for active delivery during non-interrupt-context disable. The code relies
on this native IOKit synchronization contract. The host shim tests resource
lifecycle but do not prove actual platform interrupt synchronization.

## Validation and exact limitations

Run from the workspace root with the available local compiler:

```powershell
python outputs/Mellow-7D41-runtime/tests/xe_interrupt_test.py --compiler C:/msys64/mingw64/bin/g++.exe --report outputs/Mellow-7D41-runtime/tests/xe_interrupt_result.json
python outputs/Mellow-7D41-runtime/tests/xe_interrupt_iokit_test.py --compiler C:/msys64/mingw64/bin/g++.exe --report outputs/Mellow-7D41-runtime/tests/xe_interrupt_iokit_result.json
```

The production core and actual GuC transport passed 132,009 host assertions,
including the repeated 65,536-sequence progression loop. This number is not
a count of independent hardware scenarios. Tests cover every selector bit
in both banks, decode/ack order, malformed/timeout/epoch paths, MMIO faults,
masked continuation, the rearm race, stale/advanced/regressing qwords, zero
completion before GPU simulation, CT drain boundaries and unknown sources.

The actual IOKit adapter method bodies passed 38 additional host lifecycle
assertions against an explicitly substituted OS boundary. They cover partial
attach, source creation/add failure, failed-stop retention and retry, internal
owner references, a successful write callback whose posting read still shows
the master enabled, mapping/prepare failure, busy fence release and completion
failure retry. The shim is absent from production compilation.

All four new source files also compiled with the real vendored kernel SDK and
Darwin x86_64 `-mkernel -fapple-kext -Werror` flags. The inherited SDK macro
redefinition warning is separately suppressed for this targeted compile;
there are no dummy imports or link stubs. Full final kext linking is recorded
by the root build workflow. Reports are `xe_interrupt_result.json`,
`xe_interrupt_iokit_result.json`, and `xe_interrupt_kernel_compile.json`.

Primary source revisions and content hashes are in
`tests/xe_interrupt_provenance.json`. Linux definitions were inspected at
commit `4d7d9486c04d917265f64c55bd23b2cc4fe7749c`; Intel's MIT attribution is
preserved here. Apple files were inspected from their public source with
content hashes recorded; their license headers remain in the upstream files.

Remaining physical validation is explicit: actual IRQ registration/delivery,
PCI power/reset races, controller synchronization, GuC-to-host DMA ordering,
actual post-sync fence writes, batch completion, display routing and Metal
execution. Passing these host/compiler checks does not make any of those
operations observed or proven.
