# Known Issues

## Experimental T2 Support

While upstream Dortania OpenCore-Legacy-Patcher does not officially support Apple T2 hardware, 26x86 provides experimental support for macOS 15 Sequoia and macOS 26 Tahoe on T2 Macs.

### Current T2 Status

- **Keyboard & Trackpad:** Functioning via internal SPI bridge drivers.
- **Audio:** Working on selected models; ambient microphone arrays require ongoing verification.
- **Touch Bar:** Display functioning; custom touch strip events require AppleSilicon bridge stability.
- **Thermal Management:** Requires verification to prevent fans running at default high rpm.

## Pre-AVX CPU Architecture

- **Safari WebKit JIT:** Addressed via 26x86's custom RestrictEvents translation layer.
- **Third-Party Electron Apps:** Applications bundling modern Chromium binaries compiled with hard AVX requirements may crash on launch unless launched with software rendering flags (`--disable-gpu`).
