# NextCore Build Plan (Build Plan Slot)

## Responsibility

This specification defines the *how* of NextCore — Rust workspace module layouts, phased implementation sequences, validation gates, dependencies, and build artifacts. The *what* and *why* are governed by the Design specification.

## Current Status

The active milestone is BP37: physical x86 macOS 27 display and interaction before
acceleration. Normal ARM64e entry is still `NOT_READY`; incomplete-prefix traces
are bounded diagnostics returning `ABORTED`. The seven-module integration has
native/reference/provider/UEFI coverage, not a verified physical OS desktop.

The 2026-09-12 published checkpoint `8f562` passed 31 CI checks. That is a dated
source/integration receipt, not OS-boot evidence. The pre-BFM original diagnostic
stopped after 5,373 retired instructions at BFI; it is historical prefix evidence,
not a physical run. BFM authored EFI consumption passed. The subsequent same-j274 r8 replay
retired 16,384 instructions to its budget (status 5), with 16,384 fetches, 2,763
data requests and provider status 0. No unsupported instruction stopped that
prefix; loop/progress analysis is pending. This is not OS-progress evidence. [Progress](progress.md) owns the latest result so this
historical boundary is never mistaken for the current stop.

Persistent guest display/storage and target-specific platform services remain
open. Use [the entry contract](NEXTCORE_ARM64E_ENTRY_CONTRACT.md) and
[compatibility](compatibility.md) to distinguish ABI preparation from acceptance.

## Historical baseline: 2026-09-07

- **Workspace Architecture (2026-09-07):** The physical Cargo workspace comprises seven crates: `core`, `efi`, `tool`, `ise`, `gpu`, `hal`, and `apls`. All 103 host unit tests pass cleanly. Dummy implementations (`NXC0`) have been replaced with authentic EFI image verification. NextCore EFI reads volume configuration files under strict buffer bounds and emits diagnostics via serial I/O.
- The APLS host adapter and CLI orchestrate execution across WSL, QEMU, and ARM firmware fixtures. Execution contracts BP8–BP9 are actively enforced.
- Core standard library dependencies have been separated into modular `no_std` XML and configuration parsers linked into the EFI target. NextCore implements chainloading of explicit EFI applications residing on the same volume; direct XNU kernel handoff remains under active development.
- NextCore EFI standardizes on `uefi 0.40` allocators and helpers, eliminating legacy `uefi-services` wrappers.
- All implementation gates (BP1 through BP25) are codified with verifiable automated tests.

## Target State

- Codified Rust workspace and crate hierarchy.
- Phased implementation sequence paired with strict verification gates at every step.
- Comprehensive dependency declarations for UEFI, plist formats, ACPI tables, and kext registries.
- Deterministic build artifacts (EFI binaries, directory trees, verification hashes).

---

## Codified Decisions

### BP1. Rust Module Structure

The tree below records the initial design decomposition, not the current exhaustive file inventory. The actual seven gitlinks and workspace packages are documented in [Module repositories](wiki/Nextcore-Modules.md).

```
nextcore/
├── Cargo.toml                 # Workspace root
├── crates/
│   ├── nextcore-efi/          # UEFI application binary (no_std, target x86_64-unknown-uefi)
│   │   └── src/
│   │       ├── main.rs        # UEFI entry point: pub fn efi_main(image: Handle, st: *mut SystemTable) -> Status
│   │       ├── boot.rs        # Boot Services abstractions: locate_handle, alloc_pages, open_protocol
│   │       ├── runtime.rs     # Runtime Services abstractions: set_variable, get_variable, reset
│   │       └── console.rs     # UEFI console wrappers (ConOut): write_str, write_fmt
│   ├── nextcore-core/         # Platform-neutral core logic (no_std, alloc)
│   │   └── src/
│   │       ├── config.rs      # config.plist parser and serializer: Config::load, Config::dump
│   │       ├── acpi.rs        # ACPI table parser: AcpiTables::find
│   │       ├── kext.rs        # Declarative kext registry and scanner
│   │       ├── device_props.rs # DeviceProperties configuration injection
│   │       ├── handoff.rs     # macOS handoff structures based on public specifications
│   │       └── error.rs       # CoreError enumerations (Parse, NotFound, Io, Unsupported)
│   └── nextcore-tool/         # Operator CLI utilities (std)
│       └── src/
│           ├── main.rs        # EFI build orchestration CLI
│           └── install.rs     # Boot media assembler
└── tests/
    ├── config_parse.rs
    ├── acpi_parse.rs
    └── handoff_roundtrip.rs
```

Architectural Rationale: Maps directly to Design steps 1–4. UEFI-specific bindings are isolated to `nextcore-efi`. All policy, parsing, and data models reside in `nextcore-core` to enable automated host testing. Operator tools reside in `nextcore-tool` to avoid contaminating bare-metal UEFI builds.

### BP2. Dependencies

This original dependency plan is historical. Current manifests, lockfiles and immutable module revisions determine the actual dependency graph; this table must not be used to install or pin a replacement graph.

| Crate | Dependency | Role & Scope |
|-------|------------|--------------|
| `nextcore-efi` | `uefi` (v0.40) | Standard UEFI system table and protocol bindings |
| `nextcore-efi` | `log` | Diagnostic logging facade |
| `nextcore-efi` | `embedded-alloc` | Heap allocator configured over UEFI memory pools |
| `nextcore-core` | `plist` | Property list parsing and serialization |
| `nextcore-core` | `serde`, `serde_plist` | Strongly-typed configuration deserialization |
| `nextcore-core` | `goblin` | Mach-O binary parsing and kernelcache validation |
| `nextcore-core` | `aml` | ACPI Machine Language bytecode parsing |
| `nextcore-tool` | `clap` (v4) | Command-line argument parsing |
| `nextcore-tool` | `anyhow`, `thiserror` | Robust error propagation in CLI utilities |

### BP3. Phased Implementation Roadmap

- **Step 1: Workspace & Core Structure:** Establish root Cargo workspace and minimal compiling crates.
- **Step 2: Declarative Configuration Parser:** Implement `config.plist` parsing with schema roundtrip validation in `nextcore-core`.
- **Step 3: UEFI Entry & System Table Discovery:** Implement `nextcore-efi` entry point and protocol handle acquisition.
- **Step 4: ACPI Table Discovery & Injection:** Parse RSDP/XSDT and inject configured ACPI overrides.
- **Step 5: DeviceProperties & NVRAM Injection:** Apply device property overrides to target PCI paths.
- **Step 6: Kext Cataloging & Dependency Resolution:** Scan and validate kext bundles declared in configuration.
- **Step 7: Physical Memory Map Acquisition:** Snapshot firmware descriptor tables immediately prior to handoff.
- **Step 8: Clean-Room Handoff Structures:** Construct boot argument and DeviceTree buffers conforming to target ABIs.
- **Step 9: Kernel Handoff / Child Invocation:** Execute designated EFI boot targets or transition to XNU.

### BP4. Build Deliverables

- `nextcore.efi` / `BOOTX64.EFI`: Production UEFI application binary compiled for `x86_64-unknown-uefi`.
- Standardized directory layout: `EFI/BOOT/BOOTX64.EFI` and `EFI/OC/config.plist`.
- CLI executable: `nextcore-tool` binary compiled for host environments.

### BP5. Intentional Non-Dependencies

- Zero dependency on C codebases, proprietary toolchains, or private firmware symbols.
- Zero dependency on external binary blobs, decryption keys, or pre-extracted Apple frameworks.

### BP6. Answers to Inter-Slot Open Questions

- All crate boundaries map 1:1 with Design requirements.
- Knowledge transfer adheres strictly to high-level functional specifications.

### BP7. Integration Codification (F)

Consolidates verified handoff ceilings, open reference standards, and clean-room implementation agreements.

### BP8. 2026-09-07 Execution Contracts

Codifies verification requirements across `nextcore-apls`, QEMU emulation targets, and bare-metal UEFI environments.

### BP9. Continuous Execution: EFI Handoff & Failure Isolation

Separates child EFI application execution from direct XNU kernel handoff, verifying error exit codes and diagnostic output across each boundary.

### BP10. Authentic AVP Entry Observation on macOS 27

Empirical observation of AVPBooter startup routines under bounded research harnesses.

### BP11. Standalone Kernel Image Loading & EFI Handoff

Preparation of kernelcache segments and verification of memory lifetimes prior to entering XNU.

### BP12. Authentic Recovery Path Observation

Verification of DFU state transitions and recovery USB descriptors using authentic recovery fixtures.

### BP13. Optional RPC Access Comparison in Recovery

Analysis of optional RPC boundaries within authentic iBEC execution flows.

### BP14. DataAbort VA & PA Identification at Host Boundaries

Mapping memory abort exceptions across host transaction layers during AArch64 emulation.

### BP15. NextCore APLS Adapter Integration

Unification of APLS execution adapters across host and target architectures.

### BP16. Open Contracts for Unmapped MMIO Nodes Post-bootx

Specification of peripheral MMIO apertures and memory controller handoff rules.

### BP17. Host Execution Qualification

Automated pre-flight checks validating CPU features, virtualization extensions, and toolchain readiness.

### BP18. Module Repository Distribution

Packaging and release automation for independent NextCore module repositories (`Nextcore-Core`, `Nextcore-EFI`, `Nextcore-Tool`, `Nextcore-APLS`, `Nextcore-GPU`, `Nextcore-HAL`, `Nextcore-ISE`).

### BP19. OVMF ACPI/PCI Harvesting & HAL Parser Linking

Connecting live OVMF ACPI and PCI topology tables directly to `nextcore-hal` parsers.

### BP20. macOS Boot Inputs & Accelerated Execution

Procedures for verifying bootloader handoff and graphics acceleration pipelines.

### BP20-A — Preserving Error States from EFI Loaders
Capturing diagnostic exit codes and debug logs from child loaders.

### BP20-B — NextCore Host GPU Compute Verification
Executing compute kernels and measuring latency on host graphics backends.

### BP20-C — Tahoe BootKC Format Pre-flight
Verifying Mach-O segment headers and signature boundaries in macOS 26 Tahoe kernelcaches.

### BP20-D — Native KC Memory Placement & Readback
Allocating contiguous physical memory pages for kernelcache segments and validating memory readback.

### BP20-E — Read-Only Verification of Classic/Chained Relocations
Parsing and verifying relocation fixups without mutating source images.

### BP20-F — Physical EFI Page Ownership for Native Kernelcache
Securing physical memory allocation and establishing page permissions.

### BP20-G — Boot Arguments Revision 1 Codec
Serializing boot argument structures matching target XNU ABI revisions.

### BP20-H — Applying Classic Relocations to Kernel Proper
Executing in-memory fixups for kernel base addresses.

### BP20-I — Guest Userspace Metal Execution Probe
Probing userspace Metal framework initialization in test guests.

### BP20-J — Verified EFI ConsoleControl Provider Connection
Connecting standard ConsoleControl protocols to preserve graphical displays across boot phases.

### BP21 — NextCore Branding & Native Graphical EFI Picker
Implementation of the dark-themed, tile-based graphical boot picker within UEFI Boot Services.

### BP22 — macOS 27 Bidirectional HAL & Metal Requirements
Defining hardware translation layers between x86 host hardware and macOS 27 Apple Silicon drivers.

### BP22-A — Golden Gate ARM64 Guest Metal Verification Fixture
Standalone test fixture validating Metal device enumeration in guest environments.

### BP22-B — Memory Mapping at ARM Firmware Fault Milestones
Inspecting page table structures at points of guest firmware exception faults.

### BP22-C — Standalone ARM64 XNU Boot Arguments Codec
Independent serializer generating AArch64 boot parameter blocks.

### BP22-D — ARM64 Kernelcache Metadata & Host Staging
Validating immutable staging of ARM64 kernel collections.

### BP23 — Synchronizing Verified Progress
Procedures for pushing verified milestones to remote git repositories.

### BP24 — APFS Jumpstart & Filesystem Driver Integration
Mounting APFS container volumes via embedded jumpstart drivers during early boot.

### BP24-B — Observing Driver-Published APFS Filesystems
Enumerating APFS volumes published to the UEFI protocol database.

### BP24-C — Executing Selected Boot Targets on APFS Volumes
Launching target bootloader binaries residing on designated APFS volumes.

### BP25 — WSL2 ARM64e Boot & Submodule Integration (2026-09-08)
Integrating submodules and build harnesses within development environments.

### BP25-A — Target Architecture: x86 EFI macOS-Specific JIT Compatibility Layer
Directing execution toward bare-metal x86 EFI environments running translation shims.

## OPEN_QUESTION
All engineering questions are actively tracked and resolved through standardized escalation protocols.

## Resolution Notes
- Documentation policy mandates **English Only** across all user messages, test assertions, and specifications.

## Integration Verification (F)
Summary of closed architectural reviews and verified crate boundaries.


## BP25-B — macOS 27 startup ABI and bounded original-input trace

Current: independently authored ARM64e fixtures execute in x86 EFI. The original
M1-baseline kernel collection stages unchanged, but its startup contract must be
established separately. Public XNU `osfmk/arm64/sptm/start_sptm.s` documents a cold
startup selector in x0, traditional boot arguments in x1, and SPTM arguments in
x2. A legacy x0=boot-arguments handoff cannot be assumed for this entry shape.

Decision: the EFI agent owns explicit diagnostic initial-register selection and
bounded original-input tracing. The CPU agent owns generic ARM immediate
arithmetic/condition flags and conditional control flow needed at the observed
first instruction boundary, with independently authored tests. This delegation
reopens those source scopes while module metadata/integration remains root-owned.
Unknown SPTM argument structures and services must not be fabricated or reported
as implemented. Any partial trace must state missing startup prerequisites and
must not be treated as correct macOS cold boot. Raw original instructions and
addresses stay in `_isolated/`; public receipts contain only outcomes and limits.

Reference: https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/arm64/sptm/start_sptm.s

Wanted: establish and test the selected startup ABI, virtual-address translation,
MMU and SPTM interface before advancing to sustained XNU initialization. Synthetic
success and partial original instruction execution remain distinct milestones.


## BP26 — continue original startup and runtime integration

Current: the original macOS 27 prefix retires four instructions in x86 EFI,
then stops at a standard thread-pointer system register. Submodules are locally
committed and independently linked; remote publication remains a separate pending
action. Continued implementation does not depend on publication.

Decision and delegation: the CPU agent owns ISE thread/context system registers,
architectural state and their native/reference ABI consistency, with public ISA
semantics and independently authored tests. The EFI/Core agent owns reproducible
original-prefix tracing and explicit boot prerequisites; it may add a separate
bounded firmware DeviceTree-template parser, preserving the strict runtime parser
and unresolved template state. Unknown platform values must remain explicit.
The GPU agent owns the GPU module's guest-command submission boundary: inspect
and extend existing bounded queues/adapters rather than duplicate them, connect
supported compute commands to the validated backend, and reject unsupported
operations explicitly. Root owns translation/memory integration review, submodule
revision propagation, metadata, provisioning and final regression validation.

Wanted: replace the observed standard-register boundary, observe the next actual
original instruction boundary, and improve independently testable memory and GPU
interfaces without claiming SPTM services, runtime device-tree resolution, XNU
boot or macOS Metal completion prematurely. Original code and private coordinates
remain under `_isolated/`; only public interface implementations and independently
authored fixtures enter module commits. No source copies return to the parent.


BP26-A decisions: root owns `ISE/runtime/preos/src/mmu.rs` to correct distinct
TG0/TG1 architectural granule encodings, validate disabled translation-table walks,
and retain deterministic failures for unsupported regimes. CPU source changes
outside that file remain delegated. Arm's Cortex-A73 TRM TCR_EL1 table and Arm's
Memory Management guide specify distinct TG1 and TG0 encodings; synthetic table
walks will establish lower/upper 4 KiB and 16 KiB behavior and rejection cases.
GPU agent is explicitly delegated the existing APLS SGPU codec move into GPU,
with APLS re-exporting the same public types. This is ownership consolidation of
the existing wire format, with bounded counts/lengths and compute submission
through the existing executor, not introduction of a parallel command protocol.


BP26-B review follow-up: independent review reproduced a supported upper-VA
translation fault when the initial table index has fewer than 9/11 bits.
Root owns masking that first index to the configured VA width and lower/upper
boundary regression coverage. The EFI agent is delegated only the ISE Arm CPU
oracle tools to add reduced-width 4 KiB/16 KiB cases; complete-width cases stay.
Root retains all metadata/pin ownership. The GPU agent is delegated APLS SGPU
error conversion compatibility, exact declared frame length checks and bounded
resource-creation ingress. Existing wire bytes stay compatible; malformed frame
acceptance and allocator panics become explicit errors. Regression fixtures must
cover valid existing traffic and rejected boundary inputs. GPU backend policy
and original-input startup prerequisites remain outside this follow-up.


BP26 final verification: source integration e1f64b3f passed a fresh recursive
clone check, standalone module dependency builds, 461 workspace tests plus the
compiled-EFI opt-in test, 65 reference runtime tests, four independent MMU
oracle cases, 14 authored x86 EFI cases, Python regression tests and required
Clippy checks. Original startup advanced to seven retired instructions; the
CPU override provider, native JIT MMU, SPTM services and runtime DT remain open.
The full macOS 27 build 26A5425a archive and selected input hashes are verified.
Detailed receipts: `nextcore/artifacts/integration-bp26-20260908/results.md`.
BP26 publication completed on the authorized feature branch; canonical GitHub
recursive clone and dependency resolution were verified. BP27 supersedes the
earlier pending-push state.


## BP27 — authorized publication and next EFI execution boundary

Current: BP26 passes recursive builds and authored EFI execution; original
startup stops after seven instructions at a platform interrupt-override read.
The user explicitly authorized remote pushes and continued implementation.
Publish immutable submodule objects before parent gitlinks, retain branch
codex/arm64e-boot-metal and verify canonical network clones without URL mapping.

Decision and ownership: the CPU agent owns ISE native/reference interrupt
pending state, PSTATE I/F routing, correct EL0/EL1t/EL1h vectors, and an explicit
optional platform-register provider with public-source semantics. It must
implement real mask effects and preserve pending levels, not a scratch/no-op
register. A named software compatibility profile may define its own initial
state, distinct from observed Apple reset; all unsupported fields/access modes
remain errors. Existing callers retain absent-provider behavior. The CPU agent
owns versioned C/Rust bridges and may add the standard logical-immediate ARM
instructions needed at the next generic boundary after documenting their ISA
contract. Native generated-code and reference tests must agree; the API contract
must be shared with the EFI agent before integration.

The EFI/Core agent owns explicit optional profile configuration, diagnostics,
independently authored firmware interrupt/provider tests and bounded original
input re-execution only after a working provider contract. Preserve the default
provider gate and all missing SPTM/runtime-DT outcome fields. Original bytes and
execution coordinates stay isolated. The GPU agent owns a concrete checked
adapter between existing APLS inline SGPU frames and the existing VSK grant-based
transport, using their real public ABI; no duplicate wire protocol, unchecked
pointers, fake guest driver or claimed EFI GPU backend. Write a narrow transport
contract before code and validate through existing compute sessions where
possible. Root owns Build Plan, remote publication, dependency pins, inventories,
CI, native-memory integration review and final cross-module regressions.

Wanted: make interrupt/platform state executable with explicit semantics,
advance the actual EFI compatibility path, connect an existing GPU transport
boundary, and publish reproducible independently linked modules. Actual XNU
boot and macOS Metal remain unverified until their own end-to-end outcomes.


BP27-A root memory scope: the reference walker currently ignores TCR_EL1.IPS
and can return a physical address beyond the configured output width. Root owns
only ISE/runtime/preos/src/mmu.rs plus independent physical-width oracle tools,
with public Arm TCR/AddressSize semantics. Add supported 32/36/40/42/44/48-bit
limits, explicit rejection of unsupported wider regimes, and fault-before-read
checks for out-of-range table/leaf outputs. Retain current configuration on
rejection. Verify boundary PAs and fault classes in authored descriptor tests
and an independent Arm CPU oracle. Do not change the native SCTLR.M gate or
CPU-owned arch/bridge files. This fixes reference semantics needed before native
MMU integration; it does not assert native translated-memory execution.
Reference: Arm Cortex-A73 TRM TCR_EL1 and Arm A-profile memory pseudocode.


BP27 goal update: the user requires continued development until ARM64e macOS27
is stably usable after boot inside an x86_64 EFI test machine, with milestone
pushes and final build/use documentation in the GitHub wiki. Treat authored
fixtures, original-prefix retirement and host compute as intermediate evidence.
Completion requires the real OS to reach its usable interface, preserve storage
across repeated cold boots/restarts, accept input, and pass sustained basic use;
actual graphics/Metal outcomes need their own receipt. Keep physical execution
architecture x86_64 and EFI entry explicit. Do not mark the active goal complete
while native MMU, SPTM/platform providers, OS boot, stability or wiki work remains.


BP27-B CPU delegation extends the existing shifted-register ADD/SUB family to
its flag-setting comparison aliases after the observed generic startup boundary.
Document and implement defined32/64-bit shifts, NZCV, x31 semantics and invalid
encodings, with independent native/reference checks. This extends an existing
ISA path; no platform values or original bytes are incorporated. Final original
prefix tracing follows the working provider and ALU implementation.


BP27-C user scope update: remove the retired machine-specific profile and its
content and unnecessary Windows application sandbox tester features. The GPU
agent is delegated a separate cleanup contract and the affected application,
profile, documentation and reference files; runtime VSK grant authority and
boot/JIT validation remain required dependencies. NVIDIA and Intel integrated
graphics join AMD as explicit implementation targets; hardware support requires
backend evidence and is never inferred from an API/device enumeration.

The user authorizes milestone commits, publication, pull requests into main and
merging after required checks. Publish dependency commits before parent gitlinks.
Clean up completed merged task branches only after proving their commits remain
reachable from main; preserve unrelated or unmerged work. Root owns integration,
PRs, merges and branch cleanup. The active stable macOS boot goal remains open.

BP27-D root independent MMU validation extends the physical-width oracle with
L3 page outputs and both low/high offsets within a 16 KiB L1 block. These cases
address a review gap in the initial eight block/table/root checks. Keep expected
architectural faults explicit and compare against the independent CPU model.

BP27-D oracle outcome correction: independent execution and Arm FEAT_LPA2
documentation establish that 16 KiB L1 block descriptors are reserved when DS=0.
The existing reference walker and new huge-block unit fixture wrongly accepted
them. Reject that descriptor before address/permission checks, replace the
incorrect fixture with low/high-offset Translation faults, and keep valid L2
cache-boundary checks. LPA2 remains unsupported. This supersedes the earlier
assumption that a 64 GiB block could be valid in the selected regime.

BP27 implementation milestone: Core/ISE/APLS/EFI/Tool source commits passed
fresh standalone dependency builds and were pushed before the parent gitlinks.
The original diagnostic reaches 26 retired instructions in 10 native blocks
before a standard integer store-pair boundary. Eight authored x86 EFI profile
and vector cases pass; handlers and native MMU remain separate work. The
reference suite has 73 tests, with 14 independent physical-width/descriptor
oracle cases and a deliberately failing changed-descriptor control. APLS grant
submission was differentially checked against the existing C policy and ran
on the available AMD GPU. This is neither complete macOS boot nor guest Metal.

BP28 delegation: after immutable BP27 ISE commit a6f1c46c, the CPU agent works
only in a separate ISE worktree on integer STP/LDP addressing, bounded memory
access, precise faults and writeback. The EFI agent investigates the public
SPTM startup contract and version-specific normal boot prerequisites without
fabricating private structure layouts. Root integrates and publishes BP27 in
parallel. The GPU agent completes the authorized legacy app/profile cleanup.

BP27 CI repair: the independent EFI runner installed clang/lld but omitted
LLVM tools; archive creation failed because llvm-ar was absent. Declare llvm
in the module workflow and both root firmware-building jobs, including
llvm-objcopy needed by authored fixtures. Runtime source behavior is unchanged.


BP27 publication closure: all six changed module pull requests and parent PR #9
passed required CI and merged into main. The parent merge is f345a8a4. Completed
module/task branches were deleted only after merge/reachability checks; unrelated
unmerged work remains. Cleanup artifacts and tested hashes are preserved.

## BP28 — integer pair memory and portable GPU selection

Current: the BP27 original prefix stops at an integer store pair after 26
instructions. The host Vulkan backend cannot disambiguate identical PCI device
IDs and excludes valid noncoherent HOST_VISIBLE allocations. Actual native MMU,
normal macOS startup and guest Metal remain incomplete.

Decision: the existing delegated CPU work implements integer STP/LDP 32/64-bit
signed-offset/pre/post addressing, complete RAM span validation, precise data/SP
alignment faults and success-only writeback. SIMD, MMIO pairs and translated
pairs remain explicit unsupported paths. The GPU delegation extends existing
Vulkan selection with observed device UUID, feature/queue/memory diagnostics,
and correct noncoherent flush/invalidate, without vendor filtering or fallback.
Detailed contracts live in the ISE/GPU submodules. Root owns dependency pins,
CI, inventories, independent integration tests and authorized PR/main publication.

The EFI agent supplies independently authored pair/fault fixtures and the bounded
original r4 diagnostic with no original bytes or execution coordinates published.
A fresh recursive clone must execute the same immutable module revisions.
The CPU agent is delegated the next unsigned-immediate scalar integer memory
family in a separate BP29 worktree after immutable BP28 source, with its own
contract and oracle; this cannot alter the BP28 validation input.


BP28 review correction: MMU-disabled/HCR=0 data is Device-nGnRnE, requiring
element alignment even when SCTLR.A=0. The first pair implementation incorrectly
allowed unaligned RAM in this case. Corrected ISE 07cd3e19 supersedes that
expectation before PR #2 merge. Reference/native regressions and a restored-bug
negative control prove the correction. QEMU omits this A=0 check and SP alignment;
those limits are explicit rather than treating oracle success as full coverage.
EFI observation covers status/ESR/registers/SP/retirement; host C/Rust probes
also inspect FAR and unchanged memory, which the EFI v2 result does not expose.


BP28 integration outcome: five changed modules merged PR #2 to their own main,
with immutable tested heads retained in parent gitlinks. Fresh recursive source
41aa5d95 passed472 workspace tests,77 reference tests,28 authored x86 EFI cases,
18 independent MMU cases, pair/native ABI checks,119 Vulkan tests, Python/GUI
boundaries, compiled-EFI packaging and Clippy. Corrected original diagnostic
remains47 retired/10 native blocks. Exact records live in
`nextcore/artifacts/integration-bp28-20260909`; OS/Metal acceptance remains open.


## BP29 — scalar memory and exact stage-1 failure information

Current: BP28 parent PR #10 merged into main as4ed3c9e after27 final CI checks
and a canonical recursive clone. The original diagnostic stops after47 retired
instructions at a32-bit unsigned-immediate load. The walker loses fault levels
and descriptor-read failure types, preventing a precise native memory provider.

Decision and ownership: CPU agent implements the complete standard scalar
integer unsigned-offset width/sign family in a separate ISE worktree, preserving
native MMU gates and external ABI. Root owns the existing mmu.rs detailed-error
interface, typed physical descriptor reads, cached leaf provenance and legacy
method adapter. EFI agent owns an independent Arm exact-FSC oracle using actual
captured control/table bytes, including real EL1 abort handlers. GPU agent owns
independent code review and authored actual x86 EFI scalar execution in a separate
output directory. Root owns integration, inventories, pins, tests, PR/main merges.

The metadata-only walker change retains one implementation behind both APIs.
Independent tests correct the prior noncanonical-VA AddressSize classification
to the architectural Translation level0, and keep real physical-width failures
distinct. EPD must be tested in the AArch64 target regime with HCR.RW explicitly
set, and reports Translation level0. Native M=1, strict table/memory attributes,
normal startup providers and guest Metal are not completed by this interface.

BP30 CPU delegation: after immutable scalar source8b09f876, a new isolated
worktree prepares the first native caller-owned Rust memory-provider path with
M=0. Contract and fixed-width callback ABI are reviewed before code. All native
fetch/scalar/pair accesses must route through the checked provider in that mode,
with full-span preflight and exact commit boundaries; ALU/control remain generated
x86, legacy APIs remain compatible, and every M=1 gate stays until its separate
validated activation. No duplicate walker, hidden direct-memory path or claimed
macOS completion is permitted. EFI caller wiring follows the approved ABI.


BP29 source validation: immutable ISE33fea9f passes a fresh standalone clone's
26 package and91 architectural tests,106496 scalar cases/426981 assertions,
existing native PAC/IRQ/pair/ABI proofs, independent scalar execution and158
captured AT/actual-abort comparisons plus negative controls. ISE PR #3 passed
both final CI jobs and merged asabdbd1a7. Actual authored EFI11cases pass with
frozen8b09 source; the12 linked runtime sources match33fea exactly. Historical
and combined-source binary executions must retain separate hashes/receipts.

BP30 diagnostic delegation: EFI agent owns separate Core/EFI source worktrees
for opt-in tiered tracing. Preserve the public default64 platform/8 no-platform
budget API and normal firmware behavior. A separate explicit feature may accept
bounded tiers256/1024/4096, with a build marker and host opt-in. First prove an
authored256-instruction case, then advance original diagnostics only when the
previous run stops precisely at its budget. Public output remains aggregate-only.
Root owns final dependency pins, metadata, integration tools and PR/main publication.


BP29 integration closure: fresh recursive d45b107d passes472 workspace tests,
91 reference tests,39 authored x86 EFI cases,158 captured ARM comparisons,
the prior18 MMU oracle cases, native scalar/PAC/IRQ/pair/ABI execution, Python/GUI,
Vulkan, firmware packaging and Clippy. Both changed module PR #3s are merged
and their completed branches are removed after ancestry checks. Raw receipts
and the initial CI artifact-finalization403 are preserved in
nextcore/artifacts/integration-bp29-20260909. The final evidence-only commit
receives its own canonical recursive clone/hash checks and final-head CI.


## BP30 — native Rust memory service and bounded execution tiers


The seven existing Git module repositories remain the ownership boundary. ISE
adds one no_std auxiliary Rust package at runtime/memory-service; this is not an
eighth module repository or a copy in the parent. EFI takes it through the same
canonical ISE Git URL and immutable revision as nextcore-ise. Its optional feature
and caller wiring remain explicitly diagnostic until normal startup is complete.

The parent workspace adds an explicit path patch for nextcore-memory-service to
the ISE-owned package. Exclude that nested standalone workspace from automatic
parent membership; keep the original seven members. Test cargo metadata on the
actual package layout before deciding whether the exclusion is required.

Extend Tools/verify_nextcore_submodules.py with a fixed auxiliary-package owner
mapping. Any nextcore-prefixed dependency must be a known primary or auxiliary
package and pin its owner's canonical URL and integrated commit. An auxiliary
manifest may live only at the declared path inside its owner module and must be
covered by that module's existing full file inventory. Cargo resolution must
contain exactly one local instance of every selected Nextcore package, including
the memory service when the feature is enabled. Verify host and UEFI dependency
resolution with that feature; no remote duplicate may hide behind an unused patch.

The existing metadata refresher must record one ISE revision even when EFI has
two package dependencies from that URL. It must reject conflicting revisions
instead of allowing the second dictionary assignment to conceal them. Auxiliary
package dependency manifests, if any, must obey the same module pin policy.

Validation uses an independent standalone EFI clone from canonical Git revisions,
a fresh parent recursive clone with --locked builds, and actual x86 OVMF provider
execution. Mutation checks must reject an unknown auxiliary package, wrong owner
path, mismatched ISE revisions and Cargo resolving a remote duplicate. These are
packaging checks, separate from native memory semantics, OS boot and guest Metal.


BP30 implementation and independent evidence: ISE41e8997 owns the80/80/192-byte
callback ABI, no_std RAM service and native dispatcher with no guest-RAM pointer.
Core40833dc keeps default64/8 trace limits and exposes explicit bounded tiers.
EFI2414067 joins both opt-in features; Tool926c777 pins that Core revision.
All four module PRs passed final CI and merged into their independent main.

An independent EFI clone with an empty Cargo Git cache resolved canonical Core,
ISE and its auxiliary service without parent patches. Five build modes passed;
actual combined firmware passed23 provider cases, one separately mutated callback
failure, a successful direct execution rejected as a provider bypass, and8 tier
checks. The combined tier's256 retirements/fetches/native entries were checked
separately. Historical and combined binaries retain separate public manifests.

The parent shared package policy validates7 modules/7 workspace members/8 owned
packages, aliases and target dependencies, same-owner revision agreement and
local auxiliary resolution. Actual temporary Git/Cargo duplicate resolution is
a rejected control. The integrated EFI runner requires an actual failure receipt
for its bypass control rather than accepting any exit1, and verifies that the
combined tier really uses the Rust service. Its real EFI execution is part of the
fresh recursive integration gate; host callback-failure variants stay separate.

The normal-entry audit in NEXTCORE_ARM64E_ENTRY_CONTRACT.md corrects the prior
assumption that j274 lacks SPTM components. Full manifest/member digest evidence
supports the current selected inputs, while exact target boot_args/SPTM layout,
live state and runtime-DT providers remain unresolved. No native M=1 or OS/Metal
success is asserted. BP31 conditional compares are independently implemented in
a separate frozen ISE worktree and are not part of this BP30 integration.


BP30 integration closure: implementation ea0a62e8 passes a clean fresh recursive
clone with476 workspace/149 Python/25 GUI/91 reference tests,158 captured Arm
fault comparisons,65 actual x86 EFI cases and6 separate CLI rejections. Native
provider/no_std/ABI, legacy scalar/pair/PAC/MMU/Vulkan and firmware packaging
remain passing. Full receipts are in artifacts/integration-bp30-20260909. Final
evidence/documentation receives its own canonical recursive checkout and CI.


## BP31 — conditional comparisons in the x86 EFI JIT

ISE0aabf085 adds CCMP/CCMN register/imm5 in32/64-bit forms as generated x86
flags operations, preserving other PSTATE bits/registers/SP and the M=0 memory
service. ISE PR5 and EFI PR5 are merged; EFI7495633 pins the same ISE revision
for both dependencies. Root owns parent gitlinks, current-source authored EFI
runner, CI, historical evidence and fresh recursive integration/publication.
Historical13 EFI cases and original256/1024/4096 budget diagnostics retain their
original source/binary provenance. The current combined standalone EFI separately
passes13 cases with canonical Git dependencies. A reusable parent runner records
current source hashes rather than asserting that all future runtime revisions
must equal the historical freeze. Independent native/Arm negative controls remain
in the ISE proof and historical bundle; no full OS/Metal claim follows.

BP32 is delegated separately: CPU owns the canonical shared walker, strict
immutable stage1 profile and v2 C/Rust memory execution; GPU agent owns independent
actual Arm fault-priority comparisons; EFI agent owns an opt-in authored NXMMU
probe and its allocation/callback lifetime. The runtime-DT transformer prototype
is frozen outside production pending a real allocation/reservation view. Neither
that prototype nor the M=1 work changes this BP31 integration input.


BP31 runner review: optional --require-memory-provider checks every authored
conditional case for ABI1, exact Rust fetch count, one native entry per fetch,
zero data operations/ESR/FAR and final fetch address. CI explicitly enables it.
The strengthened runner separately passes13 positive executions and rejects one
actual direct-runtime execution only for missing provider evidence, with correct
arithmetic preserved. This additional runner proof uses canonical standalone
EFI7495633, distinct from the fresh parent8bcf5c52 baseline suite.


BP31 closure: fresh recursive8bcf5c52 passes476workspace/149Python/25GUI/93reference,
78actualEFI+6CLI,3668conditionalArm+158faultoracle and native/ABI/package regressions.
The strengthenedf38a2c30runner independently passes13provider executions and one
actual bypass rejection using canonical standaloneEFI7495633. Final-head CI uses
that stronger predicate on newly built integrated firmware. Raw evidence preserves
these separate identities in integration-bp31-20260909; final publication gets its
own canonical recursive checkout and artifact-byte validation.


## BP32 — native immutable stage-1 memory execution

Current: BP31 parent0509118 is merged; normal macOS startup and guest Metal
remain incomplete. The explicitly delegated ISE implementation introduces a
separate80/160/128/320-byte C/Rust ABI for M=1 fetch/scalar/pair execution through
the canonical Rust walker. The fixed Normal-NC/A=1 profile has immutable table
backing and controls, and rejects unsupported control changes and attributes.
No guest RAM pointer enters the native dispatcher. Detailed scope and the
trusted synchronous callback failure boundary live in the ISE module contract.

Root owns immutable pins, CI, metadata, proof publication and PR/main merges.
The original BP29 oracle helpers and indexed receipts remain byte-for-byte
historical. A separately named compare_current_walker.py imports the current
canonical enum/walker; active CI and reproduction commands use that adapter.
No historical receipt is relabeled as execution of the changed helper.

Independent ARM execution distinguishes354 recorded-value matches and74 exact
BTYPE profile rejections from the original428 cases. A separately authored
ERET-entry set provides78 BTYPE=0 fetch cases, with captured state retained.
Of354 matches,32 successful fetch cases use completion snapshots, not target
fetch captures;322 are data operations. The12 QEMU PC-priority disagreements
remain failed comparisons. Controls record
explicit harness HCR adaptation and uncaptured inactive fields. The opt-in EFI
NXMMU probe executes108 authored nonidentity cases on an x86 outer computer.
Final frozen replay, canonical module builds and recursive integration are
required before closure. The separately merged Core305 runtime-DT transformer
is excluded from BP32 EFI's frozen Core408 dependency; root integration and
actual allocation/consumer execution remain a subsequent milestone.


BP34 is explicitly delegated to the CPU agent in a new ISE worktree from720d7c6:
implement one-way M=0 to M=1 activation with immutable tables, separate
architectural/effective snapshots, a new dynamic memory discriminator3 and
192-byte prepare/commit/cancel control records. Existing v1/v2/vf_cpu remain
unchanged. Full flat transition-ISB span/bytes/ownership, M=0 Device semantics,
real canonical TLBI and precise failure/uncertain-host-commit boundaries must
be validated. Exact enums and final512-byte state tags are frozen in the new
module contract before code. This is subsequent work, excluded from BP32 pins.

BP33 allocation work is delegated to the EFI agent in a separate Core worktree
from305e66a. Its design must bind observed exclusive backing, guest aperture,
nonoverlapping purpose reservations and owner/generation to DT patch commit.
No original provider values or target ABI are guessed. Root reviews the design
before implementation; Core/EFI/Tool integration remains a separate milestone.


BP32 validation closure: ISE PR6/main91721d0 and EFI PR6/main646bc5f are merged
after final CI. The completed branches were removed after ancestry checks.
Fresh recursive df60198b passes476workspace/149Python/25GUI/98reference,186actual
x86EFI plus6CLI and native/provider/Arm/Vulkan/package checks. The final EFI
pinf3f7938 changes only reproduction docs/metadata from tested8d53dd2; root
verifies this distinction and the final inventory. Actual stage1 and conditional
provider predicates run on the integrated binary. The separate fresh service
replay preserves captured-state limitations. Final evidence publication receives
canonical recursive checkout and final-head CI before parent PR merge.

BP33 ledger design is approved for both owned Box and exclusive borrowed-slice
backing,64 bounded reservations, opaque identity/generation, typed DT binding
and higher-ranked execution loan. Arbitrary provider semantics and callback
rollback are not inferred. Root source review found no concrete range/token/
lifetime defect; full tests/final freeze and actual authored EFI consumption
remain independent of this BP32 closure.


## BP33 — owned guest staging and actual DeviceTree consumption

Core305 introduced a source-bound runtime DT transformer; Coref77c98f adds
exclusive owned/borrowed backing,64 purpose reservations and opaque owner/
generation binding. The frozen implementation passes standalone default/no-std
tests, lifetime rejection and UEFI code generation. Root owns Core/EFI/Tool
pin updates, inventories, recursive validation and authorized PR/main publication.
The Tool Core dependency must advance with the same integrated Core revision;
there is no new Windows UI feature.

The EFI agent is delegated a separate opt-in NXDT consumer from BP32f3f7938:
actual ArmPages ownership, ledger-derived code/DT/stack/output placements, typed
DT commit and generated-x86 ARM loads/stores through the canonical M=1 service.
Its authored source property carries observed guest aperture values, not an
invented target ABI. Wrong-DT mapping and stale preparation are checked at their
actual different boundaries. Separate table backing stays disjoint and immutable
while the service is borrowed. Core/EFI source freezes and independent proof
remain separate from final canonical source integration.


BP34 actual dynamic EFI consumption is delegated to the EFI agent in a new
worktree from the immutable BP33 source: separate opt-in caller, one-way MMU
activation, post-ISB nonidentity accesses/faults and compiled omission negative.
BP35 is delegated to the CPU agent in separate Core/EFI worktrees: exactly one
explicit16384 diagnostic tier, unchanged legacy caps and selector rejection,
authored actual-EFI acceptance before any original replay. Root owns the
external CLI review, all integration pins and publication.


BP33 canonical EFI CI exposed a real debug code-generation failure in sha2's
x86 accelerated backend; cargo check and release-only builds had not exercised
that compiler path. Root owns the corrective Core target-UEFI force-soft
dependency, actual debug/release codegen CI, dependent EFI/Tool pins and fresh
firmware validation. Existing successful/failed source identities stay separate.


BP35's single original16384 diagnostic reached5311 retired instructions and
stopped at a real UBFM/LSL-immediate unsupported boundary; original coordinates
and bytes remain isolated. BP36 is delegated to CPU (complete UBFM32/64 native
and reference semantics), GPU (independent authored Arm oracle), and EFI
(authored existing-bin consumer proof), all in new worktrees/external fixtures.
No BFM/SBFM support or additional original run is implied.


BP33 closure: merged Core147/EFI7e7/Tool4bb pins pass the corrected fresh recursive
e0351bd47-command suite, including194actualEFI and6CLI-only cases. Core SHA2
debug failure and the earlier separate QEMU shutdown timeout remain failed
historical records. Final artifact bytes, canonical network clone and exact-head
CI are required before parent merge; subsequent BP34/35 module work is separate.


## BP34 — integrate one-way translated execution from x86 EFI

Root integrates merged ISE0d722886 and EFIed9ba255, retaining Core147 and Tool4bb.
The new opt-in NXDYN consumer owns separate RAM/table/JIT allocations and checks
architectural versus effective MMU control across PREPARE/COMMIT and guarded ISB.
Six actual firmware cases cover 4K/16K translated read/write and precise immediate
fetch/data faults. Existing memory ABIs and immutable-table restrictions remain.
The independently captured Arm six-case oracle and its native C/Rust comparison
are published separately from EFI evidence. Original HVC termination is retained
as an unsupported native boundary, without an architectural HVC dispatch claim.
Root adds native/EFI/reader gates and verifies fresh recursive and canonical
network checkouts before authorized PR/main merge and completed-branch cleanup.
BP35 deeper original diagnostics and BP36 UBFM/Undefined-IL corrections retain
separate source identities and are not included in these BP34 runtime pins.


BP34 validation closure: Fresh recursive750bda20 passes53commands: workspace502/Python149/GUI25, reference98/service44, actualEFI200 plus6separateCLI, strict DT28/dynamic30 controls, native capturedArm6 and13comparator regressions. Existing Clippy warnings remain. Full receipts are in artifacts/integration-bp34-20260909.

BP36 current-gate adaptation is delegated to CPU in a separate external tool
directory: preserve historical pair/scalar/dynamic adapters and their freezes,
require corrected unknown-reason IL only at typed unsupported boundaries, bind
the new runtime71 explicitly, and rerun captured native6 without changing real
Arm abort observations. Root owns active parent CI/driver selection and the
current EFI omission-reader expectation. No historical result is rewritten.


## BP35 — integrate explicit deep diagnostics

Root connects merged Corebab7, EFI03a and Tool8ea while retaining ISE0d.
The external CLI and authored gate are promoted byte-for-byte to parent tools.
Existing/default parser caps remain unchanged; a separate deep-capable feature
and exact deep-16384 selection are required. Root performs targeted fresh
recursive workspace/config/actual deep-control checks in addition to the just
completed BP34 full suite and canonical EFI standalone regression matrix.
CI retains all existing jobs and adds one actual deep execution with28 preflight
rejections and x1 corruption rejection. The separately compiled clamp and five
actual canonical controls retain their own recorded evidence. No repeated
original run or new unsupported instruction support belongs to this milestone.


BP35 validation closure: fresh recursive6bca2907 passes the14-command targeted
suite with workspace505/Core235+3doctests/Python149, actual integrated4 and
separately built canonical clamp1,28 CLI rejections and x1 negative. Legacy full
CI remains and final public bytes/network checkout are independently checked.

## BP37 - Physical macOS 27 display-first continuation

Root owns integration pins, new execution receipts and the build-plan contract.
The EFI picker agent owns optional presentation fallback and its module-local
contract/tests. Root will independently review that change before integration.
Use the published instruction families with the existing deep diagnostic as a
bounded observation tool, without changing normal-entry or provider gates.
Verify native semantics and actual EFI consumption before original-input replay.
Replays must identify their actual input and incomplete startup state; do not
compare different device kernels as a single execution history. Preserve raw
original inputs and traces in the ignored isolated directory. The selected
physical acceptance is external-media installation, reboot and an interactive
macOS 27 desktop on Samsung 750XHD; GPU acceleration is outside this milestone.


### BP37 documentation and evidence maintenance

The existing Design/Build Plan pages are explicitly delegated for this documentation refresh. Preserve historical receipts and immutable captures while updating reader-facing support claims. The portal, compatibility catalog and progress page separate official model eligibility, NextCore evidence and missing implementation. No documentation or CI result can authorize normal entry past an unmet provider contract.

SPTM applicability to the selected j274 target is unverified. The diagnostic
profile name does not establish its normal startup ABI; see the
[entry contract](NEXTCORE_ARM64E_ENTRY_CONTRACT.md).

### Owned non-accelerated framebuffer handoff

Current Status: The opt-in trace reserves owned boot-video storage and authored
guest writes match actual GOP RGB readback. The original-input prefix still has
a screen hash matching an all-zero frame. Physical desktop output is unverified.

Target State: An explicitly selected display path reads the real current GOP
mode, reserves a checked 32-bit guest framebuffer in the handoff allocation,
encodes its public boot-video fields, and presents that same backing buffer.
The allocation must not overlap the kernel, argument page, DeviceTree or stack;
the occupied-memory boundary must include its complete page-rounded storage.
Unknown or unsupported firmware geometry fails the optional display selection
without inventing successful video support. Normal entry readiness and existing
diagnostic limits remain unchanged until their separate providers are complete.

Root owns integration and the explicit trace consumer. The Core slot owns the
allocation/encoding contract and independent overlap/overflow tests. The EFI
slot owns checked current-GOP geometry and presentation adaptation. Authored
guest writes must be read back from the actual GOP in OVMF, with the framebuffer
bytes and geometry taken from the encoded boot arguments. Such a result proves
this display connection only, not WindowServer or a physical macOS desktop.

### Bounded memory-request observation

Current Status: A 16,384-instruction return supplies a final PC and aggregate
memory counters. It cannot establish whether initialization advanced or repeated.

Target State: A separate build-only observation feature records the last 64
memory requests and successful replies through the same MemoryService execution
path. A fixed ring avoids allocation, never changes guest inputs or replies, and
prints only after execution returns. Request sequence, operation, PC, address,
width and count are sufficient; guest instruction/data values are not emitted.
The existing budget, entry state, memory permissions and readiness gates remain
unchanged. Raw original-image coordinates stay in the isolated output directory.
Authored requests must prove chronological ring order and identical RAM/replies
with observation enabled and disabled before replaying the original input.

### Explicit long diagnostic after observed advancing stores

Current Status: The final 64-request window of the 16,384-instruction original
prefix contains successful 8-byte stores at two distinct adjacent addresses.
Observation preserves the complete prior execution result and configuration.
This refutes a fixed-address stall in that observed window, but not all loops.

Target State: A separate `arm-jit-long-trace` build and exact `long-65536`
selector permit one 65,536-instruction diagnostic with the existing named
software profile. Existing default, tiered and deep parsers keep their ceilings;
even a long-capable build requires the explicit selector and exact budget.
The host requires build and selection acknowledgement before accepting that
request. No normal-entry gate, provider behavior, guest input or instruction
semantics changes. An authored bounded loop validates the selected budget and
old-build rejection before replaying the same original input. The next fault or
observed state, not the larger count itself, determines the next implementation.

### Run-local native reuse for physical-memory execution

Current Status: The v1 provider loop fetches every instruction, translates a
single native entry and transitions the complete code allocation RW then RX on
every iteration. Original-prefix windows repeatedly execute a small set of PCs.

Target State: Reuse single-instruction native entries within one v1 provider run
only after a fresh successful fetch. Key entries by guest PC, fetched instruction
word and current EL, with provider mode fixed. Preserve state checks, interrupt
polling, fetch/reply validation, data callbacks, slow paths, retirement, faults
and native-entry counters on hits. Never cache memory replies or use epoch zero
as proof that guest code is unchanged. Other execution backends remain unchanged.

Use bounded stack metadata and the caller's existing code allocation; no new
executable allocator or persistent cache. Code slots are invalid until complete
translation and a successful RX transition. Misses may change permissions for
the whole allocation only while no cached native entry is executing. If a slot
cannot hold an otherwise valid instruction, invalidate the cache and use the
existing full-buffer translation path, preserving its status semantics. Small
buffers retain the uncached path. Failed protection or translation never leaves
a reusable entry. The original final protection restore remains mandatory.

An independently compiled uncached variant is the comparison oracle. Authored
tests must compare complete CPU/RAM/request/fault results, exercise guest code
stores, different PC/EL, fetch failures on apparent hits, collisions and small
buffers, and measure fewer real protection calls. Replay the same original input
and budget with final EFI bytes before claiming a measured improvement. Larger
budgets, new entry registers and normal readiness are outside this cache change.

The optional EFI protection observer forwards each callback exactly once and
returns its result unchanged. It counts writable/executable attempts and failures,
including the final writable restore, and emits counts only after execution.
The uncached EFI build is a compile-time comparison control, not a runtime mode.

### Explicit initialization diagnostic for collection fixups

Current Status: The original file contains 1,010,443 format-8 chained entries.
The observed final two stores at the 65,536-step boundary match consecutive
input chain nodes 2,722 and 2,723. This establishes local membership, not stored
value correctness or full phase completion. The source-defined loop performs
work per entry before later kernel/platform initialization.

Target State: Provide a separately built and explicitly selected
initialization-67108864 diagnostic with an exact 67,108,864-step ceiling and the
existing named software profile. The large bound permits an experiment beyond
the observed early chain nodes; it does not assert a complete phase or boot.
Old parsers/builds must reject this selector. New parsing retains prior deep and
long selectors and the unselected 4096 ceiling. Normal readiness is unchanged.

Require build/selection markers and memory-provider evidence in the host receipt.
Keep the existing 600-second timeout cap. Validate malformed selection and old
build rejection, then run an authored cached loop with exact retirement before
using unchanged original input. Compare the resulting PC/function region and
request membership to determine the next execution boundary. Do not modify
original pointers, skip instructions or invent platform/service responses.

### Immutable Normal-memory unaligned diagnostic profile

Current Status: The original initialization diagnostic stops at an ordinary
unaligned data load under the M=0 Device-memory contract. Suppressing that fault
would misrepresent architectural behavior. The existing immutable stage-1
profile 1 supports Normal-NC memory with SCTLR.A set.

Target State: Add explicit immutable profile 3, named fixed Normal-NC unaligned,
with SCTLR fixed to 0x30d00801 except optional SA/SA0 bits. Its other controls,
readonly table ownership, complete byte preflight and precise fault behavior
match profile 1. Ordinary data transfers may be unaligned only in this profile;
instruction and configured SP alignment checks remain. Profile 1, dynamic profile
2 and M=0 Device behavior remain unchanged. C and Rust validate the same contract
and reject fabricated alignment-fault replies for ordinary profile-3 transfers.
Cross-page stores must preflight every byte before any mutation. Add actual native
provider tests and an authored OVMF selection before using original input.

This profile does not establish the original image entry ABI, supply pointer
authentication to the immutable v2 runner, construct kernel page tables or enable
normal startup. Those require separate explicit contracts and runtime evidence.
Root owns integration and this Build Plan section; delegated runtime implementation
and independent tests have disjoint source ownership.

### Explicit mapped original-entry diagnostic

Current Status: The explicit mapped NXARMJIT path passes authored EFI acceptance
with the final published module revisions. Three native cache variants pass 31
tests each and nine complete-state comparisons; the existing M=0 suite passes
20 regressions. The first original profile-3 attempt stops at immediate stack
selection after 13 retired instructions; it does not exceed the M0 result.

Target State: Add a separately built and explicitly selected mapped diagnostic.
Use 16 KiB Normal-NC profile 3 (T0SZ=T1SZ=17, IPS=48), an immutable caller-owned
table image, and identity plus VirtualBase aliases for the validated RAM span.
The entry PC is the staged entry's corresponding VirtualBase alias. Keep the
existing declared x0=0/x1=physical boot args/x2=x3=0 and physical stack through
the identity alias. This is software-defined diagnostic setup, not a proven
original reset ABI. Tables occupy a disjoint physical range immediately after
RAM. Reject overflow, noncanonical aliases, overlap, alignment and capacity
errors before guest execution. Page tables are immutable and normal readiness
remains NOT_READY.

A distinct vf_boot_run_memory_pauth_v2 entry adds the canonical PAC callback
immediately after initial_x0_x3 in the existing v2 signature. The old v2 entry
continues without PAC. The new path must refuse callback changes to immutable
controls/current EL before committing any context. Extend the existing bounded
PAC address profile from 48 to 47 bits only with public-contract and independent
oracle evidence; do not change QARMA, key defaults or PAC enable semantics.
Profile 3 keeps its fixed enable bits, so disabled PAC instructions retain their
architecturally disabled behavior. XPAC and generic authentication instructions
must use their actual supported semantics, never instruction skipping.

Reuse native entries in the immutable v2 loop only after its existing per-step
control checks and fresh validated fetch. Match PC, word and EL, preserve all
fault/interrupt/data/retirement behavior and protection failure handling, and
retain a compiled uncached comparison. Dynamic execution remains unchanged.

Core owns a checked 16 KiB alias-table planner and a mapped-only trace parser:
parse_arm64_trace_configuration_with_mapped_tier, admitting the existing budgets
plus exact MemoryProfile=mapped-normal-nc-v1. Existing parser APIs must reject
that field instead of silently ignoring it. EFI requires arm-jit-mapped-trace
and emits build/selection/mapping/provider acknowledgements. The host requires
those acknowledgements before accepting --mapped-diagnostic. Authored mapped
execution, old-build rejection and cached/uncached equality precede the original
replay. Original assets and raw coordinates stay isolated.

Acceptance scope: the independent Arm oracle advertises APA5 while the runtime
implements APA1. Sixteen enabled lower-range sign/auth vectors and all 24
XPAC/disabled vectors compare directly. Eight upper-range enabled vectors are
not verified against a same-feature CPU. The selected mapped profile keeps
address signing disabled and does not widen that contract.

### Immutable mapped stack selection

Current Status: The first original mapped replay stopped after 13 retired
instructions at immediate SPSel selection. A dedicated immutable v2 handler now
passes 32 native tests in each of three modes and ten authored EFI checks.
Distinct banks, stale saved-bank values, following stack accesses and existing
EL0/reserved-encoding failures are verified. The unchanged original mapped replay
now retires 42,252,448 instructions and completes 6,010,803 data operations before
an unsupported scalar unscaled load. Its framebuffer remains zero. This proves
progress in the explicit diagnostic regime, not normal or physical macOS boot.

Target State: Implement the two architected immediate SPSel selections at EL1
in the immutable v2 runner. Save the active stack bank, set only PSTATE.SP,
then load the selected SP_EL0 or SP_EL1 bank. Preserve NZCV, DAIF, current EL,
all memory controls, PAC keys and unrelated registers. Retire exactly once,
advance PC once and retain the normal next-step control and fetch validation.
EL0 and reserved immediate encodings must retain their existing failure paths.
Do not open DAIF, TLBI, ERET or arbitrary system writes through this helper.
The existing M0 and dynamic implementations remain unchanged. Authored bank
switch, same-bank selection, following stack use and negative tests precede
another original replay. Arm's public PSTATE synchronization contract requires
subsequent instructions to observe the new stack without an added barrier:
https://community.arm.com/forums/f/architectures-and-processors-forum/8141/is-any-synchronization-barrier-instruction-necessary-after-writing-spsel-to-switch-to-sp0-on-armv8

### Scalar unscaled memory transfers

Current Status: The signed immediate unscaled class now passes 546 native cases,
39 actual Arm vectors compared against both C and Rust execution, and 33
canonical-memory tests in each of three cache modes. Final authored EFI passes
ten checks. An independent failure exposed missing store-fault WnR classification;
the corrected exception encoder passes exact-syndrome regressions. The previous
original run stopped at this class after 42,252,448 instructions; replay with the
verified implementation first ended without a terminal record after about 334
seconds. After the separately verified watchdog ownership change, unchanged-input
r22 completes after 413.518 seconds with 42,252,452 retired instructions and
6,010,805 completed data operations. It stops at an unsupported shifted-register
ORR. The 1280x800 framebuffer remains zero; normal and physical startup are unverified.

Target State: Support the thirteen integer unscaled forms: byte/halfword/word/
doubleword stores and zero-extending loads, signed byte/halfword loads to W/X,
and signed word loads to X. Decode only the unscaled mode with its signed nine-bit
byte displacement (-256 through 255), no scaling and no base writeback. Rn=31
uses SP and Rt=31 uses ZR. Preserve flags, precise data/stack alignment and
translation faults, destination width/sign extension, provider request semantics
and nonretirement on failure. SIMD, prefetch, reserved encodings, unprivileged
and pre/post-index variants remain outside this addition. Update all native
classification/direct/provider paths and the Rust reference consistently.
Independent authored cases must cover all forms, displacement endpoints, SP/ZR,
signed results, preserved base, cross-page Normal accesses, permission failures
and rejected adjacent encodings before original replay. Public encoding source:
https://github.com/qemu/qemu/blob/ae35f033b874c627d81d51070187fbf55f0bf1a7/target/arm/tcg/a64.decode

### Firmware watchdog ownership

Current Status: Original r21 exits QEMU after about 334 seconds without a terminal
execution record. The input and EFI remain unchanged, but no instruction count
or desktop result can be inferred. The baseline picker and NXARMJIT now request
watchdog disable immediately after service initialization and report the actual
result. An authored OVMF pair passes fifteen checks: a real two-second timer
is disabled before a three-second stall, while the armed control exits naturally
before completion. An injected DEVICE_ERROR is preserved exactly. UEFI requires
the boot manager to arm a five-minute watchdog before starting a boot image;
expiry remains a hypothesis for r21, not a confirmed cause. With the helper,
unchanged-input r22 produces a complete execution record after 413.518 seconds,
beyond the previous stop. Its next unsupported instruction is shifted-register
ORR. Duplicate success rows reflect console and serial output, not API call count. See
[watchdog validation](FIRMWARE_WATCHDOG_VALIDATION.md).

Target State: Request watchdog disable immediately after service initialization
in the baseline picker and NXARMJIT, before waiting for input or running a long
guest. Report success or the actual unsupported/error status; a failure must
not prevent otherwise usable firmware operation. Keep the host diagnostic time
limit and instruction budget intact. Use one shared helper and test it in actual
EFI by arming a short watchdog: the armed control must reset before its delayed
completion marker, while the helper path must reach that marker. Also exercise
the reported failure path without pretending that a failed disable succeeded.
No disk, NVRAM, guest instruction or memory-regime changes are part of this fix.
Public contract: https://uefi.org/specs/UEFI/2.11/03_Boot_Manager.html#load-option-processing

### Logical shifted-register execution

Current Status: Original r22 stops at shifted-register ORR after 42,252,452
retired instructions. The formerly missing general class is now implemented in
the native translator and Rust reference. Independent tests pass 64,512 native
cases, 768 actual Arm comparisons and 31 complete canonical regressions in each
of three cache modes. The immutable 98-file runtime also reproduces all six
captured Arm cases. Final EFI passes ten checks. Unchanged-original r23 then
retires 42,255,830 instructions and completes 6,012,249 data operations before
an unsupported scalar post-indexed LDR; its framebuffer remains zero.

Target State: Implement AND/BIC, ORR/ORN, EOR/EON and ANDS/BICS at both W and X
widths, with LSL, LSR, ASR and ROR applied to the second operand before optional
inversion. Register 31 means ZR in every operand position, never SP. W results
zero-extend; only ANDS/BICS update N/Z and clear C/V. Reject a W instruction with
imm6 bit 5 set before changing registers, flags, PC or retirement. Preserve
existing MOV alias behavior, all unrelated CPU state, fetch accounting and
precise rejection. Implement native execution and the Rust reference consistently.
Independent authored tests must cover eight operations, two widths, four shifts,
shift endpoints, sign bits, aliases/ZR, flags and reserved encodings. Compare
actual Arm results, native and reference state, then exercise all canonical
cache modes and final EFI before another unchanged-original replay. Original
instruction words and addresses remain private.

Primary encoding and execution reference:
https://github.com/qemu/qemu/blob/ae35f033b874c627d81d51070187fbf55f0bf1a7/target/arm/tcg/translate-a64.c#L7011-L7095

### Visible configuration recovery

Current Status: EFI `06b767498ba9af6d119b3600ce4a6aa44d0f81ee` displays a recovery
screen for missing, zero-length, malformed and empty-entry configuration. Enter
rereads the same configuration; Escape returns the original error. Ten authored
OVMF cases pass, including required display/input failures and optional screen
clear failure. The previous default binary fails the same recovery test, while
three existing picker regressions pass. The actual 1280 by 800 recovery screen
was captured and visually checked. Physical firmware input/display and macOS
startup remain unverified. See the [configuration recovery evidence](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/configuration-recovery/summary.json).

Target State: Show the exact configuration path and actual failure reason with
explicit Enter-to-retry and Escape-to-return actions. Retry only the same
`\EFI\OC\config.plist` on the current loaded-image file system and perform all
size and parse checks again. Do not search other volumes, choose an arbitrary
child, write files or NVRAM, or automatically retry/boot. A failed display write
or unavailable key-input service must return its actual error rather than
silently claim an interactive screen. Preserve valid configurations, ShowPicker
policy and child NOT_READY failure handling. Verify in actual OVMF that a first
read failure can recover through explicit input to the intended authored child;
also check persistent missing/empty/malformed/no-entry states, Escape, and
display/input failures without child execution. Use authored file-system
protocol wrappers or copied test media; never alter physical disks for this test.
Keep normal macOS readiness and the fixed original-replay binaries unchanged.

### Scalar immediate writeback

Current Status: ISE `fa5fe9e1b78cfce6b3bf0a0da82e68ece0704979` implements the
thirteen scalar pre/post-indexed forms. It passes 910 native cases with 3,432
assertions, 78 actual Arm comparisons against C and Rust, and 35 full provider
tests in each of three cache modes. Ten authored EFI checks pass. The preceding
unscaled suite also passes after removing its obsolete pre/post rejection
assertions. Original r24 passes the post-indexed LDR boundary and retires
42,255,878 instructions with 6,012,259 completed data operations before an
unsupported variable-register logical left shift. Its framebuffer still matches
zero RGB. Normal startup and physical boot remain unverified.

Target State: Admit pre-indexed and post-indexed forms of the thirteen supported
integer scalar transfers. Sign-extend the nine-bit byte offset without scaling;
pre-index uses base plus offset and post-index uses the original base. Commit
the updated base only after a successful transaction. Rn=31 uses SP and Rt=31
uses ZR; retain width/sign extension, flags, original-SP alignment checks,
translation/permission faults and exact store WnR classification. Reject
non-SP base/destination overlap as an explicit unsupported policy before data
access; do not claim this policy is the only architectural overlap behavior.
Keep unprivileged, SIMD, prefetch and reserved forms outside this addition.
Cover both indexing modes, every scalar form, signed offset endpoints, SP/ZR,
unaligned Normal transfers, page crossings and failure-before-writeback using
independent actual Arm/native/reference and all canonical cache modes. Only a
final EFI replay of unchanged original input can advance the observed boundary.

Primary encoding reference:
https://github.com/qemu/qemu/blob/ae35f033b874c627d81d51070187fbf55f0bf1a7/target/arm/tcg/a64.decode#L345-L390
Primary transaction/writeback ordering reference:
https://github.com/qemu/qemu/blob/ae35f033b874c627d81d51070187fbf55f0bf1a7/target/arm/tcg/translate-a64.c#L3079-L3138

### Variable-register shifts

Current Status: ISE `00243e65b934abb79c87719cd4ef06860c8489f2` implements all
four variable shifts and passes 16,464 native cases, 1,920 actual Arm comparisons
against C and Rust, and 31 full provider tests in each of three cache modes.
Ten authored EFI checks pass. Original r25 passes LSLV and retires 42,255,990
instructions with 6,012,273 completed data operations before a system-register
trap reading ID_AA64ZFR0_EL1. Its 1280 by 800 framebuffer still matches zero RGB.
Normal startup and physical desktop boot remain unverified. The next gate is
to reconcile this feature-register read with the advertised CPU feature profile;
returning a value must not advertise unimplemented vector execution support.

Target State: Implement LSLV, LSRV, ASRV and RORV for W and X registers. Use the
low five or six count bits respectively, including zero and counts above the
operand width. Rn, Rm and Rd use ZR semantics for register 31; W results clear
the upper half. Preserve SP and NZCV. Handle aliases by reading both operands
before writing the destination. Reject adjacent and reserved encodings without
retirement. Do not alter memory requests, CPU layout, readiness or cache keys.
The x86 emitter must preserve the CPU-pointer register if it uses CL for the
shift count. Validate every count, signed ASR and rotate boundaries, high count
bits, ZR and overlapping registers with independent actual Arm, native and Rust
reference execution. Compare canonical cached, uncached and small-slot results,
then consume the operations in authored EFI before an unchanged-original replay.

Primary execution reference:
https://github.com/qemu/qemu/blob/ae35f033b874c627d81d51070187fbf55f0bf1a7/target/arm/tcg/translate-a64.c#L7869-L7879
Width-specific shift and zero-extension reference:
https://github.com/qemu/qemu/blob/ae35f033b874c627d81d51070187fbf55f0bf1a7/target/arm/tcg/translate-a64.c#L6954-L6995

### Exact ZFR0 read in the bounded scalar profile

Current Status: ISE `401619acb1232a366af776bc1ecbfd04eb01631f` and EFI
`e7b90180d47383a34fbb43247b26809cd38f94f6` implement this exact read. Independent
validation passes 912 native assertions, 32 actual Cortex-A72 destination
vectors against C and Rust, 31 provider tests in each of three cache modes,
and ten authored EFI checks. The pinned EFI rebuild is byte-identical to the
tested candidate. The 110-file immutable runtime freeze passes six captured
cases, fourteen regressions and three negative controls. Original r26 passes
ZFR0 and retires 42,255,998 instructions with 6,012,275 data operations before
status 13 at MRS ID_AA64ISAR0_EL1. It completes in 122.167 seconds with unchanged
inputs and binaries. Its 1280 by 800 framebuffer hash matches zero RGB and GOP
readback. Physical macOS display remains unverified. The next gate is to
reconcile ISAR0 access and feature fields with the implemented scalar profile;
r25 stopped because native and Rust dispatch did not recognize ZFR0.
PFR0/PFR1 remain absent; no existing PFR read has
advertised a contradictory SVE value. Authored EL1 reads on QEMU 8.2.2 cortex-a72
return ZFR0=0. The same fixture on max,sve=off,sme=off returns nonzero ZFR0 despite
cleared PFR SVE/SME fields: that model initializes ZFR0 independently. Preserve
both observations; disabling QEMU options is not a universal zero-return oracle.

Target State: Define this runtime's bounded scalar profile as providing neither
SVE nor SME, and implement only the exact read-only ZFR0 MRS as zero at EL1
with its existing inactive HCR/SCR control contract. Preserve rejection of
nonzero unsupported controls, EL0, MSR writes and neighboring unsupported IDs.
Do not blanket-zero unknown system registers, invent PFR0/PFR1 values, advertise
vector execution, change CPU layout or ABI, or relax normal startup readiness.
Success follows XZR destination semantics, advances PC/retirement once and
preserves SP/NZCV and memory. Native direct execution, Rust reference and the
canonical provider must agree, including cached, uncached and small-slot paths.
Test exact instruction decoding, every destination, repeated reads, zero data
requests, rejected access/control cases and unchanged state on rejection. Add
authored EFI consumption before an unchanged-original replay. EL0 rejection is
the runtime's bounded policy, not proof of every FEAT_IDST trap configuration.

Arm DDI0616 B.a page 983 defines the encoding and separates EL1 reads from
applicable EL2 TID3 traps; literal HCR=0 in this software runtime is not an
assertion of the original hardware reset ABI. The two authored oracle runs use
EL2-absent machines and do not write HCR_EL2.
Primary access reference: https://documentation-service.arm.com/static/6526e1bd9e189a266cef8412
Version-matched model references:
https://github.com/qemu/qemu/blob/v8.2.2/target/arm/cpu64.c#L264-L275
https://github.com/qemu/qemu/blob/v8.2.2/target/arm/tcg/cpu64.c#L1141-L1151

### Exact ISAR0 read in the bounded scalar profile

Current Status: ISE `29413d9ca770c2b6e9487f91838452c7987f3a4e` and EFI
`2099d59fc42ec8c41a116b3ffe1a131ed1acc297` implement this exact read. Independent
validation passes 928 native assertions, 35 reference tests, 32 provider tests
per cache mode and rejection of 16 unsupported extensions. Thirty-two
Cortex-A72 model observations validate access/encoding/XZR/NZCV, with its
nonzero feature value retained separately from the software policy. ZFR0
regression tests and ten authored EFI checks pass. The preceding ZFR0 EFI
stops at the first ISAR0 read after 114 instructions in the same authored
fixture, while the new EFI reaches 65,536. The 114-file immutable freeze passes
six captures, fourteen regressions and three negative controls. Original r27
passes ISAR0 and retires 42,256,360 instructions with 6,012,373 data operations
before status 13 at MRS ID_AA64ISAR2_EL1. It completes in 106.090 seconds with
unchanged inputs and binaries. Its 1280 by 800 framebuffer hash matches zero
RGB and GOP readback; physical macOS display remains unverified. This adds
362 retired instructions and 98 data operations relative to r26.
The runtime does not implement the extensions described by its AES, SHA1,
SHA2, CRC32, Atomic, TME, RDM, SHA3, SM3, SM4, DP, FHM, TS, TLB or RNDR fields.
Baseline exclusives are not LSE; baseline TLBI is not the outer-shareable or
range extension; software CRC calculation is not guest CRC32 instruction
support. Existing ISAR1 reset values differ between C and Rust and remain a
separate issue; they are not the cause of this missing ISAR0 dispatch.

Target State: Add only exact read-only MRS ID_AA64ISAR0_EL1, S3_0_C0_C6_0.
Define each extension field as absent and the reserved low nibble as zero in
the explicit bounded software profile. Permit EL1 with live inactive HCR/SCR
controls; retain rejection of writes, other ELs, unsupported controls and
neighboring unknown registers. This policy does not claim full Arm-version
conformance or reproduce the original hardware's feature register. Preserve
XZR, SP/NZCV, memory and exact retirement semantics without changing CPU layout,
cache keys, PFR values or readiness. Independently test every destination,
live control changes after translation, rejected accesses and representative
unimplemented extensions in native, reference and all provider cache modes.
Authored EFI consumption must precede another unchanged-original execution.

Primary field reference: Arm Cortex-A520 Cryptographic Extension TRM section
2.2, table 2-2: https://documentation-service.arm.com/static/672e536f27eda361ad4da11a
Version-pinned field and feature predicates:
https://github.com/qemu/qemu/blob/ae35f033b874c627d81d51070187fbf55f0bf1a7/target/arm/cpu.h
https://github.com/qemu/qemu/blob/ae35f033b874c627d81d51070187fbf55f0bf1a7/target/arm/cpu-features.h
Read-only registration and access policy:
https://github.com/qemu/qemu/blob/ae35f033b874c627d81d51070187fbf55f0bf1a7/target/arm/helper.c
