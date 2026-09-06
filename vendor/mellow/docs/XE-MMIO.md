> **Historical record — preserved unedited.** Component documentation for the hand-written
> Intel Xe backend, which compiles into the kext but has no call path
> ([Mellow/RuntimeReadiness.hpp:84](../Mellow/RuntimeReadiness.hpp)). Scheduled to move to
> `docs/backends/xe/` in P1. For how these modules map onto the vendor-neutral abstraction
> see [MGAL.md](MGAL.md); for the current architecture see [ARCHITECTURE.md](ARCHITECTURE.md).

# BAR0 access and forcewake

`XeMmioIOKit` maps the real PCI BAR0 through IOPCIDevice and uses bounds-checked,
ordered 32-bit access. Attach requires physical 8086:7D41 at 00:02.0 before PCI-ID
spoof hooks, enabled memory decode, and sufficient BAR0 length. The caller must
already own the PF/main GT exclusively and have it in D0. Attach does not establish
that ownership or negotiate power with another driver.

`XeMmioAccess` decodes the hardware GMD_ID. The implemented register profile admits
only graphics architecture 12, release 70; the Windows PCI ID and offline compiler
selector cannot replace that read. GT/render holds use the kernel request bit and
masked writes, verified ACK transitions, nested references and render-before-GT
release ordering. Existing foreign kernel holds are refused. Waiting is bounded
both by a monotonic clock and iteration limit. Read errors, all-ones responses,
timeouts and clock regressions are reported. An uncertain write/release makes the
instance faulted and prevents unmapping potentially live registers. Clean shutdown
supports attach/detach/re-attach. All calls must be serialized outside interrupt
context; there is no implicit destructor cleanup of uncertain hardware state.

The host test runs these actual implementation functions against a register/time
simulator. The IOKit adapter is cross-compiled as part of the kernel extension.
Neither procedure reads the running Windows GPU or proves real forcewake behavior.
These classes are not automatically attached by Mellow startup. DMA, GuC firmware
authentication, GGTT binding, context publication and IRQ registration remain
separate prerequisites before execution.

Register and protocol reference: [Linux Xe forcewake implementation](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_force_wake.c)
and [Xe GT register definitions](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/regs/xe_gt_regs.h).
