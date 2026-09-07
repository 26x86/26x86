# Nextcore 프롬프트 (User Flow Slot)

## 책임

사용자가 wizard에서 보게 될 흐름, 옵션, 메시지 카피를 박제한다. *기능*은
Design 슬롯, *구현*은 Build Plan 슬롯의 영역이다.

## 현재 상태

- 없음 — Nextcore 프롬프트는 아직 시작되지 않았다.

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

> 모든 step에서 "고급" 토글은 *기본으로 숨김*. 노출 여부는 Boundary 슬롯 결정에 따르며, 현재 OPEN_QUESTION으로 남아 있다.

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

### P5. 제거된 요소

다음 요소는 wizard 메인 흐름에서 *제거*된다. 고급 토글 노출 여부는 Boundary 슬롯의 결정에 따른다 (현재 OPEN_QUESTION).

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

## OPEN_QUESTION

Prompts 슬롯이 직접 해소한 항목 (다음 슬롯이 합의를 확인하고 OPEN_QUESTION에서 제거):

- ~~`OPEN_QUESTION: Design:macOS 버전을 하드코딩할지 동적으로 가져올지`~~
  → **박제 결정**: wizard 카피에는 4개 버전(Ventura / Sonoma / Sequoia / Tahoe)을 *하드코딩*으로 노출한다. 동적 버전(베타, 구버전) 표시는 *다음 단계*의 Build Plan 결정으로 남긴다 — Build Plan이 *어떻게* 가져올지 정한다.

- ~~`OPEN_QUESTION: Design:Prompts:사용자에게 macOS 선택지를 *어떤* 수준으로 노출할지`~~
  → **박제 결정**: 메인 카피에는 *4개 버전 이름과 검증 상태 한 줄*만 노출한다. SMBIOS, ACPI, kext 선택지는 wizard에 노출하지 않는다.

- ~~`OPEN_QUESTION: Build Plan:Prompts:사용자 메시지 카피의 한국어/영어 비율`~~
  → **박제 결정**: 한 화면에 *한국어 우선*, 그 아래 *영어*를 항상 함께 박제한다. 한국어가 기본, 영어는 보조 표기 — 두 언어를 같은 줄에 섞지 않는다.

남은 OPEN_QUESTION (다른 슬롯이 답해야 함 — Prompts 슬롯은 건드리지 않는다):

- `OPEN_QUESTION: Build Plan:createinstallmedia 호출 경로 (호스트 OS별)`
- `OPEN_QUESTION: Boundary:고급 토글을 wizard에 다시 노출할지`