# macOS support

macOS support is tracked by release and by hardware capability. The same EFI
may have different results across releases, so reports must name both the
target release and the hardware configuration.

## Evidence labels

- `Static`: files, plist, package, or source checks completed.
- `Emulated`: behavior observed in a virtual or emulated environment.
- `Runtime`: behavior observed on the target operating system.
- `Physical`: behavior observed on the target physical hardware.

Only the highest directly observed layer should be reported. See the
[validation report](../../nextcore/VALIDATION.md) for the current Nextcore
evidence boundary.
