# Public architecture

**Current Status:** Executable bounded CPU/provider work; sustained physical guest execution incomplete.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

The product target is ARM64e macOS execution on an x86_64 machine entered through
UEFI. The current implementation has executable instruction/provider fixtures
and bounded original-input diagnostics; a usable physical guest is not complete.
See [current progress](../progress.md) and [compatibility](../compatibility.md).

```text
UEFI firmware
  -> NextCore picker / explicit child EFI loader
  -> clean-room guest staging and architecture-specific entry
  -> A64-to-x86 generated execution + checked memory/platform providers
  -> persistent guest devices and storage
  -> XNU, userspace, visible display and input
```

The latter transitions remain independent acceptance gates. Normal ARM64e entry
returns `NOT_READY`; opt-in bounded diagnostics return `ABORTED`. A trace's
increasing retired-instruction count is not normal startup readiness. The
[entry contract](../NEXTCORE_ARM64E_ENTRY_CONTRACT.md) distinguishes legacy
boot arguments from SPTM startup and identifies missing live services.

GOP/text output is a firmware presentation surface. Persistent guest framebuffer
mapping and post-firmware display ownership remain incomplete, as do sustained
storage/platform integration and guest Metal. A host GPU test does not satisfy
those contracts. Display and input precede acceleration in the active milestone.

External OpenCore preparation and original-booter Tahoe Recovery observations
are separate paths with their own source attribution and evidence. The VSK
service-cell design and Apple Silicon/VMApple research likewise have their own
scope; their policies must not silently replace NextCore's current x86 target.

Read [Design](../NEXTCORE_DESIGN.md), [Build plan](../NEXTCORE_BUILD_PLAN.md) and
[Module repositories](Nextcore-Modules.md) for contracts, phases and source ownership.

SPTM applicability to the selected j274 target is unverified. The diagnostic
profile name does not establish its normal startup ABI; see the
[entry contract](../NEXTCORE_ARM64E_ENTRY_CONTRACT.md).
