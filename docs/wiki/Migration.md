# Migrating to 26x86

This document describes the migration procedure when moving from official OpenCore Legacy Patcher (OCLP) or other community variants to 26x86.

> For configuration paths: see [Configuration.md](./Configuration.md).

## Architectural Differences

| Subsystem | Legacy Patchers | 26x86 |
|-----------|-----------------|-------|
| Configuration | `~/Library/Application Support/OpenCore-Legacy-Patcher/` | `~/Library/Application Support/26x86/` |
| LaunchAgent | `com.dortania.opencore-legacy-patcher.*` | `com.26x86.*` |
| macOS 26 Support | Limited / Community patches | First-class clean-room boot stack (NextCore) |
| Pre-AVX Strategy | Static feature masking | Active WebKit JIT instruction translation |

## Migration Steps

1. **Clear Legacy Services:**
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.dortania.opencore-legacy-patcher.auto-patch.plist 2>/dev/null
   rm -f ~/Library/LaunchAgents/com.dortania.opencore-legacy-patcher.*
   ```
2. **Deploy 26x86:**
   - Launch 26x86 via `26x86.command`.
   - Select **Build and Install OpenCore/NextCore to Target Disk**.
   - Select the target EFI partition.
3. **Reboot:**
   - Hold Option during reboot and select the newly installed EFI Boot option.
