# MacPro5,1 Pre-AVX + RX Vega 64 → macOS Tahoe Profile (Track K)

Reference physical host: Flashed Mac Pro (5,1 class), Pre-AVX Xeon CPU, AMD Radeon RX Vega 64, targeting macOS 26 Tahoe.

## CLI Execution

```bash
python -m x86.profiles apply macpro5-vega64-tahoe --extreme   # Or with X86_EXTREME=1
```

Equivalent direct invocation:
```bash
python -m x86.profiles.macpro5_vega64_tahoe apply --extreme
```

## Profile Specification

| Property | Value |
|----------|-------|
| Target Model | MacPro5,1 (Flashed MacPro7,1 SMBIOS for firmware handoff) |
| CPU Architecture | Intel Westmere / Nehalem (Pre-AVX, SSE4.2 only) |
| GPU | AMD Radeon RX Vega 64 (GCN 5 / Vega architecture) |
| Target OS | macOS 26 Tahoe |
| Applied Mitigations | Safari pre-AVX opcode patch, WindowServer color profile correction, APFS Fusion optimization |
