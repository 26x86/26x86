# ⚠️ Hardware Warnings & Operational Notice

This document consolidates critical warnings and operational precautions. Review thoroughly before deploying 26x86.

> [!WARNING]
> 26x86 is experimental, community-developed software. Always create full data backups on independent storage media before modifying EFI partitions or applying operating system upgrades.

## Incompatible Hardware Configurations

1. **Pre-SSE4.2 CPUs:**
   - Systems lacking SSE4.2 (such as MacPro3,1 with Core 2-based Xeon 5400 series) cannot execute the macOS 26 Tahoe kernel.
2. **Locked Firmware & T2 Activation:**
   - Never attempt to bypass firmware passwords or Activation Lock using 26x86. T2 machines must be in an unlocked, administrative state.

## Safety Guidelines

- Test new EFI builds using an external USB flash drive before flashing internal disk partitions.
- Keep a working macOS Recovery USB drive on hand to restore boot configurations if needed.
