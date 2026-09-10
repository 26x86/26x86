# 26x86 Research Executive Summary

> **Project:** macOS 26 Tahoe on x86 Macs  
> **Date:** September 4, 2026

## Executive Summary

1. **Mission:** Enable stable, performant operation of macOS 26 Tahoe on legacy x86 Macintosh hardware through clean-room boot engineering and hardware compatibility layers.
2. **Key Discoveries:**
   - **Safari Pre-AVX Crashes:** Caused by direct AVX opcodes (`vmovaps`) emitted by WebKit JIT trampolines on pre-AVX Intel Xeon CPUs. Resolved via active instruction translation in `RestrictEvents`.
   - **WindowServer Yellow/Orange Tint:** Caused by CoreDisplay compositor mismatches with legacy GPU gamma tables, rather than AVX deficiencies. Resolved through color profile calibration and linear LUT injection.
   - **Clean-Room Boot Stack (NextCore):** Built from scratch in Rust to provide an open, maintainable UEFI bootloader replacing legacy patcher mechanisms.
