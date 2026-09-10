# iBoot → XNU Handoff Contract

This specification governs the **Apple boot-chain evidence verification tier**.

## Sequential Verification Hierarchy

Execution is deemed valid if and only if the following milestones are sequentially observed in uninterrupted UART transcripts:

1. **Firmware Entry:** AVPBooter / iBSS initialization.
2. **Stage2 Execution:** iBoot Stage2 banner and command prompt.
3. **Kernel Transfer:** `Darwin Kernel Version` matching the requested target major release.
4. **Userspace Initialization:** Sequential emergence of `launchd`, `loginwindow`, and `WindowServer`.

Any session terminating prior to userspace emergence remains classified as protocol boundary research.
