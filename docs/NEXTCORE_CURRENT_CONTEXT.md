# Nextcore 현재 맥락과 재개 기준

갱신: 2026-09-07. 이 문서는 다음 작업자가 가벼운 모델이더라도 현재 상태를
과장하지 않고 이어갈 수 있게 하는 정본 요약이다. 상세 설계는
`docs/NEXTCORE_BUILD_PLAN.md`, 검증 결과는 `nextcore/VALIDATION.md`를 따른다.

## 목표와 현재 판정

목표는 공개 clean-room EFI/boot engineering으로 macOS의 EFI 부팅 경로를
검증하는 것이다. 현재 `macos_boot_verified=false`다.

| 계층 | 확인된 것 | 아직 아닌 것 |
| --- | --- | --- |
| x86 UEFI | authored OVMF probe에서 allocation, copy/zero/readback, flat DT, 32-bit transition 통과 | 실제 x86_64 XNU kernel 부팅 |
| ARM recovery | DFU, iBEC endpoint/prompt, 5 restore role, `bootx` ACK 관측 | XNU, userspace, Metal, macOS boot |
| ARM firmware | `bootx` 뒤 4-byte MMIO decode failure를 same-event trace로 확인 | 장치 register/access contract 또는 안전한 장치 모델 |
| graphics | GPU policy/virtual-device 모듈과 테스트는 존재 | 실제 graphics driver/Metal 구현과 runtime acceptance |

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

1. 실제 x86_64 target kernel을 공개·합법적인 입력 범위에서 확보하면, authored
   OVMF probe와 분리한 handoff acceptance를 새 receipt로 수행한다.
2. ARM panic은 public device contract가 새로 확인될 때만 최소 read-only MMIO
   모델로 같은 event를 한 번 비교한다.
3. native Apple Silicon macOS host가 제공되면 host identity → VM boot marker →
   XNU marker → userspace marker 순서로 별도 receipt를 만든다.
4. graphics driver는 현재 대형 모델 rate limit 때문에 구현을 보류한다. 작은
   모델은 범위를 넓히지 말고 public contract, module test, 문서 정합만 유지한다.
   구현 재개 시 GPU/driver layer의 공개 ABI와 runtime acceptance plan을 먼저
   고정한다.

## 모듈 배포 상태

Nextcore는 다음 public GitHub repositories로 배포됐고 각각 `main`과
`26x86-Nextcore-<Module>-v0.1.0` tag를 갖는다:

- `26x86/Nextcore-Core`, `Nextcore-GPU`, `Nextcore-HAL`, `Nextcore-ISE`
- `26x86/Nextcore-APLS`, `Nextcore-EFI`, `Nextcore-Tool`

`Tools/export_nextcore_repositories.py`가 fresh export, fixed dependency tag,
`repository.json`, sha256 inventory와 CI를 만든다. clone verification에서 Core
test, Tool test (8 passed, 1 externally supplied EFI fixture ignored), EFI UEFI
check는 통과했다. APLS standalone build는 `vf_policy.rs`가 루트
`sandbox/vsk/config/golden-gate.template.plist`를 `include_bytes!`로 참조해
실패했다. 이는 모듈 경계 결함이며, template를 public module-owned input으로
이관하거나 explicit runtime input으로 바꾸기 전에는 APLS를 독립 통과로 기록하지
않는다.

## 최소 재개 절차

1. `AGENTS.md`, 이 문서, `nextcore/VALIDATION.md`를 읽고 `git status --short`를
   확인한다.
2. 작업을 x86 UEFI, ARM firmware, graphics, module release 중 하나로 분류한다.
3. 변경 전후에 그 계층의 acceptance criterion과 `macos_boot_verified` 영향을
   문서화한다.
4. 의미 있는 test 또는 receipt 하나를 실행하고, 결과·실패·다음 blocker를
   `VALIDATION.md` 또는 대응 artifact에 기록한다.
