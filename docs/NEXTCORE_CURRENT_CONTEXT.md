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
조정하며 push는 승인되지 않았다. Design/Prompts는 picker 담당에게 위임됐다.

| 계층 | 확인된 것 | 아직 아닌 것 |
| --- | --- | --- |
| x86 UEFI 자체 handoff | authored OVMF probe에서 allocation, copy/zero/readback, flat DT, 32-bit transition 통과 | 자체 KC loader의 실제 x86_64 XNU 진입 |
| local virtualization | WSL KVM 모듈 적재 후 API 12·query-kvm·실제 OVMF Shell 실행, developer 전용 device ACL | 이 결과만으로 macOS boot 판정 |
| x86 UEFI → host HAL | BP19 실제 OVMF RSDP+7 SDT+5 PCI header 수집/파싱, exit 67와 원본 hash 유지 | XNU platform provider, AML 실행, 게스트 장치 게시, 물리 하드웨어 |
| Tahoe 외부 reference | CMCI 레지스터/인터럽트 실측 후 원본 XNU consumer와 idle PC 일치; launchd·recoveryosd·WindowServer 실행 | 검정 화면 해소, native Nextcore HAL, macOS 전체 부팅 |
| Tahoe native EFI | production ConsoleControl → 원본 booter → 실제 XNU/launchd PID 1, PC 256B가 원본 KC와 유일하게 일치; authored 17 checks와 두 child 반환 통과 | restore-datapartition exit(1) userspace panic 해결, 전체 native HAL/GUI/Metal |
| native KC 준비 | 67,584,000-byte 실제 EFI pages 배치/readback/해제, 65,260 classic host 적용·전체 readback, 401,606 chains/header 보존, rev1 boot_args codec, core 142 tests | EFI relocation 연결, entry/slide/provider 계약, native XNU 실행 |
| ARM recovery | DFU, iBEC endpoint/prompt, 5 restore role, `bootx` ACK 관측 | XNU, userspace, Metal, macOS boot |
| ARM firmware | `bootx` 뒤 4-byte MMIO decode failure를 same-event trace로 확인 | 장치 register/access contract 또는 안전한 장치 모델 |
| graphics | 공개 NextCore compute API로 Intel GPU의 512값 readback·실제 fence·오류 거부; x86_64/ARM64 guest Metal probe 빌드 | guest driver/Metal 실행, native macOS graphics acceptance |

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
   같다. launchd PID 1까지 도달했으며 다음 실패는 restore-datapartition exit(1)
   userspace panic이다. corrected fresh 관측은 22.0017초 자연 종료/원본 hash 유지/
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
   recoveryosd PID 65/WindowServer PID 81이 실행됐다. 298초 관측의 화면은 검정이다.
   외부 Reims+CMCI 11.1 빌드와 guest MSR probe가 통과했다. Reims PCI 장치는
   존재하나 원본 recovery에 AppleParavirtGPU/IOGPUFamily가 없어 driver attach와
   Metal은 확인되지 않았다. 공식 전체 Tahoe installer를 검증해 full OS 경로를
   진행한다. AHCI Port 2 abort는 원본 복구 디스크가 아닌 자동 생성된
   빈 CD-ROM에 대응한다는 QMP 실측이 있다.
   WSL 재시작 후 device가 없으면 설치 모듈의 적재 여부를 먼저 확인한다.
4. graphics는 public ABI와 실제 GPU submit/readback으로 진행한다. 과거의
   대형 모델 rate-limit 기록은 현재 구현 보류 근거가 아니다. BP20에서 WSL
   portable Mesa dzn을 빌드해 Intel 8086:7D41 실제 GPU를 선택하고 공개
   `ComputePipelineManager`의 두 입력 세트 512값 readback을 확인했다.
   기본 backend와 미연결 VirtualMetalDevice/SGPU의 compute·render·present는
   실행 없이 완료하지 않는다. guest API/driver 연결과 Metal은 아직 미검증이다.

## 모듈 배포 상태

Nextcore는 다음 public GitHub repositories로 배포됐고 각각 `main`과
`26x86-Nextcore-<Module>-v0.1.0` tag를 갖는다:

- `26x86/Nextcore-Core`, `Nextcore-GPU`, `Nextcore-HAL`, `Nextcore-ISE`
- `26x86/Nextcore-APLS`, `Nextcore-EFI`, `Nextcore-Tool`

`Tools/export_nextcore_repositories.py`가 fresh export, fixed dependency tag,
`repository.json`, sha256 inventory와 CI를 만든다. clone verification에서 Core
test, Tool test (8 passed, 1 externally supplied EFI fixture ignored), EFI UEFI
check는 통과했다. APLS standalone build는 `vf_policy.rs`의 workspace 외부
`include_bytes!` 경계 때문에 실패했으나, 2026-09-07에 crate 소유 테스트 fixture로
교체했다. 현재 `cargo test -p nextcore-apls`는 48개 테스트가 통과한다. 이는
APLS 계약/소프트웨어 테스트 통과이며 실제 macOS/XNU/Metal 또는 물리 화면 출력의
증거는 아니다.

## 최소 재개 절차

1. `AGENTS.md`, 이 문서, `nextcore/VALIDATION.md`를 읽고 `git status --short`를
   확인한다.
2. 작업을 x86 UEFI, ARM firmware, graphics, module release 중 하나로 분류한다.
3. 변경 전후에 그 계층의 acceptance criterion과 `macos_boot_verified` 영향을
   문서화한다.
4. 의미 있는 test 또는 receipt 하나를 실행하고, 결과·실패·다음 blocker를
   `VALIDATION.md` 또는 대응 artifact에 기록한다.
