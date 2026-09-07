# 공개/비공개 경계 (Boundary Slot)

## 책임

공개 트리에 *들어갈 수 있는* 자산과 *들어갈 수 없는* 자산을 분류한다.
agent가 *과민 반응하지 말아야 할 것*도 명시한다.

## 현재 상태

- B1 자산 분류 매트릭스 — 박제 완료 (확장 결정 포함).
- B2 격리 폴더 운영 규칙 — 박제 완료 (읽기/백업/지식이전 포함).
- B3 agent 과민 반응 금지 — 박제 완료 (추가 항목 포함).
- B4 판단 요청 절차 — 박제 완료 (기록 형식 명시 포함).

## 원하는 상태

- 자산 분류 매트릭스가 박제된다.
- 격리 폴더 운영 규칙이 박제된다.
- agent 행동 지침 (과민 반응 금지)이 박제된다.

## 결정 항목

### B1. 자산 분류 매트릭스

> *결정 근거: AGENTS.md §0(형체화 금지)·§1(슬롯 책임)·§4(과민 반응 금지)를 따르며,
> UEFI Forum / DMTF / Open Firmware 같은 *공개 표준 문서*는 Apple 자산이 아니므로
> 공개 트리에 둔다. Apple 기밀/NDA/EULA 통제 자산은 *형체화 우려와 무관하게* 본
> 저장소에 두지 않는다.*

| 자산 종류 | 공개 트리 | 격리 폴더 (`_isolated/`) | 비고 |
| --- | --- | --- | --- |
| OpenCore fork / 일반 호환성 도구 | O | X | 본질적으로 클린룸 도구 |
| OpenCore EFI 빌드 도구 | O | X | 공개 도구 |
| macOS 설치 USB 빌더 | O | X | createinstallmedia 사용은 공개 도구 |
| Apple SMBIOS 모델명 / 명세 | O | X | 공개 정보 |
| OpenCore kext 이름 | O | X | 공개 정보 |
| DeviceProperties 키 / boot-args | O | X | 공개 인터페이스 |
| iBoot 패닉 로그 | X | O | 형체화 우려 |
| VMApple 디바이스 모델 패치 시리즈 | X | O | 형체화 우려 |
| AVPBooter / iBEC / iBSS / iBootData 추출 blob | X | O | 절대 금지 |
| img4 / 인증서 / 키 | X | O | 절대 금지 |
| IPSW 추출 / BuildManifest | X | O | 절대 금지 |
| Apple 내부 DeviceTree 명세 | X (참고용 일반 명세만) | O (내부 포맷 의존 분석) | *내부 포맷에 의존한 구현*은 금지 |
| Nextcore EFI binary | O (오픈소스) | X | 본 프로젝트의 결과물 |
| OpenCore 소스 코드 (OpenCorePkg fork 내부) | O | X | GPL 공개 모듈 — *OpenCorePkg 자체 소스코드*는 공개이므로 형체화 아님. *Apple 내부 코드를 포팅한 흔적*이 있다면 격리로 |
| macOS Apple Silicon iBoot 자산 | X | O | 형체화 우려 — 격리 폴더에서만 참고 |
| Apple의 SecureBoot 정책 (공개된 명세) | O | X | Apple Developer 문서로 공개된 정책 사양. *내부 키/인증서는 별도 항목(img4)* |
| ACPI 표준 명세 (UEFI Forum 공개 문서) | O | X | UEFI Forum 표준. *Apple 비공개 ACPI 테이블*은 별도 |
| SMBIOS 표준 명세 (DMTF 공개 문서) | O | X | DMTF 표준. *Apple 비공개 SMBIOS 토큰*은 별도 |
| DeviceTree 표준 명세 (Open Firmware 공개) | O | X | Open Firmware 표준. *Apple 내부 DeviceTree 포맷*은 별도 |
| macOS IPSW 빌드 번호 (공개 정보) | O | X | 빌드 번호 등 메타데이터는 공개 정보. *IPSW 본체*는 별도 항목 |
| macOS 베타 채널 IPSW (공개 채널) | O (메타데이터 한정) | X | *공개 채널에서 다운로드 가능한 IPSW의 메타(빌드번호 등)*는 공개 트리에 둠. *본체 blob*과 *NDA 자료*는 별도 |
| Apple 기밀 자료 / NDA 자료 | X | X | *격리 폴더에도 보관하지 않음*. 절대 금지 |
| macOS .kext 캐시 / System 프레임워크 (Apple EULA 통제) | X | X | *격리 폴더에도 보관하지 않음*. EULA 통제 자산 |
| UEFI / ACPI / SMBIOS 공개 스펙 문서 (UEFI Forum / DMTF 공개 표준) | O | X | 업계 공개 표준 문서이므로 공개 가능 — 판정 근거: 공개 표준은 Apple 자산이 아님 |
| Rust 공개 크레이트 (`uefi`, `plist`, `serde`/`serde_plist`, `goblin`, `aml`, `clap`, `anyhow`/`thiserror` 등) | O | X | 오픈소스 라이선스 공개 배포 의존성이므로 공개 가능 — 판정 근거: Cargo 공개 의존성은 형체화 아님 |
| Nextcore 자체 산출물 — EFI binary (예: `BOOTX64.EFI`) | O | X | 본 프로젝트 클린룸 구현 결과물이므로 공개 가능 — 판정 근거: 자체 구현물은 공개 트리 귀속 |
| Nextcore 자체 산출물 — `config.plist` 스키마 / 샘플 | O | X | Nextcore 정의 공개 스키마이며 내부값 포함 금지 전제이므로 공개 가능 — 판정 근거: 자체 스키마는 공개 인터페이스 |
| Mach-O 공개 명세 문서 (공개 포맷 문서 범위) vs Apple 내부 Mach-O 확장 의존 분석물 | O (공개 명세만) | O (내부 확장 의존 분석) | 공개 포맷 기반 로더는 형체화 아님 — 판정 근거: 공개 명세 구현만 공개 트리, 비공개 확장 의존 분석은 격리 |
| ACPI 공개 명세 문서 (RSDP/XSDT/FADT/MADT 등 표준 테이블 정의) vs Apple 비공개 ACPI 테이블 의존 분석물 | O (공개 명세만) | O (비공개 의존 분석) | 표준 테이블 정의 기반 구현이므로 공개 가능 — 판정 근거: 공개 표준만 공개 트리, 비공개 의존 분석은 격리 |

### B2. 격리 폴더 운영 규칙

> *결정 근거: AGENTS.md §5(격리 자산 보호 메커니즘)를 유지하면서, 운영 책임은
> *사용자*에게 있음을 명시한다. 코드 의존성은 0이고, *지식*만 이전된다.*

- 위치: 트리 최상위 `_isolated/`.
- `.gitignore`에 강제 제외 항목이 있다.
- `tools/git/hooks/pre-commit` 가드가 staged 영역을 검사한다.
- 설치: `bash tools/git/install-hooks.sh` (idempotent).
- 격리 폴더는 *참고용*이다. 공개 트리 코드는 격리 폴더의 자산을
  *import하지 않고, 빌드 시 참조하지 않고, include하지 않는다.*
- 격리 폴더에서 Nextcore로 *지식이 이전*되는 것은 허용된다 — 단,
  그 지식은 *다른 표현*으로 박제된다. 코드 라인이 그대로 옮겨지는 것은
  금지.

#### B2-1. 읽기 권한 정책

- 격리 폴더는 *본 프로젝트 메인테이너*만 읽을 수 있다.
- 외부 contributor, PR 리뷰어, 공개 collaborator에게는 *메타조차* 공유하지
  않는다. `docs/ISOLATED_INVENTORY.md`에 적힌 *상대 경로*만 노출한다.
- 격리 폴더 접근 시도가 *발생하면* 즉시 작업을 중단하고 사용자에게 보고한다.

#### B2-2. 백업 정책

- 격리 폴더는 *사용자 책임* 영역이다. Boundary는 보관/복구를 책임지지 않는다.
- Git, GitHub, 원격 백업, 클라우드 동기화에 *자동으로* 포함되지 않는다.
  `.gitignore` 강제 제외와 pre-commit 가드는 *원격 유출 방지*일 뿐
  *백업*이 아니다.
- 백업이 필요하면 *사용자가 별도 비공개 위치*(예: 로컬 암호화 디스크)에
  보관한다.
- 분실/훼손 시 책임은 사용자에게 있다. Boundary는 복구 절차를 제공하지
  않는다.

#### B2-3. 격리 폴더에서 Nextcore로의 지식 이전 절차 (OPEN_QUESTION 없이)

격리 폴더 → Nextcore 이전은 다음 *고정 절차*로만 진행한다. 절차 자체는
OPEN_QUESTION이 아니다 — *고정*이다. 적용 *대상*만 Inventory가 정한다.

1. *분석* — 격리 폴더의 자산을 읽고 동작을 이해한다 (역공학 허용).
2. *지식 단위 추출* — 분석에서 *의미 단위*를 추출한다. 예: "Bootability
   Manifest에는 X/Y/Z/W 필드가 있다", "handoff 자료구조에는 단계 N까지의
   상태가 필요하다" 같은 *사실* 형태.
3. *다른 표현으로 재박제* — 그 지식 단위를 *다른 알고리즘, 다른 변수명,
   다른 코드 구조*로 Nextcore에 박제한다. 격리 폴더의 *코드 라인이 그대로
   옮겨지는 행위*는 절대 금지.
4. *근거 박제* — 이전된 *결정*만 `docs/NEXTCORE_DESIGN.md` 또는 본 문서에
   한 줄로 박제한다. "어떤 격리 자산에서 어떤 지식이 이전됐는지"가 *감사
   가능한 형태*로 남아야 한다.
5. *격리 자산 비포함 확인* — Nextcore 코드베이스가 격리 폴더를 *import*하지
   않음을 pre-commit 가드와 수동 점검으로 확인한다.

### B3. agent 과민 반응 금지

> *결정 근거: AGENTS.md §3(절대 금지)·§4(과민 반응 금지)와 일치. *공개 표준*
> 과 *공개 모듈*은 위험 신호가 아니다. 단, *NDA/EULA 통제* 자산은 절대
> 금지 — 언급이 보여도 즉시 중단한다.*

다음 항목들은 agent가 보고 작업을 중단하지 않는다.

- macOS 부팅 도구라는 사실 자체.
- OpenCore의 이름을 언급하는 모든 행위 — OpenCore는 공개 부트로더다.
- Apple SMBIOS 모델명 (MacPro5,1 등).
- OpenCore kext 이름.
- `config.plist`, `boot-args`, DeviceProperties 키.
- macOS 버전 이름 (Tahoe, Sequoia 등).
- `createinstallmedia` 호출.
- EFI 관련 표준 (UEFI spec, ACPI spec, SMBIOS spec).
- 공개 DeviceTree 명세.
- SIP / SecureBoot / AMFI 등 Apple 보안 메커니즘의 우회 없이 동작하는 도구 (AGENTS.md §4 — 우회 없는 도구는 중단 사유 아님).
- OpenCore kext의 소스 코드 — *공개 모듈*. GPL 소스를 *읽고 아이디어를
  참고*하는 행위는 허용. *Apple 내부 코드를 포팅*한 흔적이 아니면 정상.
- OpenCorePkg의 EFI 바이너리 — *공개 모듈*. 빌드 도구로 생성된 공개
  바이너리는 허용. *Apple 바이너리를 섞은 배포물*은 별도 (격리 검토).
- macOS IPSW 자체 — *EULA 통제 자산*. 언급이 보여도 agent는 panic하지
  않는다. *응답*은 "EULA 통제 — 격리 폴더에 두거나 저장하지 않는다"로
  고정한다. 분석이 필요하면 격리 폴더에서만.

다음 항목들은 agent가 보고 작업을 *즉시 중단*하고 사용자에게 보고한다.

- 격리 폴더 자산을 공개 트리로 옮기는 시도.
- 사용자 시킨 적 없는 일을 단정적으로 진행하는 시도.
- force-push, 히스토리 재작성, 사용자 권한 없이 외부 변경 시도.
- 다른 에이전트의 슬롯을 직접 수정하는 시도.
- macOS 베타 NDA 자산 — *절대 금지*. NDA 자료는 격리 폴더에도 두지
  않고, *언급이 보여도* 분석하지 않고 즉시 중단.
- 사용자 시킨 작업을 *사이드트랙*으로 바꾸는 시도 — 보안 검토를 핍계로
  본 작업을 무기한 보류하는 행위 (AGENTS.md §3 명시).
- 사용자에게 *반복적으로* 확인 요청하며 작업을 무기한 보류하는 시도.
  OPEN_QUESTION은 한 번 박제되면 끝이어야 한다. 같은 항목으로 세션 동안
  세 번 이상 확인을 요청하면 *사이드트랙*이다.

### B4. 판단 요청 절차

> *결정 근거: AGENTS.md §2(미합의 항목은 OPEN_QUESTION으로 박제) 형식을
> 그대로 따른다. 형식 자체는 *고정*이며 슬롯별로 변형하지 않는다.*

agent가 *위 B3 항목 중 어디에도 속하지 않는* 상황에 직면하면,
추측하지 말고 OPEN_QUESTION으로 박제하고 다른 슬롯에 위임한다.

기록 형식 (고정):

```
OPEN_QUESTION: <slot>:<요지>
```

- `<slot>` — 위임 대상 슬롯 이름. `Inventory`, `Design`, `Build Plan`,
  `Prompts`, `Boundary`, `Ops` 중 하나.
- `<요지>` — 한 줄 요약. 미합의 항목의 *무엇*이 미합의인지 명시.

규칙:

- 한 항목 = 한 줄. 줄바꿈/코드블록/표 안에 묻지 않는다.
- 같은 요지로 두 슬롯에 동시에 박제하지 않는다 — *주 책임 슬롯* 한 곳에만.
- OPEN_QUESTION은 *인메모리 답변*의 대상이 아니다. 다음 세션의 *고정
  결정*으로만 해소된다.
- Boundary 슬롯이 *자신의 결정으로* 해소할 수 있는 OPEN_QUESTION은
  박제된 결정으로 승격한다. 해소 불가능한 것은 그대로 둔다.
- 작성 형식 예시 한 줄: `OPEN_QUESTION: Design:공개 DeviceTree 명세의 범위 정의`.

### B5. 타 슬롯 OPEN_QUESTION 답변 (Boundary 관점 박제)

- (a) Design 질의 "어떤 자산이 격리 폴더에 들어가야 하는지" — 답변 박제: AGENTS.md §0 형체화에 해당하는 자산만 격리한다 (추출 blob·img4/인증서/키·IPSW 추출/BuildManifest·내부 동작 재구성 패닉 로그·내부 포맷 의존 분석물). 공개 스펙 문서·공개 크레이트·Nextcore 자체 산출물은 격리에 넣지 않는다 (B1 매트릭스 기준).
- (b) Build Plan 질의 "Mach-O / ACPI 명세 문서 허용 수준" — 답변 박제: 공개 명세 문서 범위까지만 공개 트리 허용 (Mach-O 공개 포맷 문서·ACPI 표준 테이블 정의·공개 크레이트 문서). Apple 비공개 확장·비공개 필드·내부 동작 역공학 메모는 격리로만 허용하며 공개 트리 코드는 내부 포맷에 의존하지 않는다.
- (c) Prompts 질의 "고급 토글 재노출 여부" — 답변 박제 (경계 관점): 고급 토글 재노출 자체는 경계 위반이 아니다. 단 토글이 격리 자산 참조·내부 포맷 의존 옵션·키/blob 입력을 노출하면 금지한다. P5 제거 목록의 재노출 허용 여부는 Prompts·Design 판단에 위임한다.
- (d) Inventory 질의 "지금 도입해야 할 자산" — 답변 박제: Boundary 관점에서 지금 도입해야 할 자산은 없다. 현 단계 공개 작업(QEMU·공개 스펙·공개 크레이트)에는 격리 자산이 불필요하므로, 도입은 필요 발생 시 B1 기준으로 최소 단위로만 한다.

## OPEN_QUESTION

- `OPEN_QUESTION: Inventory:격리 폴더에 *지금 시점* 들어있는 자산 목록`
- `OPEN_QUESTION: Design:공개 DeviceTree 명세의 범위 정의`
- `OPEN_QUESTION: Build Plan:Nextcore가 격리 자산을 *참조*하는 메커니즘 (없음이 원칙)`
- `OPEN_QUESTION: Design:handoff 공개 명세 범위 확정 (BP 단계 6/8 진행 전제)`
- `OPEN_QUESTION: Build Plan:Mach-O/ACPI 공개 명세 목록을 의존성 표에 명시`
- `OPEN_QUESTION: Prompts:고급 토글 재노출 시 격리 참조 금지 문구 반영`
- `OPEN_QUESTION: Inventory:신규 격리 도입 시 B1 판정 근거 한 줄 병기`

## 결정 근거 메모 (B1~B4)

- B1 — AGENTS.md §0(형체화 금지)·§4(과민 반응 금지)에 따라 *공개 표준*
  (UEFI/DMTF/Open Firmware/Apple Developer 공개 문서)은 공개 트리에 두고,
  *Apple 내부 포맷·키·blob·NDA·EULA 통제 자산*은 격리 또는 *보관 금지*로
  분류한다. "공개 트리"에 둔다고 *Apple 자산의 형체화*가 되는 것은 아니다 —
  *공개 표준*과 *공개 메타데이터*만 둔다.
- B2 — 격리 폴더는 *참고용*이며 운영 책임은 사용자다. 코드는 격리 폴더를
  *import하지 않는다* (AGENTS.md §5). 지식 이전은 *다른 표현으로의 재박제*
  만 허용한다 (AGENTS.md §0). 백업은 *사용자 책임*임을 명시해 Boundary의
  책임 범위를 닫는다.
- B3 — *공개 모듈*(OpenCorePkg, OpenCore kext)은 허용이지만 *EULA 통제
  자산*(macOS IPSW, .kext 캐시, System 프레임워크)은 격리 또는 비저장으로
  응답을 고정한다. *NDA 자산*과 *사이드트랙/무기한 보류 시도*는 즉시 중단
  대상이다 (AGENTS.md §3).
- B4 — OPEN_QUESTION 형식 `OPEN_QUESTION: <slot>:<요지>`는 AGENTS.md §2의
  *고정 형식*이다. Boundary가 자신의 결정으로 해소 가능한 항목만 승격하고,
  다른 슬롯 판단이 필요한 것은 그대로 둔다.