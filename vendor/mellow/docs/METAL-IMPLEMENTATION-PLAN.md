> **Historical record — preserved unedited.** This document predates the MELLOW
> re-architecture. It is retained because the record of what was known, and when, is itself
> evidence. For the current concept and architecture see [CONCEPT.md](CONCEPT.md) and
> [ARCHITECTURE.md](ARCHITECTURE.md); for what any of it is allowed to claim, see
> [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).

> Historical 0.1.1 implementation plan. Version 0.2.0 adds the Xe components described in README.md and docs/XE-*.md. The legacy probe below remains at Tools/metal-probe-legacy.swift; the new challenge probe and offline compiler are described in docs/IOACCEL-METAL.md. Hardware execution is still unverified.

# Metal implementation map: Core Ultra 7 255U / 8086:7D41 / Darwin 25

This is the implementation and acceptance plan for the local development tree.
It separates repaired source from the missing platform implementation. Successful
compilation, a kext loading, an `IntelAccelerator` service, and a `MetalPluginName`
property are different milestones. None alone establishes GPU execution.

The hardware target is physical Intel CPU family 6/model B5 paired with PCI
8086:7D41. The 9A49 ID is a compatibility identity exposed to inherited TGL
drivers, not the physical hardware. Darwin 25 is an explicit research trial in
`Mellow/StartupPolicy.hpp` and `Mellow/kern_start.cpp`; the `-mellowtahoe` argument
does not certify the Tahoe private ABI. An active `-igfxvesa` conflicts with that
trial. This document does not prescribe an EFI switch or an installation step.

## 1. The execution chain that must actually work

The intended path starts with a Metal application's buffer and pipeline creation,
continues through its command encoder and command buffer, enters the graphics
driver's user/kernel interface, places a valid job in a hardware context, and
finishes only after the device completed it and made the output visible to the
CPU. Render presentation adds display ownership and synchronization beyond that
offscreen compute/render chain. Apple's public API describes the device, queue,
encoder, commit, completion and error contracts; it does not by itself implement
a device-specific kernel driver.
[Apple command execution model](https://developer.apple.com/library/archive/documentation/Miscellaneous/Conceptual/MetalProgrammingGuide/Cmd-Submiss/Cmd-Submiss.html)

Current source locations along that chain are:

- **Entry and identity:** `Mellow/kern_start.cpp` applies the OS/trial policy;
  `MellowCore::init` and `MellowCore::processPatcher` in `Mellow/kern_mellow.cpp`
  gate the physical CPU/GPU pair and install callbacks.
- **Driver attachment:** `Gen11::init` and `Gen11::processKext` in
  `Mellow/kern_gen11.cpp` register and route the external TGL framebuffer and
  accelerator images. The source names both `com.xxxxx` and `com.apple` variants.
  These names are expected dependencies, not evidence those binaries exist in
  the package or work on 7D41.
- **Power and accelerator state:** `Gen11::hwInitializeCState`, `Gen11::start`,
  `Gen11::startGraphicsEngine`, `Gen11::forceWake` and
  `Gen11::populateResetRegisterList` contain inherited platform adaptation.
  Their presence is not a completed 7D41 power/reset implementation.
- **Task, resource and context ownership:** `Gen11::createUserGPUTask`,
  `Gen11::igAccelTaskWithOptions`, `Gen11::IGHardwareContextinitWithOptions`,
  `Gen11::IGHardwareContextwithOptions`,
  `Gen11::IGHardwareExtendedContextinitWithOptions`,
  `Gen11::wrapIgBufferWithOptions` and
  `Gen11::IGAccelSegmentResourceListprepare` operate within inherited Apple
  object layouts. `Mellow/AppleIntelParams.hpp` records partial layouts; its
  static assertions validate the declared C++ offsets, not an unknown binary.
- **Submission and synchronization:** `Gen11::submitBlit` and
  `Gen11::barrierSubmission` sit in the submission path. `Gen11::loadGuCBinary`
  has no 7D41 firmware backend. `Gen11::readAndClearInterrupts` and
  `Gen11::serviceInterrupts` contain interrupt-related code, while
  `wrapWaitForStamp` in `Mellow/kern_mellow.cpp` observes client completion.
  Some routes are commented or conditional: a function declaration must never
  be counted as proof that its callback is installed or receives interrupts.
- **User-space bundle discovery:** `Mellow/Info.plist` names
  `AppleIntelTGLGraphicsMTLDriver`, GL and VA bundles. `DYLDPatches::wrapCsValidatePage`
  in `Mellow/DYLDPatches.cpp` can log an image being seen. Such a log proves only
  an image observation, not successful loading, pipeline creation or execution.

## 2. Implemented corrections versus missing work

Implemented local corrections include exact-device PCI spoof scope, checked
DWORD MMIO and uncached map validation, removal of undocumented out-of-range
indexed access, strict MMIO GGC decoding without an invented 128 MiB floor, and
refusal to expose an old GGTT aperture through Xe-LPG BAR2. Start and stamp
wrappers preserve the underlying driver's result. Native tests exercise shared
code for these decisions. See `docs/DRIVER-CORE-CHANGES.md` and the build/audit
reports for the precise tested scope.

The submission corrections also make an unavailable blit/backend fail instead
of manufacturing success. `Gen11::barrierSubmission` no longer defaults to a
bypassed successful barrier; its selected explicit original path forwards the
arguments and underlying result. These are error/ownership corrections, not a
new command-submission implementation.

These corrections remove invalid assumptions from the path. They do not provide
the following components, which require implementation or verified compatible
external code and actual device measurements.

### Device memory and page tables

The driver needs an explicit model of system memory, CPU mappings, DMA mappings,
GPU virtual addresses, GGTT mappings, per-process address spaces, and reserved
graphics memory. A CPU virtual pointer, a physical address, a GGTT offset and a
device-memory offset are not interchangeable.

The current GGC decode records total DSM. Intel's Xe implementation excludes
reserved firmware memory before allocation and uses LMEMBAR/DM-PTE semantics on
graphics IP >=12.70; the legacy BAR2 CPU-aperture shortcut is therefore disabled.
[Intel Xe stolen-memory implementation](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/xe/xe_ttm_stolen_mgr.c)

Required implementation work is to define ownership and lifetime for every
allocation, determine usable reservation bounds, pin/map client buffers, encode
the target's page-table entries and cache attributes, handle page-table updates
and TLB invalidation, and prevent reuse until all dependent jobs are finished.
Context memory must belong to its original task/address space, with explicit
references. Copying an opaque cached task or LRCA pointer into another task does
not establish that ownership. Linux's VM code is a reference for lifecycle,
binding and synchronization responsibilities, not a drop-in macOS API.
[Intel Xe VM implementation](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/xe/xe_vm.c)

Acceptance requires guard-region preservation, correct GPU-to-CPU and CPU-to-GPU
visibility, no out-of-range DMA, correct map/unmap ordering, and isolation between
two tasks. Stop if reservation boundaries, PTE semantics, ownership or invalidation
completion are unknown. Do not expand a reservation or substitute an arbitrary
physical page to make an allocation appear successful.

### Firmware, power state and a supported submission backend

GuC-based operation requires the appropriate hardware/version firmware, validation
and authentication, correct reserved-memory layout, startup/status handling,
host-to-firmware communication, context registration, submission and teardown.
The current `Gen11::loadGuCBinary` reports the absence of an implemented 7D41
backend. It cannot be converted into a firmware implementation by returning a
successful boolean. DMC display firmware and GuC scheduling firmware have
different responsibilities.

An alternative host/Execlist submission path is a research possibility only if
primary documentation and observed hardware support it for this exact target.
`GraphicsSchedulerSelect=5` in the inherited source selects a software path; it
does not prove that path's descriptors, context format or scheduling assumptions
match 7D41. Linux exposes separate backend concepts under execution queues;
their presence is not permission to select any backend on any platform.
[Intel Xe execution queue documentation](https://docs.kernel.org/gpu/xe/xe_exec_queue.html),
[Intel Xe GuC submission source](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/xe/xe_guc_submit.c)

The first backend acceptance test is a single bounded job using a documented
command sequence, in an owned context and owned output allocation, followed by
a hardware-written result and completion record. It should not depend on the
Metal compiler yet. No command opcodes or register programming sequence is
invented in this plan. Stop if firmware fails to authenticate, forcewake fails,
the engine does not advance, or the job times out. Keep the first failure trace;
retrying until an eventual success can destroy the evidence of the real fault.

### Interrupts, fences and recovery

Submission requires an installed interrupt path, correct status decode and
acknowledgement, synchronization with queue state, and a completion fence attached
to the actual job. The fence must protect resource lifetime and ordering. A
ring-head/tail comparison, a successful driver `start`, or a timer firing is
insufficient to certify output visibility or job completion.

The current `gGfxAccelStartDone` records successful accelerator start only.
`wrapWaitForStamp` preserves failures; a failed wait must never assign the
requested stamp to the completion output. Likewise, a GPU barrier cannot be
implemented by bypassing it and returning success. The bring-up review must
confirm no active completion bypass remains in the selected profile before
interpreting test outputs.

Required acceptance includes monotonically associated job/fence IDs, exactly
one completion delivery per job, correct dependency order, no completion for a
rejected job, bounded failure on a stalled job, and safe resource cleanup after
process exit. Capture the first fault snapshot before recovery mutates hardware
state. Intel's coredump documentation explains why first-failure state is useful.
[Intel Xe device coredump](https://docs.kernel.org/gpu/xe/xe_devcoredump.html)

### IOAccelerator user client and private ABI

The existing approach wraps an accelerator implementation supplied by other
binaries. It must verify the exact accelerator/framebuffer/IOAcceleratorFamily2
versions and their user-client contracts, object layouts, selectors, shared
memory structures, resource handles, synchronization objects and return values.
The expected provenance record includes each bundle ID, version, executable hash,
architecture and linked dependencies, together with the Darwin 25 build.

Symbol resolution or a unique byte pattern is only a location check. It does not
prove the calling convention, object size or semantics. Before invoking a routed
method, establish its ABI from the exact binary and confirm pointer ownership and
failure behavior. An unavailable or mismatched external driver is a hard stop for
that integration route, even if the Mellow plugin itself builds correctly.

Acceptance starts with one client opening the intended accelerator, creating and
destroying its own resources, then submitting a known small workload. Reject
invalid sizes, handles and cross-task access with errors rather than kernel
faults. Close the process with outstanding work and verify bounded cancellation
or completion with no stale references. These tests need a real macOS kernel;
host C++ helper tests cannot substitute for them.

### Metal user-space driver and compiler

A usable Metal backend must create the device/resources/pipelines, compile or
load target-compatible shader code, emit target-compatible compute/render/copy
commands, and communicate with the matching kernel ABI. The current source
contains bundle names and hooks, not an implemented 7D41 Metal compiler or a
complete `MTLDevice` implementation. No compatible external TGL MTL bundle has
been established merely by those names.

Research must first inventory the actual external user-space binaries and prove
which shader ISA, state packets, resource formats and private interfaces they
support. If no compatible implementation can be obtained, a real user-space
driver/compiler port is a separate major development project. Renaming an ICL
bundle, passing a device-ID comparison or injecting a feature property cannot
convert its generated code into a new GPU architecture's implementation.

Acceptance proceeds from enumeration to pipeline creation, verified compute
output, verified offscreen rendering, and then presentation. Capability flags
must describe only implemented/tested operations. Passing a small shader does
not imply video decode/encode, all pixel formats, full Metal-family conformance,
WindowServer usability or suspend/resume correctness.

## 3. Staged bring-up and stop criteria

1. **Reproducible artifact and dependency inventory.** Record source revision,
   compiler/linker, SDK, binary hashes and all external driver dependencies.
   Run host tests and structural build validation. Stop on a failed build,
   unresolved dependency or ambiguous binary target. Structural success does
   not advance the hardware milestone.
2. **Physical admission and observation.** Record physical B5/8086:7D41 and
   revision, actual macOS/Darwin build, BAR lengths and the checked GGC result.
   Compare independent hardware evidence with any spoofed registry identity.
   Stop on mismatch, inaccessible BAR0 or repeated all-ones register reads.
   The current full plugin includes inherited writes; it is not a read-only
   observation driver just because its initial evidence reads are read-only.
3. **Owned memory and minimal device job.** Complete the memory and backend
   work above. Validate a bounded hardware-written output and its fence before
   attaching desktop composition. Stop on uncertain address translation,
   reservation overlap, corruption, firmware failure or timeout.
4. **Kernel/user-client integration.** Use the exact verified driver ABI,
   exercise resource lifecycle and errors, and correlate submission/completion
   logs. Stop on unverified object layout, unsafe ownership transfer, fake
   completion or missed interrupts.
5. **Real Metal compute and offscreen rendering.** Compile and execute the
   existing Swift probe on the target and correlate its selected registry ID
   with physical 7D41 driver evidence. Stop on missing target, pipeline failure,
   command error, timeout or any output mismatch.
6. **Presentation, concurrency and lifecycle.** After earlier stages pass,
   test repeated draws, two independent processes/queues, dynamic resource
   allocation, display mode changes, hotplug where applicable, sleep/wake and
   recovery. Define durations and iteration counts before the run. Stop at the
   first unexplained fault and keep its artifacts. These are future acceptance
   tests, not completed results.

## 4. Real Swift acceptance probe already present

The existing source is included as `Tools/metal-probe-legacy.swift`, copied from the
earlier GalaxyBook-Tahoe preparation package.
This plan does not claim it has been compiled or run
on macOS. Compile it on the test Mac using the installed macOS SDK and Swift
compiler, for example:

```sh
xcrun swiftc -O -framework Metal -framework IOKit Tools/metal-probe-legacy.swift -o /tmp/metal-probe
/tmp/metal-probe
/tmp/metal-probe --compute 0xREGISTRY_ID_FROM_THE_ENUMERATION
```

The first invocation only enumerates devices and prints default-device/registry
identity. The second targets the explicit registry ID and refuses an unrelated
or evidently software provider. A registry device-id of 9A49 can be spoofed and
must be correlated with the driver's physical 7D41 log.

The submitted test initializes shared output to a sentinel, compiles a Metal
compute shader, executes 1,024 unsigned-integer calculations, and checks every
word against independent CPU arithmetic. It then draws a full-screen triangle
into a private 4x4 RGBA8 texture over a different clear color, blits the result
to shared memory with a padded row stride, and verifies all 16 red pixels. A
completed-handler semaphore has a ten-second bound and command status must be
completed. A timeout does not cancel the hardware job.

Require both `PASS_COMPUTE_OUTPUT` and `PASS_RENDER_OUTPUT`, exit status zero,
correct provider correlation, and matching kernel submission/fence evidence.
`gpuStartTime/gpuEndTime` are supplementary measurements, not the sole proof.
The probe writes no CPU fallback result into the expected output. Its private
render target and explicit copy reflect the CPU/GPU access distinction in
Apple's resource guidance.
[Apple resource options](https://developer.apple.com/library/archive/documentation/3DDrawing/Conceptual/MTLBestPracticesGuide/ResourceOptions.html),
[Apple compute pipeline model](https://developer.apple.com/library/archive/documentation/Miscellaneous/Conceptual/MetalProgrammingGuide/Compute-Ctx/Compute-Ctx.html)

Keep stdout/stderr, exit status, executable/source hashes, exact boot arguments,
loaded bundle identities and `Tools/collect-mellow-logs.sh` output together for
each run. The collector is best-effort system inspection; its success means
collection succeeded, not acceleration succeeded.

## 5. Why root/UEFI/ROM patches are not the missing Metal driver

A root patch can arrange compatible driver files and loading conditions on the
installed system. UEFI/ACPI changes can affect enumeration, resource descriptions
or firmware setup. Neither operation supplies missing shader compilation, a
target-specific command encoder, a memory manager, a submission backend or the
kernel/user-space ABI required above. Firmware edits need a specific diagnosed
firmware defect before they can be tied to this implementation plan.

The next useful milestone is therefore evidence of a correct owned-memory job
and its real completion on 7D41, together with an available compatible user-space
Metal path. Until those exist, report the artifact as a development plugin with
documented missing backends, not a completed Metal acceleration driver.
