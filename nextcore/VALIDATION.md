# Nextcore 재개 검증 — 2026-09-07

전체 작업의 통합 설명과 artifact index는
`artifacts/NEXTCORE_SESSION_REPORT_20260907.md`에 있다.

## 현재 상태와 원하는 상태

첨부 세션의 우선순위인 APLS 실행과 QEMU/OVMF 검증을 병렬로 이어서 실제
프로세스/펌웨어까지 연결했다. macOS 부팅, XNU 진입, userspace, Metal 가속은
아직 완료되지 않았다. 최종 목표는 이 각각을 실제 게스트에서 관측하는 것이다.
`docs/NEXTCORE_BUILD_PLAN.md` BP8~BP14가 재개 실행 계약이다.

재개 시 존재하던 7-crate workspace와 dirty 문서/Python 변경을 보존했다.
`nextcore/`는 기존 루트 `.gitignore`의 `/nextcore/`에 의해 제외된 로컬
작업 트리이며 이번 실행에서 Git 추적 정책을 바꾸거나 커밋/push하지 않았다.

## 확인된 구현과 근거

1. **사용자 공간 / EFI 패키징**: `nextcore-tool build`와 `install-usb`가
   `NXC0` 더미를 만들던 경로를 제거했다. 명시 `--efi`의 AMD64 PE32+ EFI
   application 구조를 검증하고, 입력 검증 후 새 파일로 복사·읽기 비교한다.
   기존 출력/self-copy/hardlink 원본은 덮어쓰지 않는다.
   최종 번들은 `artifacts/efi-bundle-20260907/EFI/`에 있다.
2. **UEFI Boot Services / 파일 I/O**: 실제 EFI가 자기 부팅 볼륨에서
   `\EFI\OC\config.plist`를 읽는다. 1..1,048,576바이트만 허용하고 부분
   읽기/EOF를 처리한다. 표준 Serial I/O에 EFI 진입과 읽기 결과를 기록한다.
   BP9에서 no_std XML `Misc.Entries` 파서를 연결했다. 0개/복수 선택과
   XML/경로/상한 오류를 구분하며 UCS-2 경로와 UTF-16 옵션을 검증한다.
   같은 볼륨의 명시 application을 `LoadImage→StartImage`로 실행하고,
   자가 참조와 resident driver를 거부한다. 부모는 ExitBootServices를 먼저
   호출하지 않는다. BP11에서 별도 NXKERNEL의 공개 ABI 준비와 CPU 진입
   프로브를 추가했다. 실제 XNU 운영체제 인계 완료와는 구분한다.
3. **APLS 호스트 실행**: Rust `RunnerRequest`와 `nextcore-tool apls run`이
   명시한 native/local 또는 TCG/WSL worker를 실행하고 종료를 회수한다.
   요청/명령/PID/stdout/stderr/adapter receipt를 새 디렉터리에 보존한다.
   실제 Windows→WSL→Python→QEMU→ARM firmware 실행을 확인했다.
4. **QEMU 관측**: log backend에서 `-trace file=`가 `-D`를 덮는 결함을
   수정했다. 공용 `qemu.debug.log`에서 CPU와 PSCI 증거를 각각 읽으며 큰
   파일은 head/tail 범위와 byte offset을 기록한다. 원본 로그는 유지하고
   1 MiB 합계 sample을 별도로 남긴다.

## BP9 현재 실행 결과

- Rust workspace **135 passed, 1 ignored**. 최신 로그는
  `artifacts/workspace-chainload-final-tests-20260907.log`.
- ignored 실제 EFI 복사 통합 시험은 별도 **1 passed**:
  `artifacts/compiled-chainload-copy-tests-20260907.log`.
- core **37 passed**, no-default 파서 **12 passed**와 no_std UEFI target check
  통과. `artifacts/boot-config-review-20260907.md`에서 독립 검토 결과 확인.
- EFI release build, host check, 패키징 모두 통과. 배포용 파일은
  `artifacts/efi-chainload-bundle-20260907/EFI/BOOT/BOOTX64.EFI`이며 빌드본과
  SHA-256 `b4082331c5f8ed0f9cfa84b5bd4e9c61b0c08f42baba7e6c4c750a431cce37e8`
  가 일치한다.
- 최종 번들로 실제 OVMF **12/12 passed**. 설정 없음/빈 파일/상한/잘못된 XML,
  0개 target/대상 파일 누락/자가 참조, child 정상·오류 반환, 빈 옵션과
  한글·보충 문자 UTF-16LE 전달, resident driver 실행 전 거부를 확인했다.
  `artifacts/ovmf-chainload-final-20260907/report.json` 및 독립 재해시·프로세스
  확인 `independent-readback.json`에 기록. 원본 5개 해시 유지, QEMU 모두 종료.
  **이 결과는 EFI application 인계이며 XNU/macOS/Metal 성공이 아니다.**
- 독립 리뷰 2건을 수정했다: resident driver 반환 뒤 LoadOptions 수명,
  core에서 허용하지만 UEFI CString16이 거부하는 non-BMP 경로. 해당 수정 후
  실행/파서 시험을 다시 통과했다. `artifacts/efi-chainload-review-20260907.md`.
- 요청한 실행 절차를 `nextcore-boot-engineering` 개인 스킬과 재사용 프롬프트로
  저장했다. 구조 검증과 독립 시나리오 3건을 통과했고, 로그의 동일 실행 출처
  및 매체 역할/실행 버전 구분을 보강했다. `artifacts/skill-review-20260907.md`.

## BP10 정상 AVP entry 관측

같은 macOS 27.0 / 26A5425a 원본의 AVPBooter를 현재 fixture에 사용한 관측을
완료했다. 실행 상한은 20초였고 실제 0.605초 후 게스트가 PSCI_SYSTEM_RESET을
요청해 `-no-reboot`인 QEMU가 종료했다. AUX 읽기 33회는 모두 성공했고 root
I/O와 UART 출력, XNU/userspace는 없었다. 정상 entry에서도 부팅 상태 또는
입력 레이아웃의 내부 판단은 아직 규명되지 않았다. reset을 부팅 성공이나
호스트 오류로 표시하지 않는다. 원본 4개 pre/post hash 일치, 대상 PID 종료.

`artifacts/apls-diagnosis-20260907/avp27-observation.json`에서 공개 MMIO/ARM
exception/PSCI 관측을 확인할 수 있다. normalized command는 firmware 경로,
research-stage2 모드 및 진단 `exec` logging 유무가 달랐다. AVP worker는
translation-block logging을 켜지 않았으므로 TB count를 비교하지 않는다.
전량 230,557바이트의 예외/장치/PSCI 로그를 스캔했고 원본을 보존했다.

`input-candidates.md`의 좁은 기존 입력 조사에서는 초기화된 native VM tuple을
확인하지 못했다. 설명형 identity, reused AUX 및 추출 RestoreRamDisk/OS 이미지의
역할을 설치 완료 디스크와 구분한다. 이 결과를 바탕으로 같은 모델의 정상
restore chain 또는 실제 provisioning 결과가 생성하는 boot-state를 확인하는
것이 다음 작업이다. 펌웨어/원본 매체를 수정한 실험은 없다.

## BP11 공개 XNU ABI와 실제 EFI 메모리 배치

- 공개 XNU `xnu-12377.121.6`의 진입 소스와 wire layout을 고정했다.
  `artifacts/xnu-entry-contract-20260907.md`에 출처와 소비자 검증이 있다.
  EFI64인 boot_args와 32비트 pstart 진입 모드를 구분하며, 이 버전이 현재
  ARM 복원 이미지와 일치한다고 주장하지 않는다.
- `macho_image` no_std 파서, `LoadedKernel`의 실제 AllocateAddress/복사/
  zero-fill/readback, 4096-byte boot_args encoder, bounded flattened DT codec을
  구현했다. 원본 plan을 재파싱해 일치시킨 뒤 배치하며 VA→PA 변환은 명시
  `xnu-12377-pstart32` 프로필만 담당한다. LC_MAIN은 generic parser가 지원해도
  이 프로필에서는 실행 전 거부한다.
- `NXKERNEL.EFI`는 `Nextcore/Kernel`의 Profile/Path/Arguments를 읽고
  standalone x86_64 Mach-O를 정확한 저위 물리 주소에 배치한다. 기본 빌드는
  `PROVIDERS_PENDING`으로 반환한다. `kernel-probe` feature는 자체 작성
  fixture의 EBS/최종 메모리 맵/ABI/CPU 전환 시험용이며 배포 기본값이 아니다.
  NMI는 CLI로 차단되지 않는다. 현재 전환 계약은 SMM off와 NMI 주입이 없는
  통제된 QEMU q35에 한정하며 실제 하드웨어 NMI 전환을 검증했다고 보지 않는다.
- core **71 passed**, host workspace **169 passed, 1 ignored**.
  `artifacts/workspace-kernel-handoff-tests-20260907.log`.
  실제 EFI 복사 ignored test는 별도 **1 passed**:
  `artifacts/compiled-kernel-efi-copy-tests-20260907.log`.
  default/probe EFI target release 빌드 모두 통과했다.
- 기존 EFI application 회귀는 새 parser/build로 **12/12 OVMF passed**.
  `artifacts/ovmf-kernel-parser-regression-final-20260907/report.json`과
  `independent-readback.json`에 원본 5개 재해시 일치와 child 종료를 기록했다.
  첫 DrvFS 출력 시험은 serial polling의 `OSError 61`로 호스트 관측이 중단돼
  성공으로 세지 않았다. 해당 child는 finally에서 수거됐고 WSL `/tmp`의
  새 출력으로 실행한 위 12건이 완료된 근거다.
- 독립 검토에서 발견한 LC_MAIN 진입 종류 누락을 수정했다.
  `artifacts/kernel-handoff-review-20260907.md`.
- 새 커널 경로의 실제 OVMF 시험 **8/8 passed**: 정상 자체 probe 1건과
  production provider gate, truncated/FILESET/profile/LC_MAIN/표식 누락 거부,
  guest의 DATA 손상 검출 7건이다. 정상 경로는 정확한 물리 배치
  base=0x100000/entry=0x101000 뒤 EBS를 통과하고, CPU 상태/boot_args/
  전달 map/140-byte fixture DT/DATA 전체/BSS 전체를 guest가 검사했다.
  1.906초 후 QEMU가 debug-exit **33**으로 자연 종료했으며 하네스 kill이 아니다.
  DATA 손상은 loader의 source readback 후 독립 guest 검사에서 FAIL_DATA와
  자연 종료 **35**로 검출돼 성공 마커만 출력하는 시험이 아님을 확인했다.
  일반 DT 순회나 운영체제 필수 노드 충분성을 이 fixture로 검증하지 않는다.
- 증거는 `artifacts/ovmf-kernel-positive-20260907/report.json`과
  `artifacts/ovmf-kernel-negatives-20260907/report.json`. 루트가 입력 8개의
  hash를 독립 재확인하고 잔존 QEMU가 없음을 확인했다:
  `artifacts/kernel-probe-independent-readback-20260907.json`.
  이 결과는 **EFI→자체 32비트 프로브 실행**이며 XNU/macOS/Metal=false다.

## BP12~BP13 정상 복원 경로의 전진 경계

BP12는 현재 AVP27/VM JSON/AUX/root를 유지한 정상 DFU recovery 관측이다.
matching manifest의 iBSS/iBEC와 정상 personalization으로 Stage2 banner까지
진행했으나 prompt 전 DataAbort로 종료됐다. AUX79 read/3 write 및 root2 read는
모두 성공했다. ASR 부재나 root 쓰기 실패를 이 실패의 원인으로 단정하지 않는다.

BP13은 같은 명령과 원본 입력에 기존 default-off optional RPC adapter 하나만
켠 비교다. 이 adapter는 원래 completion/result를 보존하며 성공을 합성하지 않는다.
Stage2 prompt, restore role **5종**, `bootx` ACK까지 진행됐다. AUX117 read/3 write,
root2 read, optional RPC request1/completion unchanged1을 전량 trace에서 확인했다.
bootx 전후 PC가 바뀌었고 실행 블록 259,145개를 관측했으나 firmware panic이
남았으며 Darwin/userspace는 관측하지 못했다. macOS boot=false다.

BP14의 같은-event host callback 관측에서 VA=PA, 4-byte `MMU_DATA_LOAD`,
mmu_idx 0, `MEMTX_DECODE_ERROR`를 확인했다. 실제 실행의 QMP flatview 25개
범위에도 PA mapping이 없었다. 따라서 최초 실패는 bootx 뒤 decode되지 않은
물리 read로 좁혀졌다. 장치 정체와 올바른 register contract는 여전히 미확정이며
임의 zero-return 장치나 펌웨어 패치는 추가하지 않았다.

BP12 15.671초, BP13 42.693초로 각각 실행 상한 내였다. 원본 13개 hash 유지와
대상 프로세스 종료를 루트가 독립 재확인했다. 공개 결과는
`artifacts/apls-restore-contract-20260907/`의 comparison/observation/full-trace-counts
및 `independent-readback.json`이며 raw register/trace/ticket은 격리 경로에 유지했다.
초기 bounded sample count와 별도 전량 count를 혼합하지 않는다.

BP14 재시도는 Stage2 prompt, 복원 5종, bootx ACK 뒤 동일 firmware panic을
재현했고 XNU/userspace/macOS는 false다. debugger는 일치 event 1건만 읽고
guest/device 값을 바꾸지 않은 채 detach했다. 총 44.469초, 원본 13개 hash
동일, worker/wrapper/QEMU/GDB 잔존 0이다. 첫 시도의 GDB argv 오류는 guest/TSS/
DFU 실행 0인 실패로 별도 보존했고, 두 번째 시도 전 복합 argv round-trip과
descendant cleanup 합성 시험을 통과했다. 공개 근거는
`artifacts/apls-restore-contract-20260907/bp14-same-event-transaction.json`,
`normal-recovery-translation-b-observation.json`, `bp14b-argv-roundtrip.json`이다.
정확한 주소·레지스터·debugger 원문은 `_isolated/`에만 있다.

실제 RestoreDeviceTree의 bus range를 적용한 읽기 전용 조사에서는 BP14 fault를
포함하는 `reg` node가 하나 있었다. 비교 입력에서는 일치 node가 없었다. 그러나
그 node를 구현할 공개 장치 interface/register contract는 찾지 못했으므로 장치
정체는 미확정이고 모델 응답도 추가하지 않았다. 공개 요약은
`artifacts/apls-restore-contract-20260907/bp14-device-contract-survey.json`이다.

## BP15 Nextcore 정상 recovery adapter

Rust APLS에 명시 `tcg-recovery` backend를 추가하고 기존 Python normal recovery를
Linux supervisor로 감쌌다. supervisor는 새 session의 worker/descendant를
monotonic deadline 안에서 수거하고, VM JSON이 지정한 AUX/root를 포함한 원본
입력의 pre/post hash를 비교한다. raw QEMU PID는 같은 session에서 실제 관측한
유일한 PID/starttime과 일치해야 runtime 근거가 된다. 요청 output 원문과
canonical worker output을 분리하여 상대 경로도 안전하게 검증한다.

합성/독립 검증은 Python supervisor **17 passed**, Rust runner **17 passed**,
CLI **9 passed**다. 기존 `x86.test_vmapple_tcg`와 함께 실행한 Python 회귀는
**40 passed**다. 독립 리뷰는
`artifacts/apls-recovery-adapter-review-20260907.md`에 있으며 미해결 finding은
없다. 저장된 BP14 report는 당시 PID ledger가 없으므로 strict offline 판정에서
runtime/boot=false를 유지했다.

최종 host workspace 회귀는 **169 passed, 1 ignored**이고 `cargo check
--workspace --exclude nextcore-efi`도 통과했다. 기존 `nextcore-ise`의 unused 경고
4건은 실패가 아니며 이번 BP15 소유 파일의 변경 사항이 아니다. 로그는
`artifacts/workspace-tests-bp15-20260907.log`와
`artifacts/python-recovery-tests-20260907.log`에 보존했다.

새 adapter를 통한 실제 정상 recovery 1회는 48.365초에 Nextcore exit **2**로
끝났다. DFU, iBEC endpoint, Stage2 banner/prompt, 복원 역할 **5종**, sequence와
`bootx` ACK를 확인한 뒤 firmware panic이 발생했다. supervisor는 raw QEMU PID의
same-session 상관=true, cleanup complete=true, remaining PID 0, deadline 미초과,
입력 15개 pre/post hash 일치를 기록했다. XNU/userspace/목표 커널 major는
관측되지 않았고 macOS boot=false다. 결과는
`artifacts/apls-supervised-recovery-result-20260907.md`, 전체 host receipt는
`artifacts/apls-supervised-recovery-host-20260907/`에 있다.
독립 요약과 receipt hash는
`artifacts/apls-supervised-recovery-independent-check-20260907.json`에 있다.

## BP16 공개 MMIO 계약 조사

세 갈래 독립 조사 결과는 모두 **HOLD**다. pinned VMApple machine에는 QEMU
PL031이 이미 존재하지만 그 mapping은 선택 DeviceTree node 범위와 겹치지 않는다.
선택 compatible은 ARM/PL031 binding과 일치하지 않고 role 속성이 없으며 문제
read의 상대 offset도 PL031 정상 register/ID coverage 밖이다. PL031 alias는
bad-offset fallback을 정상 장치 응답으로 오인하게 되므로 추가하지 않았다.

Linux/OpenBSD의 Apple SMC RTC/NVMEM은 다른 transport다. Apple Virtualization의
Mac hardware model/AUX는 opaque platform state이고 custom Virtio와 공개 GPU MMIO
API는 host-supplied device의 선례지만 이번 장치의 register, reset, 반환값과
side effect를 정의하지 않는다. reset 시점 CPU system flatview 16개와 고정 machine
map의 noncoverage, same-event `MEMTX_DECODE_ERROR`를 분리했으며 reset snapshot을
fault 순간 snapshot으로 표현하지 않았다. 코드 수정과 추가 VM 실행은 없다.

공개 근거:

- `artifacts/apls-restore-contract-20260907/bp16-public-contract-survey.md`
- `artifacts/apls-restore-contract-20260907/bp16-public-contract-survey.json`
- `artifacts/apls-restore-contract-20260907/bp16-qemu-coverage-review.md`
- `artifacts/apls-restore-contract-20260907/bp16-qemu-coverage-review.json`
- `artifacts/apls-restore-contract-20260907/bp16-host-interface-survey.md`
- `artifacts/apls-restore-contract-20260907/bp16-host-interface-survey.json`

정확한 주소, node 원문과 offset은 `_isolated/`의 private receipt에만 있다.

## BP8 실행 이력

- Rust host 회귀: **123 passed, 1 ignored**.
  `artifacts/workspace-tests-20260907.log`.
- 실제 컴파일 EFI를 사용하는 ignored 통합 시험을 별도로 명시 실행:
  **1 passed**. `artifacts/compiled-efi-copy-tests-20260907.log`.
- Python TCG/boot-evidence 회귀: **32 passed, 1 skipped**.
  Windows PATH의 QEMU probe만 제외됐으며 실제 QEMU는 WSL에서 별도 실행했다.
  `artifacts/python-evidence-tests-20260907.log`.
- host check와 UEFI target check 모두 통과:
  `artifacts/host-check-20260907.log`, `artifacts/uefi-check-20260907.log`.
  최초 `cargo check --workspace`는 Windows target에 no_std EFI까지 포함해
  unwind 오류를 냈다. host/firmware target을 분리한 명령이 올바른 게이트다.
- 실제 EFI release 빌드: `target/x86_64-unknown-uefi/release/BOOTX64.efi`.
  당시 번들 복사본과 SHA-256가 동일했다. 현재 BP9 바이너리는 후속 결과를 본다.
- 패키징한 EFI의 OVMF 실행: **4/4 passed** (설정 읽기, 누락, 빈 파일,
  상한 초과). EFI/config/OVMF code/OVMF vars 원본 4개 해시 유지.
  `artifacts/ovmf-bundle-20260907/report.json`.
- 직접 작성한 AArch64 프로그램의 VMApple TCG 보정 시험: **passed**.
  QMP에서 X0가 0→42로 변했고 PC가 입력 프로그램 내 다음 명령으로 이동했다.
  이는 CPU 에뮬레이터 실행 증거이며 macOS 실행 증거가 아니다.
  `artifacts/cpu-probe-20260907/report.json`.
- 최종 APLS CLI 실매체 실행:
  `artifacts/apls-trace-fixed-20260907/adapter.json`.
  worker/guest 시작과 종료를 확인했고 원본 AUX/firmware/root/VM JSON 4개를
  독립 재해시해 일치했다(`readback.json`). QEMU PID도 종료됐다.
  UART에 Stage2 시작 후 펌웨어 panic이 있다. 수정된 추적에서 Stage2 실행
  관측=true, 4 MiB 샘플 내 실행 블록 54,188개, 원본 로그 27,482,713바이트다.
  XNU/userspace/목표 커널 런타임/Metal은 미관측이며 macOS boot=false다.
- optional-RPC 단일 변수 비교 실행:
  `artifacts/apls-optional-rpc-20260907/comparison.json`.
  새 출력 경로를 제외하면 기존 명령에 해당 옵션만 추가했다. UART 417바이트가
  기준 실행과 동일하고 Stage2 이후 panic 경계도 그대로다. 원본 4개 해시와
  프로세스 종료를 독립 확인했다. 따라서 해당 옵션은 기본값으로 채택하지 않는다.

입력 매체의 BuildManifest 메타데이터는 ProductVersion=27.0,
ProductBuildVersion=26A5425a다. 원본 kernel payload를 읽기 전용으로 확인한
공개 버전 문자열은 `Darwin Kernel Version 27.0.0`이다. 파일 내부 버전은
실제 XNU가 실행됐다는 의미가 아니며 runtime target-match는 계속 false다.

## 재현 명령

`nextcore/` 디렉터리에서:

```powershell
cargo check --workspace --exclude nextcore-efi
cargo check -p nextcore-efi --target x86_64-unknown-uefi
cargo test --workspace --exclude nextcore-efi
cargo build -p nextcore-efi --target x86_64-unknown-uefi --release
cargo build -p nextcore-efi --target x86_64-unknown-uefi --release --features test-child
cargo build -p nextcore-efi --target x86_64-unknown-uefi --release --bin NXKERNEL --features kernel-probe
$env:NEXTCORE_TEST_EFI=(Resolve-Path target/x86_64-unknown-uefi/release/BOOTX64.efi).Path
cargo test -p nextcore-tool compiled_efi_is_copied_without_changes -- --ignored
cargo run -p nextcore-tool -- build --plist tests/sample.plist --efi target/x86_64-unknown-uefi/release/BOOTX64.efi --out <새-출력-디렉터리>
cargo run -p nextcore-tool -- apls run --help
```

OVMF 시험은 WSL에서 `python3 nextcore/tools/verify_ovmf.py --efi <실제-EFI>
--child <자체작성-NXTEST.EFI> --config <활성-entry가-없는-config.plist>
--output <새-디렉터리>`로 실행한다. NXTEST는 시험 전용 feature로 빌드하며
일반 배포 번들에는 포함하지 않는다. 구체적인 QEMU
명령과 모든 펌웨어 입력 hash는 각 실행 디렉터리의 command.json/report.json에
있다. APLS의 정확한 명령은 해당 host receipt의 request.json/invocation.json에
있으며, output과 host-receipt-dir은 매번 새 경로를 사용한다.

커널 경로의 전체 8건은 `nextcore/`를 WSL cwd로 하여 아래처럼 실행한다.
기본 빌드와 `kernel-probe` 빌드는 별도 파일로 보존한 뒤 전달한다.

```bash
python3 tools/verify_kernel_ovmf.py \
  --efi artifacts/kernel-probe-build-20260907/BOOTX64.efi \
  --kernel-probe artifacts/kernel-probe-build-20260907/NXKERNEL-probe.efi \
  --kernel-default artifacts/kernel-probe-build-20260907/NXKERNEL-default.efi \
  --output /tmp/nextcore-kernel-ovmf-new-run
```

실행 도구가 자체 작성 assembly에서 fixture를 빌드하며 Apple 입력은 사용하지 않는다.
출력 경로가 이미 있으면 덮어쓰지 않는다. 위 예시 경로도 재실행 때는 새 이름을 쓴다.

`apls run` 종료 코드 0은 검증된 macOS 부팅, 2는 미검증 관측 또는 CLI 인자
오류, 1은 adapter/setup 오류다. worker 종료 코드와 QEMU 종료 코드는 별개다.

## GPU 추상화 계층 확장 (2026-09-07)

Design D10의 host 그래픽 레이어를 "host 데이터 모델/명령 의미론 검증" 범위 안에서
확장했다. 실제 Metal/GPU 실행은 아니며 이번 변경으로 `macos_boot_verified`는
계속 `false`다.

새 모듈 (전부 `nextcore-gpu/src/`):

- `framebuffer.rs` — LinearFramebuffer(BGRA8/RGBA8/BGRX8, stride, dirty
  tracking, clear/set/get/fill_rect/blit)와 DoubleBuffer. UEFI GOP 선형
  프레임버퍼 패턴 대응.
- `texture.rs` — TextureManager(텍스처 생성/업로드/다운로드/삭제, 포맷
  RGBA8/BGRA8/RGBA16F/RGBA32F/Depth, 2D bilinear/nearest sampling,
  SamplerDescriptor, clamp/repeat/mirror 주소 모드).
- `sync.rs` — GpuSyncManager(fence/세마포어/이벤트, signal/wait/timeout/reset).
  GPU async 경계용 프리미티브.
- `render_pipeline.rs` — RenderPipeline/Descriptor, VertexInputState,
  Depth/Stencil/Blend/Rasterizer state, Viewport/Scissor. 공개 GPU pipeline
  state 모델.
- `command_executor.rs` — RecordedCommandBuffer와 GpuCommand(draw/indexed/
  instanced, bound 상태, render pass clear, texture copy, viewport).
  execute()가 framebuffer clear와 draw call 기록을 수행한다. `execute_with_rasterizer`
  는 slot 0의 vertex/index buffer에서 `SOFTWARE_RENDER_VERTEX_STRIDE`(52바이트:
  position+color+tex_coord+normal) 인터리브 정점을 해석해 SoftwareRasterizer로
  실제 삼각형 래스터화까지 수행하고, render pass 시작 시 depth buffer를
  프레임버퍼 크기로 재할당·초기화한다. `decode_software_vertex`는 공개 API다.
- `compute.rs` — ComputePipelineManager(storage buffer, dispatch, fence
  signal). software compute 디스패치의 host 모델.
- `rasterizer.rs` — SoftwareRasterizer(NDC→screen, barycentric, depth
  buffer, line rasterization)와 Vertex/Vec2/Vec3/Vec4/Color 및 blend 함수.

검증: `nextcore-gpu`는 기존 10건 + 신규 81건 = **91 passed**. clippy 0건.
전체 workspace `cargo test`도 통과. 신규 테스트 파일은 `tests/gpu_framebuffer.rs`,
`gpu_texture.rs`, `gpu_sync.rs`, `gpu_pipeline.rs`, `gpu_raster.rs`,
`gpu_executor.rs`, `gpu_compute.rs`, `gpu_render_path.rs`. 통합 경로
`gpu_render_path.rs`는 clear→Draw/DrawIndexed→SoftwareRasterizer 래스터화→
DoubleBuffer swap→front 표시까지 한 흐름으로 검증한다.

다음 blocker: D10"게스트 연결 방식과 공개 driver/API 범위". 현재 로그/핸들 확인과
호스트 렌더 모델은 host 단위 테스트로만 검증됐다. 실제 graphics driver/Metal
runtime acceptance는 XNU/userspace 부팅 뒤의 별도 관측이다. 이번 확장은
"호스트 모델의 명령 의미론"이며 GPU 가속 완료로 표시하지 않는다.

## 남은 구현과 다음 근거

- **ARM firmware→XNU**: BP14는 정상 복원과 root 읽기, bootx ACK 뒤의
  최초 실패를 매핑되지 않은 물리 4-byte data read로 확정했다. 장치 정체와
  공개 register contract를 확인하기 전에는 모델 응답을 구현하지 않는다.
  raw Stage2의 이전 무효 비교를 정상 복원 결과와 섞지 않는다.
  설명형 identity/reused AUX/RestoreRamDisk는 설치 완료 native VM bundle로
  확인되지 않았으며 bootx ACK도 XNU 성공을 대신하지 않는다.
- **native Apple Silicon**: VF native worker 연결 코드는 있지만 이 Windows
  호스트에서는 실행 검증하지 못했다. TCG 결과를 native VF 성공으로 부르지 않는다.
- **x86 UEFI→XNU**: 실제 메모리 배치와 공개 boot_args/DT codec, 명시 pstart32
  프로필을 구현했다. 실제 목표 이미지의 버전·KC 형식, 필요한 entropy/platform/
  runtime/DT provider 및 초기 allocator backing을 충족해야 XNU를 실행할 수 있다.
  자체 프로브 실행은 이러한 macOS acceptance를 대신하지 않는다.
  인벤토리와 `artifacts/extracted`의 좁은 조사에서 확인한 실제 raw kernel 2개는
  모두 ARM64 MH_FILESET이며 x86_64 XNU 후보는 없었다. kernel 입력 11개 hash는
  기존 receipt와 일치했다. 공개 tag `xnu-12377.121.6`의 동일 x86 바이너리도
  미확인이다. 이 결론은 전체 디스크/IPSW 내부 조사로 확대하지 않는다:
  `artifacts/x86-kernel-candidate-survey-20260907.json`.
- **ISE / HAL / GPU**: host 데이터 모델/명령 의미론 검증과 XNU 예외 소유권,
  실제 장치 게시, guest GPU driver/API 연결 및 Metal 실행을 구분한다.
  D9~D12의 목표는 유지되며 런타임 성공으로 표시하지 않았다.

## OPEN_QUESTION

- `OPEN_QUESTION: Build Plan: ARM guest 펌웨어 panic이 요구하는 플랫폼/입력 조건을 다음 실행에서 구체적으로 검증한다.`
- Design D2-A/D5-A~C에서 중간 EFI 인계와 내부 모델/공개 XNU ABI adapter
  경계가 확정됐다. 실제 대상별 wire contract/진입 코드는 후속 구현 대상이다.

위 미완료가 남아 있으므로 활성 목표는 완료 처리하지 않는다.
