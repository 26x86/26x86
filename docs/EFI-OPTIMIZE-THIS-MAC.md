# Preparing an EFI candidate for a specific machine

**Current Status:** Machine-specific preparation only; no reader disk identity is assumed.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

This guide does not identify the current reader's disks or certify an optimized
Mac profile. Earlier `/dev/disk0`, `/dev/disk1` and `/dev/disk2` assignments were
examples and must not be used as deployment targets. Disk numbering can change.

Record the actual physical model, reported SMBIOS, CPU features, GPU, storage
controllers, ESP and current OS build. A spoofed MacPro7,1 identifier is distinct
from MacPro5,1 hardware and from a firmware update. Multiple drives alone do not
establish a Fusion Drive arrangement.

Save the complete active EFI tree and configuration, then assemble a separate
candidate with its referenced drivers and kexts. Validate file contents and
package versions and review the differences. Use external media for the first
boot attempt and keep a working recovery route.

No automatic AVX-to-SSE bridge, APFS performance gain, framebuffer fix or tint
correction is established by this page. Record those as individual runtime
outcomes if demonstrated. See [compatibility](compatibility.md),
[configuration](wiki/Configuration.md) and [troubleshooting](wiki/Troubleshooting.md).
