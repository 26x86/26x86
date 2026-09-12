# Mac Pro display tint diagnostics

**Current Status:** Diagnostic procedure; a universal cause or repair is not established.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

A yellow/orange display is a symptom, not proof of a specific WindowServer,
CoreDisplay, LUT or GPU-descriptor defect. Earlier causal explanations on this
page were not tied to a reproducible build/device receipt and are not a verified
root cause. This guide does not promise a calibrated boot-time LUT injector.

Record the real GPU, display, cable/adapter, connector, macOS build and whether
the tint appears in firmware, Recovery, the login screen or only one session.
Compare a screenshot with a photograph: their difference can help distinguish
compositor output from the physical display path, but is not conclusive alone.

Inspect Night Shift, True Tone and the selected display color profile. Save the
current selection before trying a standard profile or another connector; report
the observed result for that setup rather than calling it a universal repair.
Keep CPU `SIGILL` investigation separate from color diagnosis.

For absent guest output, see [graphics limitations](GPU-Limitations.md) and
[current progress](../progress.md). EFI presentation is not persistent guest
scanout or Metal acceleration.

## Current evidence and hardware coverage

Reviewed for documentation freshness on 2026-09-12. See the
[portal](../index.md), [progress](../progress.md),
[compatibility catalog](../compatibility.md) and
[library](../library.md) for the active evidence boundary. Historical
receipts in this guide retain their original scope and date.
