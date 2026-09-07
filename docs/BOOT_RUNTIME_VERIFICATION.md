# VenFire layered boot/runtime verification

이 문서가 다루는 계층은 **EFI/preOS → QEMU VMApple TCG → 원본 AVPBooter/iBoot → XNU → macOS 사용자 공간**이다. 각 계층은 독립적인 증거를 남긴다. 특히 QEMU capability 출력, 프로세스 종료 코드, DFU ACK, synthetic guest PASS는 macOS 부팅 증거가 아니다.

## 실행 하네스

계층별 산출물은 새 디렉터리에 보존된다.

```sh
python3 Tools/verify_boot_runtime.py \
  --output /tmp/26x86-boot-runtime-<run-id> \
  --skip-efi --skip-ovmf
```

이 명령은 M1/VMApple source contract와 source-port manifest를 검증하고, Apple 입력이 없으면 필요한 입력을 `report.json`의 `external_input_contract`에 기록한다. EFI와 OVMF를 다시 실행하려면 `--skip-efi --skip-ovmf`를 제거한다. 해당 경로는 x86-64 OVMF에서 EFI/preOS/JIT만 검증하며 iBoot/XNU/macOS를 검증하지 않는다.

원본 Apple VM bundle을 실제로 관찰할 때만 TCG 단계를 연다.

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

`qemu-system-aarch64`는 `Tools/build_vmapple_tcg.py`가 고정 QEMU revision과 `research/venfire/patches/series`를 적용해 만든 바이너리여야 한다. `--firmware`는 원본 caller-owned AVPBooter 파일이어야 하고, `macosvm.json`은 ECID·hardwareModel·AUX·root를 하나의 bundle로 지정해야 한다. AUX/root에는 qcow2 copy-on-write overlay만 사용하며 입력 전후 SHA-256이 달라지면 실행이 실패한다.

`--require-macos`는 실제 target-matching UART 증거가 필요할 때 사용한다.

```sh
python3 Tools/verify_boot_runtime.py \
  --output /tmp/26x86-boot-runtime-<run-id> \
  --qemu /absolute/path/qemu-system-aarch64 \
  --qemu-img /absolute/path/qemu-img \
  --firmware /absolute/path/AVPBooter.vmapple2.bin \
  --vm-json /absolute/path/macosvm.json \
  --target 27 --require-tcg --require-macos
```

## 증거 게이트

| 계층 | `report.json` 판정 | 통과 조건 |
| --- | --- | --- |
| EFI firmware | `firmware_efi=passed` | production EFI build와 OVMF execution |
| Rust preOS | `rust_preos=passed` | Rust ABI/policy와 EFI bridge가 같은 실행에서 통과 |
| AArch64 JIT | `aarch64_jit=passed` | built-in/external guest, unsupported instruction, budget exhaustion |
| native machine | `partial` | VMApple TCG source/patch 계약과 descriptor graph. 실제 M1 AIC/DART 증거는 아님 |
| iBoot | `apple_boot_chain=runtime-tested`의 일부 | UART에서 iBoot Stage2와 XNU 순서가 확인됨 |
| XNU | full-chain 조건의 일부 | `Darwin Kernel Version`과 요청 target major 일치 |
| macOS userspace | `macos=true` | `launchd`, `loginwindow`, 또는 `WindowServer`가 같은 로그에 있음 |

`x86/boot_evidence.py`는 marker의 절대 byte offset을 보존한다. iBoot banner나 DFU ACK만 있고 XNU/userspace가 없으면 `macos_boot_verified`는 절대로 올라가지 않는다. synthetic `virt`/`vmapple` guest는 자체 작성 ARM64 guest이므로 해당 parser를 통과시킬 수 없다.

macOS 27 j274 IPSW의 raw Stage2를 별도로 계측하려면 다음처럼 실행한다.

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

이 모드의 `firmware_execution_evidence`는 QEMU TCG `exec` trace에서
firmware window 진입과 `0x1fc000000` high-RAM relocation을 관찰했는지만
기록한다. raw Stage2에는 별도 UART banner가 없을 수 있으므로 이 값은
`iboot_stage2_verified` 또는 XNU/WindowServer 성공으로 자동 승격되지 않는다.
Reims의 `host_frame_presented`도 host synthetic swapchain 증거일 뿐 guest
WindowServer/AGX/Metal 증거가 아니다.

전체 계층을 하나의 별도 판정으로 확인하려면 `full_iboot_xnu_userspace_chain_verified=true`도 필요하다. 이 값은 iBoot Stage2 marker가 XNU marker보다 앞에 있고, target-matching XNU와 userspace marker가 같은 UART transcript에 있을 때만 설정된다. direct AVPBooter가 iBoot banner를 출력하지 않는 경우 `macos_boot_verified`와 이 stricter chain 값은 의도적으로 분리된다.

저장된 native/TCG 런처 보고서는 실행하지 않고 causal contract만 다시 확인할 수 있다.

```sh
python3 sandbox/efi/verify_iboot_xnu_handoff.py \
  /path/to/tcg-or-native/launch.json --target-major 27
```

이 검증기는 marker, target major, input hash, direct/recovery 단계의 인과성을 다시 계산한다. 보고서가 `macos_boot_verified=true`라고 적어도 이 조건을 만족하지 않으면 양성 주장을 거부한다.

현재 non-Apple host에서 실제 macOS 단계가 `blocked`인 것은 구현 누락을 숨기지 않는 의도적인 판정이다. 실제 통과에 필요한 외부 입력은 다음과 같다.

- Apple-signed, target-matching AVPBooter/VMApple firmware;
- 같은 hardwareModel과 ECID에 맞는 provisioned AUX/root pair;
- iBoot가 요구하는 복구/저장장치/DART 계약과 해당 QEMU trace;
- 수정되지 않은 guest UART에서 iBoot Stage2, target-matching XNU, userspace markers;
- native HVF 경로를 주장하는 경우 genuine Apple Silicon arm64 Darwin host와 Virtualization.framework.

따라서 OVMF, TCG machine help, synthetic guest, 또는 기존 iBoot recovery ACK를 합쳐서 “macOS 호환성 레이어가 부팅했다”고 표현하지 않는다. 이 하네스가 `macos_boot_verified=true`를 출력하는 유일한 경로는 위 UART evidence gate이다.
