> **Historical record — preserved unedited.** Component documentation for the hand-written
> Intel Xe backend, which compiles into the kext but has no call path
> ([Mellow/RuntimeReadiness.hpp:84](../Mellow/RuntimeReadiness.hpp)). Scheduled to move to
> `docs/backends/xe/` in P1. For how these modules map onto the vendor-neutral abstraction
> see [MGAL.md](MGAL.md); for the current architecture see [ARCHITECTURE.md](ARCHITECTURE.md).

# GuC CTB/HXG transport implementation (0.3 research)

This change implements the GuC wire transport and a real checked IOKit MMIO adapter. It does not claim that the Galaxy Book has executed GuC firmware, an engine batch, or a Metal shader. The shipped default proof callbacks are unavailable. Merely parsing the firmware CSS header cannot authorize a register write.

## Implemented code

`Mellow/XeGuCTransport.cpp` contains executable protocol code with these behaviors:

- The exact 64-byte CT descriptor and HXG/CTB header fields. H2G writes preserve a one-dword empty slot, zero-pad the end before a message would wrap, publish payload before tail, and notify GuC. If padding consumes the remaining room, the action stays unsubmitted and the caller retries. G2H reads take an ordered snapshot and handle messages split at the ring boundary.
- Response-space credits reserve half of G2H for unsolicited traffic. A synchronous request reserves 256 dwords, scheduling-mode completion reserves four, and deregistration completion reserves three. BUSY is intermediate and keeps the credit; success/failure/retry releases it once. An unrelated event or unknown response cannot manufacture credits.
- A bounded table tracks epoch plus 16-bit CT cookie. Bit15 distinguishes FAST_REQUEST from REQUEST. Cookies are never reused within an epoch: after 32,768 sends the transport returns `Exhausted`, requiring a confirmed hardware stop/reset and new object/epoch. This conservative policy avoids attributing a late reply to another command.
- Scheduling event replies correlate by context ID and expected transition, as the pinned Xe handler does. The transport refuses a second overlapping mode/deregister transition for the same context. This protocol acknowledgment is distinct from a GPU execution fence.
- Absolute deadlines survive BUSY messages. Timed-out requests retain credits until their real late reply arrives; their result remains `TimedOut` even then. A partial or uncertain publication returns `PublishedUnknown` and preserves response ownership. Corrupt descriptors, invalid formats, truncated messages, unexpected cookies and duplicate final responses stop the transport.
- An action allowlist encodes normal single-LRC KMD context registration, schedule, mode enable/disable, deregistration, and the existing HuC-authentication request format. Register-context is **12 dwords**, including both halves of the prepared hardware LRC descriptor, matching `__register_exec_queue()` at the pinned commit. The older offset enum's terminal length is not used to truncate the upper dword. Only render/compute classes are admitted by this bounded encoder. Multi-LRC, multi-queue and policy/KLV actions are not silently synthesized.

`Mailbox::exchange()` implements the actual main-GT MMIO HXG transaction: write up to four VF_SW_FLAG registers at `0x190240`, drain posted writes by reading the last slot, write zero to `GUC_HOST_INTERRUPT` at `0x1901f0`, and inspect actual responses. It accepts only the six CTB SELF_CFG keys and CONTROL_CTB. Initial response waiting is bounded at 50 ms; BUSY has a separate 2-second bound. Failure and retry are surfaced without implicit resend. Timeout/uncertain I/O poisons the mailbox because a later response must not be mistaken for a new request. A second iteration bound also prevents a stuck clock callback from hanging the kernel.

`configureAndEnable()` validates disjoint GGTT ranges, descriptor alignment, power-of-two rings with 4-KiB-multiple sizes, declared address limits, image release70.53.0 and submissionABI1.26.0. Before any memory write, an authoritative `configurationAllowed` callback must confirm that CTB is stopped and that these exact addresses refer to retained, directly coherent CPU/GGTT backing. It then resets descriptors/buffers and checks six SELF_CFG acknowledgments (each must return1), followed by CONTROL_CTB enable acknowledgment (must return0). Any failure leaves resource ownership with the caller until actual stop/reset is established.

## Actual IOKit path and caller contract

`Mellow/XeGuCTransportIOKit.cpp` connects the protocol to the real `MellowXe::IOKitMmio` mapping and time functions; it is not an emulator. It checks the held GT forcewake reference and measured graphicsIP12.70. Before every MMIO access it reads `GUC_STATUS` at `0xC000` and requires AUTH_GOOD, ukernel READY, BootROM JUMP_PASSED and no reset/halt indication. That is hardware status evidence only; it does not identify which image was loaded. The owning driver must also supply the actual loaded-image identity and reset epoch.

The preferred entry point is `IOKitBinding::startTransport(config, transport)`. It sets its internal CT-enabled state only after the seven real mailbox acknowledgments succeed, then attaches the rings. The action callback remains disabled until that state is reached. G2H data already emitted between enable and attach is preserved.

The kernel integration must retain `IOKitMmio`, the forcewake reference, CT descriptors/rings, their IOMemoryDescriptor/IODMACommand ownership, and GGTT mappings while the binding can access them. Calls need one serialized sleepable owner and must not run from an interrupt handler. Allocate the transport off the kernel stack: it contains 32 bounded response snapshots. Reset/power transition must revoke the epoch proof before touching these objects.

GuC CT addresses are **GGTT/global graphics addresses**. The existing private PPGTT page-table builder and `VirtualMemory::Bound` alone do not prove a GGTT mapping. `configurationAllowed` must verify direct coherent system-memory backing and the real GGTT/PAT/TLB contract above WOPCM and below the platform APIC boundary. Whole-buffer DMA bounce copies are unsuitable for CT descriptors because CPU and GuC write different fields concurrently. The adapter uses actual CPU memory fences for coherent SMEM; it does not pretend these are GPU cache flushes.

Before allowing an action, `DriverProofs::authorizeAction` must additionally establish its context-specific facts: registered owner and valid initialized LRC/ring, published ring tail for schedule, legal pending mode transition, disabled/quiescent context for deregistration, or the correct mapped RSA/GSC policy for HuC. The encoder does not construct missing LRC images or authorize an arbitrary address. The HuC helper describes that wire action; it does not replace Meteor Lake's required GSC authentication workflow.

## Validation performed

Run `python tests/xe_guc_test.py --report tests/xe_guc_result.json` with a host C++17 compiler. The harness compiles the real `XeGuCTransport.cpp` with warnings treated as errors. It exercises exact encoded dwords and CT registration KLVs, H2G padding with and without sufficient remaining credits, split G2H messages, early unsolicited events, BUSY/failure/retry, timeouts and late replies, context/state mismatch, full queues, response credits, malformed/truncated/host-origin messages, duplicate/unknown cookies, lost notify, clock regression, a stuck clock, unsupported ABI and admission denial. It exhausts all 32,768 wire cookies through the public API. The recorded 105,073 assertions include repeated checks in that exhaustive boundary loop, not 105,073 independent GPU tests.

The MMIO test peer is an explicit host emulator. The IOKit adapter is compiled with the actual kernel target as part of the full build; no macOS runtime or physical GuC validation has occurred on this Windows host. Do not infer engine completion from CT traffic, the compiler's Zebin output, a mailbox response, or an IRQ arrival.

## Physical backend still required

The firmware uploader/authentication lifecycle is not provided by this transport. It requires the real selected image in a valid GuC-addressable GGTT mapping, verified WOPCM offset/size/lock state, DMA source/destination limits, ADS/log/init-parameter buffers, platform workarounds and power/reset ordering, then the hardware boot/auth result. Although individual DMA register offsets are public, writing an isolated START_DMA value without these prerequisites is not a valid implementation. The current default backend cannot provide `ownsEpochAndLoadedImage`, so the new adapter honestly returns unavailable before a write.

After firmware bring-up, the driver still needs actual GGTT publication/TLB invalidation, PAT/MOCS setup, LRC/ring construction, per-platform compute-state/walker emission, IRQ routing and ordered hardware seqno observation. CTB transports control messages to that machinery; it does not provide a Metal compiler, a Metal user-mode driver, IOAccel resource ABI, or Apple framework compatibility. These missing components remain visible in the production readiness gate.

## Primary provenance

Definitions and algorithms were inspected at Linux commit `4d7d9486c04d917265f64c55bd23b2cc4fe7749c`. The Intel Xe source files carry MIT SPDX identifiers; this implementation is local code based on their public ABI, with Intel attribution retained here. Pinned file hashes are recorded in `tests/xe_guc_provenance.json`.

- [CTB descriptor/message ABI](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/abi/guc_communication_ctb_abi.h) and [HXG message ABI](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/abi/guc_messages_abi.h): wire fields, message types and bounds.
- [xe_guc_ct.c](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_guc_ct.c): `h2g_write`, `g2h_read`, credits, request fences and configuration order.
- [Actions ABI](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/abi/guc_actions_abi.h), [KLV ABI](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/abi/guc_klvs_abi.h), [scheduler ABI](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/abi/guc_scheduler_abi.h): action numbers, GGTT addressing, configuration sizes, context classes and flags.
- [xe_guc_submit.c](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_guc_submit.c): register-context field order, LRC descriptor, schedule and completion handlers.
- [xe_guc.c](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_guc.c), [registers](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/regs/xe_guc_regs.h) and [status ABI](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/abi/guc_errors_abi.h): main-GT mailbox registers, notify payload, polling states, authentication/ready values.

Firmware identity and CSS-only validation remain recorded separately in `docs/XE-SUBMISSION.md`; no additional firmware was flashed, uploaded, or authenticated by this change.
