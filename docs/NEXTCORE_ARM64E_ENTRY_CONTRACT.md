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
