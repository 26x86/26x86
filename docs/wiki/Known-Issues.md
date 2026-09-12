# Known issues and unresolved runtime work

**Current Status:** Normal startup, persistent devices and physical guest interaction remain incomplete.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

The current ARM64e macOS 27-on-x86 path has not reached a usable physical desktop.
[Progress](../progress.md) records the current instruction boundary and dated
receipts; [compatibility](../compatibility.md) records hardware evidence.

| Area | Current gap |
| --- | --- |
| Normal startup | Required live startup/platform providers cause `NOT_READY` |
| Bounded diagnostics | Original prefixes intentionally return `ABORTED` |
| SPTM applicability | Unverified for selected j274 inputs; conditional service contracts are incomplete |
| Memory/platform | Checked authored MMU paths do not supply the full original platform |
| Storage | Persistent guest storage/controller integration remains incomplete |
| Display/input | Persistent guest screen presentation and physical interaction unverified |
| Acceleration | Guest Metal is a later, separately measured milestone |

T2 keyboard, trackpad, audio, Touch Bar and thermal behavior require per-model
receipts. This guide does not claim those devices work merely because a fork or
profile names them. See [T2 notes](T2-Mac-Notes.md).

For pre-AVX crashes, inspect the actual faulting instruction and loaded binaries.
A boot argument or `--disable-gpu` cannot establish that every required CPU
instruction is available. See [CPU notes](Pre-AVX-Mac-Pro.md).
