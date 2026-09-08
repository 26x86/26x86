# NextCore 현재 맥락과 재개 기준

갱신: 2026-09-09. 아래 최신 BP 요약이 이후 역사 기록보다 우선한다. 이 문서는 다음 작업자가 가벼운 모델이더라도 현재 상태를
과장하지 않고 이어갈 수 있게 하는 정본 요약이다. 상세 설계는
`docs/NEXTCORE_BUILD_PLAN.md`, 검증 결과는 `nextcore/VALIDATION.md`를 따른다.

## BP35 최신 개발 상태

Core PR6/mainc08d10b, EFI PR9/main76964c0, Tool PR6/main391adb7를 병합했다.
상위는 Corebab7/EFI03a/Tool8ea를 연결하고 ISE0d를 유지한다. 별도 deep feature와
정확한 deep-16384 selector만 긴 진단을 허용하며 기존 기본값·예산은 유지한다.
정식 standalone EFI와 실제 deep5개, CLI 거부28개 및 x1변조 거부가 통과했다.
초기 control에서 non-trace 빌드를 지정해 기대한 TRACE_CONFIG_INVALID 대신
PROVIDERS_PENDING에 멈췄다. 그 실패를 보존하고 올바른 tiered-only control로
소스·판정식 변경 없이 재검증했다. 새 상위 재귀 검사와 최종 CI를 진행한다.

역사적 원본 macOS27 진단은 한 번 실행해5311명령,5312fetch,783data 이후
UBFM/LSL 미지원 경계에 도달했다. 원본 좌표·바이트는 공개하지 않는다. 이 결과는
정상 부팅이 아니며 SPTM 서비스·실제 플랫폼 DT·데스크톱·guest Metal은 미완료다.
후속 BP36 UBFM과 Undefined IL 수정은 별도 ISE PR8/main251fbd5에 병합됐고,
이 BP35 통합에는 포함하지 않는다. 관련 EFI 연결과 current adapters를 검증 중이다.

## BP34 최신 개발 상태

BP33은 상위 PR15/main9ef0e262로 최종 CI29개와 정식 재귀 클론 검사 후 병합했고
완료 브랜치를 정리했다. 이번 통합은 별도 병합된 ISE0d722886(PR7/mainbcf1ca9)과
EFIed9ba255(PR8/maincfc8af9)를 연결한다. Core147/Tool4bb 및7개 서브모듈 구조는 유지한다.
ISE는 one-way MMU enable, 분리된 architectural/effective 상태, 실제 canonical TLBI를
구현한다. 새 NXDYN의 authored6개는 x86 EFI에서 MMU를 켠 뒤 다른 물리 페이지로
fetch/load/store하며 정확한 fault도 확인한다. 실제58 fetch/data 및40 control 이벤트,
전체 RAM과 불변 테이블,30개 reader 변조 거부를 별도로 검증했다.
독립 Arm6개와 native C/Rust 비교도 통과했다. 성공2개의 원래 HVC는 변경하지 않고
unsupported boundary로 분리한다. 하드웨어 TLB refill이나 HVC dispatch를 주장하지 않는다.
정식 standalone과 새 상위750bda20 재귀53명령 검증이 통과했다. workspace502/Python149/GUI25,
참조98/service44, 실제EFI200 및 별도CLI6, native Arm6비교와13변조 검사를 확인했다.
전체 기록은 nextcore/artifacts/integration-bp34-20260909이며 최종 정식 재귀 클론/CI 후 병합한다.

별도 BP35의16384-budget 원본 진단은5311명령에서 UBFM/LSL 지원 경계에 도달했다.
좌표/바이트는 비공개이며 BP36 UBFM과 Undefined ESR의 IL 수정은 독립 검증 중이다.
이 통합의 동결된 BP34 소스와 역사적 결과는 변경하지 않는다. 정상 macOS27
handoff/데스크톱, 실제 SPTM 서비스, EFI GPU와 guest Metal은 여전히 미완료다.

## BP33 최신 개발 상태

BP32는 상위 PR14/main1b86a2e로 최종 CI29개와 정식 재귀 클론 검사 후 병합했다.
BP33 최종 연결은 Core147f4c4, EFI7e7a08b, Tool4bb09da다. Core PR4/main0e2bcca와
Tool PR4/main14977ec는 병합됐고, Core PR5/main1c5f8a1이 실제 EFI 디버그 SHA-256
LLVM 오류를 수정했다. EFI PR7/main53329bf와 Tool PR5/main6ead716도 최종 CI 후 병합하고 완료 브랜치를 정리했다.
7개 서브모듈/8개 소유 패키지 구조를 유지한다.

Core는 실제 소유/배타 차용 RAM과64개 목적별 예약을 연결하고, owner/generation에
묶인 DeviceTree patch만 커밋한다. 변환기는 공개 authored provider 값을 명시적으로
받으며 임의 식을 실행하거나 target ABI를 만들지 않는다. 독립 Core257개와 no-default232개,
수명 compile-fail 및 UEFI 코드 생성이 통과했다.

새 opt-in NXDT는 실제 EFI RAM/table/JIT 할당과 ledger에서 얻은 배치를 사용한다.
4K/16K·상/하위 VA의 authored8개에서 직렬화된 DT를 실제 generated-x86 ARM load/store로
소비한다. stale patch는 JIT 전에 거부하고 전체 RAM/immutable table을 확인한다.
별도 잘못된 mapping 바이너리가 실제 첫 DT load fault로 실패한다. 원래8-case 기록은
보존하고 보고서 envelope/주소 범위 결함을 고친 reader는28개 변조를 거부한다.
정식 빌드의 바이너리/결과는 역사적 outside-tree patch 결과와 별도로 기록한다.
EFI 대상만 software SHA-256을 선택하며, 기존 debug NXAPFS gate를 유지하고 Core/상위
CI에도 실제 debug codegen/link를 추가했다. 초기 재귀30a8e2e는 provider 우회 실행 후
QEMU 종료 대기 시간 초과로 실패했으며 해당 실패 기록도 보존한다.
공개 증거는 nextcore/artifacts/guest-memory-dt-20260909다.

다음 BP34 ISE0d722886은 PR7/mainbcf1ca9로 별도 병합했다. one-way MMU enable과
독립 Arm capture6개 비교는 통과했지만 이번 BP33은 기존 ISE720을 유지한다.
실제 dynamic EFI caller와 명시적16384 원본 진단은 별도 작업이다. 정상 macOS27
handoff/데스크톱, SPTM 서비스, EFI GPU와 guest Metal은 아직 미완료다.

BP33 최종 재귀e0351bd는47개 검증 명령을 통과했다: workspace502(문서검사 포함),
Python149/GUI25, 실제EFI194 및 별도CLI6, 참조98/service39/Vulkan119와 패키지검사.
Core no-default232개와 compile-fail3개, 실제 debug NXAPFS link, DT 변조28개도 통과했다.
Clippy의 기존 경고는 기록 그대로 유지한다. 전체 기록은
nextcore/artifacts/integration-bp33-20260909이며 최종 공개 커밋은 정식 재귀 클론/CI로 확인한다.

## BP32 최신 개발 상태

BP31은 PR #13/main0509118로 최종 CI28개 및 정식 재귀 클론 검사 후 병합했다.
BP32 ISE720d7c6는 PR #6/main91721d0으로 병합했고, 실제 native M=1 fetch/scalar/pair를
Rust의 동일 canonical walker로 실행한다. EFI는 PR #6/main646bc5f로 병합했다. 최종 pinf3f7938은 독립 검증한8d53dd2에서
재현 문서/메타데이터만 정정했다. ISE의 두 의존성을 같은 커밋으로
고정하고 명시적 NXMMU 진단 feature를 제공한다.7개 모듈과 기존8개 패키지 소유 구조는 유지한다.
새 상위 재귀 baseline df60198b는 workspace476/Python149/GUI25/참조98, 실제 EFI186개
및 별도 CLI 거부6개와 native/ARM/Vulkan/패키징 검사를 통과했다. 최종 문서 pin의
소스 동일성·인벤토리도 검증했다. 최종 상위 커밋은 정식 재귀 클론과 CI 후 병합한다.
공개 전체 기록은 nextcore/artifacts/integration-bp32-20260909다.

고정 Normal-NC/A=1 프로필에서 테이블과 제어 상태는 변경하지 않는다. 기존 v1/M=0 경로를
보존하고 새80/160/128/320-byte ABI에서 번역된 VA와 실제 RAM 주소를 구분한다.
EL0/EL1 실행 권한, 교차 EL TLB 쓰기 권한, MAIR 인코딩과 잘못된 콜백 오류 응답을 수정했다.
ISE의 최종 독립 클론은98 참조 테스트,10 C/Rust 실행,39 서비스/공유 테스트와 기존158
Arm 비교 및 의미 오류 대조를 통과했다. 과거 BP29 비교 도구/영수증은 그대로 두고
현재 검증은 compare_current_walker.py를 사용한다.

역사적 authored EFI108개 및 잘못된 VA-as-PA 대조를 별도 바이너리/해시로 보존한다.
Arm 서비스 비교는 기록된354개 값(322 data/32 완료 시점 fetch 상태)과74 BTYPE 거부다.
완료 시점 상태는 원래 target fetch 상태를 증명하지 않는다. 별도 ERET78개는 실제 BTYPE=0
진입과 서비스 결과가 일치한다. QEMU의12 PC-priority 불일치는 실패로 유지한다.
공개 증거는 arm-stage1-native/oracle/service-comparison-20260909 세 디렉터리다.

동적 MMU 켜기/제어 변경, mutable table, 예외 처리기, 실제 macOS27 정상 진입/데스크톱,
EFI GPU와 guest Metal은 남아 있다. Core305 runtime-DT 변환기는 별도 모듈 main에만 있으며
이번 통합 Core408에는 포함하지 않는다. 실제 메모리 예약/수명 연결과 EFI 소비를 이어 개발한다.

## BP31 최신 개발 상태

상위 PR #13의 새 재귀 baseline8bcf5c52는 workspace476/Python149/GUI25/참조93,
실제 x86 EFI78개 및 별도 CLI 거부6개를 통과했다. f38a2c30의 강화한 runner는
별도 canonical standalone EFI에서13개 provider 사례와 실제 우회 거부1개를 검증했다.
증거는 `nextcore/artifacts/integration-bp31-20260909`에 있다. 최종 증거 커밋은 별도
GitHub 재귀 클론과 최종 CI를 검증하고 병합한다.

BP30 상위 PR #12/main3912da33은 최종 CI28개와 최종 GitHub 재귀 클론/해시 검사를
통과해 병합했다. 완료된 상위/모듈 브랜치는 정리했고7개 서브모듈 구조를 유지한다.
BP31 ISE0aabf085와 EFI7495633은 각각 PR #5로 main 병합됐다. CCMP/CCMN을32/64-bit
register/imm5 전체와 AL/NV 조건까지 generated x86으로 실행한다. 독립 ISE 클론에서
native34264개/137070assertions, 참조93개, Arm3668개와 오류 대조군이 통과했다.
빈 Cargo cache의 독립 EFI 클론도 정식 Git 의존성으로 빌드하고 실제 combined EFI13개
조건부 비교 사례를 통과했다. 상위 통합은 그 exact heads를 별도로 검증한다.

역사적 원본 진단은256/1024/4096 예산을 순서대로 소진했고 마지막은4096명령/
1205native blocks다. checkpoint는 메타데이터 순회 진행과 일치하지만 정상 handoff나
부팅 완료를 뜻하지 않는다. 공개 증거는 `nextcore/artifacts/arm-conditional-compare-20260909`.
BP32 native M=1 및 runtime DT prototype은 별도 진행 중이며 이 통합 소스에는 없다.
정상 macOS27 부팅, 사용 가능한 데스크톱, EFI GPU와 guest Metal은 여전히 미완료다.

## BP30 최신 개발 상태

상위 PR #12의 구현 commit ea0a62e8에서 새 재귀 클론 검증이 통과했다: workspace476,
Python149, GUI25, 실제 x86 EFI65, 별도 CLI 거부6, 참조91 및 ARM 오류 대조158개.
검증 기록은 `nextcore/artifacts/integration-bp30-20260909`에 보존한다. 최종 증거/문서
커밋은 별도의 정식 GitHub 재귀 클론과 최종 CI를 거쳐 병합한다.

BP29는 상위 PR #11/main7db1a709로 병합했고 최종 CI27개 및 공개 재귀 클론이 통과했다.
BP30은 ISE의 no_std Rust 메모리 서비스를 실제 x86 EFI에 연결한다. Core40833dc,
ISE41e8997, EFI2414067, Tool926c777의 변경 PR도 각각 main에 병합했다. 상위 통합에서는
7개 Git 모듈과 7개 workspace 구성원을 유지하고, 보조 패키지 nextcore-memory-service는
ISE 안의 정식 소스로 고정한다. 별칭·대상별 의존성·중복 Git revision과 실제 Cargo
해석 결과를 검사한다. 새 standalone EFI 클론의 canonical Git fetch/5개 빌드와 실제
메모리 provider23개·별도 callback 오류1개·직접 호출 우회 대조·진단 예산8개 검사가 통과했다.

`arm-jit-memory-provider`는 fetch/scalar/pair를 호출자 소유 Rust 서비스로 연결하는
명시적 진단 feature다. `arm-jit-tiered-trace`는256/1024/4096 예산을 따로 허용한다.
일반 빌드의64/8 제한과 native SCTLR.M 차단을 유지한다. 상위 새 EFI runner와 재귀
통합 결과는 별도 commit/binary로 검증한다. 과거 독립 실행을 현재 바이너리로 바꿔 쓰지 않는다.

정상 진입 입력은 M1/j274의 현재 KC와 outer LC_UNIXTHREAD를 유지한다. 전체 manifest에는
해당 SPTM/TXM 구성 요소가 있으며, 정확한 macOS27 부팅 인자/서비스의 실제 상태 계약은
아직 미확정이다. 세부 공개 감사는 `NEXTCORE_ARM64E_ENTRY_CONTRACT.md`에 있다.
BP31 CCMP/CCMN과 원본4096명령 진단은 별도 다음 변경이며 BP30 소스에 섞지 않는다.

## BP29 현재 구현과 실행 대상

실행 컴퓨터는 항상 x86_64이며 ARM64e macOS 27 입력을 x86 EFI의 전용 JIT/HAL로 처리한다.
WSL은 빌드 환경이고 QEMU/OVMF는 x86 시험 장비다. 7개 Git 서브모듈이 각자의
정식 원격 저장소와 고정 커밋으로 연결된다. 사용자는 검증 후 커밋·푸시·PR·main 병합과
완료 브랜치 정리를 승인했다. 기기 전용 프로필과 Windows 앱의 샌드박스 테스터 제거는
BP27에서 완료했다.

BP28 상위 PR #10은 main 4ed3c9e로 병합됐다. ISE/GPU/EFI/APLS/Tool PR #2도 모두
병합했다. BP29 scalar 정수 메모리 13종과 상세 MMU 오류 API를 구현했고, 새 독립
ISE 클론의 91개 참조 테스트 및 ARM 158개 입력 대조가 통과했다. 실제 x86 EFI의
11개 authored scalar 검사와 부호 확장 오류 대조군도 검증했다. 원본 진입 진단은
47명령에서 현재 예산 64명령까지 진행했으며, 다음 중단점을 별도 진단한다.

실제 macOS 부팅·사용 가능한 데스크톱·게스트 Metal은 미완료다. native SCTLR.M도
아직 거부한다. 다음 단계는 동일 JIT의 Rust 메모리 서비스 호출, 실제 MMU·플랫폼
제공자·정상 커널 진입이다. 현재 물리 GPU는 AMD RX 6800 XT이며 Windows Vulkan
검증을 보존한다. NVIDIA/Intel 선택 및 메모리 경로는 공급사별 가정 없이 구현했지만
이 두 GPU의 현재 실기 검증과 EFI GPU/게스트 Metal 검증은 남아 있다. 아래의 Intel
실행 기록은 과거 다른 환경의 증거이며 현재 호스트의 증거로 바꾸어 쓰지 않는다.

자세한 계약은 Build Plan BP29/BP30, scalar EFI 증거는
`nextcore/artifacts/arm-scalar-memory-20260909`, MMU 오라클은
ISE 모듈의 `tools/mmu_fault_levels`에 있다.

## BP24까지의 역사 기록

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
