# NextCore 현재 맥락과 재개 기준

갱신: 2026-09-08. 이 문서는 다음 작업자가 가벼운 모델이더라도 현재 상태를
과장하지 않고 이어갈 수 있게 하는 정본 요약이다. 상세 설계는
`docs/NEXTCORE_BUILD_PLAN.md`, 검증 결과는 `nextcore/VALIDATION.md`를 따른다.

## 목표와 현재 판정

목표는 공개 clean-room EFI/boot engineering으로 **macOS 27 Golden Gate의
AMD64↔Apple Silicon HAL 및 필수 Metal 가속**, **macOS 26 Tahoe의
네이티브 HAL**을 구현하고 부팅부터 그래픽 실행까지 검증하는 것이다.
2026-09-08 사용자가 두 경로를 확정했다. 현재 `macos_boot_verified=false`다.
이어 사용자는 이 컴퓨터에서 계속 개발하도록 확정했다. 실기기 접근을 개발의
선행 조건으로 두거나 재요청하지 않는다. 로컬 QEMU/OVMF와 Intel GPU를 실행
대상으로 유지하며, 물리 Mac 미검증 상태는 결과 범위로만 기록한다.

추가 사용자 결정: 제품 브랜딩은 **NextCore**, 실제 EFI 피커 필수, x86 작업은
서브에이전트가 지속하고 검증된 진척마다 로컬 commit한다. root가 공유 index를
조정한다. 이어 사용자는 검증된 진척의 push와 원격·조직 저장소 최신화도
명시 승인했다. 본체는 PR/CI를 거쳐 반영하고 모듈은 기존 history/tag를 보존해
새 버전으로 동기화한다. Design/Prompts는 picker 담당에게 위임됐다.

| 계층 | 확인된 것 | 아직 아닌 것 |
| --- | --- | --- |
| x86 UEFI 자체 handoff | authored OVMF probe에서 allocation, copy/zero/readback, flat DT, 32-bit transition 통과 | 자체 KC loader의 실제 x86_64 XNU 진입 |
| local virtualization | WSL KVM 모듈 적재 후 API 12·query-kvm·실제 OVMF Shell 실행, developer 전용 device ACL | 이 결과만으로 macOS boot 판정 |
| x86 UEFI → host HAL | BP19 실제 OVMF RSDP+7 SDT+5 PCI header 수집/파싱, exit 67와 원본 hash 유지 | XNU platform provider, AML 실행, 게스트 장치 게시, 물리 하드웨어 |
| Tahoe 외부 reference | 원본 XNU/launchd/WindowServer와 읽을 수 있는 복구 GUI; Terminal에서 실제 Metal probe 실행 | 전체 OS 설치, Metal device/compute 성공 |
| Tahoe native EFI | 최종 BP21 피커 → ConsoleControl → 원본 booter → 실제 XNU/Recovery/Terminal, 키보드 명령으로 26.6.2/25G83 확인 | 자체 KC loader 진입, 전체 설치 OS/native HAL/Metal |
| native APFS driver | 공개 Jumpstart parser, 원본 745,080B 전량 재읽기·EFI 실행·controller 연결, 실제 후손 볼륨 4개의 root GetInfo/Read/EOF/Close SUCCESS | APFS booter 실행, 설치 OS로 연결 |
| native KC 준비 | 67,584,000-byte 실제 EFI pages 배치/readback/해제, 65,260 classic host 적용·전체 readback, 401,606 chains/header 보존, rev1 boot_args codec, core 142 tests | EFI relocation 연결, entry/slide/provider 계약, native XNU 실행 |
| ARM recovery | DFU, iBEC endpoint/prompt, 5 restore role, `bootx` ACK 관측 | XNU, userspace, Metal, macOS boot |
| ARM firmware | `bootx` 뒤 4-byte MMIO decode failure를 same-event trace로 확인 | 장치 register/access contract 또는 안전한 장치 모델 |
| ARM KC 준비 | 별도 1152B boot_args codec/C layout, 실제 ARM64E KC 81,002,496B 불변 staging·216 headers/1,096 views readback | 물리 배치/CPU/PAC/DT 연결, 실제 27 XNU 진입 |
| firmware 피커 | NextCore GOP 디자인, 방향키·선택된 child 실행·Esc·text fallback, 최종 EFI에서 원본 Tahoe Recovery/Terminal까지 연결 | 자동 OS volume discovery |
| graphics | Intel host GPU 512값/fence; 두 guest probe 빌드, 실제 Tahoe Recovery 실행은 no-metal-device/exit1 | guest Metal device와 GPU command completion/readback |

현재 Windows host와 `zuzunza`, `koreaidc2`는 x86_64다. native Apple Silicon
macOS host가 없으므로 Virtualization.framework 기반 ARM guest boot는 이 환경에서
검증할 수 없다.

## 절대 경계

- 공개 tree에는 Apple firmware, guest disk, 추출 blob, private reverse-engineering
  결과를 넣지 않는다. `_isolated/`는 stage하지 않는다.
- BP16의 MMIO node는 공개 register/access contract가 없다. zero-return, RAM alias,
  PL031 alias, firmware patch, panic skip으로 진행을 위조하지 않는다.
- static/emulator/firmware evidence는 측정한 계층만 올린다. XNU, userspace,
  graphics, physical-Mac acceptance를 대신하지 않는다.
- 작업은 문서 결정 후 코드로 진행한다. 다른 슬롯 문서는 직접 수정하지 않고
  `OPEN_QUESTION`으로 전달한다.
- GitHub에는 force-push하지 않는다. push, repo create, PR, merge는 사용자가
  승인한 경우에만 한다.

## 다음 안전한 작업

2026-09-08 BP19에서 미완료 NXHAL/raw parser를 하네스와 연결했다. workspace
280 passed/1 ignored, HAL all-targets 32 passed, Python harness 30 passed이며
실제 OVMF 실행은 4.3961초에 통과했다. 최종 gate로 같은 13 records를 재검증했다.
최신 재현 명령과 한계는 `nextcore/VALIDATION.md` BP19에 있다. HPET 등 일부
테이블은 공통 header/checksum만 검증했고 XNU/macOS 상태는 올리지 않았다.

1. 실제 x86_64 Tahoe 26.6.2 BootKC가 이제 native NextCore production
   ConsoleControl → 원본 booter 경로에서도 실행됐다. 관측 PC의 256B가
   원본 executable segment와 유일하게 일치하고 linked VA + 실제 slide가 PC와
   같다. 초기 restore-datapartition exit(1)은 2GiB VM에서 2.5GiB tmpfs를
   요구한 메모리 조건이었다. 8GiB 단일 변경으로 통과했고, 표준 SMC와 검증된 USB
   keyboard/tablet를 차례로 추가해 정상 언어 선택 및 Recovery 메뉴를 실제 조작했다.
   초기 corrected fresh 관측은 22.0017초 자연 종료/원본 hash 유지/
   cleanup 정상이다. 외부 OpenCore와 diagnostic provider/table hook은 이 경로에
   없다. Shell/HFS helper와 원본 Apple booter는 남아 있으므로 자체 KC loader
   완료와 구분한다. DataHub/SMBIOS 전체 구현을 초기 실패 원인으로 단정하지 않는다.
2. ARM panic은 public device contract가 새로 확인될 때만 최소 read-only MMIO
   모델로 같은 event를 한 번 비교한다.
3. 외부 reference의 XNU 시간 초기화 MSR #GP는 실측 invariant TSC와 공개 VMM
   frequency 계약에 따른 `invtsc=on,enforce=on` 노출 뒤 통과했다. 첫 실행의 EFI
   배치 충돌은 동일조건 재시도에서 재현되지 않았다. 재시도는 실제 PC 일치를
   다시 확인하고 MCA의 Haswell pre-C0 stepping 거부로 멈췄다. QOM의 실제 identity는
   family 6/model 60/stepping 1이었다. 공개 XNU 지원 조건에 맞춘 `stepping=3` 단일
   변경으로 launchd PID 1과 복구 서비스 실행에 도달했다. CMCI 부재 뒤 발생한
   MCEReporter page fault는 실제 KVM capability/CTL2/CMCI interrupt 검증을 거친
   선택적 QEMU 구현으로 통과했다. 원본 XNU consumer도 CMCI=true를 읽었고
   recoveryosd PID 65/WindowServer PID 81이 실행됐다. 초기 298초 화면은 검정이었으나
   표준 QEMU SMC만 추가한 대조 실행에서 194.7초에 읽을 수 있는 복구 GUI를 확인했다.
   외부 Reims+CMCI 11.1 빌드와 guest MSR probe가 통과했다. Reims PCI 장치는
   존재하나 원본 recovery에 AppleParavirtGPU/IOGPUFamily가 없어 driver attach와
   Metal은 확인되지 않았다. 공식 전체 Tahoe installer를 검증해 full OS 경로를
   진행한다. 전체 공식 18,384,624,402B installer는 XAR 서명·Apple PKI chain·모든
   entry/chunk checksum 검증을 통과했다. 실제 Recovery Terminal에서 guest Metal
   probe는 no-metal-device/exit1을 반환했고 전체 NDJSON/실행 파일 readback을 보존했다.
   전체 installer는 첫 설치와 APFS installer의 적용 단계를 마치고 각각 정상
   재부팅했다. 별도 native EFI COW에서 원본 APFS Jumpstart driver를 실제 실행하고
   controller 연결까지 확인했으며, 완료된 첫 설치 backing의 hash는 유지됐다.
   별도 COW의 실제 APFS 후손 볼륨 4개에서 root 열기/GetInfo/Read/EOF/Close도
   통과했다. 현재 APFS booter 연결과 전체 설치 OS의 후속 부팅/guest Metal을 진행한다.
   AHCI Port 2 abort는 원본 복구 디스크가 아닌 자동 생성된
   빈 CD-ROM에 대응한다는 QMP 실측이 있다.
   WSL 재시작 후 device가 없으면 설치 모듈의 적재 여부를 먼저 확인한다.
4. graphics는 public ABI와 실제 GPU submit/readback으로 진행한다. 과거의
   대형 모델 rate-limit 기록은 현재 구현 보류 근거가 아니다. BP20에서 WSL
   portable Mesa dzn을 빌드해 Intel 8086:7D41 실제 GPU를 선택하고 공개
   `ComputePipelineManager`의 두 입력 세트 512값 readback을 확인했다.
   기본 backend와 미연결 VirtualMetalDevice/SGPU의 compute·render·present는
   실행 없이 완료하지 않는다. guest Metal loader/FFI 실행은 확인했으나 device가
   없어 compute는 수행되지 않았다. 전체 OS의 driver 연결과 Metal이 다음 대상이다.

## 모듈 배포 상태

NextCore의 다음 public repositories를 기존 이력 위에서 갱신했다. Core/GPU/HAL/
ISE/APLS/EFI/Tool 중 Core·EFI의 최신 tag는 v0.1.2, Tool은 v0.1.3,
GPU/HAL/ISE/APLS는 v0.1.1이다. 각 원격 main과 해당 tag commit이 일치한다:

- `26x86/Nextcore-Core`, `Nextcore-GPU`, `Nextcore-HAL`, `Nextcore-ISE`
- `26x86/Nextcore-APLS`, `Nextcore-EFI`, `Nextcore-Tool`

APFS release source는 고정 main `65d1e85`다. Core `6547be4`, EFI `64a2d4c`,
Tool `36e0fd5`는 각각 Linux의 단일 repository만 있는 별도 parent에서 게시 전후
검증을 통과했다. Core 203 tests/no-default APFS 23/no_std, EFI all-feature UEFI
check와 NXAPFS 실제 link, Tool 17 passed/1 ignored 및 모든 exact-head CI가 통과했다.
나머지 4개 crate subtree는 이전 source와 동일해 기존 tag를 유지했다. 최종 7개
원격 ref와 모든 이전 tag 보존을 다시 확인했다. 최초 Tool v0.1.1 실패도 보존한다.
기존 exporter의 작업 중 변경은 사용하지 않았으며 source Git object와 고정
dependency tag만 배포 입력이다. 조직 profile `440e6a9`는 해당 release와 APFS
driver 실행 경계를 반영했고 원격 byte readback이 일치했다.
[최신 release 증거](../nextcore/artifacts/module-release-apfs-20260908/README.md)는
소프트웨어/배포 검사이며 guest Metal 실행을 뜻하지 않는다. 이후 BP24-B 파일시스템
관찰 기능은 이 고정 source release에 포함되지 않았다.

## 최소 재개 절차

1. `AGENTS.md`, 이 문서, `nextcore/VALIDATION.md`를 읽고 `git status --short`를
   확인한다.
2. 작업을 x86 UEFI, ARM firmware, graphics, module release 중 하나로 분류한다.
3. 변경 전후에 그 계층의 acceptance criterion과 `macos_boot_verified` 영향을
   문서화한다.
4. 의미 있는 test 또는 receipt 하나를 실행하고, 결과·실패·다음 blocker를
   `VALIDATION.md` 또는 대응 artifact에 기록한다.
