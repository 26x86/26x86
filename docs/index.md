---
hide: [navigation, toc]
---
<div class="portal" data-portal-page="home" markdown>
<div class="portal-hero" markdown>
<span class="portal-eyebrow">26x86 / Open boot engineering</span>

# NextCore, in development.

Clean-room macOS boot engineering for standard UEFI systems. Track the latest evidence and what remains before a physical desktop.

<div class="portal-actions" markdown>
[Explore development progress](progress.md){ .portal-button }
[Check a Mac model](compatibility.md){ .portal-button .secondary }
</div>
</div>

<section class="portal-progress" aria-labelledby="development-progress" markdown>
<span class="portal-eyebrow">The work, in the open</span>

## Development progress

Verified steps. Explicit boundaries. A working desktop is the destination.

<div class="portal-boundary" data-progress-boundary markdown>
<span class="portal-badge">Current execution boundary</span>

### 16,384-instruction diagnostic budget reached

The bounded local macOS 27 kernel prefix reached its diagnostic budget after BFM support. No unsupported instruction stopped this run. Budget exhaustion does not establish forward boot progress or normal startup. Physical macOS desktop output remains unverified.

[Inspect the boot evidence](BOOT_RUNTIME_VERIFICATION.md)
</div>
<div class="portal-metrics" data-progress-metrics></div>
<div class="portal-milestones" data-progress-milestones markdown>
<article class="portal-step" markdown>
<span class="portal-step-number">01</span><span class="portal-badge verified">Authored tests</span>

### EFI selection & recovery

Selected child execution and optional presentation failures are exercised in OVMF. Essential failures remain visible and recoverable.

[Picker recovery evidence](BOOT_PICKER_RECOVERY.md)
</article>
<article class="portal-step" markdown>
<span class="portal-step-number">02</span><span class="portal-badge">In development</span>

### ARM execution

Instruction coverage advances through explicit native, reference and firmware checks. Original-input progress is reported separately.

[Explore instruction coverage](A64_STARTUP_COVERAGE_20260912.md)
</article>
<article class="portal-step" markdown>
<span class="portal-step-number">03</span><span class="portal-badge pending">Not verified</span>

### Physical desktop

Sustained kernel execution, userspace and visible desktop output on the target computer still need direct evidence.

[Understand the acceptance gates](BOOT_RUNTIME_VERIFICATION.md)
</article>
<article class="portal-step" markdown>
<span class="portal-step-number">04</span><span class="portal-badge pending">Later stage</span>

### Graphics acceleration

Firmware graphics and host GPU activity do not establish guest Metal support. Acceleration follows visible desktop output.

[Read graphics limitations](wiki/GPU-Limitations.md)
</article>
</div>

[View the complete progress record →](progress.md){ .portal-text-link }
</section>

<div class="portal-route-grid" markdown>
<article class="portal-route" markdown>
<span class="portal-eyebrow">Hardware reference</span>

## Know your Mac.

Find model identifiers, Apple support references and the separate NextCore evidence status.

[Open compatibility checker →](compatibility.md)
</article>
<article class="portal-route" markdown>
<span class="portal-eyebrow">Documentation library</span>

## Find your next step.

Browse setup guides, architecture, troubleshooting and the public evidence behind engineering decisions.

[Search the library →](library.md)
</article>
</div>

**Current Status:** Experimental boot engineering. Physical macOS desktop output is not verified. **Target State:** Reproducible boot and visible desktop output on physical hardware, followed by graphics acceleration.
</div>
