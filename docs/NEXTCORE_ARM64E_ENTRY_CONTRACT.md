# ARM64e startup contract and current diagnostic boundary

Current Status: Public startup paths are distinguished; normal target-specific
entry/platform requirements remain incomplete. SPTM applicability to the selected
j274 target is UNVERIFIED. Normal ARM64e entry is
`NOT_READY`; the opt-in original-prefix diagnostic always returns `ABORTED`.

Target State: A source-bound, target-specific live entry state that reaches XNU
initialization with real platform services, followed by sustained guest devices,
storage, display and userspace. See [progress](progress.md).

## Legacy entry versus SPTM entry

| Entry shape | Register meaning |
| --- | --- |
| Legacy ARM64 startup | A boot-argument pointer in x0 applies only to that documented path |
| Public SPTM cold startup | x0 selects startup mode; x1 carries traditional boot arguments; x2 carries SPTM arguments |
| Warm/resume/panic startup | Arguments depend on the selected path; do not reuse the cold table blindly |

Apple's pinned public [SPTM startup source](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm64/sptm/start_sptm.s)
saves the cold argument pointers and invokes SPTM during initialization. The
register distinction is a public interface observation, checked on 2026-09-12;
it does not establish the exact ABI of a particular unreleased image. A legacy
boot-argument codec cannot be relabeled a complete SPTM environment.

## Current implementation scope

The bounded trace uses the explicit `unprovisioned-sptm-prefix` profile. This
name describes a diagnostic assumption, not verified j274 SPTM applicability: x0 is
zero, x1 refers to the staged legacy boot arguments and x2/x3 are zero. Its boot
video fields are zero by default; the opt-in GOP path supplies owned framebuffer
storage and geometry. Its DeviceTree platform state remains incomplete. This
profile exists to expose the next architectural requirement; it is not normal
cold-boot provisioning. The 2026-09-12 manifest-only check found no SPTM/TXM
roles in the selected j274 build identities. That absence does not independently
prove either startup ABI; target applicability remains unverified. The existing normal entry retains its provider gate.

Checked memory services and authored stage-1/dynamic-MMU fixtures demonstrate
their own translated accesses. They do not supply the complete original platform
or make the legacy v1 memory path support MMU enablement. Keep the exact selected
runtime mode in every receipt.

## Fixup phase and bounded progress observation

The pinned public legacy [initialization source](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm/arm_init.c)
calls `arm_slide_rebase_and_sign_image()` before copying boot arguments. The
separately pinned SPTM startup also invokes that routine before its fixup-complete
operation. Opaque chained words preserved by Core therefore do not, on their
own, identify a missing loader transformation. Establish the executed phase and
the required pointer producer before proposing rebasing.

The [legacy startup](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm64/start.s)
consumes an incoming x0 boot-argument pointer. That contract applies only after
the actual entry is bound to this path. The symbolic SPTM entry reasons do not
establish numeric sentinel values or missing external argument structures.

The optional `arm-jit-memory-observation` build records the last 64 request
metadata entries through the unchanged memory service. It can distinguish
repeated addresses from advancing accesses at a fixed budget. It does not reveal
branch operands, prove correct pointer values or identify a startup ABI. Raw
original-image PCs and addresses remain isolated.

## Observed chain membership

A read-only traversal of the unchanged original file finds 1,010,443 encoded
format-8 nodes in 657 page chains, including 899,149 authenticated nodes. The two
successful eight-byte stores in the final 65,536-step request window match nodes
at zero-based traversal ordinals 2,722 and 2,723. The first node's saved next
field points exactly to the second location. This is stronger than adjacent
addresses alone, but it does not verify store values, all preceding execution,
complete chain traversal or the function's identity.

The pinned public [chain walker](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/mach/dyld_kernel_fixups.h)
saves each encoded word before overwrite and advances using its saved next
field. Format 8 uses four-byte units; format 11 uses byte units. The original
metadata traversal uses these published format rules and validates file backing,
unique visited nodes and termination. Raw locations and words remain isolated.
The nearby symbol is outside the metadata-defined containing function and is
not used to name it.

The workload size motivates a separately selected initialization diagnostic.
The larger ceiling only permits observing the next boundary. It does not enable
normal startup or claim correct rebasing. The public legacy caller also does not
check the chain walker's return value; completing that call alone would not
prove that every fixup succeeded.

[Sanitized membership evidence](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/original-chain-membership-summary.json)
records the scope explicitly.

## Alignment stop and entry memory regime

The initialization diagnostic stops after 1,542,930 retired instructions at an
ordinary 64-bit load whose address is four-byte aligned. The failing address is
encoded chain node 51,889. The preceding successful stores match nodes 51,887
and 51,888. Provider status is zero; this is a guest alignment fault, not a host
callback failure or an exhausted instruction budget.

Arm [AArch64 memory attributes and properties, 102376_0200_01_en](https://documentation-service.arm.com/static/63a43e333f28e5456434e18b),
sections 3.2 (page 11) and 12.1 (page 33), specifies the MMU-off Device default
without an applicable virtualization override and alignment faults for unaligned
Device accesses. Clearing SCTLR.A does not make Device data unaligned accesses
legal. The current M=0, HCR=0 provider fault is therefore consistent with its
selected contract and must not be suppressed.

The pinned public [legacy startup](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm64/start.s)
sets bootstrap translation tables and MAIR, writes the default SCTLR and executes
ISB before returning to arm_init. That public precondition is not equivalent to
the current MMU-off diagnostic. Establish how the actual outer entry relates to
this setup before providing a mapped entry profile. HCR.DC changes additional
virtualization behavior and is not an alignment-error bypass.

## Remaining acceptance requirements

- Target-specific argument layouts backed by authoritative public contracts.
- Live platform/service dispatch and lifecycle behavior; SPTM-specific fixup
  completion and services only where the target entry contract requires them.
- Owned DeviceTree and memory mappings with actual target consumers.
- Persistent storage and interrupt/device services after firmware transition.
- Persistent guest framebuffer presentation, input and userspace evidence.

Do not invent missing structures, substitute successful service replies or drop
unsupported instructions to extend a trace. Public XNU references alone do not
provide every external SPTM interface or establish that the selected target uses it.

[Design](NEXTCORE_DESIGN.md), [Build plan](NEXTCORE_BUILD_PLAN.md),
[runtime verification](BOOT_RUNTIME_VERIFICATION.md) and
[compatibility](compatibility.md) preserve the separate acceptance layers.
