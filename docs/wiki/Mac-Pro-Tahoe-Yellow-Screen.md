# Mac Pro · macOS 26 Tahoe Display Tint (WindowServer)

Safari crash issues (AVX `SIGILL`) and **full-screen yellow/orange display tinting** are separate problems. For Safari crashes, refer to [Pre-AVX-Mac-Pro.md](./Pre-AVX-Mac-Pro.md).

This document details the root causes and recommended mitigations for the **WindowServer / CoreDisplay compositor** tint on macOS 26 Tahoe.

## Root Cause Analysis

The yellow/orange screen tint is **unrelated to AVX** and is **not solely a GCN LUT (Look-Up Table) issue:**

1. **WindowServer Compositor Pipeline:** macOS 26 Tahoe introduced updated CoreDisplay color management paths that expect modern Metal display pipelines with specific hardware transfer functions.
2. **Legacy GPU Descriptors:** On legacy AMD (GCN) and legacy Nvidia GPUs, default gamma ramps and color spaces are misinterpreted during compositor handoff, applying an unintended color matrix transformation.
3. **Color Profile Mismatch:** The default display profile applied during first boot lacks the calibrated EOTF expected by Tahoe's compositor.

## Recommended Mitigations

1. **Display Profile Reset:**
   - Open System Settings → Displays.
   - Change the color profile from the active profile to **sRGB IEC61966-2.1** or **Generic RGB**.
   - In most cases, selecting standard sRGB immediately clears the yellow cast.
2. **Night Shift & True Tone Check:**
   - Ensure Night Shift is toggled OFF.
   - On systems reporting false ambient light sensors, disable automated schedule tinting.
3. **Hardware LUT Injection:**
   - When using 26x86, enable the display profile fix in `config.json` to inject a calibrated linear identity LUT during boot.
