# Portable runtime policy implementation

This page describes the policy core. The executable object and compiler paths are
documented in [MetalObjects.md](MetalObjects.md), [OpenCLProvider.md](OpenCLProvider.md),
and [SHADER-JIT-IMPLEMENTATION](../docs/SHADER-JIT-IMPLEMENTATION.md). Their MSL and
raw AIR compute subsets have separate actual Windows GPU evidence; the core's
generic Metal capability gate is not promoted by those subset results.

`PlatformRuntime.hpp/.cpp` implements user-space **policy**, not a GL/CL provider,
Metal ABI bridge, shader compiler, Linux kernel compatibility layer, or device
driver. It has no platform calls, dynamic allocation, exceptions, or RTTI. The
existing `Mellow/Xe*` kernel research code is unchanged and is not called here.

The executable tests use synthetic adapters. A passing test proves policy
behavior; it never establishes physical GPU execution or Metal conformance.

## Provider and workload admission

`ProviderDescriptor` separates physical device identity, provider origin, API,
hardware/software execution, advertised features, and verified features. A
trusted adapter supplies a validation record and reset epoch. The library checks
their consistency; it cannot authenticate the external evidence store.

`planWorkload` accepts up to 8 providers, 8 ordered steps, 16 dependencies and 32
transfer contracts. Providers are considered in caller preference order. The
planner backtracks when an early provider choice would make a later resource
transfer impossible. Search is bounded to at most 8192 candidate attempts, and
callers can choose a smaller budget. Exhaustion returns `SearchLimit`, without
mislabeling the workload as unsupported. Results contain provider IDs and modes;
`Ready` means the route is admissible under the input contracts. It does not mean
the workload was submitted or executed.

Every step requires its individual verified semantics and an ordered queue.
Compute/render additionally require the corresponding translation capability;
merely finding OpenCL or OpenGL does not establish that MSL/AIR can be translated.
OpenGL 4.1 cannot take the core compute route. OpenCL cannot take render steps.
No aggregate `Metal2Supported` or `Metal3Supported` bit exists. Unsupported
argument-buffer, SIMD-group, mesh-shader or ray-tracing requirements are errors.
The version checks delimit the initial provider policy, not every extension
combination allowed by the underlying API specification.

`Step::input` defaults to `MetalSemantics`, preserving these translation gates.
An explicitly selected `OpenClC` input can take only an OpenCL compute route and
requires Compute and OrderedQueue, without implying Metal translation. It cannot
select GL/native/reference providers, render or blit. The native OpenCL adapter
uses this distinction for actual host OpenCL C execution while Metal remains gated.

The caller must enumerate **every resource hazard** as a `Dependency`; this
library does not discover resource aliasing. Same-provider dependencies use that
provider's verified ordered-queue contract. Cross-provider dependencies require
a direction-specific and resource-specific transfer contract for both current
reset epochs. It must cover allocation compatibility, ordering and preservation
of contents. Matching GPU identities and IOSurface handles alone are insufficient.
An explicit copy is considered only when the dependency permits it. A returned
copy plan is still a task for a future provider adapter to execute, not a copy
implementation in this library.

Software GL/CL providers are excluded from hardware plans. CPU reference runs
must explicitly set `PlanOptions::referenceOnly`; this selects only a
`CpuReference` provider and records the reference status. A failure of hardware
selection never activates the reference route.

## Completion correlation

An adapter calls `CompletionTracker::armAfterSubmission` only **after an actual
submission** and supplies its provider/device/epoch/queue/sequence token. The
tracker is confined to one provider, device and queue. It rejects duplicate
sequence numbers, unrelated events, old reset epochs, CPU results on a hardware
route, missing result verification and invalid timestamp ordering. A reset
invalidates pending work; the adapter must rediscover/revalidate provider
capabilities for the new epoch before re-arming. The tracker is not thread safe;
the queue owner serializes calls.

`GpuEvidenceAccepted` describes acceptance of a **trusted adapter observation**.
Neither the validation-record number nor a caller-supplied timestamp proves that
a GPU exists. The adapter is responsible for checking its hardware completion
source, timestamp domain, readback and evidence provenance. End-to-end GPU
acceptance remains a separate hardware test. CPU references finish in
`ReferenceComplete` and cannot become `GpuEvidenceAccepted`.

## JIT cache identity

`JitCacheIdentity` is an exact comparison contract, with no compiler or cache I/O.
It includes the device and target API plus SHA-256 identities for source and
linked inputs, entry points, front end, Mellow lowering, backend compiler, driver,
target environment, options, specialization and resource ABI. Each field is
mandatory. An empty input is represented by its SHA-256 digest, not 32 zero
bytes. Adapters must canonicalize structured inputs and include all codegen
dependencies before hashing them. This contract does not parse AIR/metallib or
claim that a Metal-to-GL/CL translator has been implemented.

## Run

```sh
python3 Tools/run-platform-tests.py --cxx g++ --out build/platform-tests --sanitize
```

Run on a host with a C++17 compiler (for Windows, WSL is suitable). The runner
compiles the production policy source with strict warnings, executes it in a
temporary directory unless `--out` requests retained artifacts. With `--out`, a
JSON report includes compiler version, source hashes and process results,
explicitly classified as software policy evidence. The optional sanitizer mode
requires host support for AddressSanitizer and UndefinedBehaviorSanitizer.
