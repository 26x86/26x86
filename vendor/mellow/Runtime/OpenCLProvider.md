# Native OpenCL C provider

`OpenCLProvider.cpp` is an actual user-space adapter, dynamically linked to an
installed host OpenCL driver. `Tools/run-opencl-runtime.py` compiles it together
with `PlatformRuntime.cpp` into a native C++17 acceptance executable. The Windows
test uses `OpenCL.dll`; Linux and macOS loader paths are also implemented, but
their availability and successful execution must be checked on those hosts.

## Implemented boundary

The acceptance API accepts bounded OpenCL C source, a kernel entry name and one
in-place `uint` buffer, with a caller-supplied expected result for acceptance.
It compiles with the installed driver's OpenCL C 1.2 compiler, allocates the
buffer, submits the kernel, waits for its event and reads the result back.
This is a useful substrate adapter, not MSL/AIR translation or a Metal driver.

The reusable runtime API compiles once with compileOpenClC, returning an owned
OpenCLPipeline; executePipeline then accepts input without an expected answer.
It sets executionCompleted only after real event correlation, profiling,
readback and checked per-dispatch cleanup. It leaves resultsVerified and
runtimeCompletionAccepted false because normal application execution has no
independent result oracle. The separately implemented MellowMTL object layer
translates supported shaders before passing OpenCL C into this adapter.

The adapter requests only GPU devices and requires the runtime's type bits to
exclude CPU devices. It never chooses another device after a failure. This first
version requires `cl_intel_device_attribute_query` for a nonzero device ID because
the current policy descriptor requires one; missing identity is an explicit
initialization error. This is an implementation limit, not an assertion that
other vendors cannot support OpenCL. The reported vendor/device IDs come from
driver queries. Names are never used to invent a PCI ID, and independent physical
PCI ownership is not established by those queries.

The context and queue are owned for the adapter lifetime. It checks the queue's
device, context, in-order property and profiling enablement. Its first bounded
witness dispatch is a bootstrap validation with no advertised capability or
`CompletionTracker` success. It publishes only Compute and OrderedQueue after
readback, profiling and event ownership checks pass. This record is local to the
live adapter and its reset epoch. It is not a transferable hardware certificate.

Subsequent dispatches use `Step::input = OpenClC` in `planWorkload()`. They must
be accepted before any enqueue. The adapter arms `CompletionTracker` only after
the actual enqueue succeeds, binding the live provider/device/queue handles,
epoch and monotonically increasing sequence. It verifies that the returned
event belongs to that queue and context, describes an NDRange kernel, is
complete and has ordered nonzero profiling timestamps. Only after matching the
readback to the expected result does it submit the completion observation.

ComputeTranslation is never advertised by this adapter. A normal/default Metal
compute step therefore still returns UnsupportedFeatures. The API supports no
texture/render/interop/display paths or GL provider, no Linux driver import and
no firmware or kernel modifications.

## Failure and lifetime

Source, entry point, input/reference size and planning errors are rejected before
submission. Compilation failures preserve their build log and do not submit a
kernel. An attempted queue submission followed by failure invalidates the session:
verification is revoked, the epoch advances, the completion tracker is invalidated
and the context/queue are drained and released. Subsequent calls cannot execute
until a fresh context and bootstrap validation are created. `invalidateSession()`
is this software lifetime operation; it does not perform a physical GPU reset.

The class is not thread safe. Acceptance dispatch objects and normal dispatch
memory/events are explicitly finalized after the queue drains; drain/release
errors are checked before reporting executionCompleted or accepted evidence.
Reusable pipelines retain compiled program/kernel objects across submissions;
resourcesReleased describes per-dispatch resources, not destruction of the
persistent pipeline. A pipeline captures its original function table and loader,
retains its provider/context owner and rejects execution after a reset epoch.
Its destructor releases the persistent objects; dispatch destructors perform
fallback cleanup for already-failing paths. A new initialization attempt clears
all prior discovery and bootstrap data, even if the new device cannot expose an
identity; monotonic epoch/sequence counters remain. Synchronous driver calls can hang,
so acceptance executes in a separate process with a 45-second deadline. The
wrapper terminates a timed-out worker and records uncertainty rather than PASS.
Production embedding must provide an equivalent isolation/cancellation boundary.
This library cannot detect a private driver reset that the driver itself hides
while preserving the OpenCL context/event semantics.

## Reproduce

```powershell
python Tools/run-opencl-runtime.py --cxx C:/msys64/mingw64/bin/g++.exe --out build/opencl-runtime --compute
```

Omitting `--compute` only builds. The hardware acceptance performs one bootstrap,
three 256-element `x * 7 + 3` runs with varied inputs, and one deliberately wrong
reference run to exercise failure handling. It also checks that invalid source
and oversized buffers are rejected, the default Metal route is unavailable, and
the invalidated session cannot submit new work. Reports include native compiler,
OS, source/binary hashes, actual output, independently recomputed reference hashes,
event evidence, runtime plan and completion decisions, and failure details.

Lifecycle and injected cleanup errors are covered separately without hardware:

```sh
python3 Tools/run-opencl-runtime-regressions.py --cxx g++ --out build/opencl-regressions --sanitize
```

This test build alone enables `MELLOW_OPENCL_TESTING`, whose constructor injects
a synthetic OpenCL dispatch table. It is absent from normal builds and provides
no production loader override. The fixture simulates operations on the CPU and
reports only software regression results, never GPU evidence.
