# Troubleshooting by evidence layer

**Current Status:** Layer-specific diagnosis retains required runtime gates.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

Identify the first failing layer and preserve the exact build/configuration.
[Current progress](../progress.md) distinguishes known implementation gaps from
configuration errors; [compatibility](../compatibility.md) prevents treating a
listed model as a tested machine.

| Observation | First check |
| --- | --- |
| Missing EFI entry | Firmware architecture, actual ESP and complete file tree |
| Picker graphics unavailable | GOP mode/pixel format and text fallback; not guest GPU support |
| Normal ARM64e entry returns `NOT_READY` | Required provider list and startup contract |
| Bounded trace returns `ABORTED` | Intended diagnostic budget, stop family and precise fault state |
| More original instructions retire | Same input/profile and immutable code identity; no boot inference |
| Original boot stops after a supported instruction | Next architectural/platform requirement, not arbitrary NOP replacement |
| XNU runs but screen is blank | Userspace markers, framebuffer mapping and presentation lifetime |
| Data disappears after restart | Guest storage persistence and controller/provider evidence |
| Host GPU test passes | Guest device/Metal evidence remains a separate test |

For a useful report, include the public commit IDs, hardware/firmware identity,
OS build, selected execution mode, last successful layer and sanitized error.
Keep original image bytes and raw private traces out of public issues. Do not
change unrelated boot arguments or replace required services with success stubs.
