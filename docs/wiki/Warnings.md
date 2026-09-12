# Hardware and deployment precautions

**Current Status:** Deployment precautions require actual hardware and recovery context.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

Experimental firmware and OS work needs a known recovery path. Read
[compatibility](../compatibility.md) and [installation boundaries](Installation-Notes.md)
for the exact model/build before changing disks or firmware configuration.

- Save a verified backup on independent storage and preserve the complete working EFI.
- Identify the actual disk and ESP from current hardware output; sample identifiers are not targets.
- Test a candidate on external media before replacing internal boot files.
- Check actual CPU features and the selected runtime's requirements. This page does
  not certify that every CPU with a named feature can run Tahoe or Golden Gate.
- Firmware passwords, activation and security policies remain platform requirements.
  Do not change them or SIP based on a generic compatibility claim.

A fallback presentation path may keep the EFI picker usable when optional
protocols fail. It cannot safely skip a missing instruction, storage service or
SPTM contract. Preserve unsupported/error outcomes and consult
[troubleshooting](Troubleshooting.md).
