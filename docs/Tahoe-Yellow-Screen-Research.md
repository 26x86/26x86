# macOS Tahoe Display Tint & Compositor Research

Investigation into the root cause of yellow and orange full-screen display tints observed on macOS 26 Tahoe when running on legacy AMD and NVIDIA graphics hardware.

## Findings

1. The anomaly is distinct from CPU instruction faults (such as AVX `SIGILL`).
2. Stemming from CoreDisplay pipeline changes that assume modern Apple Silicon or Metal 3 transfer functions, legacy GPU LUT tables are misinterpreted during scanout handoff.
3. Overriding the display color profile to standard sRGB or injecting identity linear LUTs eliminates the discoloration.
