# Intel Mac systems with T2

**Current Status:** T2 support remains per-model and unverified without matching receipts.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

T2-equipped models require model-specific firmware, recovery, security-policy
and bridge-device evidence. This repository does not establish universal T2
keyboard, trackpad, audio, Touch Bar or thermal support on Tahoe or Golden Gate.
Use the [compatibility catalog](../compatibility.md) for official eligibility
and separately recorded NextCore status.

Do not disable SIP, change Secure Boot policy or alter recovery/firmware settings
as a generic prerequisite from this guide. A change must follow the documented
requirements of the exact tool, OS build and machine, with a known recovery path.
An EFI configuration value alone does not prove that a security policy took effect.

Record the actual model and firmware versions, ownership/unlock state, external
boot policy, input devices, audio and thermal behavior. Preserve an independent
backup before an OS or firmware update. See [known issues](Known-Issues.md) and
[installation boundaries](Installation-Notes.md).
