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

OVMF 테스트는 항상 `macos_boot_verified=false`입니다. VMApple은 이제
`--boot-selection macos`에서 복구 전송을 건너뛰고 AVPBooter의 정상 macOS
항목을 직접 관찰합니다. 다만 `Darwin Kernel Version`과 `launchd`,
`loginwindow`, `WindowServer` UART 증거가 모두 확인될 때만
`macos_boot_verified=true`가 되며, Recovery 선택은 기존처럼 복구
프로토콜 경계만 기록합니다.

## qemu-t8030에서 가져온 Apple Silicon 장치 프로필

`qemu-t8030`의 [Bringing up the emulator 문서](https://github.com/TrungNguyen1909/qemu-t8030/wiki/Bringing-up-the-emulator)와
소스는 Apple AIC, Apple ANS/NVMe, DART/SART, Apple UART, NVRAM, SMC,
USB OTG/Type-C, 그리고 `m1_fb`/`xnu_ramfb` 계열의 장치 토폴로지를
보여줍니다. 이 저장소는 iPhone 11/T8030 iOS 에뮬레이터이며 현재
[보관(archived) 상태](https://github.com/TrungNguyen1909/qemu-t8030)이므로,
26x86은 그 펌웨어·iOS device tree·복구 스크립트를 가져오지 않습니다.
구성 요소의 이름과 연결 관계만 Apple Silicon Sandbox의 조사 입력으로
기록하고, 게스트 정책은 계속 `iBoot(AArch64) → macOS`로 고정합니다.

현재 구현의 경계는 다음과 같습니다.

* EFI Sandbox는 AIC 전용 계약을 유지하고, 저장소의 first-party `aic_v1`
  유선 IRQ 모델만 부분적으로 갖습니다. GIC 호환 경로를 추가하지 않습니다.
* VMApple QEMU TCG 연구 머신은 아직 GICv3와 VMApple BDIF(AUX/root)를
  사용합니다. 따라서 qemu-t8030의 AIC/ANS/DART/SART를 지원한다고 표시하지
  않으며, `macos_boot_verified`를 올리지 않습니다.
* qemu-t8030 문서에 나온 NVMe namespace 예시는 `nsid=1` 데이터와
  `nsid=5` Apple NVRAM을 **참조 값**으로만 기록합니다. macOS용 AUX/root
  레이아웃과 동일하다고 추론하지 않고 hardware-model provisioning 영수증을
  계속 요구합니다.
* 현재 TCG 연구 실행에는 Apple PV graphics가 없으므로 `m1_fb` 또는
  `xnu_ramfb` 이름만으로 설치 화면·Metal을 주장하지 않습니다.

프로필은 입력 파일을 열거나 수정하지 않고 확인할 수 있습니다.

```sh
python3 -m x86 vmapple capabilities
```

출력의 `reference` 블록은 qemu-t8030의 고정된 조사 리비전과 iOS 전용
범위를, `interrupt_controller`, `device_topology`, `storage` 블록은
현재 26x86 구현과 남은 차이를 각각 보여줍니다. 이 명령은 QEMU를 시작하지
않으며 부팅 또는 설치 성공을 의미하지 않습니다.

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
`vmapple` 머신을 제공해야 합니다. 표시 백엔드는 `auto`를 기본으로 사용하며,
native Apple Silicon/macOS에서는 Cocoa를 선택하고 Linux/WSL 연구 빌드에서는
QEMU가 광고한 headless 백엔드(`none` 등)를 선택합니다. GTK/SDL은 해당 빌드가
실제로 광고할 때만 명시적으로 선택할 수 있습니다.

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

`allow-block-writes`는 26x86 write-enabled BDIF 패치가 `-device
vmapple-bdif,help`에서 광고할 때만 런너가 자동으로 추가합니다. upstream BDIF가
그 속성을 제공하지 않으면 알 수 없는 `-global`을 전달하지 않고 읽기/부팅
관찰을 계속하며, 보고서의 `backend.bdif_block_writes=false`로 기능 차이를
명시합니다.

복구 입력은 반드시 원본 파일을 별도로 해시하고, AUX/root는 빈 raw 기반의
COW overlay를 사용합니다. 원본 IPSW, 기존 ESP 또는 물리 디스크를 QEMU의
쓰기 대상으로 지정하지 않습니다. `Apple M1 (Virtual)` / `VM0001`은
게스트가 선택한 VMApple 메타데이터이며 Apple 기기 인증이나 호환성 보증이
아닙니다. 개발자 host bypass를 사용한 실험은 로컬 연구 로그에만 남기며
제품 번들·배포 경로에는 포함하지 않습니다. `optional-rpc-unavailable`은
원본 iBEC의 선택 RPC 실패 경계를 확인하는 별도 음성 실험이므로 기본 명령에
넣지 않습니다.

26x86 GUI의 `Apple Silicon Sandbox` 단계에서 같은 런너를 사용할 수 있습니다.
`VMApple QEMU`, `qemu-img`, `AVPBooter`, 공식 BuildManifest, TSS 요청 도구,
변경하지 않은 원본 iBSS/iBEC, AUX/root 원본과 새 출력 폴더를 입력하고
`VM 창 열기`를 누르면 로컬 브리지의 `launch_vmapple`이 실행됩니다.
GUI 기본 경로는 현재 USB nonce를 읽어 Apple TSS에 요청하고 새 출력 폴더에만
개인화 IMG4를 만듭니다. Windows GUI에서 QEMU나 입력이 `/home/...` 같은 WSL
경로이면 브리지는 셸을 거치지 않고 `wsl.exe --cd ... --exec python3 -m x86
vmapple run --live-personalize --research-only --json`을 시작하며 WSLg의 GTK
창을 사용합니다.
경로는 모두 명시적 인자로 전달되고, 기존 출력 폴더는 런너가 거부합니다.
실행 결과는 입력 폴더의 `launch.json`에 기록되며, GUI 응답의 PID와 로그 경로로
프로세스를 추적할 수 있습니다.

실행 전에 GUI의 `2초 부트 피커 시작`을 누르고 2초 안에 Alt/Option을 입력해야
합니다. 피커에서 `macOS Recovery · _default.ipsw`를 선택하면 `Recovery VM 창
열기`가 활성화되고, 브리지는 실제 DOM 입력 기록을
`--boot-picker-trigger alt-enter`로 worker에 전달합니다. 시간 안에 Alt를
누르지 않으면 정상 macOS 항목이 선택됩니다. 직접 macOS 선택에서는
iBSS/iBEC 개인화나 DFU 전송을 수행하지 않고, AVPBooter가 프로비저닝된
AUX/root에서 부팅하는 동안 UART 증거를 관찰합니다. Recovery 선택만
iBSS/iBEC 입력과 DFU/IPSW 체인을 요구합니다.

직접 macOS 부팅은 다음처럼 호출할 수 있습니다. `--ibss`, `--ibec`,
`--live-personalize`, `--restore-chain`은 이 모드에서 사용하지 않습니다.

Virtualization.framework로 만든 VM은 `macosvm.json`과 같은 디렉터리에 있는
`machineId`, `hardwareModel`, `aux.img`, `disk.img`를 하나의 입력 계약으로
사용하는 것이 권장됩니다. 런너는 두 plist를 읽기 전용으로 해시하고 ECID를
검증한 뒤, JSON이 가리키는 AUX/root와 다른 수동 경로를 섞지 않습니다. 원본
`aux.img`의 첫 `0x4000` 바이트는 VMApple 메타데이터이므로 JSON 경로에서는
QEMU의 문서화된 AUX 뷰 오프셋 `0x4000`을 자동 적용합니다. 원본 이미지를
자르거나 덮어쓰지 않으며, 실행 중에는 두 원본 위에 새 qcow2 COW overlay만
만듭니다. 이 동작은 [QEMU VMApple 문서](https://www.qemu.org/docs/master/system/arm/vmapple.html)의
`dd ... bs=0x4000 skip=1` 요구사항과 일치합니다.

```sh
python3 -m x86 vmapple run --target 27 --display auto \
  --qemu /path/to/qemu-system-aarch64 \
  --qemu-img /usr/bin/qemu-img \
  --firmware /System/Library/Frameworks/Virtualization.framework/Resources/AVPBooter.vmapple2.bin \
  --vm-json /path/to/macosvm.json \
  --output /tmp/26x86-goldengate-direct --boot-selection macos \
  --boot-delay 2 --duration 600 --research-only --json
```

JSON을 사용하지 않는 경우에는 기존처럼 이미 올바른 AUX 뷰를 가리키는
`--aux`와 `--root`를 직접 지정하고, 원본 AUX를 직접 지정할 때만
`--aux-offset 0x4000`을 명시합니다. 읽기 전용 사전 검사는 다음처럼 같은
번들 계약을 사용할 수 있습니다.

```sh
python3 -m x86 vmapple inspect-storage --vm-json /path/to/macosvm.json --json
```

```sh
python3 -m x86 vmapple run --target 27 --display auto \
  --qemu /path/to/qemu-system-aarch64 \
  --qemu-img /usr/bin/qemu-img \
  --firmware /System/Library/Frameworks/Virtualization.framework/Resources/AVPBooter.vmapple2.bin \
  --aux /path/to/provisioned-aux.raw --root /path/to/provisioned-root.raw \
  --aux-offset 0 \
  --output /tmp/26x86-goldengate-direct --boot-selection macos \
  --boot-delay 2 --duration 600 --research-only --json
```

직접 실행의 `launch.json`에는 `direct_boot.dfu_entered=false`와 각 UART
marker의 절대 offset이 남습니다. marker가 없으면 런너는
`direct-boot-evidence-timeout`으로 종료하고 `macos_boot_verified=false`를
유지합니다. AUX/root가 zero-filled이거나 hardware-model provisioning
receipt가 없다는 사실은 별도의 storage blocker로 함께 기록됩니다.

동일한 경로는 CLI에서도 다음처럼 호출할 수 있습니다.

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

`--research-only`는 배포 금지 개발 플래그이며 생략할 수 없습니다. 런너는
원본 BuildManifest의 `Customer Erase Install (IPSW)` identity와 실제 USB
CPID/BDID/SDOM/nonce를 함께 검증하고, Apple TSS status `0` 및 IM4M을 받은
뒤에만 새 IMG4를 만듭니다. reset 뒤 실제 USB descriptor를 다시 읽어 bulk
OUT endpoint 4가 확인될 때만 iBEC 업로드를 시도합니다. `05ac:1227` iBSS
DFU가 유지되면 `transition_state: transition-blocked`로 종료하고 어떠한
강제 전환도 수행하지 않습니다. 입력 해시가 실행 중 바뀌면 산출물을
삭제하고 실패합니다.

CLI/GUI의 `machine_type`, `guest_os`, `recovery_protocol`,
`recovery_image_name` 값은 동일한 iBoot 정책 검증기를 통과해야 합니다.
`guest_os=iOS` 또는 `guest_os=iPadOS`를 넣으면 `VF_GUEST_SCOPE_VIOLATION`,
`recovery_protocol=Fastboot`를 넣으면 `VF_RECOVERY_SCOPE_VIOLATION`이
반환되며 QEMU 프로세스와 USB 전송은 시작되지 않습니다.

실행 전에는 GUI의 `AUX · root 설치 대상 검사`를 사용하거나 CLI의 읽기 전용
검사를 먼저 실행할 수 있습니다.

```sh
python3 -m x86 vmapple inspect-storage \
  --aux /path/to/aux.raw --root /path/to/root.raw --aux-offset 0
```

검사는 원본 파일을 열어 쓰지 않고, 512바이트 정렬 뷰의 크기와 제한된
zero-content 범위, 일부 APFS 표식만 기록합니다. `provisioning_status`가
`unprovisioned-zero` 또는 `partially-unprovisioned`이면 해당 파일은 프로토콜
경계 실험용일 뿐 설치 대상이 아닙니다. 0이 아닌 바이트나 `NXSB` 표식만으로는 Apple Silicon
hardware-model과 일치하는 `VZMacAuxiliaryStorage`, APFS 설치 대상, 서명된
부팅 가능성을 증명할 수 없으므로 상태는 `unverified`로 남습니다. 이 검사는
IPSW/설치 파일을 추출·복호화·변조하지 않으며, 입력 파일을 별도 출력 폴더에
복사하지도 않습니다.

최신 확인된 VMApple GUI 범위는 원본 27.0 iBSS의 173개 DFU 블록 전송(DFU
suffix 포함), `WAIT_RESET`, USB reset acknowledgement, 실제 `05ac:1281`
재열거와 bulk OUT endpoint 4, LocalPolicy/iBEC 전송 및 `go` acknowledgement
입니다. Apple TSS status `0`, nonce 일치, 원본 payload 해시 보존과
`installer_modified: false`도 확인했습니다. 선택적 RPC 비가용성 실험에서
원본 iBEC의 Stage2 UART command prompt를 관찰했고, 이어서 BuildManifest와
일치하는 다섯 개 restore role을 전송했습니다. pre-boot 알림에서는 게스트의
실제 `0200` STALL을 성공으로 바꾸지 않고 기록한 뒤 `bootx` acknowledgement를
받았지만, iBoot가 XNU 이전에 패닉했습니다. 따라서
`signature_acceptance_verified`, `xnu_executed`, `macos_boot_verified`와
Golden Gate 설치 UI는 모두 `false`입니다. Linux QEMU 빌드에는 Apple
ParavirtualizedGraphics 장치가 없어 `graphics_device_enabled`도 `false`입니다.
VMApple 창이 열렸거나 DFU/`go`/`bootx`가 완료되어도 Golden Gate 부팅 성공으로
판정하지 않습니다. 2초 게이트의 실제 Alt→Recovery 입력을 포함한 실행 요약은
[`integration/vmapple-gui-bootpicker-report.json`](../integration/vmapple-gui-bootpicker-report.json)에
고정되어 있으며, 원본 전체 `launch.json`은 보고서의 `source_report` 경로에서
확인할 수 있습니다.

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
