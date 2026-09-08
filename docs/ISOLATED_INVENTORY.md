# 격리 자산 인벤토리 (Inventory Slot)

## 책임

`_isolated/`에 들어있는 자산의 *메타*만 박제한다. 자산 *내용*은 절대 적지
않는다. 본 문서는 *어떤 자산이 있는지*를 추적하기 위한 운영 문서다.

## 현재 상태

- `_isolated/` 폴더 부재 — 본 문서 작성 전.
- **(F) 현시점 목록 박제:** 현재 격리 폴더는 미생성이고 도입 자산은 0건 —
  *지금 시점의 목록*은 **빈 목록**이다 (Boundary `격리 폴더에 지금 시점
  들어있는 자산 목록` OPEN_QUESTION 회수). 장래 도입 시에는 I1 서식
  (`근거` 필드 포함) 한 줄이 유일한 등록 경로다.
- (사용자가 별도 비공개 위치에 두고 있는 자산을 *언젠가* 이 폴더로 옮길 수
  있다. 그 시점에 본 문서가 *인벤토리* 역할을 한다.)

## 원하는 상태

- `_isolated/` 자산의 *목록*이 박제된다.
- 각 자산의 *출처*, *도입 일자*, *격리 사유*, *소유자*, *검토 일자*,
  *유효 기한*이 한 줄로 박제된다.
- 자산 *내용*은 절대 본 문서에 적지 않는다.
- 자산 *도입*/*폐기* 모두 인벤토리 갱신이 *커밋* 단위로 강제된다.

## 2026-09-08 Intel recovery 실행 입력 (위임된 신규 메타)

현재 상태: BP20에 따라 Apple 서버에서 받은 별도 Intel recovery 입력의 chunklist
검증을 root가 완료했다. 아래 목록은 이번 입력만 추가하며, 위의 과거 빈 목록
판정이나 이전 격리 조사 전체 인벤토리를 재작성하지 않는다. 원하는 상태는 실제
버전·아키텍처·매체 역할을 읽기 전용으로 판별한 뒤 정확한 부팅 입력을 선택하는 것이다.

- `_isolated/nextcore/intel-recovery-20260908/recovery/` :: 출처=apple-public-recovery-server 도입=2026-09-08 격리=external-runtime-media 소유=user 검토=2026-09-08 유효=permanent 근거=B1-사용자 보유 원본 macOS 설치·복구·게스트 디스크 매체
- `_isolated/nextcore/intel-recovery-20260908/extracted/` :: 출처=apple-public-recovery-server 도입=2026-09-08 격리=runtime-media-derived-input 소유=user 검토=2026-09-08 유효=permanent 근거=B1-macOS 원본 .kext 캐시 / System 프레임워크
- `_isolated/nextcore/intel-recovery-20260908/inspection/` :: 출처=local-read-only-media-inspection 도입=2026-09-08 격리=private-raw-metadata-audit 소유=user 검토=2026-09-08 유효=permanent 근거=B1-IPSW 추출 / BuildManifest 원본

- `_isolated/nextcore/tahoe-baseline-20260908/release/` :: 출처=acidanthera-OpenCorePkg-official-release 도입=2026-09-08 격리=external-reference-only 소유=user 검토=2026-09-08 유효=permanent 근거=B1-OpenCore EFI 빌드 도구
- `_isolated/nextcore/tahoe-baseline-20260908/completed-observations/` :: 출처=authorized-local-recovery-VM-observation 도입=2026-09-08 격리=private-runtime-analysis 소유=user 검토=2026-09-08 유효=permanent 근거=B1-사용자 보유 원본 macOS 설치·복구·게스트 디스크 매체

- `_isolated/nextcore/tahoe-mca-contract-20260908/` :: 출처=authorized-original-recovery-kext-inspection 도입=2026-09-08 격리=private-runtime-fault-analysis 소유=user 검토=2026-09-08 유효=permanent 근거=B1-macOS 원본 .kext 캐시 / System 프레임워크
- `_isolated/nextcore/qemu-cmci-20260908/` :: 출처=qemu-official-source-and-local-kvm-probes 도입=2026-09-08 격리=external-experiment-only 소유=user 검토=2026-09-08 유효=permanent 근거=B1-OpenCore fork / 일반 호환성 도구
- `_isolated/nextcore/kc-bootargs-contract-20260908/` :: 출처=apple-official-public-xnu-header-and-local-abi-probe 도입=2026-09-08 격리=public-source-contract-audit 소유=user 검토=2026-09-08 유효=permanent 근거=B1-Apple 공식 공개 XNU 헤더 / 공개 소스에서 확인되는 ABI


- `_isolated/nextcore/tahoe-guest-gpu-20260908/` :: 출처=original-recovery-kext-metadata-and-public-xnu-contract 도입=2026-09-08 격리=private-media-inventory-and-guest-diagnostic 소유=user 검토=2026-09-08 유효=permanent 근거=B1-macOS 원본 .kext 캐시 / System 프레임워크
- `_isolated/nextcore/tahoe-full-installer-20260908/` :: 출처=apple-official-software-update-production-catalog 도입=2026-09-08 격리=original-installer-and-download-audit 소유=user 검토=2026-09-08 유효=permanent 근거=B1-사용자 보유 원본 macOS 설치·복구·게스트 디스크 매체

- `_isolated/nextcore/arm-fault-time-20260908-r1/` :: 출처=original-arm-guest-readonly-mmio-observation 도입=2026-09-08 격리=private-runtime-observation 소유=user 검토=2026-09-08 유효=permanent 근거=B1-IPSW 추출 / BuildManifest 원본
- `_isolated/nextcore/arm-fault-time-20260908-r2/` :: 출처=original-arm-guest-readonly-mmio-observation 도입=2026-09-08 격리=private-runtime-observation 소유=user 검토=2026-09-08 유효=permanent 근거=B1-IPSW 추출 / BuildManifest 원본
- `_isolated/nextcore/arm-fault-time-20260908-r3/` :: 출처=original-arm-guest-readonly-mmio-observation 도입=2026-09-08 격리=private-runtime-observation 소유=user 검토=2026-09-08 유효=permanent 근거=B1-IPSW 추출 / BuildManifest 원본
- `_isolated/nextcore/bp16-public-delta-20260908/` :: 출처=official-primary-source-pin-review 도입=2026-09-08 격리=source-comparison-audit 소유=user 검토=2026-09-08 유효=permanent 근거=B1-VMApple 디바이스 모델 패치 시리즈

결정: 매체 본체·추출물·원시 조사 결과는 stage하지 않는다. 공개 결과는 빌드 식별자,
아키텍처, 역할, 해시, 종료 상태 메타로 제한하며 `nextcore/artifacts/boot-media-candidates-20260908.md`에 기록한다.
외부 다운로드/추출 도구는 같은 실행 작업 디렉터리의 `tools/`에 별도 보관하고
Nextcore 소스 또는 Cargo 빌드 의존성에 포함하지 않는다. 이는 도구 자체를 Apple
비공개 자산으로 분류하는 결정이 아니다.

## 결정 항목

### I1. 메타 형식

각 자산은 다음 형식으로 한 줄 박제:

```
- <상대 경로>  ::  출처=<source>  도입=<date>  격리=<reason>  소유=<owner>  검토=<review-date>  유효=<valid-until>
```

필드 정의:
- `출처` — 자산의 원出处 (예: `iboot-raw-analysis`, `apple-public-spec`,
  `user-personal-note`).
- `도입` — 본 인벤토리에 *최초* 박제된 일자 (YYYY-MM-DD).
- `격리` — *왜* 이 자산이 격리 폴더에 있어야 하는지 한 줄 (예:
  `apple-internal`, `re-impl-block`, `audit-trail`). 형체화 우려 사유를
  명시.
- `소유` — 자산 책임자. `user` (사용자 본인) 또는 협업자 식별자.
- `검토` — 마지막으로 *격리 사유*를 재검토한 일자 (YYYY-MM-DD).
- `유효` — 격리 유지 기한 (YYYY-MM-DD 또는 `permanent`). 사용자 결정.
- `근거` — (F) 신설. 해당 자산이 B1 매트릭스 어느 행의 판정에 해당하는지
  그 **행 이름 한 줄** (`B1-<행 이름>` 형식). 신규 도입부터 필수이며,
  I1 서식 코드 블록의 `유효` 뒤에 병기한다. 판정 근거의 *재요약·내용
  기재는 금지* — 행 이름 참조만 적는다.

> 결정 근거: 격리 사유는 시간이 지남에 따라 약해질 수 있다 — `검토`/`유효`는
> *재평가* 메커니즘이다. `소유`는 비공개 위치 → 격리 이동 시 책임자가
> 유실되지 않도록 한다.

### I2. 도입 후보

각 후보에 대해 *도입 여부*와 *도입 사유* 또는 *미도입 사유*를 한 줄씩
박제한다. *지금* 시점의 결정만 박제하며, 자산의 실제 도입은 사용자
결정에 따른다.

- `_isolated/apple/avpbooter-notes/` — AVPBooter 분석 메모.
  - 도입 여부: **보류** (사용자 결정 시 도입).
  - 사유: B1상 iBoot 패밀리 일부; 형체화 우려로 격리 후 D2.4 인계 단계 설계 참고.
- `_isolated/apple/iboot-handoff/` — iBoot handoff 자료구조 분석.
  - 도입 여부: **보류** (사용자 결정 시 도입).
  - 사유: D2.4 인계 단계의 *외부 동작* 이해 목적; *내부 구현* 모방은 D3상 금지.
- `_isolated/apple/img4-format/` — img4 포맷 분석.
  - 도입 여부: **보류** (사용자 결정 시 도입).
  - 사유: B1 격리 대상; 인증서/키는 X; D3상 검증 미수행이므로 *호환성 진단* 목적 한정.
- `_isolated/openlegacy/upstream-comparison/` — OpenCore와의 비교 분석.
  - 도입 여부: **보류** (사용자 결정 시 도입).
  - 사유: OpenCore는 공개 부트로더 (B1, B3); *공개 사양/동작*만 비교, 내부 디테일 비교 X.
- `_isolated/apple/device-tree-internal/` — Apple 내부 DeviceTree 명세
  분석 (Public 명세와 차이점).
  - 도입 여부: **미도입** (현 시점).
  - 사유: D3 "Nextcore는 *공개 DeviceTree 명세*만 사용, 내부 포맷 비의존";
    공개 명세로 충분하여 내부 분석 불필요. 향후 내부 포맷 의존 구현이
    필요해지면 Boundary와 재협의.
- `_isolated/apple/secureboot-policy/` — SecureBoot 정책 공개 부분 분석.
  - 도입 여부: **보류** (사용자 결정 시 도입, 범위 제한).
  - 사유: B3상 "SecureBoot *우회 없이* 동작하는 도구"는 위험 신호 아님;
    *공개 부분*만 분석 (UEFI 사양, 공개 변수), *우회* 목적 분석은 X.
- `_isolated/nextcore/knowledge-base/` — Nextcore 구현 시 참고한 지식
  단위의 메타 (코드 아님).
  - 도입 여부: **보류** (사용자 결정 시 도입, 프레임워크만).
  - 사유: B2 격리 → Nextcore 지식 이전 허용 (다른 표현); *지식 단위
    식별자*만 추적하는 메타 폴더, 코드 없음, 형체화 방지 감사용.

> 결정 근거: 모든 후보를 *지금* 도입하지 않음 — 사용자 비공개 위치에 자산이
> 존재하지 않는 한 인벤토리는 빈 상태로 유지. `Boundary:어떤 자산을 *지금*
> 도입해야 하는지` OPEN_QUESTION은 본 I2 결정으로 해소.

### I3. 인벤토리 규칙

- 본 문서는 *메타만* 다룬다. 자산 *내용*은 격리 폴더 안에만 존재한다.
- 본 문서를 *통해* 자산 내용을 *요약*하지 않는다. 한 줄 설명조차
  형체화로 이어질 수 있으면 적지 않는다.
- 자산 *도입* 시: 사용자는 *반드시* 본 인벤토리에 `I1` 형식의 한 줄을
  *먼저* 추가한 후, 해당 자산을 `_isolated/<경로>`에 두고 커밋한다.
  `tools/git/hooks/pre-commit` 가드는 staged 영역에 `_isolated/` 자산이
  들어왔을 때, 본 인벤토리 *최신 박제*에 해당 경로가 *없으면* 커밋을
  거부한다. (가드 구현 디테일은 Build Plan 슬롯 영역; 본 슬롯은 *계약*만
  정의한다.)
- **(F) 개정 — Boundary `신규 격리 도입 시 B1 판정 근거 한 줄 병기` 회수:**
  신규 자산 도입 시에는 `I1` 기본 필드에 더해 `근거=<B1 행 이름>` 병기를
  필수로 한다. 가드는 이 필드 누락 시에도 커밋을 거부하는 *계약*으로
  정의한다(구현은 Build Plan 영역).
- 자산 *폐기* 시: 본 인벤토리에서 해당 줄을 *제거*하고, 다음 형식으로
  *폐기 기록*을 한 줄 박제한다:
  ```
  - ~~<경로>~~  ::  폐기=<date>  사유=<reason>
  ```
  폐기 사유는 `유효` 만료, `검토` 결과 격리 불필요, `소유` 변경 등.
  폐기 기록은 *히스토리*로 남으며, 이후 자산을 *재도입*할 경우 새
  `도입` 일자로 새 줄을 박제한다.

> 결정 근거: 도입/폐기 모두 *커밋 단위*로 강제되어야 형체화 방지 가드가
> *우회*되지 않는다 — 인벤토리 갱신 없는 staged 변경은 *어떤* 형태로든
> pre-commit 가드가 막는다.

### I4. 지식 단위 기록 형식 (F 박제)

Design `OPEN_QUESTION: Inventory:지식 단위 재서술 결과의 메타 한 줄 형식을
확정하라`(D8이 Inventory로 위임한 분)에 대한 답변 — B2-3 절차를 통과한
재서술 결과를 `_isolated/nextcore/knowledge-base/`에 아래 한 줄 메타로
기록한다. *메타만* 담고 지식 단위 본문은 공개 문서 쪽에만 존재한다.

```
- KB-<번호>  ::  interface=<필요한 외부 인터페이스 한 문장>  origin=<출처 카테고리>  rephrased=<date>  verified_by=<주체>  target=<공개 문서 박제 위치>
```

- `interface` — D8의 이전 가능 단위 정의(자연어 한 문장 인터페이스 서술)를
  그대로 따른다. 코드 줄·구조체 레이아웃·상수·오프셋·바이너리 인용 금지
  (D8·AGENTS §0).
- `origin` — I1 `출처`에 쓰는 카테고리 식별자만 적고, 원문·출처 인용을
  담지 않는다(D8 재서술 조건).
- `target` — 재박제 결과가 공개 문서 어디에 결정으로 들어갔는지 위치만
  적는다(B2-3 4단계 "감사 가능한 형태"의 Inventory 측 실행 형식).
- 본 절은 *형식*만 박제하며 예시 내용은 적지 않는다(I3 규칙과 동일).

## OPEN_QUESTION

- `OPEN_QUESTION: Design:격리 자산에서 Nextcore로 이전 가능한 *지식 단위*의 정의`
  — *지식 단위*의 정의는 Design 슬롯 영역. 본 슬롯 (I2의
  `_isolated/nextcore/knowledge-base/` 후보)에서는 *식별자만* 추적하기로
  박제.
  → RESOLVED-BY-F: Design D8이 이전 가능 단위(자연어 한 문장 인터페이스
  서술)와 금지 항목을 박제; D8이 Inventory로 되위임한 메타 한 줄 형식은
  본 문서 I4 (F)에서 박제. 이 관점으로 본 문서의 잔여 미합의는 없다.

## 통합 검증 (F)

| 질문 (본 문서) | 결론 | 박제 위치 |
| --- | --- | --- |
| 지식 단위 정의 | RESOLVED — D8 앵커 | Design D8, 본 문서 I4 (F) |

- 타 슬롯이 본 문서에 던져 여기에서 회수한 항목: Boundary `현시점 자산
  목록` → 현 상태 (F) 빈 목록 박제, Boundary `B1 판정 근거 병기` →
  I1 `근거` 필드 + I3 (F) 개정, Design `메타 한 줄 형식` → I4 (F).
- (F) 확인: I2 도입 후보의 보류/미도입 결정은 사용자 도입 전까지 유효 —
  인벤토리 운영 규칙(I3)과 정합. 자산 내용·키·blob·내부 포맷 레이아웃은
  본 회수 과정에서 어떤 문서에도 기재하지 않았다.
