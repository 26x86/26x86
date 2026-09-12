# MacPro5,1 and Radeon RX Vega 64 reference profile

**Current Status:** Configuration reference, not physical boot or acceleration evidence.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

This is a configuration reference for a MacPro5,1-class machine with an older
Xeon CPU and Radeon RX Vega 64 targeting Tahoe. It is not a physical-boot,
Safari-fix, color-correction or storage-performance receipt.

A MacPro7,1 SMBIOS override changes the reported identity; it does not change the
physical model or prove that firmware was flashed. Record both identities and
the actual CPU/GPU/firmware revisions before evaluating the profile.

Earlier apply commands on this page selected an aggressive profile mode. Review
the current profile implementation and its proposed changes before invoking an
apply operation. No disk identifier or mitigation is universally appropriate.
Use a complete backup and external test media.

See [compatibility](../compatibility.md), [CPU notes](../wiki/Pre-AVX-Mac-Pro.md),
[display diagnostics](../wiki/Mac-Pro-Tahoe-Yellow-Screen.md) and
[installation boundaries](../wiki/Installation-Notes.md).
