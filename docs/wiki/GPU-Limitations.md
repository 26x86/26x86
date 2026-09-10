# GPU Limitations and Acceleration Tiers

Current graphics acceleration support matrix for macOS 26 Tahoe on legacy x86 GPUs.

## GPU Support Tiers

### Tier 1: Fully Accelerated Metal 3 GPUs
- **Hardware:** AMD Radeon RX 400/500 series (Polaris), RX Vega 56/64, Radeon VII, Navi (RX 5000/6000 series).
- **Status:** Native Metal acceleration supported. Minor color management calibrations applied on select display connections.

### Tier 2: Legacy Metal GPUs (Under Active Development)
- **Hardware:** Intel HD Graphics 4000/5000/Iris (Ivy Bridge, Haswell), NVIDIA Kepler (GTX 600/700 series).
- **Status:** Requires backward compatibility shims for WindowServer compositor handoff.
- **Warning:** Forcing unaccelerated fallback paths without shims may lead to kernel panics or login loop stalls.

### Tier 3: Non-Metal Legacy GPUs
- **Hardware:** Intel HD 3000, NVIDIA Tesla/Fermi, AMD TeraScale.
- **Status:** Non-Metal acceleration is strictly experimental and not recommended for daily operation.
