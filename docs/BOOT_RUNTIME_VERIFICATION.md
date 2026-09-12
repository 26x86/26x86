# Layered boot and runtime verification

**Current Status:** Layered acceptance gates with separately scoped VMApple harness history.

**Target State:** Source-bound XNU/userspace evidence, then physical guest display/input and storage persistence.

The layers covered in this specification span **EFI/preOS → QEMU VMApple TCG → authentic AVPBooter/iBoot → XNU → macOS userspace**. Each layer generates independent verification evidence. Crucially, QEMU capability dumps, process exit codes, DFU acknowledgments, or synthetic guest passes do NOT constitute valid evidence of macOS boot.

## Current NextCore physical milestone

Normal ARM64e entry reports `NOT_READY` because live providers are incomplete.
The explicit original-prefix trace returns `ABORTED`; its instruction count and
stop reason are diagnostic evidence. See [progress](progress.md) for the latest
source-bound replay and [entry contracts](NEXTCORE_ARM64E_ENTRY_CONTRACT.md) for
legacy versus SPTM startup.

Physical acceptance requires the named target computer, external-media boot,
reboot, persistent guest display and interactive input. Firmware GOP or a
post-run test blit does not establish guest scanout or post-ExitBootServices
ownership. Persistent storage/platform service behavior is also required.
Acceleration follows as a separate guest Metal gate. CI and authored fixtures
cannot promote any of these missing results.

The harness below records the separate VMApple/original-booter research path.
Its legacy tool names and dated observations are preserved for reproduction;
it is not the physical x86 EFI runtime architecture. A VM running on Apple
Silicon remains virtualization evidence. Check [compatibility](compatibility.md)
for model eligibility separately from these execution results.

## Execution Harness

Layer-specific artifacts are stored in newly created isolated run directories.

```sh
python3 Tools/verify_boot_runtime.py \
  --output /tmp/26x86-boot-runtime-<run-id> \
  --skip-efi --skip-ovmf
```

This command verifies the M1/VMApple source contract and source-port manifest. If Apple-proprietary inputs are absent, the missing requirements are recorded in `report.json` under `external_input_contract`. To run EFI and OVMF validation, remove `--skip-efi --skip-ovmf`. Note that this path validates EFI/preOS/JIT under x86_64 OVMF only, and does not validate iBoot, XNU, or macOS.

The TCG step is initiated only when observing an authentic Apple VM bundle:

```sh
python3 Tools/verify_boot_runtime.py \
  --output /tmp/26x86-boot-runtime-<run-id> \
  --qemu /absolute/path/qemu-system-aarch64 \
  --qemu-img /absolute/path/qemu-img \
  --firmware /absolute/path/AVPBooter.vmapple2.bin \
  --vm-json /absolute/path/macosvm.json \
  --target 27 \
  --require-tcg
```

The `qemu-system-aarch64` binary must be compiled via `Tools/build_vmapple_tcg.py` matching pinned QEMU revisions and the patch series in `research/venfire/patches/series`. The `--firmware` argument specifies caller-owned, authentic AVPBooter binaries, and `macosvm.json` must declare the ECID, hardwareModel, AUX, and root disk as a unified bundle. AUX and root disks must use qcow2 copy-on-write overlays; any modification to input SHA-256 digests triggers execution failure.

Use `--require-macos` when target-matching UART transcript evidence is strictly required:

```sh
python3 Tools/verify_boot_runtime.py \
  --output /tmp/26x86-boot-runtime-<run-id> \
  --qemu /absolute/path/qemu-system-aarch64 \
  --qemu-img /absolute/path/qemu-img \
  --firmware /absolute/path/AVPBooter.vmapple2.bin \
  --vm-json /absolute/path/macosvm.json \
  --target 27 --require-tcg --require-macos
```

## Evidence Gates

| Layer | `report.json` Gate | Passing Criteria |
|-------|--------------------|------------------|
| EFI Firmware | `firmware_efi=passed` | Production EFI build and successful OVMF execution |
| Rust preOS | `rust_preos=passed` | Rust ABI/policy and EFI bridge pass within the same run |
| AArch64 JIT | `aarch64_jit=passed` | Built-in/external guest, unsupported instruction trapping, budget exhaustion limits |
| Native Machine | `partial` | VMApple TCG source/patch contract and descriptor graph (not physical M1 AIC/DART) |
| iBoot | `apple_boot_chain=runtime-tested` component | Sequential iBoot Stage2 and XNU handoff markers confirmed via UART |
| XNU | Full-chain criterion | `Darwin Kernel Version` matches requested target major version |
| macOS Userspace | `macos=true` | `launchd`, `loginwindow`, or `WindowServer` present in the same log transcript |

`x86/boot_evidence.py` records absolute byte offsets for all evidence markers. If only an iBoot banner or DFU ACK is present without XNU and userspace markers, `macos_boot_verified` is never asserted. Synthetic `virt`/`vmapple` guests written for test purposes cannot satisfy this parser.

To measure raw Stage2 execution from the macOS 27 j274 IPSW independently:

```sh
python3 -m x86 vmapple run-tcg \
  --target 27 \
  --qemu /absolute/path/qemu-system-aarch64 \
  --qemu-img /absolute/path/qemu-img \
  --firmware /absolute/path/iboot-stage2-decoded.bin \
  --firmware-kind iboot-stage2 \
  --vm-json /absolute/path/macos27-j274-macosvm.json \
  --research-graphics --duration 60 --research-only --json
```

In this mode, `firmware_execution_evidence` only records whether the QEMU TCG `exec` trace observes entry into the firmware window and relocation to high-RAM (`0x1fc000000`). Because raw Stage2 may omit UART banners, this observation is never promoted to `iboot_stage2_verified` or XNU/WindowServer success. Host synthetic swapchain presentation (`host_frame_presented`) proves only host presentation, not guest WindowServer/AGX/Metal execution.

A unified verdict requires `full_iboot_xnu_userspace_chain_verified=true`. This flag is set if and only if the iBoot Stage2 marker precedes the XNU marker, and target-matching XNU and userspace markers appear within the same UART transcript. When direct AVPBooter suppresses banners, `macos_boot_verified` and this stricter chain verification are maintained separately.

Saved native/TCG launcher reports can be re-evaluated for causal contract integrity without executing:

```sh
python3 sandbox/efi/verify_iboot_xnu_handoff.py \
  /path/to/tcg-or-native/launch.json --target-major 27
```

This verifier re-calculates marker ordering, target major matching, input hashes, and direct/recovery step causality. Even if an input report claims `macos_boot_verified=true`, inconsistent conditions cause the affirmative claim to be rejected.

For this VMApple harness, missing execution prerequisites keep the corresponding phases incomplete:

- Apple-signed, target-matching AVPBooter / VMApple firmware;
- Provisioned AUX and root disk pairs calibrated to identical hardwareModel and ECID parameters;
- Recovery, storage, and DART contracts mandated by iBoot with corresponding QEMU trace validation;
- Unmodified guest UART transcripts demonstrating sequential iBoot Stage2, matching XNU, and userspace markers;
- When claiming native HVF paths: authentic Apple Silicon arm64 Darwin host with Virtualization.framework.

OVMF, TCG machine help, synthetic guests, or legacy iBoot recovery ACKs are never conflated with "macOS compatibility layer has booted". This harness sets `macos_boot_verified=true` only through its empirical UART gate. That flag alone does not establish a physical desktop or completed installation.
