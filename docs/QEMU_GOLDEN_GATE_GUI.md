# QEMU GUI Validation Pathways

**Current Status:** Development VM/firmware harnesses; no physical x86 desktop claim.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

This document does NOT claim that macOS 27 Golden Gate has "booted". Rather, the QEMU GUI serves as an empirical harness for verifying two distinct boundary layers:

* **EFI Layer:** An x86_64 OVMF instance executes the 26x86 VSK input verification EFI application.
* **iBoot / Recovery Layer:** A dedicated research-grade VMApple QEMU instance executes authentic AVPBooter firmware and DFU USB transports.

VMApple's MachineType is locked to `iBoot(AArch64)` and used exclusively for macOS guests. iOS, iPadOS, and other mobile Apple operating systems are strictly out of scope and rejected during policy validation prior to DFU upload. The recovery protocol for this tier is DFU/IPSW for macOS, with a local recovery default filename of `_default.ipsw`.

OVMF test cases always conclude with `macos_boot_verified=false`. VMApple now skips recovery transport when `--boot-selection macos` is specified, monitoring AVPBooter's authentic macOS boot entry directly. However, `macos_boot_verified=true` is asserted ONLY when target-matching XNU and userspace UART evidence meet the selected harness's parser contract. A visible desktop or completed installation needs additional evidence. Selecting Recovery continues to record only recovery protocol boundary states.

## Apple Silicon Device Profiles Derived from qemu-t8030

The [Bringing up the emulator documentation](https://github.com/TrungNguyen1909/qemu-t8030/wiki/Bringing-up-the-emulator) and source code of `qemu-t8030` illustrate Apple AIC, Apple ANS/NVMe, DART/SART, Apple UART, NVRAM, SMC, USB OTG/Type-C, and `m1_fb`/`xnu_ramfb` family device topologies. Because that repository is an archived iPhone 11 / T8030 iOS emulator, 26x86 does not import its firmware, iOS device trees, or recovery scripts. Component names and interconnect topologies are recorded solely as research inputs for the Apple Silicon Sandbox, while guest policy remains strictly locked to `iBoot(AArch64) -> macOS`.

Current implementation boundaries are defined as follows:

* The EFI Sandbox maintains an AIC-specific contract and contains only a partial first-party `aic_v1` wired IRQ model. No GIC-compatible fallback path is added.
* The VMApple QEMU TCG research machine utilizes GICv3 and VMApple BDIF (AUX/root). Consequently, it does not claim support for qemu-t8030's AIC/ANS/DART/SART, and never asserts `macos_boot_verified`.
* NVMe namespace examples in the qemu-t8030 documentation (`nsid=1` data and `nsid=5` Apple NVRAM) are preserved strictly as **reference values**. They are not inferred to match macOS AUX/root layouts, and hardware-model provisioning receipts continue to be required.
* Because current TCG research runs lack Apple Paravirtualized Graphics, mentioning `m1_fb` or `xnu_ramfb` names does not imply installer UI or Metal execution claims.

Capabilities can be inspected without opening or mutating input files:

```sh
python3 -m x86 vmapple capabilities
```

The `reference` block in the output highlights the pinned research revision and iOS-only scope of qemu-t8030, while `interrupt_controller`, `device_topology`, and `storage` blocks delineate the current 26x86 implementation and remaining deltas. This inspection command does not launch QEMU and implies no boot or installation success.

## OVMF EFI Window

When clang, QEMU, OVMF, and test bundles are prepared in WSL Ubuntu or Linux, run:

```sh
cd /path/to/26x86
python3 sandbox/vsk/tools/verify_efi_inputs.py \
  --bundle /path/to/signed-vsk-bundle \
  --output /tmp/26x86-goldengate-gui \
  --case valid \
  --gui \
  --qemu /usr/bin/qemu-system-x86_64 \
  --ovmf-code /usr/share/OVMF/OVMF_CODE_4M.fd \
  --ovmf-vars /usr/share/OVMF/OVMF_VARS_4M.fd
```

`--gui` spawns a single GTK window and captures EFI debug-exit status and debug console streams. The full 3-case validation suite defaults to `--display none` for automated CI. Interactive GUI execution requires specifying a single test case (e.g. `--case valid`). Paths can also be supplied via `QEMU_SYSTEM_X86_64`, `OVMF_CODE`, and `OVMF_VARS` environment variables.

A successful GUI execution report must contain the following fields:

```json
{
  "passed": true,
  "validation_level": "SIMULATED",
  "actual_efi_executed": true,
  "display_backend": "gtk",
  "boot_authorized": false,
  "macos_boot_verified": false
}
```

The report records the QEMU revision alongside SHA-256 digests of the OVMF code and variable templates, enabling reproducible correlation of window creation with EFI input verification results.

## VMApple Recovery Window (Research Use)

VMApple is an AArch64 machine architecture distinct from OVMF. A custom-built research QEMU binary providing the `vmapple` machine target is required. The display backend defaults to `auto`, which selects Cocoa on native Apple Silicon macOS and headless backends (`none`) on Linux/WSL research builds. GTK or SDL are selected only when explicitly advertised by the build.

```sh
qemu-system-aarch64 \
  -M vmapple,research-headless=on,uuid=0 \
  -accel tcg,thread=single \
  -cpu max,pauth=on,cntfrq=24000000 \
  -m 4G -smp 2 \
  -bios /path/to/AVPBooter.vmapple2.bin \
  -global vmapple-cfg.soc_name='Apple M1 (Virtual)' \
  -global vmapple-cfg.model=VM0001 \
  -display none -monitor none -nic none -no-reboot \
  -blockdev '<COW overlay over an immutable AUX fixture>' \
  -blockdev '<COW overlay over an immutable root fixture>'
```

The `allow-block-writes` flag is added automatically by the runner only when the 26x86 write-enabled BDIF patch is advertised via `-device vmapple-bdif,help`. If upstream BDIF lacks that property, the runner continues read and boot observation without injecting unknown `-global` options, explicitly noting the divergence via `backend.bdif_block_writes=false`.

Recovery inputs require independent cryptographic hashing of authentic files, and AUX/root images must utilize copy-on-write overlays over raw backing fixtures. Never designate authentic IPSW archives, active ESPs, or raw physical disks as writable targets. The `Apple M1 (Virtual)` and `VM0001` metadata strings reflect guest-facing VMApple parameters and carry no hardware authorization or warranty claims. Experiments utilizing developer host bypasses remain confined to local research logs and are excluded from production distributions. The `optional-rpc-unavailable` case tests authentic iBEC failure handling as an explicit negative control and is omitted from standard commands.

The same runner is accessible via the `Apple Silicon Sandbox` step in the 26x86 GUI. Providing `VMApple QEMU`, `qemu-img`, `AVPBooter`, the official BuildManifest, TSS tooling, unmodified iBSS/iBEC binaries, AUX/root sources, and a clean output directory, then clicking `Open VM Window` triggers `launch_vmapple` via the local bridge. The GUI default pathway reads the current USB nonce, queries Apple TSS, and generates personalized IMG4 payloads exclusively inside the designated output folder. Under Windows, if inputs reference WSL paths (e.g. `/home/...`), the bridge directly invokes `wsl.exe --cd ... --exec python3 -m x86 vmapple run --live-personalize --research-only --json` using the WSLg GTK display.
All file paths are passed as explicit arguments, and pre-existing output folders are rejected. Execution results are serialized to `launch.json` in the run directory, with process tracking available via returned PID and log path metadata.

Prior to execution, operator action requires clicking `Start 2-Second Boot Picker` in the GUI and pressing Alt/Option within 2 seconds. Selecting `macOS Recovery · _default.ipsw` enables `Open Recovery VM Window`, with the bridge transmitting DOM input records to the worker via `--boot-picker-trigger alt-enter`. If the timeout expires without Alt input, standard macOS boot is selected. In direct macOS mode, iBSS/iBEC personalization and DFU transfer are skipped, with AVPBooter monitored via UART while booting from provisioned AUX/root storage. Only Recovery selection engages the iBSS/iBEC pipeline and DFU/IPSW chain.

Direct macOS boot can be invoked as follows (omitting `--ibss`, `--ibec`, `--live-personalize`, and `--restore-chain`):

For VMs generated via Virtualization.framework, designating `machineId`, `hardwareModel`, `aux.img`, and `disk.img` within the same directory as `macosvm.json` constitutes the recommended input contract. The runner hashes both property lists read-only and validates the ECID, preventing cross-contamination with manual paths. Because the initial `0x4000` bytes of `aux.img` contain VMApple metadata, JSON pathways automatically apply QEMU's documented AUX view offset of `0x4000`. Authentic images are neither truncated nor overwritten; execution runs on top of freshly instantiated qcow2 COW overlays. This adheres to the `dd ... bs=0x4000 skip=1` specification in the [QEMU VMApple documentation](https://www.qemu.org/docs/master/system/arm/vmapple.html).

If a `macosvm.json` bundle does not yet exist, a new bundle can be provisioned on an authentic Apple Silicon macOS host as follows. IPSW images are supplied by the operator; tooling does not download, decrypt, or tamper with source archives.

```sh
python3 -m x86 vmapple provision \
  --ipsw /path/to/UniversalMac_26...ipsw \
  --output /path/to/new-goldengate-vm \
  --disk-size 32g --timeout 86400 --json
```

This command rejects Linux/WSL environments, hosts lacking AVPBooter, existing output directories, and invalid disk sizes, writing `provision-report.json` and session logs to the newly initialized directory. Provisioning receipts satisfy direct-run input verification but do not constitute proof of macOS boot; subsequent direct runs via `--vm-json` must independently confirm XNU and userspace UART markers.

The Apple Silicon VM comparison path uses Virtualization.framework separately from QEMU direct entry. This is virtualization on a physical host, not the physical x86 NextCore product boot. Because `macosvm` connects the primary serial console to stdout and instantiates storage clones with `--ephemeral`, 26x86 wraps the process in a bounded worker. PTYs are avoided in automated pipelines because upstream tooling requires carriage returns on standard input prior to connecting.

```sh
python3 -m x86 vmapple run-native \
  --target 27 \
  --macosvm /usr/local/bin/macosvm \
  --vm-json /path/to/goldengate-vm/macosvm.json \
  --output /tmp/26x86-goldengate-native \
  --observation-timeout 900 --duration 900 \
  --research-only --json
```

This command executes solely on Apple Silicon macOS hosts, logging Darwin/XNU and `launchd`/`loginwindow`/`WindowServer` userspace markers from `macosvm.log`. `macos_boot_verified=true` is asserted only when both marker tiers appear; absent installation receipts, `installation_verified` remains `false`. Where QEMU VMApple documentation disclaims support for newer guest versions, QEMU direct entry is not employed for Golden Gate boot verification.

```sh
# Legacy QEMU direct-entry invocation (target 27 is rejected by the runner;
# use the separately scoped native VM workflow for its own evidence).
python3 -m x86 vmapple run --target 27 --display auto \
  --qemu /path/to/qemu-system-aarch64 \
  --qemu-img /usr/bin/qemu-img \
  --firmware /System/Library/Frameworks/Virtualization.framework/Resources/AVPBooter.vmapple2.bin \
  --vm-json /path/to/macosvm.json \
  --output /tmp/26x86-goldengate-direct --boot-selection macos \
  --boot-delay 2 --duration 600 --research-only --json
```

When operating without JSON descriptors, `--aux` and `--root` specify pre-configured AUX views, with `--aux-offset 0x4000` applied only when referencing raw authentic AUX fixtures. Read-only pre-flight checks enforce the identical bundle contract:

```sh
python3 -m x86 vmapple inspect-storage --vm-json /path/to/macosvm.json --json
```

```sh
# Legacy raw-input QEMU invocation; this serves as a protocol compatibility experiment,
# not an endorsed Golden Gate boot command.
python3 -m x86 vmapple run --target 27 --display auto \
  --qemu /path/to/qemu-system-aarch64 \
  --qemu-img /usr/bin/qemu-img \
  --firmware /System/Library/Frameworks/Virtualization.framework/Resources/AVPBooter.vmapple2.bin \
  --aux /path/to/provisioned-aux.raw --root /path/to/provisioned-root.raw \
  --aux-offset 0 \
  --output /tmp/26x86-goldengate-direct --boot-selection macos \
  --boot-delay 2 --duration 600 --research-only --json
```

In direct execution mode, `launch.json` records `direct_boot.dfu_entered=false` and absolute byte offsets for each UART marker. Missing markers cause execution to terminate with `direct-boot-evidence-timeout`, preserving `macos_boot_verified=false`. Zero-filled AUX/root fixtures or missing hardware provisioning receipts are categorized as independent storage blockers.

The identical execution path can be invoked via CLI:

```sh
python3 -m x86 vmapple run --target 27 --display auto \
  --qemu /home/developer/.../qemu-system-aarch64 \
  --qemu-img /usr/bin/qemu-img \
  --firmware /path/to/AVPBooter.vmapple2.bin \
  --build-manifest /path/to/BuildManifest.plist \
  --tss-helper /path/to/venfire-tss-request-v2 \
  --original-ibss /path/to/iBSS.vma2.RELEASE.im4p \
  --original-ibec /path/to/iBEC.vma2.RELEASE.im4p \
  --aux /path/to/aux.raw --root /path/to/root.raw \
  --output /tmp/26x86-vmapple-run --boot-selection recovery \
  --boot-picker-trigger alt-enter --boot-delay 2 \
  --live-personalize --research-only --json
```

`--research-only` is a mandatory internal safety flag. The runner verifies the `Customer Erase Install (IPSW)` identity from the BuildManifest against live USB CPID/BDID/SDOM/nonce parameters, generating personalized IMG4 payloads only after receiving Apple TSS status `0` and valid IM4Ms. iBEC upload is initiated only when re-reading USB descriptors confirms bulk OUT endpoint 4. If `05ac:1227` iBSS DFU persists, the runner exits with `transition_state: transition-blocked` without forcing transitions. Any mutation of input hashes during execution immediately aborts the run and purges artifacts.

Input values for `machine_type`, `guest_os`, `recovery_protocol`, and `recovery_image_name` must satisfy policy validation. Supplying `guest_os=iOS` or `guest_os=iPadOS` triggers `VF_GUEST_SCOPE_VIOLATION`, while `recovery_protocol=Fastboot` raises `VF_RECOVERY_SCOPE_VIOLATION`, halting QEMU launch and USB transport.

Storage targets should be pre-flighted using the GUI storage inspector or CLI:

```sh
python3 -m x86 vmapple inspect-storage \
  --aux /path/to/aux.raw --root /path/to/root.raw --aux-offset 0
```

The inspector evaluates 512-byte aligned views, bounded zero-content spans, and APFS signatures without modifying files. If `provisioning_status` reports `unprovisioned-zero` or `partially-unprovisioned`, the files are flagged for protocol testing only. Non-zero bytes or `NXSB` headers alone cannot prove `VZMacAuxiliaryStorage` compatibility with Apple Silicon hardware models, APFS installation validity, or signed boot capability, keeping status at `unverified`. This tool does not extract, decrypt, modify, or copy input files.

Empirically verified VMApple GUI scope includes transmitting 173 DFU blocks of authentic 27.0 iBSS (including DFU suffix), `WAIT_RESET`, USB reset acknowledgment, authentic `05ac:1281` re-enumeration with bulk OUT endpoint 4, and LocalPolicy/iBEC transfer with `go` acknowledgment. Apple TSS status `0`, matching nonces, original payload hash retention, and `installer_modified: false` have been established. In selective RPC unavailability experiments, the authentic iBEC Stage2 UART command prompt was captured, followed by transmission of five restore roles matching the BuildManifest. During pre-boot notification, the guest's authentic `0200` STALL was faithfully recorded, followed by receipt of `bootx` acknowledgment before iBoot encountered a kernel panic prior to XNU entry. As a result, `signature_acceptance_verified`, `xnu_executed`, `macos_boot_verified`, and the Golden Gate installation UI are all marked `false`. Due to the absence of Apple Paravirtualized Graphics in Linux QEMU builds, `graphics_device_enabled` is also `false`. Spawning the VMApple window or completing DFU/`go`/`bootx` stages does not constitute Golden Gate boot success. Full session summaries (including Alt-to-Recovery input handling) are codified in [`integration/vmapple-gui-bootpicker-report.json`](https://github.com/26x86/26x86/blob/main/integration/vmapple-gui-bootpicker-report.json), with root `launch.json` logs accessible via `source_report`.

## Verification Verdicts

QEMU GUI validation ensures reproducible testing of EFI, JIT, and recovery USB layers during development. Production qualification requires distinct physical milestones:

1. Verification that OpenCore reliably loads `Sandbox.efi` on physical Intel Mac hardware.
2. Verification of `ExitBootServices`, VMX/EPT, and VT-d / interrupt remapping states on bare metal.
3. Verification that authentic iBoot enters XNU via genuine AIC device models and storage controllers.
4. Independent log verification of macOS 26/27 userspace initialization and GPU/Metal acceleration.

Any report lacking complete verification across these tiers is categorized strictly as EFI self-test or recovery protocol boundary evidence.

## Current evidence and hardware coverage

Reviewed for documentation freshness on 2026-09-12. See the
[portal](index.md), [progress](progress.md),
[compatibility catalog](compatibility.md) and
[library](library.md) for the active evidence boundary. Historical
receipts in this guide retain their original scope and date.
