> **Historical record — preserved unedited.** This document predates the MELLOW
> re-architecture. It is retained because the record of what was known, and when, is itself
> evidence. For the current concept and architecture see [CONCEPT.md](CONCEPT.md) and
> [ARCHITECTURE.md](ARCHITECTURE.md); for what any of it is allowed to claim, see
> [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).

# Native Xe backend integration audit

## Verdict

The source tree does not currently provide hardware-backed Metal acceleration
for PCI `8086:7D41` on macOS Tahoe. It contains two different paths which must
not be treated as equivalent:

1. The active `-mellowtglwithgfx` path is a legacy Apple-driver compatibility
   experiment in `kern_gen11.cpp`. It patches or advertises TGL/ICL Apple driver
   names and performs inherited MMIO work. It remains enabled for hardware
   discovery and regression evidence.
2. The newer Xe MMIO, memory, GuC, context, interrupt, and fence components are
   compiled into the kext, but no IOKit provider owns and starts them. They have
   no call path from `MellowCore::init()` or `MellowCore::processPatcher()`.

Compiling those components is useful structural evidence. It is not evidence
that a GuC was authenticated, a context ran, an interrupt arrived, a fence was
written by the GPU, an IOAccelerator provider opened, or a Metal plugin loaded.

## Actual startup path

`kern_start.cpp` creates the single `MellowCore` object. After Lilu admits the
plugin, its configuration callback calls `MellowCore::init()`. That function
registers Lilu patcher/kext callbacks and initializes `Genx`, `Gen11`, and DYLD
patches. It does not construct or retain any of these native objects:

- `MellowXe::IOKitMmio`
- `XeMemory::IOKitPageTable`
- `XeGuCFirmware::Loader` or `XeGuCFirmware::IOKitBinding`
- `XeGuC::Transport` or `XeGuC::IOKitBinding`
- `MellowXeInterrupt`
- `XeFence::IOKitSlot`
- `XeContext::EvidenceExecution`

The `IOResources` personality in `Mellow/Info.plist` also has no active provider
class behind it. The `PRODUCT_NAME` `IOService::probe()` and `start()`
implementation in `kern_start.cpp`, and its class declaration in
`kern_mellow.hpp`, are commented out. Consequently there is no workloop,
interrupt source lifetime, reset epoch, stop/quiesce sequence, or exclusive
PCI/BAR owner for the new components.

With the current experimental arguments

```
-mellowtahoe -MellowDebug -mellowtglwithgfx mellow-dmc=skip
```

the legacy path remains admitted. The new `-mellownativexe` argument is an
explicit request for the native backend and is rejected while
`BackendOwnerIntegrated` is false. The current arguments do not contain that
new flag, so this gate does not disable the existing TGL experiment.

On an accepted Arrow Lake-U `8086:7D41` device, the current diagnostic evidence
mask is expected to be `0x7`: Tahoe opt-in, VESA disabled, and physical PCI
identity read before spoofing. The expected missing mask is `0xFFFF8`, the
stage is `physical-provider`, the first missing proof is `bar0-mapped`, and
`MellowNativeXeMetalReady` is zero. These values are published on the iGPU
entry as:

- `MellowNativeXeVerifiedMask`
- `MellowNativeXeMissingMask`
- `MellowNativeXeStage`
- `MellowNativeXeBackendIntegrated`
- `MellowNativeXeMetalReady`

They are diagnostics, not attestation. A non-7D41 device accepted by the older
multi-device compatibility code does not receive the 7D41 identity evidence
bit.

## Legacy TGL path findings

The TGL selection in `Gen11::init()` asks Lilu to observe binaries under
`/Library/Extensions/AppleIntelTGLGraphics*.kext`. Neither the runtime tree nor
the USB bundle contains those Apple binaries. The Tahoe recovery inventory
available for this audit contains `AppleIntelICLLPGraphicsFramebuffer`, but no
`AppleIntelICLGraphics` accelerator binary. A kext name or IOCatalogue property
cannot supply a missing executable.

When a TGL hardware kext is observed, `injectAcceleratorPersonality(true)`
creates an `IntelAccelerator` personality containing the local bundle ID
`com.xxxxx.driver.AppleIntelTGLGraphics` and the string
`AppleIntelTGLGraphicsMTLDriver`. That operation only inserts a dictionary into
the IOCatalogue. It does not load a Metal user-space plugin or implement
Tahoe's private IOAccelerator ABI.

The legacy `IGHardwareGuC::loadGuCBinary()` hook explicitly returns zero for
the 7D41 path and logs `GUC_NOT_LOADED`; it delegates to Apple only for a real
TGL device. The `IGAccelDevice::deviceStart()` hook preserves the original
return value, which correctly avoids turning a failed Apple backend start into
a false success. Several legacy patch/route failures still use `PANIC_COND`, so
serial/OpenCore logs are required before expanding this experiment.

## Missing native ownership and proof providers

### BAR0, GMD, and force wake

`XeMmioIOKit.cpp` can map BAR0 and initialize the GMD 12.70 access path, but no
caller constructs `IOKitMmio`, calls `attach()`, owns the PCI device exclusively,
or detaches it during stop/reset. The older `setRMMIOIfNecessary()` mapping is
not the same ownership contract and therefore is not counted as native evidence.

### GGTT, page tables, PAT/MOCS, and ADS

The new page-table code has mapping primitives, but no runtime GGTT allocator
or publisher reserves an address range, writes PTEs, invalidates the correct
TLB, and proves readback for one reset epoch. The firmware IOKit adapter's
callbacks for epoch ownership, quiescence, GGTT retain/release, mapping
publication, PAT3 readback, and full ADS validation have no implementation.
`populateMinimalAds()` is intentionally only a hardware-configuration boot
structure and does not describe the engine set needed for submission.

### GuC firmware and transport

`XeGuCFirmware::Loader` checks the pinned firmware identity and has bounded
reset, WOPCM, DMA, and authentication logic. No caller supplies its real IOKit
proofs or invokes `start()`. The required 320,320-byte GuC image with SHA-256
`7794f0b6abe5fcd9c6f47035dafe2199f30a6e7d230bd5a53fbf8005a60e5911`
is not packaged inside `Mellow.kext`. The only binary in the runtime tree is
the 6,944-byte compiler evidence kernel, which is not GuC firmware.

`XeGuCTransportIOKit.hpp` states that the missing firmware, GGTT, and LRC proof
callbacks still require a driver owner. No code supplies those callbacks or
starts the transport.

### Context, interrupt, and fence

`XeContext::EvidenceExecution` requires an authoritative backend for admission,
stopped-epoch freshness, VM retain/release, staging, cache sync, and quiescence.
No production caller supplies it. `MellowXeInterrupt::attach()` can build an
`IOFilterInterruptEventSource`, but no object supplies and retains the workloop,
vector, or dispatcher. `XeFence::IOKitSlot` can map a descriptor, but no owner
supplies the mapping proofs or ties its lifetime to the submitted context.

### IOAccelerator and Metal userspace

There is no implemented Tahoe IOAccelerator provider/user-client contract for
the new backend. There is also no loadable Intel 7D41 Metal plugin, no verified
private ABI handshake, and no MSL/AIR-to-ZeBin compiler route. The
`MetalPluginName` string and the `mellow_evidence_mtl.bin` compiler artifact do
not establish those links.

## Fail-closed integration change

`Mellow/RuntimeReadiness.hpp` defines the ordered evidence contract consumed by
the actual startup and PCI discovery paths. It exposes only observed state and
requires all 20 proofs before `mayAdvertiseMetal` can become true. A boot
argument cannot set backend evidence.

`StartupPolicy.hpp` and `kern_start.cpp` reject an explicit
`-mellownativexe` request while the provider owner is absent. They continue to
admit the current `-mellowtglwithgfx` legacy experiment. `kern_mellow.cpp`
publishes the bounded early evidence described above before the legacy spoof
and MMIO path proceeds.

This change prevents an unintegrated native backend from being presented as a
working accelerator while preserving read-only identity diagnostics and the
existing experimental Apple-driver path.

## Verification performed

The focused host test was compiled with `-Wall -Wextra -Werror -pedantic` and
passed 4,151 assertions. It checks existing pattern/policy behavior, preserves
legacy admission, rejects the unowned native request, and verifies that every
individual missing evidence bit denies Metal-ready state.

```
C:\msys64\mingw64\bin\g++.exe -std=c++17 -O2 -Wall -Wextra -Werror -pedantic outputs\Mellow-7D41-runtime\tests\patcher_policy_tests.cpp -o work\gpu-integration-audit\patcher_policy_tests.exe
work\gpu-integration-audit\patcher_policy_tests.exe
```

The complete production source set also cross-compiled and linked as a Mach-O
`MH_KEXT_BUNDLE` with the repository's `cross-build.py` path. That validates
translation units and linkage only. It does not validate Tahoe KPI/Lilu exports
on a running kernel, kext loading, firmware authentication, GPU execution, or
Metal.

The 0.4.1 build compiled all 30 translation units and passed structural Mach-O
validation. The linked binary is 449,448 bytes with SHA-256
`cee0482b2d858856c0696e0d8d6f18e6e12f87bb81bb0a0e1330984e1329eb36`.

```
python outputs\Mellow-7D41-runtime\Tools\cross-build.py --llvm-bin work\mellow-build\llvm-20.1.8\bin --output work\mellow041-build --configuration Release --darwin-linker work\mellow-build\ld64-prefix\bin\x86_64-apple-darwin13.4.0-ld --wsl-distro Ubuntu-24.04
```

A read-only import eligibility pass then checked that exact 0.4.1 binary and
the staged Lilu 1.7.2 binary against the extracted Tahoe 26.6.2 / build 25G83
kernel collections. All 378 declared imports had an eligible declared provider.
The malformed-input/eligibility suite passed 15 methods and 28 subcases.
Those reports deliberately retain `kernel_linker_executed=false`,
`runtime_loaded=false`, `private_abi_verified=false`, and
`metal_verified=false`.

```
python outputs\Mellow-7D41-runtime\Tools\tahoe-abi.py --extracted-system "work\tahoe-abi\extracted\macOS Base System" --lilu outputs\GalaxyBook-Tahoe-USB\EFI\OC\Kexts\Lilu.kext --mellow work\mellow041-build\Mellow.kext --output work\mellow041-build\tahoe-abi
python outputs\Mellow-7D41-runtime\Tools\tahoe-abi-tests.py --real-report work\mellow041-build\tahoe-abi\tahoe-import-resolution.json --output work\mellow041-build\tahoe-abi\tahoe-abi-test-results.json
```

The existing high-count GuC, context, interrupt, and fence test reports are
host/emulation results. Their own metadata records
`iokit_adapter_runtime_tested=false`, `hardware_executed=false`, and
`physical_irq_or_fence_tested=false`.

## Required physical acceptance sequence

Do not set any later readiness bit until its corresponding evidence is captured
from the target boot:

1. Capture the pre-spoof `8086:7D41` identity and diagnostic masks from IORegistry.
2. Start a real provider owner, map BAR0, read GMD 12.70, and prove force-wake
   acquire/release under the same reset epoch.
3. Reserve and publish GGTT mappings, invalidate the device TLB, and compare
   PTE readback; validate the physical PAT/MOCS state.
4. Build a complete ADS for enumerated engines, package the pinned GuC image,
   and capture BootROM authentication status without overriding a failure.
5. Start the GuC transport and one context with an owned VM, interrupt source,
   and fence page. Prove a GPU-written fence and expected output buffer after
   cache synchronization.
6. Implement and open the Tahoe IOAccelerator provider/user client, then prove
   the private ABI handshake from a real user-space plugin.
7. Connect the shader compiler path and run a Metal compute command whose output
   is verified independently. `system_profiler`, registry strings, or an
   `MTLDevice` object alone are insufficient acceptance evidence.

No step in that physical sequence was completed by this Windows cross-build.
