# macOS compatibility and evidence

**Current Status:** Official model eligibility and project runtime evidence are tracked separately.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

Use the [compatibility catalog](../compatibility.md) for official Apple model
eligibility and the independently tracked NextCore result. The catalog links
its public sources; model coverage is not a runtime support promise.

| Evidence | What it establishes |
| --- | --- |
| Source/build/CI | The named source and checks passed |
| Authored CPU or firmware fixture | The exercised instruction, provider or EFI behavior |
| Original-input prefix | Bounded execution reached a reported architectural boundary |
| XNU and userspace | Ordered target-matching runtime markers in the same run |
| Physical display and interaction | Visible guest output and working input on the named machine |
| Guest acceleration | Guest API device, commands, synchronization and readback |

An EFI picker screen is not a macOS screen. Host Vulkan compute is not guest
Metal. A VM on a physical Apple Silicon host is still a VM result. Record these
as distinct observations rather than a single highest-level support label.

Tahoe Recovery/Terminal observations belong to the documented original-booter
QEMU/OVMF path. The active ARM64e macOS 27-on-x86 work remains incomplete; normal
entry is `NOT_READY` and bounded diagnostics return `ABORTED`. See
[current progress](../progress.md) and [runtime gates](../BOOT_RUNTIME_VERIFICATION.md).
