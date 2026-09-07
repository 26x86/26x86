# Nextcore 설계 (Design Slot)

## 책임

Nextcore의 *무엇*과 *왜*를 박제한다. *어떻게* 구현할지는 Build Plan 슬롯의
영역이다.

## 현재 상태

- D1(정체성) 합의됨 — Design 슬롯이 외형 정의 + 비목표 + 근거 메모를 추가 심화.
- D2/D3/D4 심화 완료 (에이전트 A) — Design 슬롯이 각 항목에 *근거 메모*를 추가, D3에는 Memory Map / Console / Boot Args / SMBIOS 4행 추가, D4 비승계에 OpenRuntime·OpenCanopy / AptioMemoryFix 2항 추가.
- D5~D8 신규 결정: 다른 슬롯이 Design에 던진 4건에 대한 답변.
- Rust 모듈 트리·wizard 문구·격리 자산 목록 등 구현/운영 상세는 각 슬롯 영역.
- (F) 통합 검증 — 본 문서 OPEN_QUESTION 6건 전부 종결(RESOLVED 5 · HOLD 1).
  D6×Prompts 버전 목록 절충과 D5×BP3×B1 대조 결론을 본문에 병기했다.
  회수 대조표는 "통합 검증 (F)" 참조.

## 원하는 상태

- Nextcore가 *무엇인지* 한 문단으로 설명된다.
- macOS 부팅 흐름이 *어떤 단계*로 구성되는지 박제된다.
- iBoot가 하는 일과 Nextcore가 그 일을 *어떤 다른 방식*으로 하는지가
  병렬로 박제된다.
- OpenCore의 *어떤 아이디어가 승계*되고 *어떤 부분이 의도적으로 버려졌는지*
  명시된다.

## 결정 항목

### D1. Nextcore 정체성

(결정: 합의 — 본 세션 Design 슬롯이 심화.)

> **근거:** AGENTS.md §0 핵심 원칙 — (a) macOS는 EFI 환경에서 부팅,
> (b) iBoot와 *기능적으로 동등*하되 *구현은 독립*, (c) OpenCore 아이디어
> 승계 + 소스 비의존. 이 세 원칙을 만족시키는 *외형 정의*는 Design 슬롯이
> 닫는다 (구현 디테일은 Build Plan).

Nextcore는 UEFI 펌웨어 환경에서 macOS를 부팅하기 위한 *공개* 부트로더다.
핵심 사상은 다음 두 가지다.

1. **iBoot의 *역할*을, iBoot와 다른 방식으로 채운다.** macOS가 EFI 이후
   단계에서 요구하는 *외부 인터페이스*(DeviceTree, memory map, boot args,
   kext 등록, handoff 자료구조)만 동등하게 제공하며, iBoot의 내부 코드·
   키·blob·내부 명칭은 일절 사용하지 않는다. *기능 동등, 구현 독립.*
2. **OpenCore의 *아이디어*를 승계한다.** `config.plist` 기반 설정 주도형
   부트로더 사상, `EFI/OC/` 디렉터리 구조의 *위치* 호환, ACPI·
   DeviceProperties·boot-args 키의 *인터페이스* 호환, 공개 kext 목록
   호환. 소스 코드 의존성은 없다.

구현 언어는 Rust다(이 사실 자체는 Design 합의이며, *모듈 구조*·*의존성*
·*빌드 단계*는 Build Plan이 결정한다). Nextcore는 부팅 신뢰성 검증
(Bootability Manifest, img4)을 *하지 않으며*, 신뢰는 호출자 정책에
위임된다. iBoot/Apple 보안 메커니즘의 우회 도구가 아니다.

비목표:
- iBoot/Apple 내부 구현의 *형체화* (AGENTS.md §0).
- img4 / Apple 보안 토큰 우회, IPSW blob 재사용.
- 펌웨어 패치·NVRAM 변조 등 OpenCore의 *hack* 계층 채택 (D4 참조).

대상 사용자: Hackintosh/OpenCore 사용자가 기존 `config.plist` 자산으로
EFI 환경에서 macOS를 부팅하고자 할 때, *공개 트리만으로* 구성된 경로를
제공하는 것.

### D2. macOS 부팅 흐름 (EFI 환경 기준)

(결정: 합의 — 각 단계의 입력/출력/책임 경계를 한 줄씩 박제한다.)

> **근거:** AGENTS.md §0 (EFI 부팅, iBoot와 기능 동등/구현 독립) +
> UEFI 공개 명세 + macOS 부팅 요구사항 — 5단계 흐름은 *책임 단위*로
> 박제하며, 각 단계의 구현은 Build Plan이 다룬다.

macOS는 다음 단계를 거쳐 EFI 환경에서 부팅된다. 1~4단계의 *역할*은 기존
펌웨어 부트로더가 수행하던 것과 기능적으로 동등하나, Nextcore는 그 역할을
*다른 방식*(공개 규격 + Rust 구현)으로 제공한다. 5단계는 macOS 자체 영역이다.

1. **EFI 진입 + 시스템 테이블 인식** — 입력: UEFI firmware가 로드한 Nextcore EFI binary와 시스템 테이블. 출력: 확보된 Boot Services 핸들(메모리 맵, 콘솔, 파일시스템 프로토콜). 경계: firmware 선택·서명 판단에는 관여하지 않고, 전달받은 테이블을 읽기만 한다.
2. **설정 로드** — 입력: `EFI/OC/config.plist` 호환 형식의 `config.plist` 파일. 출력: 검증된 설정 구조체(SMBIOS, ACPI 목록, kext 목록, DeviceProperties, boot-args). 경계: 설정 *해석*까지가 책임이며, 설정값의 하드웨어 정합성 판단은 later 단계에 위임한다.
3. **하드웨어 추상화** — 입력: D2-2의 설정 구조체와 firmware 제공 ACPI 테이블. 출력: 적용된 ACPI 테이블 집합, DeviceProperties 적용 기록, 등록된 kext 카탈로그. 경계: kext·테이블을 *읽기 전용으로 등록·기록*할 뿐, 커널 내부 동작을 패치하지 않는다.
4. **부트 체인 인계** — 입력: D2-3까지 구성된 메모리 맵·로드된 커널 이미지·커널 인자. 출력: Nextcore 정의 인계 자료구조(D5 범위)와 XNU 진입 가능 상태. 경계: 인계 구조체를 *마련*하는 것까지가 책임이며, 진입 이후 커널 동작은 책임 밖이다.
5. **XNU 로드 + macOS userspace 진입** — 입력: D2-4의 인계 상태. 출력: 실행 중인 macOS (Nextcore 산출물 아님). 경계: 이 단계 시작과 동시에 Nextcore의 책임은 끝나고, 실패 분류도 macOS 영역으로 넘긴다.

### D3. iBoot 대체 방식

(결정: 합의 — 각 행의 "왜 다른 방식인지" 근거를 한 줄씩 박제한다. Apple 내부
명칭·내부 포맷 의존 없음. 아래 좌측 열은 *기능 영역(참고용 일반 명칭)*이며
내부 구현 명칭이 아니다.)

> **근거:** AGENTS.md §0 (형체화 금지, iBoot 내부 동작 모방 금지) +
> §4 (OpenCore 아이디어는 승계 가능) — 모든 대체 행은 *공개 명세에
> 한정*하며, iBoot의 *내부 동작*을 모방하는 표현은 배제한다. 좌측 열은
> 기능 영역의 *일반 명칭*이며 내부 구현 명칭이 아니다.

| 기능 영역 (참고) | Nextcore 구현 방향 | 왜 다른 방식인지 |
| --- | --- | --- |
| 부팅 대상 신뢰 목록 검증 | Nextcore는 목록을 검증하지 *않는다*. 부팅 신뢰성은 호출자·상위 정책이 제공한다. | 신뢰 판단은 부트로더 바깥(호출자·플랫폼 정책)의 책임으로 분리하므로 독자 검증기를 품지 않는다. |
| 하드웨어 기술 트리 구성 | Nextcore는 *공개 DeviceTree 명세*(D7 범위)만 읽어 구성하고, 벤더 내부 바이너리 레이아웃에 의존하지 않는다. | 내부 레이아웃에 묶이면 공개 규격만으로 빌드·검증할 수 없으므로 공개 명세만 사용한다. |
| RAM 디스크 구성 | Nextcore는 벤더 전용 ramdisk 포맷 파서에 의존하지 *않고* 표준 ramdisk 인터페이스를 사용한다. | 특정 벤더 포맷 파서는 공개 트리에서 검증할 수 없으므로 표준 인터페이스로 대체한다. |
| 커널 모음 로드 | Nextcore는 표준 EFI 메모리·파일시스템 프로토콜로 Mach-O를 로드한다. | 공개 Mach-O·UEFI 규격만으로 로드·검증이 가능하므로 벤더 전용 로더를 두지 않는다. |
| kext 등록 | Nextcore는 공개 호환 kext 목록 형식을 사용한다. | kext 목록 형식은 설정 주도 사상의 공개 인터페이스이므로 호환하되 독자 구현한다. |
| 서명 검증 (펌웨어·커널 서명 일반) | Nextcore는 서명 검증 책임을 지지 *않는다*. 신뢰는 상위 정책(예: 플랫폼의 공개 UEFI 서명 정책)에 따른다. | 키·인증서 취급은 공개 트리의 책임 밖이므로 검증 책임을 상위 정책에 위임한다. |
| Memory Map 구성 | UEFI Boot Services가 제공한 memory map을 *변조 없이* XNU에 전달한다. *(공개 명세 기반)* | memory map은 UEFI 공개 규격으로 충분하므로 벤더별 재구성 계층을 두지 않는다. |
| Console / Framebuffer | 표준 EFI GOP/ConOut 프로토콜을 그대로 사용한다. *(공개 명세 기반)* | 그래픽 출력은 UEFI 공개 프로토콜만으로 충당 가능하므로 전용 출력 계층을 두지 않는다. |
| Boot Args 전달 | 표준 EFI 변수 / RuntimeServices로 boot-args 키를 노출한다. *(공개 명세 기반)* | boot-args는 공개 인터페이스이므로 표준 EFI 경로로만 노출한다. |
| SMBIOS 노출 | SMBIOS 테이블을 Nextcore가 *생성하지 않고* firmware 테이블을 그대로 사용한다. *(공개 SMBIOS 명세 기반)* | SMBIOS는 공개 명세로 표현 가능하므로 firmware 테이블을 그대로 신뢰한다. |

> 핵심: Nextcore는 기존 부트로더의 *내부 동작*을 모방하지 않는다. macOS가 EFI 환경에서
> 부팅되기 위해 필요한 *외부 인터페이스*만 *공개 명세 기반으로* 제공한다.

### D4. OpenCore 아이디어 승계

(결정: 합의 — 항목마다 판정 근거 한 줄.)

> **근거:** AGENTS.md §0 (OpenCore 아이디어 승계 + 소스 비의존) +
> §3 (iBoot 비밀키/blob 사용 금지) — 비승계 항목은 의도적 경계 선언이며,
> 펌웨어 패치/hack 계층은 *공개 명세 기반* 원칙과 *구현 독립* 원칙
> 모두에 반하므로 일괄 비승계한다.

승계:

- `config.plist` 기반 설정 (plist 호환 파서). — 근거: 설정 주도형 부트로더라는 공개 아이디어의 핵심이므로 승계한다.
- `EFI/OC/` 디렉터리 구조 (Nextcore도 같은 위치에 자기 파일 둠). — 근거: 기존 공개 도구·문서와 호환되는 배치 관례이므로 위치만 공유한다(코드·상표 의존 없음).
- ACPI·DeviceProperties·boot-args 키 호환. — 근거: 공개 인터페이스이므로 키 이름 호환은 형체화가 아니라는 경계 원칙에 따른다.
- kext 등록 방식 호환. — 근거: 공개 kext 목록 형식은 구현이 아닌 인터페이스이므로 호환한다.

의도적 비승계:

- OpenCore C 소스 코드 의존 — 없음. — 근거: 클린룸 Rust 구현 원칙이므로 코드를 가져오지 않는다.
- OpenCore 빌드 시스템 의존 — 없음. — 근거: Cargo 기반 독립 빌드가 목표이므로 빌드 체계를 공유하지 않는다.
- OpenCore 기호 / 상표 — 사용 안 함. — 근거: 식별자·상표는 승계 대상이 아니라는 원칙이므로 사용하지 않는다.
- 비밀키 / 인증서 / blob — 일절 사용 안 함. — 근거: 신뢰 자산 취급은 공개 트리의 책임 밖이므로 다루지 않는다.
- OpenCore의 `OpenRuntime` / `OpenCanopy` 류 펌웨어 패치 추상화 — 채택하지 않음. UEFI RuntimeServices를 직접 호출한다. — 근거: 공개 UEFI RuntimeServices만으로 충당 가능하므로 전용 추상화 계층을 두지 않는다.
- AptioMemoryFix 류 memory map hack — 채택하지 않음. firmware가 제공한 memory map을 그대로 신뢰한다. — 근거: memory map 변조는 *공개 명세 기반* 원칙과 어긋나므로 firmware 출력 그대로를 채택한다.

### D5. handoff 자료구조의 공개 명세 범위 (Build Plan 질문에 대한 답)

(결정: 합의 — `OPEN_QUESTION: Design:handoff 자료 구조의 공개 명세 범위`에 답함.)

- 공개 명세 범위는 다음 4종으로 한정한다: (1) UEFI 메모리 맵, (2) 로드된 커널 이미지의 주소·크기, (3) 커널 인자 문자열, (4) 적용된 ACPI·DeviceProperties 요약 기록.
- 위 4종은 Nextcore가 *자체 정의한* Rust 구조체로 표현하며, 공개 UEFI·ACPI·Mach-O 규격에서 읽은 값만 담는다. 벤더 내부 구조체 레이아웃·상수·오프셋 복제는 금지한다.
- 정확한 필드 목록·직렬화 형식은 Build Plan 슬롯의 책임이다(D5는 범위만 정의한다).

> **(F) 대조 결론 (D5 × Build Plan BP3 단계 6/7·8 × Boundary B1):** 모순 없음.
> BP3 단계 6(`BootArgs` 공개 컨벤션, `DeviceTreeBuf` 공개 명세, memory map
> 정규화, roundtrip+size-cap), 단계 7(공개 Mach-O 헤더 열람), 단계 8(mock
> handoff blob)은 모두 본 절 4종 — (1) UEFI 메모리 맵, (2) 커널 이미지의
> 주소·크기, (3) 커널 인자 문자열, (4) 적용된 ACPI·DeviceProperties 요약
> 기록 — 에서 읽은 값만 사용하며, B1 매트릭스의 공개/격리 분리(공개 명세만
> 공개 트리, 내부 포맷 의존 분석은 격리)와도 부합한다. 잔여 질문 확정:
> D5 4종 밖의 필드가 필요해지면 **먼저 D5를 개정하고** 그다음 Build Plan을
> 개정한다 — 단계 설명 단독으로 필드를 추가하지 않는다.

### D6. macOS 버전 목록 정책: 동적 우선 (Prompts 질문에 대한 답)

(결정: 합의 — `OPEN_QUESTION: Design:macOS 버전을 하드코딩할지 동적으로 가져올지`에 답함.)

- 원칙은 *동적 목록*이다. Design 문서는 특정 상용 릴리스 번호·이름의 열거를 박제하지 않으며, wizard는 호스트의 설치 매체·공개 릴리스 식별자가 제공하는 값을 그대로 전달한다.
- 근거: 버전 열거를 Design에 하드코딩하면 릴리스마다 문서·구현이 어긋나므로, Design은 "매체가 준 식별자를 그대로 전달한다"는 원칙만 정의한다.
- 빈 목록·오프라인 등 예외 시 UX 문구는 Prompts 슬롯의 책임이다.

### D7. 공개 DeviceTree 명세의 범위 (Boundary 질문에 대한 답)

(결정: 합의 — `OPEN_QUESTION: Design:공개 DeviceTree 명세의 범위 정의`에 답함.)

- 공개 DeviceTree 명세란 UEFI·ACPI 공개 규격, IEEE 1275 device-tree 개념, 공개 OS의 하드웨어 기술 관행으로 표현 가능한 키-값 하드웨어 기술 집합에 한정한다.
- 벤더 내부 DeviceTree 필드·바이너리 레이아웃의 복제·의존은 금지한다. 내부 형식 분석이 필요하면 격리 폴더에서만 다룬다.
- 허용 출처의 확정 목록(어떤 공개 규격을 인용하는지)은 Boundary 슬롯의 책임이다.

### D8. 격리 자산→Nextcore 지식 단위의 정의 (Inventory 질문에 대한 답)

(결정: 합의 — `OPEN_QUESTION: Design:격리 자산에서 Nextcore로 이전 가능한 지식 단위의 정의`에 답함.)

- 이전 가능한 지식 단위는 자연어 한 문장으로 표현되는 *필요한 외부 인터페이스* 서술(예: "커널 인계 시 메모리 맵이 필요하다")에 한정한다.
- 코드 줄, 구조체 레이아웃, 상수값·오프셋, 바이너리 추출물의 이전은 금지한다. 이전 시에는 다른 표현으로 재서술하며(Boundary B2 규칙), 출처·원문은 인용하지 않는다.
- 재서술 결과의 메타 기록 형식(한 줄 형식 등)은 Inventory 슬롯의 책임이다.

## OPEN_QUESTION

(Design 슬롯이 다른 슬롯에 위임하는 항목 — 본 문서 직접 수정 대상 아님.)

- `OPEN_QUESTION: Build Plan:Rust 모듈 트리 — Nextcore의 코어 디렉터리 구조`
- `OPEN_QUESTION: Build Plan:handoff.rs 필드 목록을 D5 공개 범위에 맞춰 확정하라`
- `OPEN_QUESTION: Prompts:동적 macOS 목록의 빈 상태·오류 문구를 확정하라`
- `OPEN_QUESTION: Boundary:공개 DeviceTree 허용 출처 목록을 확정하라`
- `OPEN_QUESTION: Boundary:어떤 자산이 격리 폴더에 들어가야 하는지 (Inventory 슬롯 결정)`
- `OPEN_QUESTION: Inventory:지식 단위 재서술 결과의 메타 한 줄 형식을 확정하라`
