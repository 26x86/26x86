# Pre-AVX Mac Pro (MacPro5,1 / 6,1)

**26x86 Phase 1** — Mac Pro 5,1 / 6,1 Pre-AVX detection, Metal branch hints, and automated Safari 26 Pre-AVX RestrictEvents application.

> [!IMPORTANT]
> Safari `SIGILL` (AVX opcode crash) and WindowServer display tint (yellow/orange tint) stem from **completely separate root causes and require different remediations.** This document addresses the Safari and AVX instruction pathway. For compositor tint, refer to [Mac-Pro-Tahoe-Yellow-Screen.md](./Mac-Pro-Tahoe-Yellow-Screen.md).

## Quick Verification

Run detection to inspect pre-AVX CPU flags:

```bash
python3 -m x86 detect --json
```

Output includes the following fields:

| Field | Description |
|-------|-------------|
| `cpu_model` | CPU model string (e.g. `Intel(R) Xeon(R) CPU X5675 @ 3.07GHz`) |
| `has_avx` | AVX instruction support (`false` on MacPro5,1 Westmere/Nehalem) |
| `is_pre_avx_macpro` | Mac Pro 5,1/6,1 without AVX support |
| `auto_pre_avx_patch` | Automatic pre-AVX fix status (`true` by default) |
| `recommended_boot_args` | Recommended boot-args (`revpatch=jsc` added automatically) |

## Safari 26 Pre-AVX Fix

- **Problem:** Safari 26.6.1 WebContent executes AVX instructions (`vmovaps`) in WebKit JIT on CPUs without AVX, resulting in `EXC_BAD_INSTRUCTION` (`SIGILL`).
- **Solution:** 26x86 automatically replaces `RestrictEvents.kext` with the pre-AVX instruction patch build and injects `revpatch=jsc` into NVRAM `boot-args`.
- **Target Systems:** MacPro5,1 (and early MacPro6,1 configurations without AVX).
- **Details:** See [Safari-PreAVX-Fix.md](./Safari-PreAVX-Fix.md).

## Configuration Options

In `config.json` or `com.26x86.plist`:

```json
{
  "General": {
    "AutoPreAVXPatch": true
  }
}
```

When set to `false`, automated RestrictEvents substitution and `revpatch=jsc` injection are disabled.

## Validation Checklist

1. Verify `has_avx: false` via `python3 -m x86 detect --json`.
2. Build EFI: verify `RestrictEvents.kext` is injected and `boot-args` contains `revpatch=jsc`.
3. Boot macOS 26 Tahoe: launch Safari, open complex websites, and verify WebContent does not trigger `SIGILL`.
