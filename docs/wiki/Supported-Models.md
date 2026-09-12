# Hardware coverage and support evidence

**Current Status:** Hardware documentation coverage is distinct from verified NextCore support.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

The [compatibility catalog](../compatibility.md) is the starting point for model
families, official macOS eligibility and NextCore evidence. Those are separate
columns: a documented model or an Apple-supported OS does not establish a
successful NextCore installation.

No all-Mac or all-UEFI compatibility claim is made. The active physical target
for ARM64e macOS 27 on x86 is Samsung 750XHD; external-media boot, persistent
screen output and an interactive desktop remain acceptance requirements.

| Hardware context | Guide | Required evidence |
| --- | --- | --- |
| Older Mac Pro | [CPU capability notes](Pre-AVX-Mac-Pro.md) | Actual CPU flags, GPU and target build |
| Intel notebooks and desktops | [Configuration](Configuration.md) | Exact model, firmware, storage, input and sleep |
| Intel Macs with T2 | [T2 notes](T2-Mac-Notes.md) | Per-model security/recovery and bridge-device results |
| Apple Silicon Macs | [Sandbox](../APPLE_SILICON_SANDBOX.md) | Native VM result distinct from the x86 EFI product |
| General x86 UEFI hardware | [Progress](../progress.md) | Per-machine firmware and guest-runtime receipts |

A single successful boot does not certify upgrades, every GPU output, suspend,
networking or storage persistence. Record each demonstrated capability and its
build, configuration and test date.
