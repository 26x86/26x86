> **Historical record — preserved unedited.** Component documentation for the hand-written
> Intel Xe backend, which compiles into the kext but has no call path
> ([Mellow/RuntimeReadiness.hpp:84](../Mellow/RuntimeReadiness.hpp)). Scheduled to move to
> `docs/backends/xe/` in P1. For how these modules map onto the vendor-neutral abstraction
> see [MGAL.md](MGAL.md); for the current architecture see [ARCHITECTURE.md](ARCHITECTURE.md).

# One evidence job through VM, native commands, GuC and a real fence

`Mellow/XeContextExecution.hpp/.cpp` connects the existing VM, Zebin loader,
native command builder, GuC transport and coherent fence reader. It supports one
job in one immutable owner/context/reset epoch. No native hardware backend is
installed by default and no GPU execution was performed during this Windows
build. Missing GGTT, primed-context, firmware, cache, IRQ or preemption proof
returns Unavailable; the coordinator does not manufacture those prerequisites.

The object must be allocated off the small kernel stack. It owns an immutable
copy of the context identity, six VM handles and the CPU execution heaps. The
VM, GuC transport, fence and backend must outlive it until `close()` succeeds.
Calls, DMA mapping changes, retirement, fence observation and GuC reply dispatch
must be serialized by one driver ownership domain.

The executed source path is:

1. `begin` validates the exact RCS0 descriptor, context/ring ranges, epoch,
   expected empty disabled context and initial coherent fence value zero. The
   mandatory driver's admission callback must inspect the actual primed context,
   platform workarounds, preemption mode, live firmware/full ADS, MOCS/PAT,
   PPGTT/TLB, GGTT mapping ownership and IRQ route.
2. It retains the GGTT context/ring through the driver callback and acquires
   `VirtualMemory::retainUse` on six already-Bound handles: instruction heap,
   indirect heap, surface heap, batch heap, input and output. A partial failure
   retains whatever was acquired until explicit cleanup with quiescence proof.
3. `prepareBoundEvidence` copies the real included Intel-compiled kernel and
   builds its native execution heaps. The required `stageHeaps` backend copies
   these immutable bytes to the exact held DMA allocations and completes real
   CPU-to-device synchronization. A callback that merely returns true without
   those operations is not a valid backend.
4. It writes the native ring fragment, reserves sequence 1 with
   `XeFence::Timeline::published`, writes the actual supplied LRC tail CPU mapping
   and executes CPU ordering fences plus the required context synchronization.
   Reservation precedes every execution-capable GuC message.
5. It invokes the real `XeGuC::Transport::send` with REGISTER_CONTEXT followed by
   SCHED_CONTEXT_MODE_SET(enable). Linux's single-LRC disabled-queue path uses
   this mode-enable message to schedule the already published ring. An additional
   SCHED_CONTEXT is not sent as if enable were inert. The mode-enable message
   can start GPU work before the asynchronous mode-change acknowledgment.
6. `poll` examines transport-correlated control replies and calls the actual
   `XeFence::Timeline::observe`. GuC control success alone remains Pending.
   Only an acquire-ordered qword `{1,0}` for the exact owner/context/epoch/RCS0
   fence releases the six VM uses and marks the execution Completed.

The real IRQ/workloop must call `Transport::receive` to dispatch G2H replies;
`poll` does not consume and discard unrelated GuC events. This is a separate
trusted evidence-job path. The existing MI_NOOP-only `XeSubmission` validator is
unchanged, so arbitrary user command streams are not newly admitted.

A timeout, backwards clock, lost notify, failed synchronization, unknown command
acceptance or corrupt fence retains ownership. A timed-out job can later complete
through a genuine fence observation. No retry republishes the job. `close` needs
the backend's authoritative hardware quiescence and the independent fence
mapping's stop proof. It closes the fence, drops any remaining VM uses and then
releases the GGTT context. Completion alone does not release an active context or
its GGTT/fence mappings. Destroying the object before successful close violates
the explicit lifetime contract. Context teardown/deregistration or GT reset is
the backend's job; this code does not mislabel a timeout as either action.

Completed means the GPU completion fence was observed. It does not itself assert
that output matches the CPU reference, that a Metal user-mode driver exists, or
that native Metal acceleration works. Output validation and physical-device
correlation remain subsequent acceptance checks. The underlying command and
heap formats are documented in [context/dispatch construction](XE-CONTEXT-DISPATCH.md).

The scheduling sequence was checked against Intel's
[pinned Linux `submit_exec_queue`](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_guc_submit.c#L1145),
which publishes ring tails before scheduling and uses mode-enable for a disabled
single-LRC queue. Register/scheduling wire formats are implemented by the existing
[GuC transport](XE-GUC-TRANSPORT.md), and ordered completion is supplied by the
[IRQ/fence implementation](XE-INTERRUPT-FENCE.md).

`tests/xe_context_execution_tests.cpp` passes 224 host checks while linking the
real VM, Zebin, native command builder, GuC transport and fence modules. Its
hardware mapping/stop/DMA callbacks and GPU fence writes are explicitly simulated.
Checks cover real generated H2G register/enable packets; resource retention before
tail publication; acknowledgment without GPU completion; timeout followed by a
late completion; a corrupt high qword; stage/synchronization/notify failures;
retired-output reuse blocked by active uses; and quiescence-only cleanup. The new
translation unit compiles with Clang for x86_64 Apple kernel target and
`-Wall -Wextra -Werror`. These results establish source integration, not native
GPU execution.

## Reproduce the release host tests

From the repository root, run the aggregate launcher with a C++17 host compiler
and the original Intel `mtl_guc_70.bin`. For example, in PowerShell:

```powershell
python Tools/run-runtime-tests.py --cxx C:/msys64/mingw64/bin/g++.exe --out work/runtime-tests --firmware C:/path/to/mtl_guc_70.bin --baseline
```

`--out` contains scratch executables, component reports and the combined
`runtime-tests.json`. `--baseline` is optional and adds the existing VM, page-table,
Zebin, submission and related baseline suite. The standard run always includes
context, dispatch, execution coordinator, GuC transport, GuC firmware emulator,
IRQ/fence core, IOKit adapter lifecycle and Metal session lifecycle tests.

The report preserves exact compiler/runner commands, return codes, output,
production source lists, source SHA-256 hashes and component reports. It fails if
any component fails or a hashed source changes during execution. Its hardware,
native Metal and driver-loaded fields remain false: no test accesses the GPU.
The release copy of the aggregate result is `validation/runtime-tests.json`.
