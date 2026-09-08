# Application

The NextCore application provides a guided workflow around EFI preparation,
diagnostics, and evidence collection.

## Modes

- **x86 Mac mode** prepares EFI and root-patch inputs for native hardware.
- **Apple Silicon Sandbox mode** is a contained diagnostic and research path;
  it does not imply host-kext or root-patch support.

## Safe operating pattern

Use the application with a backup, keep the target hardware identified, and
review the proposed file changes before transferring an EFI. For failures,
capture the log and identify the first failing layer before changing settings.
