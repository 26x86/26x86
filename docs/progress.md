---
hide: [toc]
---
<div class="portal" data-portal-page="progress" markdown>
<span class="portal-eyebrow">Development / Evidence ledger</span>

# Progress you can inspect.

Each milestone has its own acceptance gate. Passing a firmware test does not establish kernel, userspace or physical display success.

**Development channel:** These latest runtime results belong to [PR #19](https://github.com/26x86/26x86/pull/19) and its pinned module branches. Publishing this documentation does not merge that runtime into `main` or release a bootable macOS system. Use the [explicit development checkout](wiki/Nextcore-Modules.md#clone-and-build) to reproduce it.

<div class="portal-boundary" data-progress-boundary markdown>
<span class="portal-badge">Current execution boundary</span>

## 16,384-instruction diagnostic budget reached

The bounded local macOS 27 kernel prefix reached its diagnostic budget after BFM support. No unsupported instruction stopped this run. Budget exhaustion does not establish forward boot progress or normal startup. The next check must distinguish a repeated loop from meaningful advancement.

[Reviewed r8 summary](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/original-prefix-r8-summary.json) · [Acceptance criteria](BOOT_RUNTIME_VERIFICATION.md)
</div>

<div class="portal-metrics" data-progress-metrics></div>

## Evidence by layer

<div class="portal-milestones" data-progress-milestones markdown>
<article class="portal-step" markdown>
<span class="portal-badge verified">Authored firmware tests</span>

### EFI picker & child execution

OVMF exercises selection, failure reporting, return to the picker and optional display fallback.

[Read picker recovery](BOOT_PICKER_RECOVERY.md)
</article>
<article class="portal-step" markdown>
<span class="portal-badge">Active development</span>

### ARM64 translation

Native execution, reference semantics and authored EFI fixtures constrain each increment. Original-input progress has a separate record.

[Instruction coverage](A64_STARTUP_COVERAGE_20260912.md)
</article>
<article class="portal-step" markdown>
<span class="portal-badge verified">Authored firmware display</span>

### Owned guest framebuffer → GOP

An authored guest reads the encoded boot-video fields and writes its reserved framebuffer. Nine checks pass at 1280 by 800 pixels, including exact RGB readback from GOP. A separate run without GOP completes the 64-instruction CPU diagnostic while video reports `NOT_FOUND`; it does not pass video validation.

This connects guest memory to firmware output. Persistent presentation, firmware-exit lifetime, normal startup and a physical macOS desktop remain unverified.

The original local kernel prefix also accepts the owned video buffer and reaches the same 16,384-instruction budget. Its screen hash still matches a zero-filled frame; no kernel-generated visible output has been established.

[Framebuffer contract and validation](BOOT_FRAMEBUFFER_VALIDATION.md)
</article>
<article class="portal-step" markdown>
<span class="portal-badge pending">Not verified</span>

### Kernel → userspace → display

An ordered boot transcript and direct physical display evidence are required for a successful macOS boot claim.

[Runtime acceptance gates](BOOT_RUNTIME_VERIFICATION.md)
</article>
</div>

## Latest reviewed updates

<div data-progress-latest markdown>
Follow the [public validation ledger](https://github.com/26x86/26x86/blob/main/nextcore/VALIDATION.md) for pinned revisions, exact proof scope and replay results. The [repository history](https://github.com/26x86/26x86/commits/main/) records published changes.
</div>

## What a completed milestone requires

| Milestone | Required evidence |
| --- | --- |
| Firmware behavior | Real UEFI target build and explicit runtime checks |
| Boot framebuffer connection | Guest reads encoded video fields, writes owned storage and matches actual GOP readback |
| Original-input advancement | Replay with final source revision and exact stopping boundary |
| macOS boot | Ordered early boot, XNU and userspace markers from the same run |
| Physical desktop | Direct verification on the identified target computer |
| Graphics acceleration | Guest driver and rendering evidence beyond firmware output |

**Current Status:** Experimental, with distinct verified and unverified layers. **Target State:** Repeatable physical macOS desktop output, then accelerated graphics.
</div>
