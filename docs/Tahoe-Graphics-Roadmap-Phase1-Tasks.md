# Tahoe Graphics R&D — Phase 1 Execution Tasks

Task checklist for resolving graphics acceleration and display anomalies on legacy x86 GPUs under macOS 26 Tahoe:

1. [x] Isolate Safari pre-AVX WebKit crashes from display tint anomalies.
2. [x] Document CoreDisplay compositor transfer functions.
3. [x] Validate sRGB profile override as an immediate user-facing mitigation.
4. [ ] Implement automated LUT injection within the 26x86 display helper.
5. [ ] Verify Metal 3 feature levels across Polaris and Vega architectures.
