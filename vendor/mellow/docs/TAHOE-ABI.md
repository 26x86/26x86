> **Historical record — preserved unedited.** This document predates the MELLOW
> re-architecture. It is retained because the record of what was known, and when, is itself
> evidence. For the current concept and architecture see [CONCEPT.md](CONCEPT.md) and
> [ARCHITECTURE.md](ARCHITECTURE.md); for what any of it is allowed to claim, see
> [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).

# Actual Tahoe binary evidence and static linkage eligibility

The final Mellow 0.4.0 binary has **378 imports, and all 378 have eligible
declared providers in the inspected Tahoe 26.6.2 / 25G83 Recovery artifacts
and EFI Lilu 1.7.2 binary**. All eight `OSBundleLibraries` version requirements
fall within the providers' declared compatibility intervals. This is an actual
binary comparison, including the kernel's KPI export whitelist and aliases.
It does not establish native kernel-linker acceptance, loading, private C++
object layouts, correct method behavior, GPU execution, or Metal support.

The checked Mellow executable is 445,320 bytes, SHA256
`e3c1ce4f91d8288cee75b71126e1d72720392beffe6e3245c3580d7b07b3daa1`.
The separate Mach-O validator confirms `MH_KEXT_BUNDLE`, matching 0.4.0 KMOD
metadata, 784 definitions, 2,031 external and 94 local relocations, and real
24-byte initialization and termination arrays.

## Exact inputs and provenance

The local installer recovery manifest identifies Apple recovery product
`140-93589`, obtained through `osrecovery.apple.com` / `oscdn.apple.com` using
OpenCore's macrecovery tool. Its signed chunklist and image verification passed
in the installer preparation workflow. The ABI extraction reads that existing
image; it does not download another OS image or change the USB.

- `BaseSystem.dmg`: 960,530,321 bytes, SHA256
  `edddd0d5869caaa12e29e6996a04f11590280580976a119dbd42c24fa62fe18e`.
- `BaseSystem.chunklist`: SHA256
  `06f7c498f856341f467ba1faedf2717fb2c172ae0aff4658a1467cbf46b711f9`.
- The image's `SystemVersion.plist` reports macOS 26.6.2, build 25G83.
- `BootKernelExtensions.kc`: 67,584,000 bytes, SHA256
  `c80161fa3065883753fc285339281361a8469cbb6fb27653c88e2a22eb4807a4`.
- `BaseSystemKernelExtensions.kc`: 22,282,240 bytes, SHA256
  `60d3f43f1a23847aa8b60b7c57153fd93d20d0653c116d14da4875f09e5d2f04`.
- `dyld_shared_cache_x86_64`: 760,791,040 bytes, SHA256
  `e5f4c3ff1cd2d985d6c3d370aa34a22034f6f815bcc4a2f0a044093e39e7dceb`.
- `dyld_shared_cache_x86_64.01`: 232,357,888 bytes, SHA256
  `9db68bbe532a4d99babc588767b67ba58942e14c2b74f1082bad857f74e9b377`.

Actual extracted Apple binaries remain under `work/tahoe-abi/extracted` for
local analysis. The deliverable contains the parser and evidence reports,
including UUIDs, hashes, symbol names and dependency metadata.

## How imports were checked

`Tools/tahoe-abi.py` walks actual `LC_FILESET_ENTRY` records in both
`MH_FILESET` kernel collections: 204 Boot images and 95 BaseSystem images.
It reads their Mach-O symbol tables and `__PRELINK_INFO` bundle metadata.
The kernel's `__LINKINFO,__symbolsets` section contains nine KPI symbol sets.
An import attributed to a KPI is accepted only when that KPI is declared by
Mellow, its version interval is satisfied, its whitelist names the symbol,
and the whitelist's alias target is actually defined in the kernel. For
example, `_IOMalloc` resolves through the published alias to
`_IOMalloc_external`; merely finding a similarly named kernel symbol does not
pass this check.

The 378 matches consist of 254 `com.apple.kpi.iokit`, 85
`com.apple.kpi.libkern`, 28 `as.vit9696.Lilu`, seven `com.apple.kpi.mach`, three
`com.apple.iokit.IOPCIFamily`, and one `com.apple.kpi.bsd` imports. No match
uses an undeclared library. Private external symbols are not accepted as
exports. Providers are KPI 25.6.0, IOPCIFamily 2.9, and Lilu 1.7.2. Empty
usage of the declared dsep/unsupported dependencies is not an error.

Every import's provider, alias target, definition address, and version result
is retained in `abi-evidence/tahoe-import-resolution.json`. The file explicitly
sets `kernel_linker_executed`, `runtime_loaded`, `private_abi_verified`, and
`metal_verified` to false. Cross-build flags still say the build alone did not
check target exports; the subsequent ABI report records this separate check.

The dependency rules follow Apple's documentation for
[OSBundleLibraries](https://developer.apple.com/documentation/bundleresources/information-property-list/osbundlelibraries)
and [OSBundleCompatibleVersion](https://developer.apple.com/documentation/bundleresources/information-property-list/osbundlecompatibleversion).
Mach-O parsing follows Apple's
[loader declarations](https://github.com/apple-oss-distributions/xnu/blob/main/EXTERNAL_HEADERS/mach-o/loader.h).

## Graphics and userspace evidence

The Recovery kernel collections contain real IOAcceleratorFamily2 487.4.3,
IOGraphicsFamily, IOSurface, AppleIntelICLLPGraphicsFramebuffer,
AppleIntelCFLGraphicsFramebuffer, and AppleIntelKBLGraphicsFramebuffer images.
The IOAcceleratorFamily2 image has 4,063 symbol definitions. The collection
inventory does not contain the full Intel acceleration kext or a Tiger Lake
graphics backend. Framebuffer presence alone does not establish acceleration.

The actual x86_64 dyld cache contains 719 images. The parser correlates shared
cache virtual addresses with bounded file mappings and validates subcache
UUIDs. It inventories actual Metal, IOAccelerator, and CoreDisplay Mach-O
images, including imports, exports, dependencies and Objective-C method-name
strings. Metal has 22,728 definitions and 615 imports; IOAccelerator has 365
definitions and 116 imports; CoreDisplay has 4,022 definitions and 932 imports.
These counts include internal definitions and are not counts of public API.
Format definitions come from Apple's
[dyld_cache_format.h](https://github.com/apple-oss-distributions/dyld/blob/main/include/mach-o/dyld_cache_format.h).

These are concrete inputs for future interface work. They do not reveal every
IOUserClient selector, C++ vtable layout, command-buffer format, compiler
calling convention, resource lifetime rule, or Intel device plugin contract.
No guessed IOAccelerator object or fake `MTLDevice` registration was added.
The genuine Intel IGC/ocloc Zebin artifact and its bounded loader are separate
from Apple's Metal Shading Language and proprietary driver ABI. See
`IOACCEL-METAL.md` and `XE-ZEBIN.md` for the exact compiler and loader scope.

## Full installer lookup, bounded partial result

The official Apple software-update catalog also identifies full installer
product `140-93587`. Its MobileAsset metadata identifies x86_64 build 25G83 /
26.6.2, matching the Recovery version. The observed package is
[Apple InstallAssistant.pkg](https://swcdn.apple.com/content/downloads/37/33/140-93587-A_GRFFH93NOL/f944yaqo1cjhh2m0kxrl0zhcpg9yb9qphv/InstallAssistant.pkg),
18,384,624,402 bytes. The metadata and package index were read from Apple
HTTPS endpoints, not inferred from a model name or third-party driver listing.

A bounded HTTP Range exploration read the XAR table, embedded SharedSupport
DMG's UDIF block map, HFS+ catalog and nested MobileAsset ZIP central directory.
The HFS and ZIP indexes required approximately 376 KB of network data before
selected metadata entries were read. The ZIP has 2,483 entries. Selected
PBZX/YAA metadata includes paths for `AppleIntelICLGraphics.kext` and
`AppleIntelICLGraphicsMTLDriver.bundle`. Subsequent bounded extraction obtained
the actual bundle Info.plist and its 3,285,040-byte `libigdmd.dylib` helper.
The helper SHA256 is
`0d3e31c7e3e2977d611b6c7febb4875a96779caf677c5187debf8b158fb5adcf`;
it has 1,321 definitions and 149 imports, including performance telemetry
interfaces. It is **not** the declared `AppleIntelICLGraphicsMTLDriver`
executable. That main executable remains unextracted; a separate system
cryptex uses RIDIFF10 and has not been reconstructed into a verified image.
Selected ZIP shards passed CRC and PBZX/XZ decoding, but the full package
signature and whole-package digest were not verified by this partial download.
Neither the helper nor path metadata is used as a provider in the 378-import
result. See `abi-evidence/intel-umd-partial.json` and `METAL-USERSPACE.md` for
the precise metadata/helper evidence and the separate public Metal client.

The bounded exploration and cached ranges remain in `work/tahoe-abi`; no full
18 GB download was necessary for this lookup. Apple publishes the underlying
[XAR implementation](https://github.com/apple-oss-distributions/xar/blob/main/xar/lib/archive.c)
and [HFS format definitions](https://github.com/apple-oss-distributions/hfs/blob/main/core/hfs_format.h).
This partial result does not turn an ICL plugin into a 7D41 implementation.

## Reproduction and tests

Extract the selected paths listed in `Tools/tahoe-extract.py` from the existing
verified BaseSystem image using 7-Zip. Then, from the workspace root:

```powershell
python outputs/Mellow-7D41-runtime/Tools/tahoe-extract.py --image outputs/GalaxyBook-Tahoe/installer/com.apple.recovery.boot/BaseSystem.dmg --output work/tahoe-abi/extracted --seven-zip 'C:/Program Files/7-Zip/7z.exe'
python outputs/Mellow-7D41-runtime/Tools/tahoe-abi.py --extracted-system 'work/tahoe-abi/extracted/macOS Base System' --lilu outputs/GalaxyBook-Tahoe/EFI/OC/Kexts/Lilu.kext --mellow outputs/Mellow-7D41-runtime/build/Release/Mellow.kext --output outputs/Mellow-7D41-runtime/abi-evidence
python outputs/Mellow-7D41-runtime/Tools/tahoe-abi-tests.py --real-report outputs/Mellow-7D41-runtime/abi-evidence/tahoe-import-resolution.json --output outputs/Mellow-7D41-runtime/abi-evidence/tahoe-parser-tests.json
```

The parser passed 15 host test methods with 28 malformed/version/provider
subcases and the actual final 378-import report. Tests reject command overruns,
duplicate/out-of-range filesets, malformed dyld mappings and subcache suffixes,
cyclic export tries, overflowing ULEB values, missing aliases, undeclared
providers, private exports, and incompatible versions. These are meaningful
parser and static-eligibility checks; they do not execute a GPU or load a kext.

Evidence files are `tahoe-source-inventory.json`,
`tahoe-import-resolution.json`, `tahoe-graphics-inventory.json`, and
`tahoe-parser-tests.json` under `abi-evidence/`.
