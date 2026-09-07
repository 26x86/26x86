# Venfire Sandbox EFI — EFI-integrated micro-preOS and M1 reference contract

## Scope and evidence boundary

Venfire's preOS is an **EFI-integrated micro-runtime**, not a second operating
system or another boot stage. The unit under test is one x86-64 PE/COFF EFI
application:

```text
x86-64 UEFI firmware (or x86-64 QEMU + OVMF)
  -> Venfire EFI package
       -> existing C EFI entry and firmware preparation
       -> statically linked Rust micro-preOS
       -> C-owned AArch64 diagnostic-JIT wrapper or Rust architectural core
       -> bounded AArch64 guest and native M1 reference graph
       -> C EFI cleanup and EFI_STATUS return
```

The host is an **x86-64 EFI/OVMF environment**. The guest is a deliberately
small AArch64 diagnostic payload executed by the repository's AArch64 subset
JIT. QEMU/OVMF is a development and validation fixture for that EFI
application; it is not a Venfire runtime dependency and no QEMU executable is
started by the EFI image.

The current implementation does **not** claim any of the following:

- physical Apple M1/t8103 compatibility or hardware validation;
- a physical Apple M1/T8103 register map, Apple virtual-Mac ABI, signed device
  tree, or Apple firmware trust-chain contract;
- iBoot execution, an iBoot-to-XNU handoff, XNU execution, macOS boot, macOS
  installation, storage, display, or recovery success; or
- `ExitBootServices` ownership, a bare-metal kernel, or a general-purpose VM
  monitor.

`VF_MACHINE_PROFILE_M1_DIAGNOSTIC` (`M1_DIAGNOSTIC`) remains a fail-closed
machine-policy seed. The Rust path now constructs a fixed, M1-only semantic
reference graph (T8103 identity, eight logical CPUs, timer/AIC, DART-style
bounded DMA, storage/recovery/display contracts, and handoff metadata), but
that graph is not evidence of physical Apple register compatibility. A passed
build, unit test, OVMF boot, or QEMU VMApple run remains evidence only for the
named layer in the validation matrix below.

## One package, not a boot chain

The deployable production artifact is one EFI application, normally placed at
the removable-media fallback path:

```text
EFI/BOOT/BOOTX64.EFI
```

When OpenCore owns the preceding boot-picker step, the same application can be
loaded as:

```text
EFI/26x86/Sandbox.efi
```

The Rust crate is built as a `staticlib` and linked into that existing PE/COFF
image. A build-time archive is an input to the linker, not another deployable
program. Rust, C, and any future read-only resources are modules of the same
Venfire EFI package.

The EFI package must not stage or boot any of the following:

- a separate Rust `.efi` image, executable, kernel image, or ELF payload;
- a stage-2 EFI loader or another boot protocol;
- an initramfs, Linux root filesystem, service manager, shell, VFS, or package
  manager;
- a QEMU system-emulator process, generic VM-monitor host environment, or a
  reimplemented general-purpose boot manager.

A companion resource is allowed only when Venfire directly owns and validates
it. Examples are a bounded diagnostic AArch64 guest, a minimal configuration
resource, a signed machine profile, or a future read-only firmware-input
manifest. No Apple binary is a Phase-1 guest input.

`build/BOOTX64.EFI` is the production artifact. `build/TESTX64.EFI` may add
test-console and QEMU-exit instrumentation, but is never the production image.
The repository build report and OVMF report are the authoritative evidence for
the artifacts and tests actually run.

`python3 sandbox/efi/build.py` also runs the host-only `abi_layout.c` receipt
and the Rust `#[repr(C)]` receipt with `--nocapture`, then refuses to link the
EFI image if any size, alignment, or offset differs.  It separately executes
the first-party AIC v1 model test that is linked into the EFI self-test.  Those
executables remain build-time verifiers and are not companion deployment
images; the AIC result is a device-model unit result, not M1 hardware or
device-tree evidence.

## Layer ownership

The ownership boundary is intentionally narrow. It prevents a Rust runtime
from accidentally becoming another UEFI application or a hidden kernel.

| Layer | Owner in Phase 1 | Owns | Explicitly does not own |
| --- | --- | --- | --- |
| **A — UEFI firmware / EFI application** | Existing C EFI entry | EFI entry ABI; protocol lookup; Boot Services page allocation/free; W^X transitions and verification; EFI image lifetime; console/trace emission; final `EFI_STATUS` | Rust does not take `EFI_SYSTEM_TABLE`, arbitrary protocol pointers, or Boot Services ownership. |
| **B — micro-preOS runtime** | Rust `no_std` static library | Context/ABI validation; machine-policy selection; bounded-execution policy; machine seed validation; JIT-request validation; result/error normalization | No process model, scheduler, VFS, shell, userspace ABI, driver manager, package manager, async runtime, generic allocator, or firmware lifecycle. |
| **C — AArch64 guest execution** | C `vf_cpu`/exception boundary plus Rust reference core and JIT wrapper | Explicit x0..x30/SP/PC/PSTATE/EL state; EL-indexed exception banks; system-register bank; 4 KiB/16 KiB TTBR0/TTBR1 walk; bounded TLB; distinct fault status/ESR; timer/counter and interrupt decision; atomics/exclusive monitor; code buffer; guest RAM; W^X callback; instruction budget | No complete privileged instruction set, full vector-handler continuation, PAuth execution, SMP scheduler, or physical Apple CPU semantics. The C host-code fast path still rejects system instructions; feature-requested runs use the Rust reference core. |
| **D — native machine / device model** | Rust `M1MachineGraph` plus VMApple reference descriptor | M1-only T8103 semantic identity; fixed CPU topology; RAM/MMIO contracts; AIC/timer routing; bounded DART DMA; caller-owned storage; recovery envelope; XRGB framebuffer; reset and handoff metadata; graph-local guest MMIO | No Apple physical register map, signed iBoot acceptance, ANS/DART hardware equivalence, or WindowServer/Metal proof. VMApple/GIC windows remain a separate QEMU reference graph. |

The Phase-1 normal path remains inside the EFI application interval. It does
not call `ExitBootServices`. Therefore C retains responsibility for all
firmware-owned allocations and returns control to firmware after cleanup. A
post-`ExitBootServices` runtime, if ever needed, is a separate transition
milestone with a new allocation, return-path, and protocol-ownership review.

The current Rust call seeds one fixed RAM region, keeps a bounded static MMIO
registry, constructs and resets the M1 semantic graph, and re-validates the
execution result before normalization. Its architectural reference core
performs decode -> architectural state update -> translation -> bus access ->
commit, with 4 KiB/16 KiB TTBR0/TTBR1 walks, AF/AP/PXN/UXN checks, ASID-tagged
TLB invalidation, EL-indexed system registers, normalized ESR/FAR/ELR, timer
and external-interrupt entry, and bounded exclusive atomics. The C JIT remains
the fast path for the original diagnostic guest; it records the same
architectural fault classes but does not pretend that a trapped system
instruction executed successfully. A feature-requested call goes through the
Rust reference core and the same M1 bus, including logical MMIO dispatch.

The bounded VMApple descriptor is also constructed and reset on that call,
with a `VF: VMAPPLE_GRAPH_READY` trace marker. It records QEMU VMApple/TCG
guest-visible windows for cross-checking, not native M1 hardware. AES/PCIe
semantics, Apple physical AIC/DART maps, signed firmware acceptance, and
guest-wide macOS graphics remain unverified.

## Stable C/Rust boundary

The public call boundary is deliberately limited to these C ABI entry points:

```c
int vf_preos_run(const VF_PREOS_CONTEXT *context, VF_PREOS_RESULT *result);

int vf_preos_jit_execute(const VF_JIT_REQUEST *request,
                         VF_JIT_RESULT *result);
```

The first call enters the statically linked Rust micro-preOS. The second is a
C wrapper invoked by Rust; it owns the existing JIT's internal structures and
calls `vf_run(...)` on Rust's behalf. The C EFI entry is the sole creator and
final consumer of the context/result chain:

```text
C EFI entry
  -> C-validated VF_PREOS_CONTEXT
  -> vf_preos_run(context, preos_result)              [Rust]
  -> vf_preos_jit_execute(jit_request, jit_result)    [C wrapper]
  -> existing vf_run(...)                             [existing C JIT]
  -> Rust normalizes VF_PREOS_RESULT
  -> C cleans pages and maps the result to EFI_STATUS
```

`sandbox/efi/preos_abi.h` is the C-side source of truth for that boundary. Its
Rust counterpart must use `#[repr(C)]` for every shared structure; no Rust
layout, enum representation, or pointer-width assumption may be implicit.
`VF_PREOS_ABI` is the platform-compatible C ABI: the EFI COFF target uses the
Microsoft x64 ABI, while the native host-only ABI test uses its native C ABI.
Both sides must reject, before dereferencing caller data:

- an unsupported `abi_version` or invalid `struct_size`;
- non-zero reserved/unused fields;
- an invalid machine profile or execution budget;
- a null pointer when a non-zero byte length is required, or an invalid
  pointer/length pair for an optional empty span;
- integer overflow in size, address, range-end, or alignment calculations; and
- misaligned pointers, unbounded spans, or result buffers too small for the
  selected ABI version.

### Context, lifetime, and ownership

`VF_PREOS_CONTEXT` carries only C-validated, bounded data: ABI/version fields,
the `VF_MACHINE_PROFILE_M1_DIAGNOSTIC` policy seed, an instruction budget, a
guest-byte pointer/length pair, a guest-RAM pointer/length pair, an opaque
C-owned execution handle, a C-owned trace callback/opaque value, and optional
golden-result expectations. It must not expose an `EFI_SYSTEM_TABLE`, raw UEFI
protocol pointer, unbounded allocation, or the JIT's private CPU/code-buffer
layout.

`VF_JIT_REQUEST` is the even smaller request assembled by Rust after policy
validation. `VF_JIT_RESULT` reports only the information Rust needs to
normalize the guest outcome: status, termination reason, retired-instruction
count, guest PC, faulting instruction where applicable, and x0/x1/x3 result
registers. `VF_PREOS_RESULT` is the Rust-to-C normalized final result, which C
initializes as ABI v1 and all-zero before the call.

Both sides close the terminal-result enum: `VF_NEXT` is an internal JIT
continuation value and cannot cross the wrapper, while every terminal status
must match its corresponding termination reason. Rust additionally rejects an
over-budget result and an invalid successful halt PC before emitting
`VF: GUEST_HALT`.

All pointer-backed memory is caller-owned C memory. It remains valid only for
the synchronous duration of the call that receives it, is not retained by Rust,
and is released only by the C EFI owner after the entire call chain returns.
Guest bytes are read-only to the runtime; guest RAM is mutable only through the
validated JIT request. The opaque handle is never decoded, freed, or retained
by Rust. The trace endpoint is also C-owned: Rust passes only immutable static,
NUL-terminated messages through it and never observes a firmware pointer.
These rules also apply on every failure path.

Expected, non-panic failures use explicit, bounded return codes. The status
taxonomy includes success plus distinguishable ABI, context, profile,
guest-input, machine-initialization, JIT, budget, protection, and internal
failure classes (for example `VF_PREOS_E_ABI`, `VF_PREOS_E_CONTEXT`,
`VF_PREOS_E_PROFILE`, `VF_PREOS_E_GUEST_INPUT`, `VF_PREOS_E_MACHINE_INIT`,
`VF_PREOS_E_JIT`, `VF_PREOS_E_BUDGET`, `VF_PREOS_E_PROTECTION`,
`VF_PREOS_E_INTERNAL`, and `VF_PREOS_E_RESULT`). A budget exhaustion, unsupported instruction,
fetch/data fault, or failed W^X transition must not be normalized into success.
C maps the normalized result to its final `EFI_STATUS` only after cleanup.

## Rust static-library rules

The micro-runtime is intentionally constrained:

```text
crate type: staticlib
language surface: no_std
panic policy: abort
unwinding across the C/EFI boundary: forbidden
allocator: not introduced
runtime dynamic allocation: forbidden
Rust EFI/PE executable: forbidden
```

All normal error handling returns through the ABI; a Rust panic must never cross
into C or UEFI. The initial design must use stack storage or caller-owned fixed
buffers. Before any allocation is introduced, the implementation must document
why those options cannot work, the maximum allocation, lifetime, failure
behaviour, EFI memory owner, and cleanup owner. Until then the expected Rust
dynamic-allocation count and byte total are both zero.

## Diagnostic guest contract

The initial guest is a short, Venfire-owned AArch64 diagnostic payload, not an
operating system or Apple boot component. The ABI bounds it to 4..65,536 bytes,
four-byte instruction alignment, one fixed 65,536-byte guest-RAM span, and an
execution budget of 1..100,000 retired instructions. It uses only instructions
already supported by the existing JIT and proves all of the following in one
bounded run:

- an arithmetic result;
- a guest-RAM write followed by a read;
- a checked retired-instruction count;
- an explicit diagnostic halt convention; and
- the Rust -> C wrapper -> JIT -> Rust result-return chain.

At least two negative runs are required: an undefined AArch64 instruction and
instruction-budget exhaustion (for example, a bounded loop). The CPU boundary
also keeps privilege, system-register, instruction-abort, data-abort, and
alignment failures distinct. These failures retain their actual termination
reason and never become `GUEST_HALT`.

The normal trace has distinct evidence markers equivalent to:

```text
VF: EFI_ENTRY
VF: EFI_MEMORY_READY
VF: PREOS_CONTEXT_READY
VF: RUST_ENTER
VF: RUST_POLICY_OK
VF: MACHINE_RESET
VF: AARCH64_STATE_READY
VF: VMAPPLE_GRAPH_READY
VF: MACHINE_READY
VF: JIT_ENTER
VF: GUEST_HALT
VF: RUST_RETURN_OK
VF: EFI_RETURN_OK
```

Failure output must instead preserve its layer and reason, such as
`VF: GUEST_STOP reason=UNDEFINED_INSTRUCTION`, `PRIVILEGE_FAULT`,
`SYSTEM_REGISTER_TRAP`, `INSTRUCTION_ABORT`, `DATA_ABORT`,
`ALIGNMENT_FAULT`, or `BUDGET_EXHAUSTED`, followed by
`VF: PREOS_FAIL code=...` and an EFI error return. Exact text can change, but
the stage boundaries and failure/success distinction cannot.

## Required validation matrix

Run the repository-defined build and OVMF verifier (currently
`python3 sandbox/efi/build.py` and `python3 sandbox/efi/verify_ovmf.py`) only
as evidence for the checks they actually perform. The Phase-1 acceptance matrix
is:

| Check | Required evidence | Layer proved | Does **not** prove |
| --- | --- | --- | --- |
| Build verification | One PE/COFF EFI image links the Rust `staticlib`; artifact hashes/sizes are recorded | build/package | EFI runtime behaviour or Apple compatibility |
| Static ABI verification | C/Rust size, offset, alignment, version, reserved-field, null/span, and overflow negatives pass | C/Rust boundary | JIT execution |
| Existing C JIT regression | Current unit tests preserve supported operations, faults, W^X, and host-code ABI behaviour | JIT | Rust integration |
| AArch64 state/exception unit | EL/PSTATE/SP-bank validity, exception classification, ESR/FAR/ELR recording, raw fault-instruction retention, and explicit vector-take state transition pass | guest architectural decision boundary | complete handler continuation or physical hardware |
| System-register bank | EL1/EL2/EL3 bank, CurrentEL/ID registers, physical/virtual timer registers, privilege and read-only rules pass in the Rust reference core and C bank receipt | guest architectural state | complete system-register coverage or Apple implementation-defined registers |
| MMU/TLB reference | 4 KiB and 16 KiB TTBR0/TTBR1 walks, dynamic start levels, block/page descriptors, AF/AP/PXN/UXN faults, ASID-tagged invalidation pass | guest memory-translation boundary | host page tables, full ARM MMU, or Apple DART |
| Timer/interrupt reference | 24 MHz counter/timer state, IRQ mask/vector entry, M1 AIC source routing, and bounded external IRQ propagation pass | guest interrupt boundary | real-time scheduling, SMP execution, or Apple AIC equivalence |
| M1 semantic graph | T8103-only graph reset/activation, logical MMIO, bounded DART/storage/recovery/display/handoff contracts pass | native machine contract | physical register map, signed firmware, or macOS boot |
| EFI attribute W^X predicate | The protocol-path RO/XP predicate rejects RWX and NX-executable combinations | UEFI memory-protection policy | firmware protocol implementation or hardware page tables |
| Rust unit tests | Policy, context, request, and result normalization test success and explicit failures | Rust micro-preOS | firmware interaction |
| C/Rust ABI integration | A C-built context reaches Rust, Rust uses the C wrapper, and C receives a normalized result | boundary integration | OVMF firmware execution |
| OVMF normal guest | x86-64 OVMF log contains EFI entry, Rust entry, machine-ready, JIT, halt, return, cleanup | EFI + Rust + JIT diagnostic path | M1, iBoot, XNU, macOS, storage, or display |
| Invalid-instruction guest | Actual undefined-instruction reason returns as failure | guest/JIT error path | guest OS exception support |
| Budget-exhaustion guest | Actual exhausted-budget reason returns as failure | bounded-execution policy | scheduler/timer semantics |
| Size/allocation measurement | Required metrics below are emitted or marked `unknown`/`not measured` | footprint accounting | any unmeasured value |

The OVMF verifier uses an x86-64 virtual firmware host. It must not label an
OVMF screen or an EFI return as AArch64 hardware, physical M1, iBoot, XNU, or
macOS evidence. Reports should present each result explicitly as:

```text
firmware / EFI layer:       passed | failed
Rust preOS layer:           passed | failed
JIT execution layer:        passed | failed
native machine layer:       not implemented | partial | passed
Apple boot-chain layer:     not attempted | blocked | runtime-tested
macOS layer:                not attempted | blocked | runtime-tested
```

The CPU, MMU, timer, and M1 rows can now be passing for their bounded
reference contracts. They remain scoped semantic tests, not claims of physical
M1 or macOS compatibility. Apple boot-chain and userspace rows require an
independent signed-firmware/storage run.

## Footprint and allocation metrics

Every relevant build record must contain measured values, rather than estimates:

| Metric | Required recording rule | Phase-1 expected value where defined |
| --- | --- | --- |
| Baseline EFI image size | bytes before Rust linkage | measured baseline |
| EFI image size after linkage | bytes in the linked production EFI | measured |
| EFI growth | after-link bytes minus baseline bytes | measured |
| Rust `staticlib` size | linker input archive byte size | measured |
| Separate companion executable count | staged deployable executables other than the EFI package | `0` |
| Separate kernel-image count | staged kernel/ELF/initramfs images | `0` |
| Fixed Rust stack requirement | record only if toolchain analysis provides it | `unknown` / `not measured` otherwise |
| Fixed guest RAM size | exact byte value supplied to the diagnostic run | measured |
| JIT code-buffer size | exact byte capacity supplied to the JIT | measured |
| Rust dynamic-allocation count / bytes | allocations after runtime entry | `0` / `0` |
| Boot Services allocation count / bytes | EFI page allocations made for the run | measured; not assumed zero |
| Host OS dependency | dependency needed by the deployed EFI runtime | `0` |
| External QEMU-process dependency | process needed by the deployed EFI runtime | `0` |

`unknown` and `not measured` are valid values when a tool cannot establish a
metric. They are not interchangeable with zero and must not be silently
replaced by estimates.

## Native M1 work: semantic core present, physical source port outstanding

The Rust `M1MachineGraph` is the first bounded implementation of an explicitly
M1-only target contract. It joins CPU topology, logical memory/MMIO, interrupt
and timer contracts, caller-owned storage, recovery transport, XRGB framebuffer,
DART-style DMA policy, reset, and handoff metadata. It fails closed for an
invalid T8103 identity and does not accept a generic QEMU `virt`, iPhone T8030,
or an Apple name string as a substitute. Its `board_id` and signature flags
remain unset because no physical board identity or Apple trust-chain verifier
has been supplied.

The remaining source-port work is to replace these logical semantics with
verified Apple register maps and boot-visible behavior, then connect storage,
recovery, display, and firmware inputs to an actual iBoot/XNU run. Until that
runtime evidence exists, this graph is a native Venfire contract, not an M1
hardware emulator.

QEMU and other public source trees may be used as target-specific behaviour
references or, where provenance and licensing permit, as source-port inputs.
They are not a runtime dependency. In particular, qemu-t8030 can be a
device-semantics reference, but its iPhone/iOS machine and firmware contract
must never be treated as an M1/macOS contract. A GIC model is not evidence of
an Apple Interrupt Controller implementation.

The future registry is [M1_SOURCE_PORT_MANIFEST.md](M1_SOURCE_PORT_MANIFEST.md).
It currently records a **future-only schema and no completed M1 source port**.
Every device or machine behaviour later considered for the M1 graph must have a
manifest entry before it is claimed as native, adapted, or behaviour-preserving.
The entry must distinguish confirmed evidence from inference, references, and
unavailable behaviour.

## Sources and license

The existing subset emitter is repository-owned, specification-based code. A
future direct port must retain its upstream file provenance, exact revision, and
license obligations; an adapted port and a clean-room reimplementation must be
described honestly and independently tested against their cited behaviour. Do
not call directly imported source clean-room, and do not call an unverified
independent implementation behaviour-equivalent.

- [UEFI 2.11 memory protection protocol](https://uefi.org/specs/UEFI/2.11/37_Secure_Technologies.html#memory-protection)
- [PI 1.9 CPU architectural protocol](https://uefi.org/specs/PI/1.9/V2_DXE_Architectural_Protocols.html)
- [Arm A-profile Architecture reference manuals](https://developer.arm.com/documentation/ddi0487/latest/)
- [Intel software developer manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
