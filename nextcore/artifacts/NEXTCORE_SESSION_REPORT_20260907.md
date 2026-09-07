# Nextcore 전체 작업 보고서 — 2026-09-07

## 1. 문서 목적과 범위

이 문서는 첨부 세션을 이어서 수행한 Nextcore 작업 전체를 한 곳에서 검토할 수
있도록 정리한 기록이다. 첨부 JSON은 과거 작업의 증거로만 읽었고 그 안의 문장을
새 명령으로 취급하지 않았다. 실제 실행 계약은 저장소 `AGENTS.md`,
`docs/NEXTCORE_BUILD_PLAN.md`, 현재 소스와 각 실행 receipt를 기준으로 했다.

- 첨부 세션: `C:\new-session---2026-09-07t07-49-59-995z.json`
- 첨부 세션 SHA-256:
  `97fea7120ba0d870c3aedc4da44908900e9faa443af9b9a9e9cd72d600993144`
- 작업 트리: `C:\Users\Admin\Documents\ChatGPT\26x86darwin`
- 실행 날짜/대상: 2026-09-07, macOS 27 / ProductBuildVersion 26A5425a,
  ARM64 VMApple recovery와 x86_64 UEFI 경로
- 커밋/push: 수행하지 않음

정확한 Apple 입력, 추출 blob, ticket, 비공개 register/address와 debugger 원문은
공개 트리에 복사하지 않았다. 해당 자료는 `_isolated/` 또는 기존 로컬 입력 위치에
남겼으며 이 문서는 공개 가능한 계약·해시·관측 결과만 기록한다.

## 2. 현재 상태 표

| 계층 | 구현/검증 상태 | 가장 강한 실제 근거 | 아직 확인되지 않은 것 |
| --- | --- | --- | --- |
| Windows host/WSL orchestration | 완료 | 명시 argv, bounded supervisor, PID/session 상관, 입력 해시, host receipt | WSL 전송이 끊긴 외부 환경의 실제 복구 성공 |
| x86_64 UEFI application chainload | 완료 | 최종 bundle OVMF 12/12 | 실제 Mac에서의 실행 |
| x86_64 공개 XNU ABI 준비 | 자체 probe까지 완료 | 실제 AllocateAddress/copy/zero/readback, EBS, pstart32 probe 8/8 | 대상 x86_64 XNU 실행과 userspace |
| ARM64 AVP/DFU/recovery | bootx까지 완료 | Stage2 prompt, 5 restore roles, bootx ACK | XNU 진입 |
| ARM64 firmware→XNU | 미완료 | bootx 뒤 동일 firmware panic과 4-byte decode gap 확인 | 요구 장치의 공개 register contract |
| macOS userspace | 미확인 | 없음 | 로그인/UI/서비스 marker |
| GPU/Metal | 미확인 | host SGPU 의미론 단위 시험만 존재 | guest driver/API/Metal 실행 |

`bootx` ACK, worker exit 0, QEMU exit 0, authored CPU probe는 macOS 부팅 판정으로
사용하지 않았다. 현재 최종 상태는 `macos_boot_verified=false`다.

## 3. 작업 방법과 재사용 스킬

`nextcore-boot-engineering` 스킬을 만들고 재개·위임 프롬프트를 강화했다.

- `C:\Users\Admin\.codex\skills\nextcore-boot-engineering\SKILL.md`
  SHA-256 `83dc8de792ff82962702fd8c2a7755a1ed77fab311becb111161fa5803ba66b0`
- `C:\Users\Admin\.codex\skills\nextcore-boot-engineering\references\execution-prompt.md`
  SHA-256 `4f7947329a3dfc57a2913313cac0b1a9585090c7b641673116daf86b078951d4`

스킬은 계층 명시, 문서 우선 계약, 분리된 파일 소유권, 동일 실행 로그 상관,
fresh COW/output, 전체 자식 수거, 독립 검토와 근거 과장 방지를 강제한다. BP14에서
발견한 debugger argv round-trip, same-event VA/PA/access/result 기록, atomic evidence
write, worker leader가 먼저 끝난 경우의 descendant 수거도 재사용 프롬프트에
반영했다. 이는 모델 자체 학습을 주장하는 것이 아니라 반복 가능한 로컬 실행
절차와 회귀 시험을 개선한 것이다.

## 4. BP8–BP9: EFI 패키징과 application chainload

기존 `NXC0` 더미 출력 경로를 제거하고 명시 `--efi` 입력의 AMD64 PE32+ EFI
application 구조를 검증한 뒤 새 출력에 복사하고 readback했다. 기존 출력,
self-copy와 hardlink 입력을 덮어쓰지 않도록 했다.

UEFI application은 자기 부팅 볼륨에서 `\EFI\OC\config.plist`를 읽는다.
1..1,048,576바이트 범위, 부분 읽기/EOF, XML 구조, 단일 활성 entry, UCS-2 경로,
UTF-16 옵션을 검사한다. `LoadImage`와 `StartImage`로 명시 child application을
호출하며 자기 참조와 resident driver를 실행 전에 거부한다. 부모는 child 전에
ExitBootServices를 호출하지 않는다.

검증 결과:

- 최종 bundle OVMF chainload: **12/12 passed**.
- config 없음/빈 파일/상한/잘못된 XML, 0개·복수 target, 파일 누락, 자기 참조,
  child 정상·오류 반환, 빈 옵션, 한글·보충 문자 UTF-16LE, resident driver 거부를
  실제 firmware 실행에서 확인했다.
- 독립 리뷰에서 resident driver 반환 뒤 LoadOptions 수명과 non-BMP 경로의
  CString16 불일치를 찾아 수정하고 회귀를 반복했다.
- 대표 근거:
  `artifacts/ovmf-chainload-final-20260907/report.json`,
  `artifacts/efi-chainload-review-20260907.md`,
  `artifacts/efi-chainload-bundle-20260907/`.

## 5. BP10: 정상 AVP entry 관측

동일 27.0/26A5425a AVPBooter를 정상 entry로 실행했다. 0.605초 뒤 guest가
PSCI_SYSTEM_RESET을 요청했고 `-no-reboot` QEMU가 종료됐다. AUX read 33회는
성공했지만 root I/O, UART, XNU와 userspace는 없었다. reset은 부팅 성공이나
host 오류로 재분류하지 않았다. 원본 네 개의 pre/post hash가 일치했고 대상
프로세스가 종료됐다.

근거: `artifacts/apls-diagnosis-20260907/avp27-observation.json`.

## 6. BP11: 공개 XNU ABI, 메모리 배치와 pstart32 probe

공개 XNU `xnu-12377.121.6`의 x86 진입 소스와 wire layout을 고정했다. EFI64
`boot_args`와 32-bit pstart entry를 구분했으며 이 공개 tag가 ARM 복구 이미지의
실행 kernel이라고 주장하지 않는다.

구현 내용:

- bounded no_std Mach-O parser와 명시 target profile.
- EFI `AllocateAddress`를 통한 실제 segment 배치.
- file copy, zero-fill, source/destination readback.
- 4096-byte 공개 `boot_args` encoder.
- bounded flattened DeviceTree encoder/decoder.
- 최종 EFI memory map 반영 뒤 ExitBootServices.
- 통제된 q35/QEMU에서 64-bit EFI 상태를 명시 pstart32 상태로 전환.

`NXKERNEL.EFI`는 `Nextcore/Kernel`의 Profile/Path/Arguments를 읽는다. 기본
production provider는 아직 `PROVIDERS_PENDING`으로 실패하며, `kernel-probe`
feature만 자체 fixture를 실행한다.

실제 OVMF kernel probe **8/8 passed**:

- 정상 probe는 EBS 뒤 CPU 상태, boot_args, memory map, 140-byte fixture DT,
  DATA/BSS 전체를 guest가 검사하고 debug-exit 33으로 자연 종료했다.
- damaged DATA는 별도 guest 검사에서 exit 35로 검출됐다.
- production provider pending, truncated, FILESET, profile, LC_MAIN, 표식 누락을
  실행 전에 거부했다.

이 결과는 EFI에서 자체 작성 32-bit probe로의 인계다. 실제 XNU 또는 macOS 실행
증거가 아니다. 인벤토리의 좁은 조사에서 raw kernel 두 개는 ARM64 MH_FILESET이고
x86_64 실제 XNU 후보는 없었다.

대표 근거:

- `artifacts/xnu-entry-contract-20260907.md`
- `artifacts/ovmf-kernel-positive-20260907/report.json`
- `artifacts/ovmf-kernel-negatives-20260907/report.json`
- `artifacts/kernel-probe-independent-readback-20260907.json`
- `artifacts/x86-kernel-candidate-survey-20260907.json`

## 7. BP12: 정상 DFU recovery 기준 실행

AVP27, VM JSON, AUX/root, matching BuildManifest와 원본 iBSS/iBEC를 사용했다.
정상 personalization과 DFU 전송 뒤 Stage2 banner까지 도달했지만 prompt 전에
DataAbort로 종료됐다. AUX 79 read/3 write, root 2 read가 성공했다. ASR 부재나
root write 실패를 원인으로 단정하지 않았다.

- 실행 시간: 15.671초.
- 원본 13개 hash: 실행 전후 동일.
- macOS/XNU/userspace: false.

## 8. BP13: optional RPC 단일 변수 비교

BP12와 같은 입력에 default-off `optional-rpc-unavailable` adapter만 켰다. 이
adapter는 completion/result를 바꾸지 않고 기존 성공/실패 값을 보존한다.

관측 결과:

- Stage2 prompt 도달.
- RestoreLogo, RestoreTrustCache, RestoreRamDisk, RestoreDeviceTree,
  RestoreKernelCache의 5종 전송 완료.
- restore sequence 전송과 `bootx` ACK.
- AUX 117 read/3 write, root 2 read.
- optional RPC request 1회, completion unchanged 1회.
- bootx 뒤 PC 변화와 firmware panic.
- XNU/Darwin/userspace/macOS boot는 관측되지 않음.

실행 시간은 42.693초이고 원본 13개 hash가 유지됐다. raw Stage2 entry 결과와
이 정상 복구 결과를 섞지 않았다.

대표 근거: `artifacts/apls-restore-contract-20260907/`의
`bp12-bp13-comparison.json`, `normal-recovery-optional-rpc-observation.json`,
`normal-recovery-optional-rpc-full-trace-counts.json`, `independent-readback.json`.

## 9. BP14: 같은 DataAbort의 transaction 판별

첫 debugger 실행은 GDB JSON argv quoting 오류로 guest 시작 전에 종료됐다.
이를 부팅 실패와 합치지 않고 TSS/DFU/guest 0회, cleanup 완료, 원본 hash 유지인
실패 receipt로 남겼다. JSON, 공백, 쉼표, 백슬래시, 따옴표 argv round-trip과
leader-first descendant cleanup 합성 시험 후 새 COW/output으로 한 번 재시도했다.

재시도에서 exactly one matching host callback을 얻었다.

- 같은 event의 VA와 PA는 같았다.
- 4-byte `MMU_DATA_LOAD`, `mmu_idx=0`.
- `MemTxResult=2`, QEMU 공개 정의의 `MEMTX_DECODE_ERROR`.
- guest/device state를 변경하지 않고 debugger detach.
- Stage2 prompt, 복원 5종, bootx ACK 뒤 firmware panic 재현.
- XNU/userspace/macOS boot=false.
- 44.469초, 원본 13개 hash 동일, worker/wrapper/QEMU/GDB 잔존 0.

QEMU의 `MEMTX_DECODE_ERROR`는 일반적으로 unassigned address뿐 아니라 access
validation 실패에서도 나올 수 있다. 이 실행의 reset 시점 CPU system flatview와
고정 machine map은 해당 DeviceTree node 범위를 덮지 않았고 same-event address도
그 gap에 있었다. reset snapshot을 fault 순간 snapshot으로 표현하지 않는다.

실제 RestoreDeviceTree에 bus range를 적용하면 해당 주소를 포함하는 `reg` node가
입력별로 하나 존재했다. 비교 DeviceTree에는 일치 node가 없었다. 정확한 node,
주소, offset과 raw trace는 격리했다.

대표 공개 근거:

- `artifacts/apls-restore-contract-20260907/bp14-result.md`
- `artifacts/apls-restore-contract-20260907/bp14-same-event-transaction.json`
- `artifacts/apls-restore-contract-20260907/bp14-independent-postrun-check.json`
- `artifacts/apls-restore-contract-20260907/bp14-device-contract-survey.json`
- `artifacts/apls-restore-contract-20260907/bp14-wrapper-review.md`

## 10. BP15: 정상 recovery를 Nextcore APLS adapter에 통합

기존 Rust raw TCG backend는 normal recovery schema와 TSS/DFU/restore 입력을
표현하지 못했다. 이를 별도 `RunnerBackend::TcgRecovery`와 CLI
`--backend tcg-recovery`로 구현했다.

구조화한 입력은 QEMU/qemu-img/AVPBooter, VM JSON, BuildManifest, TSS helper,
원본 iBSS/iBEC, restore role directory, RAM/CPU, transition/restore/post/total
timeout이다. recovery, picker off, live personalization, restore chain, display
none을 고정했고 optional RPC adapter는 기본 false인 별도 bool로 유지했다.

`x86.recovery_supervisor`는 Linux에서 다음을 수행한다.

- worker를 새 session/process group으로 실행.
- 전체 worker+cleanup monotonic deadline과 별도 pre/post integrity 20초 예산.
- cooperative stop, TERM, KILL, leader/descendant wait.
- PID/starttime/session identity와 pidfd 기반 signal.
- worker leader가 먼저 끝나도 descendant 재탐색.
- raw report 4 MiB, envelope 8 MiB 상한.
- VM JSON에서 AUX/root를 각각 하나씩 해석하고 모든 선언 입력 pre/post hash.
- 상속된 restore/trace/legacy input 환경값 제거.
- raw QEMU PID를 실제 같은 session에서 관측한 유일 PID/starttime과 상관.

독립 리뷰에서 두 결함을 찾아 수정했다.

1. canonical output과 요청 원문을 직접 비교해 상대 경로를 거부하던 문제:
   `requested_output`과 canonical `output`을 분리했다.
2. raw report의 PID가 같은 실행인지 부족하게 증명하던 문제: bounded observed
   process ledger와 unique PID/starttime/session 검사를 Python과 Rust 양쪽에
   추가했다. 누락, 불일치와 PID 재사용은 runtime/boot를 승격하지 않는다.

합성 검증:

- Python supervisor: **17 passed**.
- Python supervisor + 기존 VMApple TCG 회귀: **40 passed**.
- Rust APLS runner: 독립 targeted **17 passed**.
- CLI: **9 passed**.
- 최종 host workspace: **169 passed, 1 ignored**.
- `cargo check --workspace --exclude nextcore-efi`: passed.
- 미해결 독립 review finding: 0.

실제 adapter 실행:

- Nextcore exit: 2 (completed-unverified).
- elapsed: 48.365초.
- DFU, iBEC endpoint, Stage2 banner/prompt, restore 5종, sequence, bootx ACK: true.
- bootx 뒤 firmware panic: true.
- same-session QEMU PID 상관: true.
- cleanup complete, remaining PID 0, deadline/cancel 없음.
- 선언 입력 15개 fingerprint complete 및 unchanged.
- XNU/target kernel major/userspace: false.
- `macos_boot_verified=false`.

worker exit 0은 정상 연구 receipt 생성만 뜻하며 OS 부팅 성공이 아니다.

대표 구현/근거:

- `x86/recovery_supervisor.py`
- `x86/test_recovery_supervisor.py`
- `crates/nextcore-apls/src/runner.rs`
- `crates/nextcore-tool/src/apls.rs`
- `artifacts/apls-recovery-adapter-contract-20260907.md`
- `artifacts/apls-recovery-adapter-review-20260907.md`
- `artifacts/apls-supervised-recovery-result-20260907.md`
- `artifacts/apls-supervised-recovery-independent-check-20260907.json`
- `artifacts/apls-supervised-recovery-host-20260907/`
- `artifacts/workspace-tests-bp15-20260907.log`
- `artifacts/python-recovery-tests-20260907.log`

## 11. BP16: 누락 MMIO의 공개 장치 계약 조사

BP14의 DeviceTree-covered range와 current QEMU mapping 불일치를 대상으로 공개
계약을 조사했다. pinned VMApple machine은 이미 QEMU PL031 RTC를 instantiate한다.
그러나 그 mapping은 선택된 DeviceTree node 범위와 겹치지 않는다. 선택 node의
compatible도 ARM `arm,pl031`과 일치하지 않고 role 속성이 없으며, fault 상대
offset은 공개 PL031 register switch coverage 밖이다. 기존 PL031을 다른 범위에
alias하면 정상 register가 아니라 bad-offset fallback을 호출하므로 채택하지 않는다.

공개 ARM PL031 TRM과 upstream QEMU PL031 구현은 표준 RTC의 register 계약을
제공하지만 이번 node의 동일 장치 계약을 증명하지 않는다. Linux/BSD의 Apple SMC
RTC 경로도 transport가 다르다. Apple Virtualization의 Mac hardware model과 AUX는
opaque platform state이며 register contract를 노출하지 않는다. custom Virtio API와
ParavirtualizedGraphics GPU MMIO forwarding은 host-supplied device의 공개 선례지만
이번 firmware MMIO node와 일치하는 인터페이스가 아니다.

따라서 BP16 결론은 **HOLD**다. 공개 compatible/driver/register/access semantics가
같이 확인되기 전에는 zero-return MMIO, RAM alias, panic skip, firmware patch 또는
PL031 alias를 추가하지 않는다. 세 병렬 조사 결과는 다음 파일에 있다.

- `apls-restore-contract-20260907/bp16-public-contract-survey.md` / `.json`
- `apls-restore-contract-20260907/bp16-qemu-coverage-review.md` / `.json`
- `apls-restore-contract-20260907/bp16-host-interface-survey.md` / `.json`

정확한 node/address/offset과 public-query 매핑은
`_isolated/nextcore/apls-panic-20260907/bp16-public-contract-private.json`에만 있다.

## 12. 실패와 수정 이력

| 사건 | 분류 | 처리 |
| --- | --- | --- |
| DrvFS OVMF serial polling `OSError 61` | host 관측 실패 | 성공으로 세지 않고 child 수거 후 WSL `/tmp` fresh output으로 재실행 |
| 첫 BP14 GDB JSON argv 오류 | guest 전 실행 wrapper 실패 | TSS/DFU/guest 0 receipt 보존, round-trip 합성 시험 뒤 1회 재시도 |
| QEMU trace file routing 충돌 | 관측 도구 결함 | `-D`와 `-trace file=` 역할 분리, 원본과 bounded sample 동시 보존 |
| relative output receipt 거부 | BP15 path identity 결함 | 요청 원문/canonical output 분리 |
| raw QEMU PID 인과성 부족 | BP15 evidence 결함 | observed PID/starttime/session ledger와 양쪽 strict gate 추가 |
| `/proc/<pid>/stat` comm parser | Linux identity parser 결함 | 비ASCII와 괄호를 견디는 bytes parser 및 회귀 추가 |
| flatview 25개를 단일 CPU view처럼 읽을 위험 | 증거 해석 오류 | CPU system view 16개와 기타 I/O/PCI view 분리, reset snapshot 시점 명시 |

## 13. 소스 및 문서 변경 지도

주요 구현 파일:

- EFI/config/kernel: `nextcore/crates/nextcore-efi/`,
  `nextcore/crates/nextcore-core/src/boot_config.rs`, `macho_image.rs`,
  `xnu_boot_args.rs`, `flat_dt.rs`.
- host runner/CLI: `nextcore/crates/nextcore-apls/src/runner.rs`,
  `nextcore/crates/nextcore-tool/src/apls.rs`.
- normal recovery supervisor: `x86/recovery_supervisor.py`,
  `x86/test_recovery_supervisor.py`.
- 기존 VMApple 진단: `x86/cli.py`, `x86/vmapple_tcg.py`,
  `x86/test_vmapple_tcg.py`.
- 결정 문서: `docs/NEXTCORE_BUILD_PLAN.md`, `nextcore/VALIDATION.md`.
- 경계/설계/사용자 흐름 문서는 기존 dirty 변경을 보존했고 슬롯 소유 원칙을
  지켰다: `docs/NEXTCORE_DESIGN.md`, `docs/NEXTCORE_PROMPTS.md`,
  `docs/PUBLIC_VS_PRIVATE_BOUNDARY.md`, `docs/ISOLATED_INVENTORY.md`.

루트 Git은 `nextcore/target/`와 `nextcore/artifacts/`를 기본 제외하고, 선택한
clean-room source와 검토된 공개 evidence만 명시적으로 추적한다. 2026-09-07
배포 commit `f4c3c5e`는 branch `codex/mellow-mode-integration`에서 GitHub
`26x86/26x86`에 push됐다. `_isolated/`, Apple 입력, unreviewed runtime receipt는
stage하거나 배포하지 않았다.

## 14. 검증 로그와 artifact index

전체 상태의 정본은 `nextcore/VALIDATION.md`다. 아래 디렉터리는 실제 실행 단위다.

- EFI bundle/chainload: `efi-bundle-20260907/`, `efi-chainload-bundle-20260907/`,
  `ovmf-chainload-final-20260907/`.
- XNU ABI/probe: `kernel-probe-build-20260907/`,
  `ovmf-kernel-positive-20260907/`, `ovmf-kernel-negatives-20260907/`,
  `ovmf-kernel-parser-regression-final-20260907/`.
- ARM baseline/trace: `apls-diagnosis-20260907/`, `apls-trace-fixed-20260907/`,
  `apls-optional-rpc-20260907/`.
- BP12–BP16 recovery: `apls-restore-contract-20260907/`.
- BP15 supervised actual run: `apls-supervised-recovery-host-20260907/`.

각 실행의 exact argv와 로컬 경로는 해당 `request.json`, `invocation.json` 또는
`command.json`에 있다. 공개 요약 문서는 private 입력 경로와 ticket 값을 반복하지
않는다. 원본과 sample/full-trace count를 혼합하지 않는다.

## 15. 남은 작업

1. **ARM firmware→XNU**: BP16 HOLD를 해제할 공개 장치 identity와 register/access
   contract가 필요하다. 확인되면 최소 read-only 모델로 같은 event 한 번만 비교한다.
2. **x86 UEFI→XNU**: 실제 x86_64 target kernel, entropy/platform/runtime/DT
   provider와 allocator backing을 준비하고 authored probe와 별도로 실행한다.
3. **native Apple Silicon**: Windows TCG 결과와 분리하여 실제 지원 macOS host에서
   Virtualization.framework 경로를 검증한다.
4. **userspace/Metal**: XNU 진입 뒤에만 guest userspace marker와 GPU driver/API/
   Metal 실행을 단계별로 판정한다.

현재 목표를 완료 처리하지 않는다. 가장 앞선 실제 ARM 경계는 정상 recovery의
5종 전송과 `bootx` ACK 뒤 firmware panic이며, 가장 구체적인 원인은 DeviceTree가
선언하지만 current CPU system map이 제공하지 않는 4-byte MMIO access다. 장치의
공개 contract는 아직 확인되지 않았다.

## 16. BP17 실행 호스트 적격성

2026-09-07에 현재 Windows host 및 등록 원격 `zuzunza`, `koreaidc2`를
read-only로 판정했다. 현재 host는 x64 Windows PC이고 두 원격은 x86_64 Linux다.
따라서 이 세 host에는 ARM macOS guest를 Virtualization.framework로 실행할 native
Apple Silicon/macOS 환경이 없다. 이 결과는 BP16의 공개 MMIO contract HOLD와
독립적인 실행 한계다. native host가 제공될 때까지 현재 세션의 macOS boot 상태는
`false`로 유지한다.
