# Nextcore 프롬프트 (User Flow Slot)

## 책임

사용자가 wizard에서 보게 될 흐름, 옵션, 메시지 카피를 박제한다. *기능*은
Design 슬롯, *구현*은 Build Plan 슬롯의 영역이다.

## 현재 상태

- P1~P9 박제 완료 — (F) 정정: 종전 "없음 — 아직 시작되지 않았다"는 본문
  (P1~P7)과 어긋난 기재였고, P8·P9는 F 통합 검증으로 신설된 박제다.
- 본 문서 OPEN_QUESTION 2/2 종결(RESOLVED 2; P9에 검토 HOLD 1건 부속).

## 원하는 상태

- 3-step 단순화 흐름이 박제된다 (사용자 시킨 요구: 심플하게).
- 일반 사용자에게 이해 안 되는 요소가 *명시적으로 제거*된다.
- macOS 설치 USB 생성 기능이 흐름에 포함된다.

## 결정 항목

### P1. 3-step 흐름

각 step의 *이름* / *역할* / *진입 조건* / *종료 조건*:

**Step 1 — macOS 선택**

- 이름: "macOS 선택" (영어: "Choose macOS")
- 역할: 사용자가 설치할 macOS 버전(Ventura / Sonoma / Sequoia / Tahoe) 하나를 고른다.
- 진입 조건: wizard가 처음 열렸을 때, 또는 Step 1로 돌아왔을 때.
- 종료 조건: 사용자가 4개 옵션 중 하나를 확정하고 "다음"을 눌렀을 때 → Step 2 진입.

**Step 2 — EFI 생성**

- 이름: "EFI 생성" (영어: "Generate EFI")
- 역할: 선택된 macOS 버전을 토대로 `EFI/BOOT/BOOTX64.EFI`와 `EFI/OC/config.plist`를 작성한다.
- 진입 조건: Step 1에서 macOS 버전이 확정된 상태.
- 종료 조건: EFI/ 디렉터리와 그 하위 산출물(BOOTX64.EFI, config.plist)이 디스크에 생성 완료 → Step 3 진입.

**Step 3 — 설치 USB 생성**

- 이름: "설치 USB 생성" (영어: "Create Installer USB")
- 역할: `createinstallmedia`를 호출해 부팅 가능한 macOS 설치 USB를 만들고, Step 2의 EFI를 USB의 EFI 파티션에 복사한다.
- 진입 조건: Step 2의 EFI 산출물이 디스크에 존재.
- 종료 조건: 사용자가 USB 드라이브를 선택하고 "시작"을 눌러 작업이 끝났거나, wizard를 종료.

> 모든 step에서 "고급" 토글은 *기본으로 숨김*. 노출 여부는 Boundary 슬롯 결정에 따르며, (F) 종결: v1에서는 재노출하지 않는다 — 판단 근거와 조건부 문구는 P9 참조.

> 근거: 사용자 요구(심플하게)와 3-step 골격을 1:1로 일치시키기 위함. 진입/종료 조건을 박제해 Build Plan 단계 게이트(BP3)와 1:1로 대응시킨다.

### P2. Step 1 카피 (한국어 / 영어)

한국어 우선:

> "설치하려는 macOS 버전을 선택하세요."

영어:

> "Select the macOS version you want to install."

옵션 (각 항목 *설명 한 줄* 추가):

- **macOS Ventura (13)** — macOS 13세대. 호환성 검증 범위가 가장 넓고, 구형 하드웨어에 권장된다.
- **macOS Sonoma (14)** — macOS 14세대. 일반 데스크톱 부팅에서 가장 흔히 쓰이는 검증 빌드다.
- **macOS Sequoia (15)** — macOS 15세대. Apple Intelligence 기능군을 포함하며, 최신 kext/드라이버를 반영한다.
- **macOS Tahoe (26)** — macOS 26세대. Apple Silicon / Intel 모두 지원하며, Nextcore가 *최신* 빌드로 검증한 타깃이다.

> 근거: 4개 버전이 현재 Nextcore가 검증 대상으로 박제하는 범위(Build Plan BP3 단계 9와 일치)와 같다. 카피는 짧게, 설명 한 줄로 *검증 상태*만 알린다 — 사용자가 추가로 알아야 할 결정(예: SMBIOS, ACPI)은 wizard에 노출하지 않는다.

### P3. Step 2 카피

한국어 우선:

> "Nextcore 부트로더를 생성합니다. 1~3분 정도 걸릴 수 있습니다."

영어:

> "Generating Nextcore bootloader. This may take 1–3 minutes."

진행률 단계별 *사용자용 메시지*:

- **단계 0 — 작업 디렉터리 준비**
  - KO: "작업 폴더를 준비하는 중…"
  - EN: "Preparing working directory…"
- **단계 1 — config.plist 작성**
  - KO: "선택한 macOS에 맞게 config.plist를 작성하는 중…"
  - EN: "Writing config.plist for the selected macOS…"
- **단계 2 — Nextcore EFI binary 빌드**
  - KO: "Nextcore EFI 바이너리를 빌드하는 중…"
  - EN: "Building the Nextcore EFI binary…"
- **단계 3 — EFI 디렉터리 구조 검증**
  - KO: "EFI 디렉터리 구조를 확인하는 중…"
  - EN: "Verifying the EFI directory structure…"

각 단계가 끝나면 wizard는 즉시 다음 단계 메시지로 전환하고, 마지막 단계가 끝나면 Step 3로 진입한다.

> 근거: Build Plan BP3의 단계 0~3과 1:1 매핑. 사용자 입장에서는 *무엇이 일어나는지* 한 줄로 보이게 하고, *어떻게*는 wizard에 노출하지 않는다.

### P4. Step 3 카피

한국어 우선:

> "macOS 설치 USB를 만들 수 있습니다. USB를 선택하고 시작하세요."

영어:

> "Create a macOS installer USB. Select your USB drive and start."

USB 드라이브를 선택하는 순간 표시되는 *경고 문구*:

- KO: "⚠️ 선택한 USB 드라이브의 모든 데이터가 삭제됩니다. 중요한 파일은 미리 백업하세요."
- EN: "⚠️ All data on the selected USB drive will be erased. Back up important files before continuing."

"시작" 버튼을 누른 뒤 표시되는 안내:

- KO: "Apple의 정식 도구(createinstallmedia)를 호출합니다. macOS 설치 이미지를 다운로드하므로 인터넷 연결이 필요하며, USB 용량에 따라 수십 분이 걸릴 수 있습니다."
- EN: "Calling Apple's official tool (createinstallmedia). A macOS installer image will be downloaded — an internet connection is required, and the process may take tens of minutes depending on USB capacity."

> 근거: 사용자가 *데이터 손실*을 인지한 상태로만 "시작"이 가능하도록 한다. createinstallmedia 호출 자체는 Boundary B1에서 공개 도구로 분류되어 있으므로 wizard에 이름을 노출해도 무방하다.
>
> **(F) 호스트 OS 분기 문구 (Build Plan BP3.9/BP6(b) 정합 — 분기 카피 누락 보강):**
> - macOS 호스트: 위 "시작" 뒤 안내를 그대로 사용한다(공개 도구 직접 호출). 카피 변경 없음.
> - Windows(비-macOS) 호스트: "시작" 버튼을 누른 뒤 안내를 아래로 대체한다.
>   - KO: "이 OS에서는 createinstallmedia를 직접 실행할 수 없어 Nextcore는 EFI 산출물만 USB에 복사합니다. 복사가 끝나면 macOS로 부팅해서 화면 안내에 따라 설치 USB 만들기를 마무리하세요."
>   - EN: "createinstallmedia can't run directly on this OS, so Nextcore copies the EFI payload to the USB. When the copy finishes, boot macOS and follow the on-screen instructions to complete the installer USB."
>   - 완료 표시: KO "EFI 복사 완료 — macOS에서 계속하세요." / EN "EFI copy complete — continue on macOS."
> - 정합 확인 결과: BP3.9의 Windows 분기(EFI 복사 + macOS 측 실행 안내 1줄)와 위 카피가 1:1 대응한다. macOS 분기는 BP3.9의 `make-usb: done` 게이트 문구와 충돌 없이 병존한다.

### P5. 제거된 요소

다음 요소는 wizard 메인 흐름에서 *제거*된다. (F) 종결: 고급 토글의 v1 재노출 없음 — P9 참조.

| 제거 항목 | 왜 제거했는지 |
| --- | --- |
| Mellow 배포 방식 선택 | 일반 사용자가 결정할 필요가 없는 배포 채널 — 자동 결정으로 충분하다. |
| 실행 모드 (x86 / Apple Silicon Sandbox) | EFI 빌드와 직접 관련 없는 실행 옵션이며, 일반 사용자에게 의미 없는 구분이다. |
| Mellow 패키지 폴더 경로 입력 | 사용자가 알 필요가 없는 내부 경로 — 도구가 자동으로 탐색한다. |
| 루트 패치 직접 호출 | 부팅 안정성을 해치는 위험 요소 — 고급 사용자가 격리 환경에서 별도로 진행한다. |
| 모델 체인저 | 일반 사용자가 부팅에 사용하지 않음 — EFI 단계에서 자동으로 처리된다. |
| Sandbox EFI 자가 진단 | 진단은 로그로 충분하며, wizard의 흐름을 방해한다. |
| Apple Silicon Sandbox 데모 | 메인 흐름과 무관한 데모 — 별도 진입점에서 제공한다. |

> 근거: 위 7개는 모두 *내부 운영 / 디버깅* 용도이며, "심플한 wizard" 요구와 충돌한다. 제거 목록은 Build Plan이 *구현하지 않아도 되는* 영역을 짚어 주는 역할도 한다.

### P6. 유지된 요소

다음 요소는 wizard 메인 흐름에 *유지*된다.

| 유지 항목 | 왜 유지했는지 |
| --- | --- |
| macOS 버전 선택 | 이후 단계의 EFI 템플릿을 결정하는 *유일한* 핵심 입력이다. |
| Nextcore EFI 생성 | Nextcore라는 프로젝트의 *핵심 산출물*을 만드는 단계이며, 없으면 부팅 자체가 불가능하다. |
| macOS 설치 USB 생성 | 사용자가 macOS를 *실제로 설치할 매체*를 만드는 단계이며, EFI만으로는 설치가 진행되지 않는다. |

> 근거: 세 항목은 Nextcore의 정의(Design D1 — EFI 기반 macOS 부팅)와 1:1 대응. 사용자가 "심플한 흐름"을 요구했지만, 이 세 단계는 *최소* 단위라 줄일 수 없다.

### P7. 에러 메시지

규칙:

- *실패는 단계별로 표시* — 어느 단계에서 왜 멈췄는지 한 줄로.
- *해결 방법은 wizard가 제시하지 않음* — 로그 파일 경로만 안내.
- 한국어 우선, 그 아래 영어.

**Step 1 (macOS 선택)**

- KO: "macOS 버전을 선택하지 않았습니다. 목록에서 하나를 골라 주세요."
- EN: "No macOS version was selected. Pick one from the list."
- KO: "선택한 macOS 버전의 설치 이미지를 찾을 수 없습니다. 인터넷 연결을 확인하고 다시 시도하세요. 자세한 내용은 로그 파일을 확인하세요: <log path>"
- EN: "The installer image for the selected macOS was not found. Check your internet connection and try again. See the log file for details: <log path>"

**(F) 추가 — Design `동적 macOS 목록의 빈 상태·오류 문구를 확정하라` 답변:**

- KO: "설치 매체에서 읽은 버전 목록이 없습니다. 매체를 연결하거나 인터넷에 연결한 뒤 다시 시도하세요. 로그 파일: <log path>"
- EN: "No macOS version list could be read from the installer media. Attach the media or connect to the internet, then try again. Log file: <log path>"
- 원칙 박제: 버전 선택기는 *빈 목록을 노출하지 않는다* — 목록이 비면 Step 1에 머무르고 위 안내를 표시한다(Design D6의 예외 처리 = Prompts 책임 원칙에 부응).

**Step 2 (EFI 생성)**

- KO: "EFI 디렉터리를 만들 수 없습니다. 쓰기 권한이 있는 폴더를 선택하고 다시 시도하세요. 로그 파일: <log path>"
- EN: "Could not create the EFI directory. Choose a folder you have write access to and try again. Log file: <log path>"
- KO: "Nextcore EFI 바이너리 빌드에 실패했습니다. 자세한 내용은 로그 파일을 확인하세요: <log path>"
- EN: "Nextcore EFI binary build failed. See the log file for details: <log path>"

**Step 3 (설치 USB 생성)**

- KO: "선택한 USB 드라이브가 감지되지 않습니다. USB를 다시 연결하고 목록을 새로 고치세요."
- EN: "The selected USB drive was not detected. Reconnect the USB and refresh the list."
- KO: "createinstallmedia 실행에 실패했습니다. 로그 파일을 확인하세요: <log path>"
- EN: "createinstallmedia failed to run. See the log file for details: <log path>"

> 근거: 해결 방법은 *사용자가 직접 검색*할 수 있도록 로그 파일 경로만 노출한다. 단계별 표시는 Build Plan BP3의 검증 게이트와 짝을 이뤄, 어느 단계에서 막혔는지를 wizard가 그대로 알려준다.

### P8. macOS 버전 선택기 노출 정책 (F 통합 박제)

- wizard v1은 P2 목록의 **4종 고정**(Ventura / Sonoma / Sequoia / Tahoe)만
  노출하고, 동적 확장 목록은 노출하지 않는다.
- Design 원칙은 **동적 목록**(D6)이다 — D6과 P8은 **상하 관계**다:
  원칙(전달 방식) = D6 동적 / v1 노출 집합 = P8 고정 4종. 충돌이 아니다.
  동일 결론이 Design D6 (F)에 병기되어 있으며, 한쪽만 바꾸는 개정은 금지한다(F).
- 고정 4종이 소진·부족해지면 설치 매체·공개 릴리스 식별자가 주는 값을
  선택기에 추가할 수 있다(동적 확장 여지). 확장 구현 시점은
  `HOLD: wizard v1 출시 이후 BP 단계표 밖의 별도 단계로 수립`.
- 빈 목록·오프라인 예외 시 카피는 P7 (F) 추가분에 박제.

> 근거: F 통합 검증이 결정한 절충. Design D6("동적 원칙")과 종전 P2 결정
> ("4종 고정 노출")의 충돌을 원칙/노출 층위 분리로 해소해 양쪽에 같은
> 결론으로 박제했다.

### P9. 고급 토글 정책 (F 박제)

- Boundary의 두 질의(`고급 토글을 wizard에 다시 노출할지`, `고급 토글
  재노출 시 격리 참조 금지 문구 반영`)에 대한 답변 — **v1 방침: 재노출
  없음**. P5의 제거 항목 7개는 v1에서도 제거 상태로 유지한다.
- Boundary B5(c)는 재노출 자체를 경계 위반으로 보지 않으나, v1은 그 권한을
  행사하지 않는다. 근거: 사용자 요구 "심플하게"(P1 근거)가 계속 우선한다.
- 향후 재노출 검토: `HOLD: 사용자 요구가 발생할 때만 재개 — 격리 참조
  금지 항목은 B5(c)로 고정` — 명시적 보류.
- 향후 노출 시 전제 조건(사전 박제): 토글 UI를 구현하게 되면 아래 안내
  한 줄을 그대로 포함해야 하며, 격리 자산 참조·내부 포맷 의존 옵션·
  키/blob 입력은 어느 경우에도 노출하지 않는다.
  - KO: "고급 옵션에는 격리 자산 참조, 내부 포맷 의존 옵션, 키/블롭 입력이 포함될 수 없습니다."
  - EN: "Advanced options must not expose isolated-asset references, internal-format-dependent options, or key/blob inputs."

## OPEN_QUESTION

Prompts 슬롯이 직접 해소한 항목 (다음 슬롯이 합의를 확인하고 OPEN_QUESTION에서 제거):

- ~~`OPEN_QUESTION: Design:macOS 버전을 하드코딩할지 동적으로 가져올지`~~
  → **박제 결정**: wizard 카피에는 4개 버전(Ventura / Sonoma / Sequoia / Tahoe)을 *하드코딩*으로 노출한다. 동적 버전(베타, 구버전) 표시는 *다음 단계*의 Build Plan 결정으로 남긴다 — Build Plan이 *어떻게* 가져올지 정한다.
  → (F) 흡수: 본 결정은 P8로 흡수·일반화됨 — 원칙은 Design D6(동적), v1
    노출은 본 결정(고정 4종)의 상하 관계로 통합 박제. 확장 구현 시점은
    P8의 HOLD를 따르고, Build Plan이 아니라 Design·Prompts 공동 박제로
    정정한다.

- ~~`OPEN_QUESTION: Design:Prompts:사용자에게 macOS 선택지를 *어떤* 수준으로 노출할지`~~
  → **박제 결정**: 메인 카피에는 *4개 버전 이름과 검증 상태 한 줄*만 노출한다. SMBIOS, ACPI, kext 선택지는 wizard에 노출하지 않는다.

- ~~`OPEN_QUESTION: Build Plan:Prompts:사용자 메시지 카피의 한국어/영어 비율`~~
  → **박제 결정**: 한 화면에 *한국어 우선*, 그 아래 *영어*를 항상 함께 박제한다. 한국어가 기본, 영어는 보조 표기 — 두 언어를 같은 줄에 섞지 않는다.

남은 OPEN_QUESTION (다른 슬롯이 답해야 함 — Prompts 슬롯은 건드리지 않는다):

(F) 통합 검증 회수: 아래 2건 전부 종결했다.

- `OPEN_QUESTION: Build Plan:createinstallmedia 호출 경로 (호스트 OS별)`
  → RESOLVED-BY-F: Build Plan BP6(b)/BP3.9가 macOS 직접 호출·Windows
  복사+안내로 박제 완료 — 본 문서 P4 (F) 분기 카피와 3자 정합 닫힘.
- `OPEN_QUESTION: Boundary:고급 토글을 wizard에 다시 노출할지`
  → RESOLVED-BY-F: Boundary B5(c)(경계 관점 답변) + 본 문서 P9 (F)가
  v1 재노출 없음으로 최종 박제 — 향후 재노출 검토만 P9 내 HOLD로 부속.

## 통합 검증 (F)

| 질문 (본 문서) | 결론 | 박제 위치 |
| --- | --- | --- |
| createinstallmedia 호출 경로 (OS별) | RESOLVED — BP6(b)/BP3.9 앵커 + 분기 카피 | P4 (F) |
| 고급 토글 재노출 여부 | RESOLVED — v1 재노출 없음 | P9 (F) (향후 검토 HOLD 부속) |

- 신규 박제: P8(버전 선택기 노출 정책 — Design D6 (F)와 동일 결론 병기),
  P9(고급 토글), P4 (F) 호스트 OS 분기 카피, P7 (F) 빈 목록 오류 카피
  (Design 위임 회수).
- 정정: 현 상태의 "아직 시작되지 않았다" 기재, P1/P5의 "현재
  OPEN_QUESTION" 표기 2곳을 종결 상태로 수정.