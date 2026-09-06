# QEMU GUI 검증 경로

이 문서는 macOS 27 Golden Gate를 “부팅했다”고 표시하기 위한 문서가
아닙니다. QEMU GUI는 현재 두 계층을 확인하는 도구입니다.

* **EFI 계층:** x86_64 OVMF가 26x86 VSK 입력 검증 EFI를 실제로 실행합니다.
* **iBoot/복구 계층:** 별도 연구용 VMApple QEMU가 원본 AVPBooter와 DFU USB
  전송을 실행합니다.

VMApple의 MachineType은 `iBoot(AArch64)`로 고정되어 macOS 게스트에만
사용됩니다. iOS와 iPadOS 및 기타 모바일 Apple OS는 지원 대상이 아니며,
정책 검증 단계에서 DFU 업로드 전에 거부됩니다. 이 계층의 복구 범위는
macOS용 DFU/IPSW이고 Local Recovery 기본 파일명은 `_default.ipsw`입니다.

둘 다 `macos_boot_verified`를 `false`로 유지합니다. OVMF 테스트는 iBoot나
XNU를 로드하지 않고, VMApple 테스트는 Apple 복구 프로토콜까지의 관찰만
기록합니다.

## OVMF EFI 창

WSL Ubuntu에서 clang, QEMU, OVMF와 테스트 번들이 준비되어 있을 때 다음
명령을 실행합니다.

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

`--gui`는 GTK 창을 하나만 열고, EFI의 debug-exit 결과와 debug console을
수집합니다. `--display none`이 기본값인 전체 3-case 검증은 CI용으로
사용합니다. GUI를 사용하려면 `--case valid`처럼 단일 case를 선택해야
합니다. `QEMU_SYSTEM_X86_64`, `OVMF_CODE`, `OVMF_VARS` 환경 변수로 경로를
지정할 수도 있습니다.

성공적인 GUI 보고서에는 다음 값이 함께 있어야 합니다.

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

보고서는 QEMU 버전과 OVMF 코드/변수 템플릿의 SHA-256도 기록합니다. 이
정보는 창이 생성되었다는 사실과 EFI 입력 검증 결과를 같은 실험으로
재현하기 위한 것입니다.

## VMApple 복구 창(연구용)

VMApple은 OVMF와 다른 AArch64 머신입니다. 별도로 빌드한 연구용 QEMU가
`vmapple` 머신과 GTK를 제공할 때만 다음 형태로 실행합니다.

```sh
qemu-system-aarch64 \
  -M vmapple,research-headless=on,uuid=0 \
  -accel tcg,thread=single \
  -cpu max,pauth=on,cntfrq=24000000 \
  -m 4G -smp 2 \
  -bios /path/to/AVPBooter.vmapple2.bin \
  -display gtk -monitor none -nic none -no-reboot \
  -global vmapple-cfg.optional-rpc-unavailable=on \
  -global vmapple-bdif.allow-block-writes=on \
  -blockdev '<COW overlay over an immutable AUX fixture>' \
  -blockdev '<COW overlay over an immutable root fixture>'
```

복구 입력은 반드시 원본 파일을 별도로 해시하고, AUX/root는 빈 raw 기반의
COW overlay를 사용합니다. 원본 IPSW, 기존 ESP 또는 물리 디스크를 QEMU의
쓰기 대상으로 지정하지 않습니다. 개발자 host bypass를 사용한 실험은
로컬 연구 로그에만 남기며 제품 번들·배포 경로에는 포함하지 않습니다.

26x86 GUI의 `Apple Silicon Sandbox` 단계에서 같은 런너를 사용할 수 있습니다.
`VMApple QEMU`, `qemu-img`, `AVPBooter`, 개인화 iBSS/iBEC, AUX/root 원본과
새 출력 폴더를 입력하고 `GTK VM 창 열기`를 누르면 로컬 브리지의
`launch_vmapple`이 실행됩니다. Windows GUI에서 QEMU나 입력이 `/home/...` 같은
WSL 경로이면 브리지는 셸을 거치지 않고 `wsl.exe --cd ... --exec python3 -m x86
vmapple run --research-only --json`을 시작하며 WSLg의 GTK 창을 사용합니다.
경로는 모두 명시적 인자로 전달되고, 기존 출력 폴더는 런너가 거부합니다.
실행 결과는 입력 폴더의 `launch.json`에 기록되며, GUI 응답의 PID와 로그 경로로
프로세스를 추적할 수 있습니다.

동일한 경로는 CLI에서도 다음처럼 호출할 수 있습니다.

```sh
python3 -m x86 vmapple run --target 27 --display gtk \
  --qemu /home/developer/.../qemu-system-aarch64 \
  --qemu-img /usr/bin/qemu-img \
  --firmware /path/to/AVPBooter.vmapple2.bin \
  --ibss /path/to/iBSS.personalized.img4 \
  --ibec /path/to/iBEC.personalized.img4 \
  --aux /path/to/aux.raw --root /path/to/root.raw \
  --output /tmp/26x86-vmapple-run --research-only --json
```

`--research-only`는 배포 금지 개발 플래그이며 생략할 수 없습니다. 런너는
reset 뒤 실제 USB descriptor를 다시 읽어 bulk OUT endpoint 4가 확인될 때만
iBEC 업로드를 시도합니다. `05ac:1227` iBSS DFU가 유지되면
`transition_state: transition-blocked`로 종료하고 어떠한 강제 전환도 수행하지
않습니다.

CLI/GUI의 `machine_type`, `guest_os`, `recovery_protocol`,
`recovery_image_name` 값은 동일한 iBoot 정책 검증기를 통과해야 합니다.
`guest_os=iOS` 또는 `guest_os=iPadOS`를 넣으면 `VF_GUEST_SCOPE_VIOLATION`,
`recovery_protocol=Fastboot`를 넣으면 `VF_RECOVERY_SCOPE_VIOLATION`이
반환되며 QEMU 프로세스와 USB 전송은 시작되지 않습니다.

현재 확인된 VMApple GUI 범위는 원본 27.0 iBSS의 173개 DFU 블록 전송(DFU
suffix 포함),
`WAIT_RESET`, USB reset acknowledgement와 재열거입니다. iBSS가 서명을
수락했다는 응답, iBEC/XNU 실행, 그래픽 로그인 화면은 확인되지 않았습니다.
따라서 VMApple 창이 열렸거나 DFU 전송이 완료되어도 Golden Gate 부팅
성공으로 판정하지 않습니다. 재현 실험의 요약은
[`integration/vmapple-gui-recovery-report.json`](../integration/vmapple-gui-recovery-report.json)에
고정되어 있습니다.

## 결과 판정

QEMU GUI 검증은 개발 중인 EFI/JIT 및 복구 USB 계층의 재현성을 높입니다.
실제 제품 판정에는 다음 단계가 별도로 필요합니다.

1. 물리 Intel Mac에서 OpenCore가 `Sandbox.efi`를 로드하는지 확인합니다.
2. EFI에서 `ExitBootServices`, VMX/EPT, VT-d/인터럽트 리매핑을 실제 하드웨어
   상태로 확인합니다.
3. 원본 iBoot가 AIC 장치 모델과 저장장치를 통해 XNU까지 진입하는지 확인합니다.
4. macOS 26/27 사용자 공간과 GPU/Metal을 별도 로그로 확인합니다.

이 중 하나라도 완료되지 않은 보고서는 EFI 자체 검사 또는 복구 프로토콜
증거로만 보존합니다.
