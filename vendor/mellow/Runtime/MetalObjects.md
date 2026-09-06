# Explicit Mellow compute objects

This is a portable C++17 user-space API in MellowMTL, not Apple's Objective-C
Metal ABI. It does not register a system MTLDevice, implement the Metal framework,
provide a WindowServer driver, or establish macOS/Metal 2/3 compatibility.

Device::createOpenCL creates the existing GPU-only OpenCL provider and runs its
bounded substrate bootstrap. A Library owns source or AIR bytes; translation is
intentionally lazy at Library::newFunction(entry). Unlike Apple's library API,
library construction by itself does not compile or validate the whole source.
newComputePipeline performs actual OpenCL driver compilation and owns the native
program/kernel. Repeated command buffers reuse that compiled pipeline.

The supported frontend contract is one writable uint buffer at binding zero,
one-dimensional exact dispatch, and the checked MSL/AIR subset in
SHADER-JIT-IMPLEMENTATION.md. Unsupported shaders and dispatch shapes fail.
Raw AIR requires an explicitly selected LLVM C API library and actual decoding
and module verification before AIR lowering. A synthetic AIR-shaped fixture
remains synthetic even when LLVM parses it and a physical GPU executes its result.

Buffers own immutable-length host shadows, capped at 4,096 words. Each dispatch
uploads the current shadow to a bounded OpenCL allocation, submits the compiled
kernel, checks event/context/queue identity and profiling, reads back, and checks
queue drain and resource release. This is an explicit copy implementation;
persistent GPU allocations and zero-copy/shared-storage Metal semantics are absent.
Within a command buffer, later encoders observe the previous dispatch's readback.

Commit is synchronous: Executable -> Committed -> Completed/Error.
It does not accept an application-provided expected answer. ExecutionCompleted
records checked driver execution/readback/cleanup, while resultsVerified and
runtimeCompletionAccepted remain false for normal submissions. Independent
tests compare output with arithmetic reference results; the initialization
bootstrap retains its separate oracle-based substrate evidence.

Objects retain their required owners: command buffers retain dispatch pipelines
and buffers, pipelines retain functions/libraries/device, native pipelines retain
their context owner and original loader/functions. Cross-device objects and
pipelines from stale reset epochs are rejected. Destroying an active encoder
without ending encoding marks its command buffer erroneous. Duplicate commits
are rejected.

Command buffers, encoders, and access to their status/execution records require
single-thread use. Buffer reads/writes are locked, and pipeline compilation and
commits serialize per device; this is not a generally concurrent Metal API.
Run native GPU tests in the deadline-limited worker because synchronous vendor
driver calls cannot be safely preempted in-process.

Tools/run-metal-objects.py --compute --out ... builds and tests MSL translation,
native pipeline reuse, independent GPU output, object lifetime, ordering, and
negative API cases. Optional --air-text or --air-bitcode --llvm-library selects
AIR input. Reports pin source, binary, fixture, and decoder library hashes.
The harness deliberately expects the test kernel x = x * 7 + 3; the runtime
itself accepts other supported frontend expressions without this oracle.

The Windows LLVM decoder pins its selected DLL for the process lifetime.
Unload-after-use caused an observed process-exit access violation with the
tested LLVM-C DLL; the ordinary LoadLibrary reference is still balanced.
Use the supervised worker for this explicit dependency and native GPU execution.

Both final Windows tests executed 10,000 submissions with one native pipeline
compilation, independent readback checks and two ordered encoder dispatches:
[MSL GPU evidence](../validation/msl-object-gpu.json) and
[synthetic raw AIR GPU evidence](../validation/air-object-gpu.json).
The latter fixture is synthetic; neither result establishes Apple-produced AIR
compatibility, macOS execution or the system Metal/WindowServer driver ABI.
