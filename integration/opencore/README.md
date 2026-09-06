# Native Apple Silicon Sandbox integration

This change belongs to the EFI loader and configuration layers. It selects a
compiled x86-64 EFI engine with `LoadImage` and `StartImage`; it does not invoke
Linux or QEMU as its runtime. AIC and iBoot are invariants of handoff version 1.
GIC, an ARM UEFI guest, or a different boot protocol are rejected.

## Configuration

`Docs/Sample.plist` and `Docs/SampleCustom.plist` contain disabled defaults. The
two new root dictionaries are optional for existing OpenCore configurations.
An exported fragment must be merged into a complete OpenCore configuration.

`AppleSiliconSandbox` has these fields:

- `Enabled`: boolean, default `false`.
- `TargetMajor`: integer, `26` or `27`, default `26`. This is a requested target,
  not a statement that either macOS version has booted in the native engine.
- `InterruptController`: string, exactly `AIC`.
- `BootProtocol`: string, exactly `iBoot`.
- `EnginePath`: absolute EFI path, default `\EFI\26x86\Sandbox.efi`.
- `IBootPath`: absolute EFI path to the user's original iBoot input; empty by
  default and required when enabled. The loader opens it only in read mode,
  rejects an empty file or directory, and leaves payload verification to the
  engine. File availability is not Apple signature verification.
- `Hardware.MemorySizeMiB`: integer, `4096..1048576`, default `4096`.
- `Hardware.CPUCount`: integer, `1..64`, default `2`.
- `Hardware.DeviceProperties`: device-key dictionaries containing property-key
  scalar values (`data`, UTF-8 `string`, unsigned 64-bit `integer`, `boolean`).
  This is guest device configuration, separate from host `DeviceProperties`.

`SandboxSMBIOS` contains `SystemProductName`, `SystemSerialNumber`, `SystemUUID`,
and `BoardProduct`. Defaults are empty; enabled mode requires all four and a
canonical `8-4-4-4-12` hexadecimal UUID. No Apple identity is invented. These
fields describe the requested guest identity; they neither attest the host nor
cause the loader to rewrite host SMBIOS tables.

Paths are printable ASCII, at most 191 characters, on the **same EFI volume as
OpenCore**. Relative paths, empty path components, slash/colon, and `.`/`..`
components are rejected. Identity strings and device/property keys are printable
ASCII, at most 255 characters. Maps have at most 4096 entries each; each data
value is at most 1 MiB. Each serialized XML document, including its trailing NUL,
is at most 1 MiB. The runtime serializer rejects an oversized combined document.

DeviceProperties is serialized to `<data>` using OpenCore's usual representation:
strings include a trailing NUL; booleans occupy one byte; integers through
`UINT32_MAX` occupy four little-endian bytes, and larger unsigned integers occupy
eight. Sandbox-specific parsing prevents the original generic OC 32-bit integer
truncation and decodes XML's five named entities before serialization. Numeric
or unknown entity references in manually authored Sandbox XML are rejected.
As in OpenCore maps, keys beginning with `#` are comments.

## Selection and ABI

After reading the config and applying existing vault requirements, enabled mode
enters `OcSandboxBoot` before the host NVRAM, UEFI quirks, ACPI, PlatformInfo,
DeviceProperties, kernel hooks, or normal boot picker. Early configured drivers,
Shim retain, and forced NVRAM initialization are also skipped in this mode.
Logging/serial setup and configured firmware watchdog behavior remain available.
All parse errors now stop firmware startup, including malformed `Enabled`; they
cannot fall through to legacy boot using a default false value.

The loader uses the firmware's normal `LoadImage` path, so it does not install an
image-authentication bypass. This does not claim that external engine files are
covered by an OpenCore vault rooted under a different path; the configured vault
and firmware image authentication remain their existing, distinct mechanisms.

`Include/Acidanthera/Library/OcSandboxBoot.h` defines a 64-byte, version 1 ABI,
matching `sandbox/efi/handoff.h` in 26x86. The wire fields, in order, are:

1. `UINT64 Magic = 0x3149424146583632` at offset 0.
2. `UINT32 Version = 1`, `UINT32 Size = 64` at offsets 8 and 12.
3. `UINT64 Flags = 0`, `UINT64 MemoryBytes` at offsets 16 and 24.
4. `UINT32 CpuCount`, `UINT32 TargetMajor` at offsets 32 and 36.
5. `UINT64 IBootPath`, `SmbiosXml`, `DevicePropertiesXml` at offsets 40, 48, 56.

`EFI_LOADED_IMAGE_PROTOCOL.LoadOptions` points to this record, and
`LoadOptionsSize` is exactly 64. The first pointer is a NUL-terminated CHAR16
absolute iBoot path; the other pointers are NUL-terminated UTF-8 plist documents.
OpenCore owns the record and pointed-to storage through `StartImage` return.
It requires an EFI application (`EfiLoaderCode`). Firmware unloads an application
when its entry point returns. The loader then frees allocated storage without
dereferencing the old loaded-image protocol or unloading that image again.
Load failures before `StartImage` still clean up the created image. Return-status
logs occur after cleanup because OpenCore's configured `HaltLevel` may stop
inside the logger. X86-32 handoff is rejected.

The API contract is based on the UEFI specification's
[Loaded Image protocol](https://uefi.org/specs/UEFI/2.9_A/09_Protocols_EFI_Loaded_Image.html)
and [image services](https://uefi.org/specs/UEFI/2.10_A/07_Services_Boot_Services.html).

The current engine returns **EFI_UNSUPPORTED** for the configured iBoot/AIC
platform runtime. CPU subset/JIT or AIC model tests are separate acceptance
results. An image load or return does not establish original iBoot execution,
macOS boot, a supported device tree, display acceleration, or native Mac support.
Failure stays in the selected mode; it does not select a different OS silently.

## Reproduce the build and parser tests

Validated source baselines:

- 26x86 OpenCore fork: `6a65d9bd39bbb5d843b1f2d42b0f16e8d3a44e0e`, plus this diff.
- [Acidanthera audk](https://github.com/acidanthera/audk):
  `0672a009e9ca85753d240324d761341adf0291b3`, recursively pinned submodules.
- Ubuntu 24.04, GCC 13, NASM, Python 3; X64 DEBUG GCC EFI build.

Initialize audk submodules and build its BaseTools. **audk itself includes an
OpenCorePkg submodule**: do not build that unchanged package accidentally. Use a
separate workspace with the modified package at its `OpenCorePkg` path:

```sh
set -eu
git -C "$AUDK" submodule update --init
make -C "$AUDK/BaseTools" -j8
mkdir -p "$NATIVE_WORKSPACE"
ln -s "$MODIFIED_OPENCORE" "$NATIVE_WORKSPACE/OpenCorePkg"
export WORKSPACE="$NATIVE_WORKSPACE"
export PACKAGES_PATH="$AUDK"
export EDK_TOOLS_PATH="$AUDK/BaseTools"
cd "$WORKSPACE"
. "$AUDK/edksetup.sh" BaseTools
test "$(readlink -f OpenCorePkg)" = "$(readlink -f "$MODIFIED_OPENCORE")"
build -p OpenCorePkg/OpenCorePkg.dsc \
  -m OpenCorePkg/Application/OpenCore/OpenCore.inf -a X64 -b DEBUG -t GCC -n 8
build -p OpenCorePkg/OpenCorePkg.dsc \
  -m OpenCorePkg/Application/Bootstrap/Bootstrap.inf -a X64 -b DEBUG -t GCC -n 8
strings Build/OpenCorePkg/DEBUG_GCC/X64/OpenCore.efi | grep 'AppleSiliconSandbox'
strings Build/OpenCorePkg/DEBUG_GCC/X64/OpenCore.efi | grep 'OCSB: StartImage ABI'
```

The EFI outputs are `Build/OpenCorePkg/DEBUG_GCC/X64/OpenCore.efi` and
`Bootstrap.efi`. Place Bootstrap at `EFI/BOOT/BOOTX64.EFI`, OpenCore at
`EFI/OC/OpenCore.efi`, and the full config at `EFI/OC/config.plist`. Copying
OpenCore itself to the fallback path instead requires its config alongside that
copy. In the modified
OpenCore checkout, set `AUDK` to the absolute audk path and run:

```sh
make -C Utilities/ocvalidate -j8 UDK_PATH="$AUDK" WERROR=1
make -C Utilities/SandboxConfigTest -j8 UDK_PATH="$AUDK" WERROR=1
python3 Tests/SandboxConfig.py
python3 Library/OcConfigurationLib/CheckSchema.py \
  Library/OcConfigurationLib/OcConfigurationLib.c
Utilities/ocvalidate/ocvalidate Tests/SandboxHandoff.plist
```

The parser regression executes actual C code, checks the disabled and legacy
defaults, exercises all supported scalar representations and XML/base64
round-trips, and rejects unsupported protocols, wrapped integers, missing
identity/path, invalid resource bounds, and oversized serialized XML.
`Tests/SandboxHandoff.plist` is a **synthetic test configuration**, with explicitly
synthetic identity and a `.fixture` input. It is not an Apple boot profile. It is
used only to check the OpenCore-to-engine handoff and expected unsupported status
under an x86 EFI firmware test environment.

`Tests/NativeSourceAudit.py` verifies the resolved native package path against
this checkout, hashes every C/header/assembly/build-description source (including
untracked new files), requires compiler-log entries for the four critical C
files, and checks four Sandbox markers in the EFI. Run it before a runtime test:

```sh
python3 OpenCorePkg/Tests/NativeSourceAudit.py \
  --native-package "$WORKSPACE/OpenCorePkg" \
  --build-log /path/to/full-native-build.log \
  --binary Build/OpenCorePkg/DEBUG_GCC/X64/OpenCore.efi \
  --output /path/to/native-source-audit.json
```

The initial `4aa8f56d3b3323cd517d26d84b0127ab5a36b3f14bca241e8d9b8c2de235d07e`
candidate mistakenly compiled audk's unchanged OpenCore 1.0.7 submodule. Its
runtime reported missing Sandbox schema. That binary and failure evidence are
retained for provenance, and are not Sandbox build or boot evidence. The
corrected independent workspace build resolves the modified package explicitly.

Original upstream license notices are retained. New native integration files use
BSD-3-Clause; this does not relicense other components.
