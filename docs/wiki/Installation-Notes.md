# Installation and upgrade boundaries

**Current Status:** No universal clean-install or upgrade support is established.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

There is no verified general NextCore macOS 27 installation or upgrade path.
A successful configuration build, a boot picker or an original-input trace does
not authorize erasing a disk. Read [compatibility](../compatibility.md) and
[current progress](../progress.md) before choosing a workflow.

For the separate external OpenCore workflow, installation feasibility depends
on the exact Mac, OS build, firmware, GPU and existing system modifications.
Neither clean installation nor an in-place upgrade is universally certified by
this repository. Existing root patches require their own tool's documented
reversal and upgrade procedure; this page does not diagnose snapshot corruption
from the mere presence of another patcher.

1. Identify the actual target disk and partition using current hardware output.
2. Save a verified backup and a working external recovery/boot route.
3. Review the complete candidate configuration and referenced files.
4. Test external media before considering internal EFI replacement.
5. Record installer, reboot, storage persistence, guest display and input results
   for the exact configuration. Stop at the first unimplemented runtime boundary.

For tool migration, use [Migration](Migration.md). Application setup belongs in
[Setup](../SETUP.md), not in an OS installation-success claim.
