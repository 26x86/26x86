# 26x86 VSK implementation

The adopted design is the user-supplied **VF-SPEC-001 v0.1**, dated 2026-09-06.
The public product name is 26x86. `VSK`, `vf_*` and the legacy `venfire` namespace
are retained internally. The reference ZIP mentioned by the document was not
provided; the implementation here is original code, not a copy of that package.

## Current implementation boundary

`sandbox/vsk` begins the spec's **M0 policy/ABI** and the bounded input validation
needed by **M1**. It does not produce a bootable VSK kernel. Existing
`sandbox/efi` artifacts remain executable EFI/JIT diagnostics; their OVMF and
OpenCore handoff results do not establish VMX, EPT, VT-d or service-cell isolation.
They must not be used as the spec's product loader.

The intended runtime is a small VMX-root kernel and static VMX non-root service
cells. ARM interpretation, DBT and software MMU belong in the Execution Cell;
GPU and shader translation belong in their service cells. The existing EFI JIT
will need to move behind that boundary. It is currently executed under EFI
Boot Services and is not isolated as required by VSK.

## Product admission

The v0.1 product policy is fixed **AppleIntelOnly**. There is no config key to
allow a general PC, Hackintosh or outer VM, and no security downgrade when VMX,
EPT, DMA remapping or interrupt remapping is absent. This replaces the earlier
Sandbox product policy that merely declined support for non-Apple machines.
Offline tests may run on development hosts; they never authorize product boot.

SSE4.2 is the ISA baseline. AVX/AVX2 are optional and depend on the intersection
of usable per-CPU features and enabled XSTATE in the migration domain. Mac Pro
2009 remains the requested minimum generation, not a verified hardware profile:
its actual firmware, VT-d/interrupt-remap state, storage and display path remain
unmeasured. SMBIOS text alone is not authentic hardware evidence.

## Implemented interfaces

- `x86/vsk_config.py` parses bounded UTF-8 XML plist and normalizes the VSK policy.
  Duplicate/unknown keys, weakened security settings and unsupported guest
  profiles are rejected. Reports always contain `boot_authorized=false`.
- `sandbox/vsk/include/vf_abi.h` defines the 64-byte message envelope. The policy
  implementation separates envelope shape from root-owned capability/grant
  identity, permissions, lifetime and range checks.
- Block policy binds an exact configured partition identity and uses bounded
  partition-relative requests. It is not a controller driver, physical GPT CRC
  reader or proof of write durability.
- `vf_boot` validates copied EFI memory-map descriptors and acquired handoff
  ranges. Ordered states fail closed where a real signature verifier or
  hardware executor is not implemented. There is no externally supplied
  "verified" boolean that can turn a unit test into boot authorization.
- `vf_dmar` decodes a copied DMAR table, checks checksum and structure bounds,
  records DRHD/RMRR/ATSR/RHSA and device paths, and rejects RMRR/register overlap
  with protected acquired ranges. It never dereferences a reported physical
  address or enables hardware. Unknown structures and extended register sizes
  are unsupported, not silently accepted.

DMAR scope paths still need actual PCI bridge traversal, alias/ACS/reset-group
resolution and active-requester coverage checks. A DMAR interrupt-remapping
flag is only a firmware advertisement; live unit capability/state, default-deny
domains and invalidation completion are separate required implementations.

## Build and use

From the repository root, on a development system with Python 3:

```sh
python -m x86 vsk --config sandbox/vsk/config/example.plist
python -m x86 vsk --config sandbox/vsk/config/golden-gate.template.plist
```

The first command validates an authored conformance configuration. The second
must fail until an exact, separately reviewed guest contract exists; it contains
no invented macOS build or validated graphics adapter.

On Linux or WSL with clang, GNU binutils and sanitizer runtimes:

```sh
python3 sandbox/vsk/build.py
python3 -m unittest x86.test_vsk_config x86.test_vsk_cli x86.test_vsk_build -v
```

The native build emits relocatable freestanding C17 objects, rejects unresolved
runtime dependencies and checks root disassembly for SIMD/FPU registers. It
also executes C tests under AddressSanitizer and UndefinedBehaviorSanitizer.
`sandbox/vsk/build/report.json` records source hashes and **UNIT** results;
it explicitly says that no EFI image or hardware validation was produced.
The Python build-guard tests use fake tools to verify receipt rejection; only
the native build report proves that the C compiler and sanitizer tests ran.

VSK configuration is currently a separate offline contract. The older OpenCore
`AppleSiliconSandbox` / `SandboxSMBIOS` schema and 64-byte EFI LoadOptions are
preserved as the diagnostic transport. The new physical-memory handoff is a
different ABI and must not be cast to that structure. Connecting the validated
VSK config to a signed bundle and an actual post-EBS kernel remains M1 work.

## Remaining release requirements

Pinned trust keys and a real signed-bundle verifier, EFI allocation/snapshot and
ExitBootServices, GDT/IDT/APIC/SMP/XSTATE, VMXON/VMCS/EPT, VT-d/IRQ remapping and
native storage/display drivers are not implemented here. Then M2 requires a
reference interpreter and differential DBT tests for privileged ARM execution,
MMU, exceptions, atomics and timers. Apple guests retain the requested AIC/iBoot
contract; GIC research is not substitute evidence.

The GPU path requires an actual backend plus an exact guest graphics adapter.
Neither SGPU envelopes nor an abstraction receipt establish Metal support.
The original-image constraint still applies: this design does not authorize
altering macOS images, signatures or personalization. If a proposed graphics
adapter needs guest modifications, that conflicts with the Sandbox constraint
and cannot be considered the accepted boot path. Native root patching remains
a separately selected feature.

M0 passes cannot satisfy M1-M5. Hardware isolation, a physical Mac boot,
original iBoot execution and macOS 26/27 plus Metal are separate acceptance
results, all currently unverified. The proposed 30% SSE overhead and root
memory budgets remain unmeasured targets.
