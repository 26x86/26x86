# Installation and Upgrade Notes

## Supported Installation Paths

- **Clean Installation:** Erasing the target APFS volume and installing macOS 26 Tahoe from prepared media is the primary, officially tested path.
- **Official Upgrade:** Upgrading an existing, unmodified macOS installation (e.g. macOS 14 Sonoma or macOS 15 Sequoia) is fully supported.
- **Unsupported:** Systems with pre-existing legacy root modifications from older tools (such as Patched Sur or bigmac) **cannot be upgraded directly** due to APFS snapshot sealed system volume corruption. A clean installation is required.

## Transitioning from Other Patchers

1. Revert any pre-existing root volume patches using your previous tool's uninstaller.
2. Remove older LaunchAgents and privileged helper tools.
3. Deploy the 26x86 EFI configuration to the EFI partition.
4. Reboot through the new EFI boot picker and proceed with the macOS 26 installation or upgrade.
