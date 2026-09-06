# Apple 원본 펌웨어 실행과 복구 경로

다루는 계층은 **VMApple 장치 모델 → 원본 AVPBooter → 공식 Apple 개인화 iBSS/iBEC → 원본 ARM64e XNU**다. 021에서 x86_64 Linux/WSL TCG 위의 XNU EL1 실행을 원본 명령 바이트와 실제 커널 console ring으로 확인했다. 현재 가장 멀리 확인한 단계는 IOKit 전원 관리 watchdog panic이며 macOS 설치·복원 사용자 공간·부팅 완료는 아직 확인하지 못했다. 아래는 최초 ROM 실패부터 장치 모델 수정, 실제 단계별 실행에 이르는 증거다.

## 원본 확보

사용자가 이미 보유한 `C:/Users/Admin/Downloads/macOS_Monterey_12_6_1.iso`를 읽기 전용으로 열었다. 다른 Mac에서 펌웨어를 가져오거나 macOS를 호스트에 설치하지 않고 필요한 파일을 확보했다.

- ISO 크기: 13,639,653,376바이트.
- ISO SHA-256: `f5c91576cc0c1ae94394eb52c46c11904d320de0f553ef10f10c94ec6718a643`.
- HFS 멤버 `Install macOS Monterey/Install macOS Monterey.app/Contents/SharedSupport/SharedSupport.dmg`: 12,399,095,056바이트.
- 중첩 DMG 멤버 `Shared Support/com_apple_MobileAsset_MacSoftwareUpdate/3a30a133b90552c8e80475e5d0d5462b521bd5d2.zip`: 11,486,783,850바이트.
- OTA 멤버 `AssetData/payloadv2/payload.031`: PBZX/XZ 압축의 YAA 파일 스트림. 압축 해제 크기 1,147,031,314바이트.
- YAA 정규 파일 `System/Library/Frameworks/Virtualization.framework/Versions/A/Resources/AVPBooter.vmapple2.bin`: 164,440바이트.
- **AVPBooter SHA-256**: `bff6e4dd750f206aa06dc8f2510ff7484b0be8412754bd1c2558dbccbe26ba5a`.
- 원본 내부 버전 문자열: `iBoot-7459.141.1`.

ISO의 기본 ISO9660 뷰는 SharedSupport.dmg의 크기를 4,294,967,295바이트로 표시했다. 완전한 HFS+ 뷰(`7z -tHFS`)를 지정해야 4GiB에서 잘린 사본을 피할 수 있다. 암호 해제, 업데이트 델타 적용, 실행 코드 수정은 하지 않았다. YAA의 정확한 정규 파일 멤버를 복사했다.

`tools/apple_assets.py`는 7-Zip 아카이브 멤버 추출과 Python 표준 라이브러리 PBZX/XZ/YAA 추출을 제공한다. 파일은 배타적으로 새로 생성하며, 원본 경로·크기·시각, ZIP CRC32, 압축 및 해제 페이로드 SHA-256, YAA 헤더/본문 오프셋, 결과 SHA-256을 영수증으로 남긴다. CRC와 해시는 바이트 동일성 검증이며 Apple 서명 검증과 구별한다. YAA 헤더에는 해당 파일의 별도 SH2 해시가 없었다.

포맷은 [blacktop/ipsw의 YAA 구현](https://github.com/blacktop/ipsw/blob/cf022ce7e5afb6a34d2ebfb95766797f17c3dd2f/pkg/ota/yaa/yaa.go)과 실제 아카이브 바이트를 대조했다. 참조 저장소 고정 커밋은 `cf022ce7e5afb6a34d2ebfb95766797f17c3dd2f`이다. macOS 전용 `aa` 실행 파일에 의존하지 않는다.

프로젝트 루트에서 재현하는 추출 명령은 다음과 같다. 출력 파일이 이미 있으면 덮어쓰지 않고 실패한다.

```powershell
python outputs/venfire/tools/apple_assets.py extract C:/Users/Admin/Downloads/macOS_Monterey_12_6_1.iso --type HFS --member "Install macOS Monterey/Install macOS Monterey.app/Contents/SharedSupport/SharedSupport.dmg" --output work/apple-assets/Monterey-SharedSupport.dmg
python outputs/venfire/tools/apple_assets.py extract work/apple-assets/Monterey-SharedSupport.dmg --member "Shared Support/com_apple_MobileAsset_MacSoftwareUpdate/3a30a133b90552c8e80475e5d0d5462b521bd5d2.zip" --output work/apple-assets/Monterey-MacSoftwareUpdate.zip
python outputs/venfire/tools/apple_assets.py extract-ota work/apple-assets/Monterey-MacSoftwareUpdate.zip --payload AssetData/payloadv2/payload.031 --member System/Library/Frameworks/Virtualization.framework/Versions/A/Resources/AVPBooter.vmapple2.bin --output work/apple-assets/firmware/AVPBooter.vmapple2.bin
```

같은 OTA의 BuildManifest는 macOS **12.6.1 / 21G217**, 장치 `vma2macosap`, BDID `0x20`, CPID `0xFE00`, 보안 도메인 `0x01`을 명시한다. 해당 복구 구성의 최소값은 CPU 2개, 메모리 4096MiB, 호스트 버전 12.0.0이다. 첫 ROM 진단은 CPU 1개로 실행했으므로 복구 설치 구성을 검증한 것이 아니다.

## 확보된 복구 컴포넌트의 범위

동일 ZIP에서 iBSS, iBEC, LLB, iBoot, DeviceTree, VMApple kernelcache, `apticket.vma2macosap.im4m`, BuildManifest와 Restore.plist를 그대로 추출했다. 인벤토리는 `work/apple-assets/components/inventory.json`, 압축된 VMApple 구성 정보는 `work/apple-assets/components/vmapple-build-manifest.json`에 있다. 별도 ARM64e 복구 RAM 디스크도 아카이브에 존재한다.

IM4P 파일, IM4M 티켓의 존재와 해당 VM이 수락하는 개인화된 IMG4/AUX가 준비되었다는 것은 서로 다른 상태다. 본 실험은 타 VM의 티켓·LocalPolicy·키를 가져오지 않았고 서명을 무효화하지 않았다. 추출한 티켓이 새 VM 복구에 유효하다는 판단도 하지 않았다.

[Apple의 설치 문서](https://developer.apple.com/documentation/virtualization/installing-macos-on-a-virtual-machine)는 복구 이미지, 호환 플랫폼 구성, 설치를 순서대로 요구한다. [VZMacAuxiliaryStorage 문서](https://developer.apple.com/documentation/virtualization/vzmacauxiliarystorage)는 AUX와 hardwareModel의 일치, 설치 프로그램에 의한 AUX 데이터 배치, 주 디스크와 AUX의 동반 보존을 명시한다. [플랫폼 구성 문서](https://developer.apple.com/documentation/virtualization/vzmacplatformconfiguration)는 기존 VM의 hardwareModel·machineIdentifier·AUX를 원래 값으로 복구하도록 설명한다.

## 실제 ROM 실행에서 확인한 실패

비공개 개발 프로파일과 명시적인 `--developer-host-bypass`로 Windows/WSL의 Intel+AVX2 호스트를 승인했다. CPU 요구, 입력 무결성, ARM PAuth 의미론은 유지했다. Apple ROM은 `-bios`, AUX와 root는 읽기 전용 `pflash` 뷰로 전달했다. 진단용 AUX 64MiB와 root 128MiB는 모두 0으로 채워진 **미설치 저장소**이며 UUID 0은 진단 구성값이다.

기준 실행은 20초 제한 전에 QEMU 종료 코드 0으로 끝났다. 원본·AUX·root·백엔드 네 파일의 실행 전후 SHA-256은 일치했다. 시리얼 출력은 없었고 macOS 부팅 성공 신호도 없었다. 코드 0의 실제 원인은 뒤의 실행 추적에서 확인한 **펌웨어의 재시작 요청과 `-no-reboot`**였다.

1. ROM 시작 PC는 `0x100000`이다. AVPBooter가 자체 EL0/EL1 실행 환경을 구성하고 SVC/PAuth 코드를 실행했다.
2. BDIF에서 root와 AUX 장치를 초기화했고, AUX 오프셋 0에서 512바이트를 성공적으로 읽었다. 빈 AUX에서 설치된 다음 단계를 얻지 못한 후 복구 경로로 진행했다.
3. USB 장치 주소는 `0x30100000`이다. ROM `0x107264`의 계산 `0x30000000 + (0x10 << 16)` 및 실행 레지스터로 확인했다.
4. 초기화 함수 `0x106a40`에 기대 프로토콜 값 `X1=0x1a01`이 전달됐다. QEMU는 `0x30100004` 읽기에 블록 장치용 값 `2`를 반환했다. `0x106a8c` 비교가 실패하며 반환값은 `0xfffffffd`(-3)이었다.
5. 실패 경로가 USB 상태를 해제했다. 이후 `0x1075a8`의 `str x0,[x8,#48]`에서 NULL 포인터에 접근했다. **ESR `0x92000047`, FAR `0x30`, ELR `0x1075a8`**이다. 상태 포인터 슬롯은 `0x700296c8`이다.
6. ROM이 pvpanic에 crash-loaded 이벤트를 쓰고 PSCI `SYSTEM_RESET`(`X0=0x84000009`)을 요청했다. 따라서 정상 프로세스 종료 코드는 게스트 부팅 성공을 뜻하지 않는다.

원본 로그는 `work/apple-assets/boot-probe-001`, 전체 명령 추적은 `boot-trace-002`, 예외/PSCI 레지스터 추적은 `boot-trace-003`, USB 초기화 레지스터·BDIF 증거는 `boot-trace-004`이다. `-dfilter`는 BDIF 이벤트에도 적용되므로 특정 주소만 추적한 로그에서 I/O가 없다고 판단하면 안 된다. 이 때문에 최종 판정은 더 넓은 범위의 004 로그와 교차 검증했다.

## 복구 USB 장치 패치

[QEMU 원저자의 BDIF 패치 설명](https://lists.gnu.org/archive/html/qemu-block/2025-01/msg00206.html)은 USB OTG를 구현하지 않았으며 이 경로가 게스트 복구에 필요하다고 명시한다. 따라서 확인된 문제는 누락된 **호스트 장치 모델**에 속한다.

`patches/0003-vmapple-recovery-usb.patch`는 [Anees Iqbal의 공개 DMA 전송 구현](https://github.com/steelbrain/experiment-macOS-arm64-on-asahi-linux-arm64/blob/657bb2423ec8d572b22a97dd33563dbba1680e6a/patches/vmapple-usb-chardev.patch)을 검토하고 보완했다. 원본 저장소 커밋은 `657bb2423ec8d572b22a97dd33563dbba1680e6a`, 원래 패치 커밋은 `e8714ab84bc76b89091fb2ccb41c34e69e4ae9a2`이다. 다른 저장소의 게스트 코드 수정과 상태 응답 대체는 포함하지 않는다.

- `usbdev` chardev를 명시했을 때만 USB 프로토콜 `0x1a01`을 제공한다.
- 큐 0은 호스트 프레임을 원본 ROM이 게시한 수신 버퍼에 DMA로 복사한다. 실제 복사가 성공해야 완료 비트를 제공한다.
- 큐 1은 원본 ROM이 만든 응답 버퍼를 읽어 호스트에 보낸다. DMA 읽기와 호스트 전송의 성공 여부를 확인한다. USB descriptor나 DFU 상태를 호스트가 대신 만들어 반환하지 않는다.
- 관찰된 16바이트 단일 descriptor를 지원하고 다른 flags/chain 형태는 성공 처리하지 않는다. 프레임 경계와 구현상의 최대 길이를 검사한다.
- 소켓에는 LE32 길이 접두사를 사용한다. 이는 호스트 간 전송 규약이며 Apple 게스트 내부 프로토콜이나 보안 검증을 변경하지 않는다.
- 비동기 송신 큐는 아직 구현하지 않았다. 현재 상한은 1 MiB+6의 DMA 패킷과 4바이트 소켓 접두사다. 동기 chardev 쓰기가 느린 상대를 기다릴 수 있으므로 현재 실험은 시간 제한과 로컬 소켓으로 실행한다. 이 상한이 쓰기 지연까지 제한하지는 않는다.

## 원본 ROM의 실제 USB 응답

0001+0002+0003를 빌드한 x86_64 QEMU에서 CPU 2개, RAM 4GiB로 수행한 `recovery-usb-007` 검증은 성공했다. 여덟 번의 실제 USB 제어 요청과 원본 응답을 기록했다.

- Apple DFU 식별자: **`05ac:1227`**.
- Device descriptor 18바이트: `1201000200000040ac052712000002030401`.
- Configuration descriptor 25바이트: `0902190001010580fa0904000000fe0100000721010a000008`.
- SET_ADDRESS, SET_CONFIGURATION에 원본 ROM이 빈 데이터의 정상 제어 응답을 반환했다.
- DFU GETSTATE의 실제 데이터: **`02`**.
- DFU GETSTATUS의 실제 6바이트 데이터: **`003200000200`**. 상태 바이트 0, poll timeout 50ms, DFU 상태 2이다. 빈 응답을 치환하지 않았다.
- 원본 ROM의 USB 문자열은 `SDOM:01 CPID:FE00 CPRV:00 CPFM:03 SCEP:01 BDID:20 ECID:0000000000000000 IBFL:3C SRTG:[iBoot-7459.141.1]`이었다. ECID 0은 이번 진단에 지정한 VM 값이다.
- 펌웨어·진단 AUX·진단 root·백엔드 네 파일의 전후 SHA-256이 모두 일치했다.

직전 005/006 실험은 송신 큐의 초기 ready 비트를 완료 비트로만 해석해서 실패했다. 원본 ROM `0x1078e8`은 첫 송신 descriptor를 게시하기 **전에** 큐 1의 가용 상태를 읽는다. 따라서 초기 빈 송신 큐는 ready이며, 읽기로 ready를 지우지 않는다. 실제 송신이 시작하면 ready를 내리고 DMA와 호스트 전송이 모두 끝나야 다시 올린다. 이 수정 후 007에서 원본 응답을 받았다.

이 결과가 증명하는 범위는 **수정하지 않은 Apple 부트 ROM의 실행, 복구 USB 초기화, 양방향 DMA, 실제 DFU 제어 통신**이다. 서명된 다음 부트 단계 수락, AUX 구성, XNU 진입, macOS 설치/부팅은 아직 별도 검증 대상이다. 로그와 입력 매니페스트는 `work/apple-assets/recovery-usb-007/`에 보존했다.

## DFU OUT 전송 규약의 독립 복원

008에서 같은 ROM의 단순 소켓 재접속, descriptor/GETSTATE/GETSTATUS 재조회가 통과했다. USB 문자열 descriptor 1에서 원본 NONC/SNON을 얻었다. 이는 [libirecovery의 nonce 조회](https://github.com/libimobiledevice/libirecovery/blob/95dec3aa25b1e30654ca107eb971971f6a216520/src/libirecovery.c)의 표준 GET_DESCRIPTOR 경로와 일치한다. nonce 값은 세션별 비공개 작업 파일에만 기록하며 다른 세션이나 기기의 값을 이식하지 않는다. 일반 소켓 재접속은 아직 유효한 게시 RX 버퍼를 유지한다. USB bus reset이나 장치 disable은 별도 동작이다.

공개 참고 클라이언트의 `type 3 = DATA_OUT` 해석은 이번 원본 AVPBooter에서 성립하지 않았다. 010/011에서 이 형태로 2048바이트를 전송하면 type 5 ACK만 받았고, 다음 GETSTATUS의 데이터가 비었다. 재조회한 실제 응답은 `093200000a00`, 즉 errNOTDONE/state 10이었다. 이를 정상 상태로 치환하지 않았다.

원본 어셈블리와 실행 추적으로 다음을 구분했다.

- `0x1073f0`의 type 3 분기는 `0x107470`에서 endpoint 대기열을 취소하고 type 5 ACK를 보낸다. DFU 데이터 콜백을 호출하지 않는다.
- type 2는 `0x1074dc`에서 type 4 ACK를 보낸다. 실제 콜백 `0x10db64`는 이를 `0x108e10(event=2)`의 USB bus reset으로 전달한다.
- type 1의 콜백 `0x10dbac..0x10dc34`는 필요할 때 앞 8바이트 SETUP과 뒤의 OUT 데이터를 내부 큐로 나눈다. 따라서 DFU OUT은 **SETUP+데이터를 하나의 type 1 프레임**으로 보낸다.
- 2048바이트 DNLOAD의 DMA 프레임은 6바이트 `<int32 length, uint8 endpoint, uint8 type>` + 8바이트 SETUP + 2048바이트 데이터로 총 2062바이트다. 이는 원본이 게시한 RX 버퍼 크기 `0x80e`와 일치한다.

016/017에서 이 규약을 실행했다. 자체 생성한 `a5` 2048바이트의 SHA-256은 `9c9b3365a5704fb1bbd5dbac227ecc2e878dedce86338eca2ec1278e21ac1a9e`다. 실제 단일 DMA 프레임의 헤더는 `080800000001`, 길이는 2062, SHA-256은 `1f50e3b34b6d038f4b3c7ae6d6b62742d51708346a16460b9bf195211f358eb1`이다. 원본 응답 `0100` 뒤 GETSTATUS가 실제 **`003200000500`**을 반환했다. 표준 DFU CRC suffix를 별도 블록으로 보낸 뒤에도 state 5였다. Zero-length DNLOAD 뒤 실제 status 6, status 7, GETSTATE 8을 관찰했고 USB reset의 실제 type 4 ACK도 받았다. 이 단계의 통과는 데이터 전달과 DFU 상태기계에 관한 증거이며, 자체 데이터가 서명 검사를 통과했다는 뜻이 아니다.

`venfire/recovery.py`는 이 결과에 맞춘 OUT 프레이밍과 `send_dfu_file` API를 제공한다. 입력을 안전한 읽기 전용 regular-file 경로로 읽고 전후 매니페스트를 확인한다. 2048바이트 블록과 표준 DFU suffix를 전송하고 실제 6바이트 GETSTATUS를 검사한다. 제어 전송별 제한과 전체 업로드의 절대 시한을 함께 적용한다. 비정상 응답·상태·시간 초과는 부분 진행을 포함한 `RecoveryUploadError.report`로 보고한다. `transfer_complete`는 실제 WAIT_RESET 상태를 뜻하며 서명 수락이나 macOS 부팅을 뜻하지 않는다. 관련 12개 테스트에는 분할 소켓 응답, 실제 OUT 프레임 구성, 오류 상태 보존, 절대 시한, symlink 거절, 취소 시 무결성 검사가 포함된다.

## 공식 개인화 iBSS 전송과 다음 장치 종료 문제

012와 018에서 각각 새 VM의 실제 nonce로 Apple TSS에 요청했고, TLS 인증서와 호스트 이름 검증을 유지한 HTTPS 응답 `STATUS=0`과 `ApImg4Ticket`을 받았다. iBSS의 원본 IM4P SHA-256은 계속 `c063245ed47e3026e48fb93a1b3b2cfd320d1e8acf9373c046d65ed2c853a4c5`이며, 공식 restore BuildManifest의 컴포넌트 digest와 대조했다. 개인화 컨테이너 안의 원본 payload는 변경하지 않았다. 세션마다 티켓이 달라지므로 다른 세션의 IMG4를 재사용하지 않았다.

각 318720바이트 개인화 iBSS와 DFU suffix를 156개 블록으로 전송했다. 모든 블록에서 실제 state 5, manifest에서 실제 6/7/8, reset 전에 실제 GETSTATE 8, USB reset ACK를 확인했다. 이후 descriptor 재조회는 시간 초과였고 UART 출력은 없었다. 입력 원본·AUX·root·백엔드·개인화 IMG4 다섯 파일의 전후 SHA-256은 일치했다.

018의 QMP 레지스터와 명령어 기록은 PC **`0x106c0c`**를 보여준다. 이는 iBSS가 아닌 원본 AVPBooter의 장치 종료 루틴이다. `0x106c00`에서 USB MMIO `0x30100404`에 0을 쓰고 `0x106c0c`에서 0이 될 때까지 읽는다. 기존 QEMU에서는 이 레지스터가 미구현이라 `-1`을 반환했다. 초기화 `0x106afc`는 같은 레지스터에 1 또는 3을 기록한다.

0003의 추가 lifecycle 구현은 관찰한 0/1/3 control 값을 보존한다. Disable은 수신 버퍼 소유권·주소·ready·남은 프레임을 취소하고 기존 연결을 끊는다. 현재 DMA와 송신이 동기식이므로 이 정리가 끝난 MMIO 쓰기 이후에 control 0을 읽을 수 있다. Disabled 상태의 새 수신/DMA는 차단한다. 무조건 성공을 반환하거나 게스트 종료 루틴을 건너뛰지 않는다. 이 수정은 019의 실제 qtest MMIO/DMA 검증과 020/021의 원본 iBSS 실행으로 검증했다.


## 원본 iBSS 및 iBEC 실행 확인: 020/021

020에서 원본 AVPBooter의 종료 루프를 통과한 후 UART에 `Supervisor iBootStage1 for vma2`, `iBoot-7459.141.1`, `Entering iBootStage1 recovery mode, starting command prompt`가 나타났다. iBSS 실행은 확인됐지만 USB 재조회가 실패했다. 원본 iBSS payload의 메모리 재배치 기준 주소는 실행 바이트 대조로 `0x7006c000`이다. 이 기준의 `0x7007e328..0x7007e340`은 recovery 모드에서 수신 용량을 1 MiB+6으로 설정하고, 실제 descriptor 기록도 `len=0x100006, flags=2`였다. 기존 128 KiB 구현 상한이 이 descriptor를 거부했다. 이는 펌웨어 수정이나 서명 문제가 아닌 장치 모델의 버퍼 용량 문제였다.

0003의 상한을 관찰된 1 MiB+6으로 맞췄고 Python `MAX_FRAME`도 일치시켰다. DMA는 descriptor 용량 전체가 아닌 실제 수신 패킷 길이만 복사한다. `tools/verify_recovery.py`는 게스트를 `-S`로 정지한 상태에서 자체 생성 데이터만 사용한다. 실제 MMIO/DMA로 disable·부분 프레임 취소·재접속·소유권 취소·단회 완료·큰 수신 버퍼·초과 용량 거절을 검증했다. 12개 확인 항목과 세 입력 파일·QEMU 전후 해시가 통과했고 `evidence/recovery-lifecycle.json`에 기록했다. 실행 예:

```sh
python3 tools/verify_recovery.py --qemu /absolute/path/qemu-system-aarch64 --output recovery-lifecycle.json
```

021은 수정된 QEMU로 새 nonce를 생성하고 Apple TSS에서 새 iBSS 티켓을 받아 원본을 다시 전송했다. iBSS UART와 함께 실제 USB descriptor가 `05ac:1281` recovery 모드로 바뀌었고, 이 단계가 반환한 새 NONC/SNON을 읽었다. 실제 DFU GETSTATE는 이제 지원하지 않는 요청으로 거절됐다. 이를 DFU 상태로 변환하지 않았다. 해당 독립 증거는 `evidence/apple-ibss.json`에 있다.

이후 같은 세션의 새 nonce를 사용해 Apple TSS에서 iBEC와 표준 restore LocalPolicy에 대한 두 개의 실제 STATUS=0 응답을 받았다. LocalPolicy는 다음 단계 티켓의 SHA-384에 결합되며 자체 서명이나 정책 완화로 대체하지 않는다. 원본 iBEC payload의 바이트는 계속 불변이다.

[libirecovery의 실제 복구 전송](https://github.com/libimobiledevice/libirecovery/blob/95dec3aa25b1e30654ca107eb971971f6a216520/src/libirecovery.c)에 맞춰 vendor request `0x41/0`으로 수신을 준비하고, endpoint 4로 32 KiB씩 원본 바이트를 보낸다. DFU suffix는 추가하지 않는다. 파일 길이가 512의 배수이면 실제 zero-length bulk 전송도 보낸다. 명령은 `0x40` OUT control에 NUL로 끝나는 원본 문자열을 싣는다. `lpolrestore`는 request 0, `go`는 request 1이다. descriptor의 실제 endpoint와 ACK endpoint를 검사한다. interface 0은 libirecovery에서 호스트 측 claim만 수행하므로 불필요한 SET_INTERFACE 0 요청을 추가하지 않는다.

021에서 공식 서명 LocalPolicy 3039바이트 전달과 `lpolrestore` ACK, 개인화 iBEC 351614바이트의 11개 bulk 전송과 `go` ACK가 확인됐다. 이어 UART가 `End of iBootStage1 serial output`에서 `Supervisor iBootStage2 for vma2`로 전환했고 `Entering iBootStage2 recovery mode, starting command prompt`를 출력했다. 실제 원본 iBEC 실행과 iBootStage2 복구 모드 진입 증거는 `evidence/apple-ibec.json`에 있다. 이는 별도의 guest UART 관찰로 확인했으며 전송 API의 ACK 성공만으로 부팅 성공을 추론하지 않았다.

원본 AUX/root는 아직 진단용 빈 읽기 전용 파일이다. 이 결과는 설치된 macOS나 유효하게 초기화된 VM 디스크, XNU 진입을 증명하지 않는다. 티켓·nonce·개인화 이미지·원본 Apple 바이너리는 공개 산출물에 포함하지 않는다. 처음부터 `-trace file=<세션>/transport.log`가 USB trace와 명령어 기록을 세션별로 분리했다. 021 실행 도중 HMP `logfile`도 전용 경로로 명시했다. 단계 전환의 공개 증거는 해당 세션의 UART와 USB 응답이다. 복구 모드 API를 포함한 프로토콜 테스트 15개가 통과했다.

## 원본 restore 컴포넌트와 XNU 실행: 021의 후속 단계

021의 같은 iBootStage2 세션에서 공식 12.6.1 restore ramdisk, trust cache, Device Tree, kernelcache를 전송하고 **원본 ARM64e XNU가 EL1에서 실행되는 것을 확인했다**. 이후 IOKit 전원 관리 watchdog panic으로 정지했다. 복원 사용자 공간이나 macOS 설치 완료는 확인되지 않았다. 공개 증거는 `evidence/apple-kernel-entry.json`이다.

원본 컴포넌트는 공식 IPSW의 ZIP CRC와 BuildManifest digest에 대조했다. [idevicerestore img4.c](https://github.com/libimobiledevice/idevicerestore/blob/540c352c4c44896f7415abef87a166e8bbaea9b0/src/img4.c)의 표준 restore 개인화는 IM4P의 역할 필드 네 바이트를 `krnl→rkrn`, `dtre→rdtr`, `logo→rlgo`로 바꾼다. `rdsk`와 이미 `rtsc`인 파일은 그대로다. `venfire/restore.py`는 DER 구조의 정확한 역할 필드만 바꾸고, 변경 밖의 바이트·실행 코드와 데이터 OCTET·원본 파일을 보존한다. 준비된 컨테이너의 공식 Restore digest 및 OCTET 전후 SHA-256을 검증한다. Apple 티켓을 넣는 IMG4 래핑도 IM4P와 IM4M 원본 바이트를 보존한다. 증거는 `evidence/restore-role-metadata.json`이다. 이 표준 메타데이터 처리에 대한 승인을 받은 범위이며, 펌웨어 코드 패치나 서명 우회가 아니다.

다른 공식 TSS 응답을 같은 nonce로 새로 받는 것만으로는 기존 부트 체인과 일치하지 않았다. 새 batch 티켓을 사용한 첫 시도에서 게스트는 ramdisk를 거절했다. 이후 실제 현재 nonce·VM identity와 기존 iBEC 개인화 자료를 다시 대조하고, 이미 수락된 LocalPolicy가 결합한 **같은 iBEC Apple 티켓**을 표준 `client->tss` 흐름대로 재사용했다. 다른 VM이나 이전 nonce의 티켓을 사용하지 않았다. 이 시도에서 ramdisk `0x9fc9800`바이트와 Device Tree가 실제로 로드됐으며 원본 kernelcache가 이어 실행됐다. `tools/restore_stage.py --boot`는 `--chain-personalization`으로 기존 iBEC/LocalPolicy 개인화 디렉터리를 지정해야 한다. 해당 경로에서는 현재 VM과 기존 자료를 검증하는 `reuse_restore_ticket`을 호출하고 새 TSS 티켓을 받지 않는다. 이 인자가 없는 독립 batch TSS 발급은 진단·준비용이며 `--boot`를 거절한다.

[표준 recovery.c 순서](https://github.com/libimobiledevice/idevicerestore/blob/540c352c4c44896f7415abef87a166e8bbaea9b0/src/recovery.c)를 따라 trust cache의 `firmware`, ramdisk의 `ramdisk`, Device Tree의 `devicetree`, 커널 전송 및 `bootx`를 수행했다. 커널 실행 직전 `0x21/1` 알림은 원본 게스트가 실제 STALL `0200`을 반환했다. upstream은 이 알림의 반환값을 사용하지 않는다. API는 정확한 STALL을 실패 응답으로 남기고 표준 다음 명령으로 진행한다. 다른 프로토콜 오류·전송 실패를 무시하지 않는다. 명령 전송 성공과 커널 실행 검증은 별도 값으로 기록한다. 최신 recovery/restore 회귀 테스트 23개가 통과했다.

커널 실행 검증은 PC 주소만으로 판단하지 않았다. 원본은 `xnu-8020.240.7~1/RELEASE_ARM64_VMAPPLE`, Darwin 21.6.0의 60,325,888바이트 ARM64e Mach-O payload다. 원본 고유 문자열과 게스트 가상 메모리의 일치로 KASLR slide `0x1adc8000`을 확인했다. 최종 PC 및 FP 체인 반환 지점의 **14개 96바이트 명령 구간**을 읽어 원본 파일의 해당 구간과 대조했으며 모두 SHA-256이 같았다. 최종 CPU0 PC는 `0xfffffe00224e8f80`, PSTATE는 `0x804033c4`, EL1t였다. 실제 게스트 console ring도 읽기 전용 QMP 메모리 저장으로 확보했다. AppleImage4 validator, AMFI의 UDID enforcement, Seatbelt, Quarantine, 424개 항목의 외부 trust cache 로딩 메시지가 있었다.

최초 panic 호출 `0xfffffe0022ab5930`은 원본 `_panic`으로 `Sleep/Wake hang detected @%s:%d`, `IOPMrootDomain.cpp`, 줄 번호 12600을 전달했다. 최종 정지 PC의 `b .` 명령도 원본과 동일하다. 이는 **XNU IOKit 전원 관리 watchdog** 계층으로 원인을 좁힌 결과이며, 아직 어떤 장치나 전원 전환이 지연됐는지는 확인하지 못했다. [관련 공개 XNU 8020.140.41 소스](https://github.com/apple-oss-distributions/xnu/blob/27b03b360a988dfd3dfdf34262bb0042026747cc/iokit/Kernel/IOPMrootDomain.cpp#L11673)도 ARM `sleepWakeDebugTrig`의 동일한 panic 역할을 보여준다. 이 공개 소스는 실행한 8020.240.7과 정확히 같은 버전이 아니므로 주소와 줄 번호의 근거는 실제 원본 바이너리와 게스트 스택이다.

이번 오래된 실행 구성에는 읽기 전용 빈 AUX/root, virtio PCI root/AUX 장치 부재, Apple PV 그래픽 부재가 남았다. CPU1도 최종 관찰에서 reset 상태였다. console ring에는 NVRAM nonce seed 부재와 IOResources 등록 오류가 기록됐다. 이 사실을 특정 단일 원인으로 단정하거나 watchdog을 끄는 방식으로 넘어가지 않는다. 다음 실험은 원본을 보존하는 COW 디스크와 실제 장치 요청의 완료 상태를 확보하면서 게스트 초기화·전원 전환 로그를 다시 관찰해야 한다.

021 종료 직전 독립적인 읽기 전용 검토에서 더 구체적인 시간 불일치를 확인했다. 두 QEMU CPU의 `cntfrq`는 1GHz였으나 공식 원본 Device Tree의 `timebase-frequency`와 실행 중 XNU의 환산 변수는 24MHz, 즉 `125/3 ns`였다. 게스트가 시간을 약 41.67배 빠르게 해석하는 조건이다. PM workloop의 원본 스택은 정상 전원 요청 처리 도중 선점된 상태였으며 특정 GPU 응답 지연을 입증하지 않았다. 이후 Apple 실행에서는 호스트 CPU 모델의 `cntfrq=24000000`으로 주파수를 맞춘다. 이는 게스트 코드나 watchdog 정책을 바꾸지 않는 가상 하드웨어 수정이다. 해당 주파수로 XNU를 다시 실행해 panic이 해소되는지 확인하는 단계는 별도다. 021을 정상 종료한 뒤 ROM·원본 AUX·원본 root·백엔드 네 파일의 SHA-256은 모두 일치했다.

## 원본 27.0 / 26A5425a 복원 경로

공식 Apple CDN의 27.0 / 26A5425a IPSW 전체 22,740,609,058바이트를 확보했고 1,485개 ZIP 항목의 CRC를 검증했다. 전체 SHA-256은 `71a339de0fafd6ef75a5fdecd64def62ff642aab4e5d10b384e035b388bcd1c8`, 공식 BuildManifest의 SHA-256은 `4137196616826e4e8eca265eedea52bc59c925113dd96bf2a59460075080a364`다. 같은 `vma2macosap`, CPID `fe00`, BDID `20` 구성의 원본 iBSS와 iBEC를 사용했다. [공식 restore 이미지](https://updates.cdn-apple.com/2026SummerSeed/b3d7996f-4f91-4586-842a-345c550d7d47/UniversalMac_27.0_26A5425a_Restore.ipsw)의 실행 코드는 수정하지 않았다.

초기 27 iBSS는 AUX 쓰기 요청이 실패한 뒤 panic했다. 기존 upstream BDIF는 iBoot이 읽기만 한다는 가정으로 WRITE 명령을 구현하지 않았다. 0004에서 실제 guest DMA 읽기→COW 블록 쓰기→실제 결과 상태 반환을 구현하고, 명시적으로 켠 개발 세션에서 같은 AUX/root 블록 노드를 BDIF와 virtio 양쪽에 연결했다. 원본 기반 파일은 읽기 전용으로 유지했다. 이 수정의 004 실행에서는 Apple TSS의 실제 티켓으로 개인화한 **원본 `mBoot-20457.1.29` iBSS가 Microkernel iBootStage1 복원 프롬프트에 도달했다**. 같은 세션의 총 세 건 AUX 쓰기가 실제 성공했고, 종료 뒤 ROM·원본 AUX·원본 root·백엔드 네 파일의 해시는 일치했다. 독립 증거는 `evidence/apple-ibss-27.json`이다.

004와 24MHz 대조 실행 005에서 새 실제 nonce를 사용해 공식 iBEC와 LocalPolicy 티켓을 각각 발급받았다. `lpolrestore`와 `go` ACK 다음 실제 UART가 iBootStage2 시작을 출력했다. 이어 동일한 `4962211b03d706d:203` panic으로 정지했다. 005에서 일반 예외 처리기 이전의 원인은 **EL0 Data Abort, ESR `0x92000050`, FAR `0x4ffff8`, ELR `0x700b0200`**으로 확인됐다. 해당 명령은 원본 iBEC의 `str x0,[x8]`이며 원본 디코드 파일과 게스트 명령 구간도 일치했다. 24MHz에서도 발생했으므로 이 iBEC 오류를 021 XNU의 시간 불일치와 혼동하지 않는다.

원본 iBEC는 `0x4fc000`의 새 인터페이스 영역을 초기화하고 `0x4ffff8`에 요청의 물리 주소를 기록한다. 그 뒤 요청 구조에 대한 호스트의 완료·결과를 확인한다. 기존 QEMU의 config RAM 범위는 `0x400000..0x40ffff`이므로 이 주소가 매핑되어 있지 않았다. 호출자는 요청이 실패할 경우 기존 config 필드에서 `SCfg` 구조를 만드는 대체 경로도 갖는다. 원본 27 restore ramdisk 220,200,987바이트, kernelcache 23,128,927바이트와 나머지 세 컴포넌트는 이미 읽기 전용 추출 및 공식 Restore digest 대조를 마쳤다. 이 자료의 존재는 iBEC 이후의 실행 완료를 뜻하지 않는다.

005의 원본 iBEC 요청 함수 `0x700b0190`은 스택에 24바이트를 만든다. 앞 네 바이트는 little-endian `0x00010001`로, 16비트 version 1, byte 2의 type 1, byte 3의 초기 completion 0이다. 이어 32비트 opcode 2, 64비트 입력 물리 주소, 64비트 인자 `0x500000`을 기록한다. `0x700b0200`의 64비트 store 이후 version, completion, 결과를 검사한다. **completion byte가 원래의 0이면 반환값 -1**이며, 호출자의 `0x70086ad4` 경로가 기존 config를 읽어 `SCfg`를 만든다. 성공 분기는 별도의 `vmvp` 구조를 만든다. 이 부분의 의미는 원본 바이너리와 실제 게스트 코드의 세 구간 대조로 확인했으며, Apple 호스트 RPC 서비스의 전체 ABI를 복원했다는 뜻은 아니다.

0007은 명시적으로 켜는 **실험적 optional RPC unavailable** 장치다. `-global vmapple-cfg.optional-rpc-unavailable=on`일 때만 16 KiB 영역이 활성화된다. 정확한 doorbell의 정렬된 64비트 쓰기와 관찰한 version/type/opcode만 다룬다. 요청 주소가 실제 MachineState RAM의 연속 24바이트인지 확인한 뒤 그 헤더만 읽고 trace에 원래 필드를 남긴다. 펌웨어 RAM·config RAM·MMIO·빈 주소·범위 초과는 거절한다. 입력 데이터 포인터는 따라가지 않으며 DMA 쓰기는 없다. 버스 쓰기가 끝나도 요청의 completion, 상태, 결과 및 모든 데이터 바이트는 원래 그대로다. 따라서 원본의 명시적인 실패 분기가 실행될 수 있다. 지원하지 않는 주소·읽기·형식은 버스 오류다. 장치가 정상 Apple RPC를 구현한다거나 요청이 성공했다고 주장하지 않는다. 기본 설정은 비활성이다.

자체 바이트를 쓰는 `tools/verify_optional_rpc.py`는 `-S` qtest에서 기본 비활성, 요청/주변 guard/payload 불변, 완료 byte 0 보존, firmware/config/MMIO/빈 주소/정수 초과/부분 RAM, 잘못된 헤더·opcode·크기·정렬, 오류 후 재요청을 검사한다. 이 장치 검증과 원본 iBEC의 실제 fallback 확인은 별도의 결과로 기록한다. 005를 종료한 뒤 원본 ROM·AUX·root·백엔드 네 해시가 일치했다.
