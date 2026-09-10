# EFI Optimization Guide for Physical Mac Systems

Reference hardware configuration: Fusion Drive (HDD + SSD), flashed MacPro7,1 SMBIOS on physical MacPro5,1 architecture, Dual Intel Xeon X5675 (Pre-AVX), AMD Radeon RX Vega 64.

## Disk Architecture

- `/dev/disk0`: High-speed PCIe NVMe SSD (APFS container for macOS Tahoe system and applications).
- `/dev/disk1`: High-capacity SATA HDD (Data and archival storage).
- `/dev/disk2`: EFI system partition (FAT32, containing OpenCore / NextCore bootloader).

## Backup Paths

Before applying optimizations, create full block-level backups of:
- Primary EFI partition: `/Volumes/EFI/EFI/`
- Current boot configuration: `/Volumes/EFI/EFI/OC/config.plist`
- NVRAM variable dumps: `nvram -xp`

## Applied Optimizations

### 1. Flashed Mac Pro Compatibility
- Enforce clean SMBIOS spoofing (MacPro7,1) to allow macOS Tahoe kernel acceptance without tripping prohibited symbol checks.
- Prevent circular path traversal during APFS container resolution.

### 2. Pre-AVX CPU Instruction Translation
- Inject `RestrictEvents.kext` with the WebKit JIT AVX-to-SSE instruction bridge.
- Set `boot-args` parameter `revpatch=jsc`.

### 3. Vega 64 Color Profile & Framebuffer Alignment
- Set custom display device property injections in OpenCore `DeviceProperties` to ensure clean framebuffer initialization without tint anomalies.
