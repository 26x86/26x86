# NextCore 설계 (Design Slot)

## 책임

NextCore의 *무엇*과 *왜*를 박제한다. *어떻게* 구현할지는 Build Plan 슬롯의
영역이다.

## 현재 상태

- 2026-09-08 현 세션 최종 사용자 결정: 물리 호스트는 항상 x86이다. macOS 27
  ARM64e 빌드를 x86 EFI 단계의 macOS 전용 JIT/HAL 호환성 레이어에서 실행한다.
  WSL2는 개발 도구이며 host OS 기반 QEMU나 ARM Mac은 제품 실행의 전제가 아니다.
  이후의 ARM host 지원·범용 VM 관련 과거 설명은 본 목표를 대체하지 않는다.
  EFI 이후 지속 실행에 필요한 메모리·예외·장치 소유권은 이 호환성 레이어가
  구현해야 한다. 본 결정은 구현 완료나 macOS/Metal 실행 성공 판정이 아니다.

- 2026-09-08 사용자 확정: 제품 표시 브랜드는 **NextCore**다. macOS 27
  GoldenGate, AMD64↔Apple Silicon HAL 및 실제 Metal 실행은 필수 목표이며,
  현재 지원 완료라는 표시와 구분한다. D13/D14에서 제품 화면과 EFI 피커의
  이번 구현 범위를 확정한다. 외부 OpenCore의 출처·파일 호환 규약·과거 실험
  이름은 제품 브랜드 변경으로 개명하지 않는다.

- D1(정체성) 합의됨 — Design 슬롯이 외형 정의 + 비목표 + 근거 메모를 추가 심화.
- D2/D3/D4 심화 완료 (에이전트 A) — Design 슬롯이 각 항목에 *근거 메모*를 추가, D3에는 Memory Map / Console / Boot Args / SMBIOS 4행 추가, D4 비승계에 OpenRuntime·OpenCanopy / AptioMemoryFix 2항 추가.
- D5~D8 신규 결정: 다른 슬롯이 Design에 던진 4건에 대한 답변.
- D9~D12 목표 합의: ISE(명령어 세트 에뮬레이션), GPU 추상화 레이어, HAL, Apple Silicon Sandbox 통합. 런타임 구현 완료를 뜻하지 않는다.
- 2026-09-07 재개 대조: 첨부 세션의 최근 우선순위는 `nextcore-apls`와 QEMU/OVMF를 이용한 실제 macOS 부팅 검증이다. 이전 세션의 마지막 보고는 host 테스트 103개 통과 후 CLI 확인·QEMU 검증으로 넘어가는 지점이며, 이 수치는 당시 보고로만 취급한다.
- 현재 검증 기록 대조(`nextcore/VALIDATION.md`, 2026-09-07): EFI의 자기 볼륨 설정 파일 읽기와 OVMF 4개 분기, APLS CLI→WSL→QEMU→ARM Stage2 실행까지 확인됐다. Stage2는 펌웨어 panic으로 끝났고 XNU/userspace/Metal은 미관측이다. 이는 해당 실행 보고의 범위이며 native Apple VM 실행이나 직접 XNU 인계 성공을 뜻하지 않는다.
- D2/D5/D7의 2026-09-07 개정: 명시 OS EFI loader 실행을 중간 통합 경로로 허용하고, 내부 handoff 모델과 공개 XNU ABI adapter를 분리했다. 과거 D5의 4종 상한은 본 개정으로 대체한다. 실제 설정 해석·child 실행의 후속 구현 및 검증 상태는 Build Plan과 `nextcore/VALIDATION.md`가 기록한다.
- Rust 모듈 트리·wizard 문구·격리 자산 목록 등 구현/운영 상세는 각 슬롯 영역.
- (F) 이전 통합 검증 — 당시 OPEN_QUESTION 6건 종결(RESOLVED 5 · HOLD 1).
  D6×Prompts 버전 목록 절충과 D5×BP3×B1 대조 결론을 본문에 병기했다.
  회수 대조표는 "통합 검증 (F)" 참조.

## 원하는 상태

- NextCore가 *무엇인지* 한 문단으로 설명된다.
- macOS 부팅 흐름이 *어떤 단계*로 구성되는지 박제된다.
- iBoot가 하는 일과 NextCore가 그 일을 *어떤 다른 방식*으로 하는지가
  병렬로 박제된다.
- OpenCore의 *어떤 아이디어가 승계*되고 *어떤 부분이 의도적으로 버려졌는지*
  명시된다.
- EFI 진입, OS 로더 진입, XNU 실행, macOS userspace, 실제 Metal 실행을 별도 증거로 판정한다. 첫 단계의 성공만으로 나머지 완료를 선언하지 않는다.

## 결정 항목

### D1. NextCore 정체성

(결정: 합의 — 본 세션 Design 슬롯이 심화.)

> **근거:** AGENTS.md §0 핵심 원칙 — (a) macOS는 EFI 환경에서 부팅,
> (b) iBoot와 *기능적으로 동등*하되 *구현은 독립*, (c) OpenCore 아이디어
> 승계 + 소스 비의존. 이 세 원칙을 만족시키는 *외형 정의*는 Design 슬롯이
> 닫는다 (구현 디테일은 Build Plan).

NextCore는 UEFI 펌웨어 환경에서 macOS를 부팅하기 위한 *공개* 부트로더다.
핵심 사상은 다음 두 가지다.

1. **iBoot의 *역할*을, iBoot와 다른 방식으로 채운다.** macOS가 EFI 이후
   단계에서 요구하는 *외부 인터페이스*(DeviceTree, memory map, boot args,
   kext 등록, handoff 자료구조)만 동등하게 제공하며, iBoot의 내부 코드·
   키·blob·내부 명칭은 일절 사용하지 않는다. *기능 동등, 구현 독립.*
2. **OpenCore의 *아이디어*를 승계한다.** `config.plist` 기반 설정 주도형
   부트로더 사상, `EFI/OC/` 디렉터리 구조의 *위치* 호환, ACPI·
   DeviceProperties·boot-args 키의 *인터페이스* 호환, 공개 kext 목록
   호환. 소스 코드 의존성은 없다.

**계층 범위(2026-09-07 정합):** 위 정의는 EFI 부트로더 코어에 해당한다.
D9~D11의 지속 실행 기능은 별도 커널·가상화·드라이버 계층이 필요하고,
D12의 Apple Silicon host 제어는 macOS 사용자 공간 계층이다. EFI 앱 하나가
`ExitBootServices()` 뒤에도 모든 장치·예외 처리를 소유하는 것으로 해석하지 않는다.
부트 코어의 완료와 이들 동반 런타임의 완료는 별도로 검증한다.

구현 언어는 Rust다(이 사실 자체는 Design 합의이며, *모듈 구조*·*의존성*
·*빌드 단계*는 Build Plan이 결정한다). NextCore는 부팅 신뢰성 검증
(Bootability Manifest, img4)을 *하지 않으며*, 신뢰는 호출자 정책에
위임된다. iBoot/Apple 보안 메커니즘의 우회 도구가 아니다.

비목표:
- iBoot/Apple 내부 구현의 *형체화* (AGENTS.md §0).
- img4 / Apple 보안 토큰 우회, IPSW 추출물의 공개 코드·빌드·배포 편입.
  외부 로컬 원본 매체를 실행 시험에 사용하는 경계는 Boundary B7-2를 따른다.
- 펌웨어 패치·NVRAM 변조 등 OpenCore의 *hack* 계층 채택 (D4 참조).

대상 사용자: Hackintosh/OpenCore 사용자가 기존 `config.plist` 자산으로
EFI 환경에서 macOS를 부팅하고자 할 때, *공개 트리만으로* 구성된 경로를
제공하는 것.

### D2. macOS 부팅 흐름 (EFI 환경 기준)

(결정: 합의 — 각 단계의 입력/출력/책임 경계를 한 줄씩 박제한다.)

> **근거:** AGENTS.md §0 (EFI 부팅, iBoot와 기능 동등/구현 독립) +
> UEFI 공개 명세 + macOS 부팅 요구사항 — 5단계 흐름은 *책임 단위*로
> 박제하며, 각 단계의 구현은 Build Plan이 다룬다.

목표 macOS EFI 경로는 다음 단계로 구성한다. 현 EFI 코드가 아래 전부를
수행한다는 뜻은 아니다. 1~4단계의 *역할*은 기존
펌웨어 부트로더가 수행하던 것과 기능적으로 동등하나, NextCore는 그 역할을
*다른 방식*(공개 규격 + Rust 구현)으로 제공한다. 5단계는 macOS 자체 영역이다.

1. **EFI 진입 + 시스템 테이블 인식** — 입력: UEFI firmware가 로드한 NextCore EFI binary와 시스템 테이블. 출력: 확보된 Boot Services 핸들(메모리 맵, 콘솔, 파일시스템 프로토콜). 경계: firmware 선택·서명 판단에는 관여하지 않고, 전달받은 테이블을 읽기만 한다.
2. **설정 로드** — 입력: `EFI/OC/config.plist` 호환 형식의 `config.plist` 파일. 출력: 검증된 설정 구조체(SMBIOS, ACPI 목록, kext 목록, DeviceProperties, boot-args). 경계: 설정 *해석*까지가 책임이며, 설정값의 하드웨어 정합성 판단은 later 단계에 위임한다.
3. **하드웨어 구성 준비** — 입력: D2-2의 설정 구조체와 firmware 제공 ACPI 테이블. 출력: ACPI·DeviceProperties의 적용 계획과 kext 카탈로그. 경계: host 구조체에 기록하는 단계와 EFI 테이블에 실제 게시하는 단계를 구분한다. D11의 런타임 HAL은 별도 계층이다.
4. **부트 체인 인계** — 입력: 준비한 구성과 명시 선택한 OS EFI loader 또는 커널 이미지. 출력은 아래 D2-A의 표준 EFI child 실행 또는 D5의 대상별 ABI를 만족한 직접 커널 진입으로 구분한다. 내부 handoff roundtrip은 어느 실행의 증거도 아니다. 실제 메모리 수명·진입 상태·오류 처리는 Build Plan이 구현하고 검증한다.
5. **XNU 실행 + macOS userspace 진입** — 입력: D2-4의 실제 인계 상태. 출력: 커널 로그와 userspace 실행 증거. 부트 코어 인계 뒤에는 XNU·동반 런타임 계층으로 전환한다. 실패 시 원인 계층을 확인하며, 잘못된 인계로 인한 실패를 자동으로 macOS 책임으로 넘기지 않는다.

UEFI Boot Services는 성공한 `ExitBootServices()` 이후 사용할 수 없고,
OS 로더가 이후 시스템 운영을 책임진다. 인계 직전 memory map과 map key를
확보해야 한다. GOP/ConOut 사용 가능 여부와 런타임 framebuffer 접근은
이 경계에서 별도로 다룬다. [UEFI 2.10A §7.4.6](https://uefi.org/specs/UEFI/2.10_A/07_Services_Boot_Services.html#efi-boot-services-exitbootservices)

#### D2-A. 명시 OS EFI loader를 통한 중간 통합 경로

(결정: 2026-09-07 확정 — EFI Boot Services 계층의 독립 검증 단계.)

- x86_64 UEFI에서 사용자가 설정한 동일 아키텍처의 EFI application을
  `LoadImage()`로 로드한 뒤 `StartImage()`로 실행하는 경로를 허용한다.
  파일의 EFI device path와 부모 ImageHandle을 사용하여 firmware가 정상
  Loaded Image 환경·SystemTable을 제공하게 한다. 임의 entry 주소 호출로
  이를 대신하지 않는다. 이미지에 대한 firmware의 보안 정책과 오류를 따른다.
- 대상은 명시 경로로 선택하며, NextCore 자신을 재귀 실행하지 않는다.
  외부 로컬 원본 매체의 loader를 시험 입력으로 참조할 수 있다(Boundary
  B7-2). 그 파일을 공개 소스·빌드 입력·배포물·CI fixture에 편입하지 않는다.
- `LoadOptions`는 선택한 child가 명시한 계약이 있을 때만 그 형식으로
  전달한다. 계약이 없으면 비운다. NextCore의 내부 직렬화, plist 전체 또는
  `boot-args` 문자열을 모든 child가 받아들이는 표준으로 간주하지 않는다.
  읽고 검증한 설정과 실제 적용·전달한 설정을 별도로 기록한다.
- 부모 NextCore는 child 실행 전에 `ExitBootServices()`를 호출하지 않는다.
  이후 OS별 이미지/KC 준비, 최종 memory map·runtime 처리 및 커널 진입은
  해당 child의 책임이다. 직접 XNU 경로를 선택할 때는 이 책임을 NextCore의
  D5 adapter와 별도 실행 전환 코드가 맡는다.
- 로드 결과와 시작 직전 기록, child 자체 진입 증거, 반환 status/ExitData를
  구분한다. `StartImage()` 호출 직전 로그는 child 진입 증거가 아니고,
  성공 반환은 macOS 부팅 증거가 아니다. 반환 뒤에는 ExitData와 소유 자원을
  정리한다. 직접 작성한 시험 child는 이 EFI 서비스 경계만 검증한다.
- 이 경로는 최종 독립 XNU 로더, iBoot 역할 대체, ISE/HAL/GPU 런타임 목표를
  유지하는 중간 단계다. 외부 loader가 실행됐다는 사실을 그 목표의 구현
  완료로 표시하지 않는다.

근거: [UEFI 2.10A §7.4 Image Services](https://uefi.org/specs/UEFI/2.10_A/07_Services_Boot_Services.html),
[§9 Loaded Image Protocol](https://uefi.org/specs/UEFI/2.10_A/09_Protocols_EFI_Loaded_Image.html).
이 문서는 child별 옵션 ABI나 macOS 매체별 loader 위치를 추정해 확정하지 않는다.

### D3. iBoot 대체 방식

(결정: 합의 — 각 행의 "왜 다른 방식인지" 근거를 한 줄씩 박제한다. Apple 내부
명칭·내부 포맷 의존 없음. 아래 좌측 열은 *기능 영역(참고용 일반 명칭)*이며
내부 구현 명칭이 아니다.)

> **근거:** AGENTS.md §0 (형체화 금지, iBoot 내부 동작 모방 금지) +
> §4 (OpenCore 아이디어는 승계 가능) — 모든 대체 행은 *공개 명세에
> 한정*하며, iBoot의 *내부 동작*을 모방하는 표현은 배제한다. 좌측 열은
> 기능 영역의 *일반 명칭*이며 내부 구현 명칭이 아니다.

| 기능 영역 (참고) | NextCore 구현 방향 | 왜 다른 방식인지 |
| --- | --- | --- |
| 부팅 대상 신뢰 목록 검증 | NextCore는 목록을 검증하지 *않는다*. 부팅 신뢰성은 호출자·상위 정책이 제공한다. | 신뢰 판단은 부트로더 바깥(호출자·플랫폼 정책)의 책임으로 분리하므로 독자 검증기를 품지 않는다. |
| 하드웨어 기술 트리 구성 | 내부 하드웨어 모델과 D7의 공개 XNU 인계 표현을 분리한다. | 공개 출처에서 확인한 외부 형식으로 독립 변환하며 격리된 내부 구현을 이식하지 않는다. |
| RAM 디스크 구성 | NextCore는 벤더 전용 ramdisk 포맷 파서에 의존하지 *않고* 표준 ramdisk 인터페이스를 사용한다. | 특정 벤더 포맷 파서는 공개 트리에서 검증할 수 없으므로 표준 인터페이스로 대체한다. |
| 커널 모음 로드 | UEFI 파일·메모리 서비스로 입력을 얻고, 대상별 공개 이미지/KC 요구와 진입 상태를 D5에서 검증한다. | Mach-O 헤더 인식과 실행 가능한 커널 배치를 구분한다. 현재 헤더 시험은 KC 로더 완료가 아니다. |
| kext 등록 | NextCore는 공개 호환 kext 목록 형식을 사용한다. | kext 목록 형식은 설정 주도 사상의 공개 인터페이스이므로 호환하되 독자 구현한다. |
| 서명 검증 (펌웨어·커널 서명 일반) | NextCore는 서명 검증 책임을 지지 *않는다*. 신뢰는 상위 정책(예: 플랫폼의 공개 UEFI 서명 정책)에 따른다. | 키·인증서 취급은 공개 트리의 책임 밖이므로 검증 책임을 상위 정책에 위임한다. |
| Memory Map 구성 | firmware descriptor의 의미·속성을 보존하고, D5 adapter가 주소·크기·stride·version을 대상 ABI로 표현한다. | 원본 맵과 커널 인계 표현은 구분한다. ABI 변환을 임의 memory map hack과 혼동하지 않는다. |
| Console / Framebuffer | EFI 중에는 GOP/ConOut, 인계 시에는 검증한 framebuffer 정보와 메모리 수명을 다룬다. | Boot Services 이후 콘솔 프로토콜을 계속 호출하지 않는다. framebuffer 출력과 D10 GPU 가속은 별개다. |
| Boot Args 전달 | 직접 XNU 경로에서는 D5의 인자 문자열 표현, child 경로에서는 D2-A의 명시 옵션 계약을 따른다. | EFI 변수 쓰기만으로 커널이 그 값을 받았다고 판정하지 않는다. |
| SMBIOS 노출 | 기본 EFI 경로는 firmware 테이블을 사용한다. 명시한 HAL 프로파일에 따른 별도 변환 목표는 D11에서 다룬다. | 원본 테이블의 수집과 게스트용 변환·게시의 책임을 분리하며, 문자열 변환을 하드웨어 지원으로 판정하지 않는다. |

> 핵심: NextCore는 기존 부트로더의 *내부 동작*을 모방하지 않는다. macOS가 EFI 환경에서
> 부팅되기 위해 필요한 *외부 인터페이스*만 *공개 명세 기반으로* 제공한다.

### D4. OpenCore 아이디어 승계

(결정: 합의 — 항목마다 판정 근거 한 줄.)

> **근거:** AGENTS.md §0 (OpenCore 아이디어 승계 + 소스 비의존) +
> §3 (iBoot 비밀키/blob 사용 금지) — 비승계 항목은 의도적 경계 선언이며,
> 펌웨어 패치/hack 계층은 *공개 명세 기반* 원칙과 *구현 독립* 원칙
> 모두에 반하므로 일괄 비승계한다.

승계:

- `config.plist` 기반 설정 (plist 호환 파서). — 근거: 설정 주도형 부트로더라는 공개 아이디어의 핵심이므로 승계한다.
- `EFI/OC/` 디렉터리 구조 (NextCore도 같은 위치에 자기 파일 둠). — 근거: 기존 공개 도구·문서와 호환되는 배치 관례이므로 위치만 공유한다(코드·상표 의존 없음).
- ACPI·DeviceProperties·boot-args 키 호환. — 근거: 공개 인터페이스이므로 키 이름 호환은 형체화가 아니라는 경계 원칙에 따른다.
- kext 등록 방식 호환. — 근거: 공개 kext 목록 형식은 구현이 아닌 인터페이스이므로 호환한다.

의도적 비승계:

- OpenCore C 소스 코드 의존 — 없음. — 근거: 클린룸 Rust 구현 원칙이므로 코드를 가져오지 않는다.
- OpenCore 빌드 시스템 의존 — 없음. — 근거: Cargo 기반 독립 빌드가 목표이므로 빌드 체계를 공유하지 않는다.
- OpenCore 기호 / 상표 — 사용 안 함. — 근거: 식별자·상표는 승계 대상이 아니라는 원칙이므로 사용하지 않는다.
- 비밀키 / 인증서 / blob — 일절 사용 안 함. — 근거: 신뢰 자산 취급은 공개 트리의 책임 밖이므로 다루지 않는다.
- OpenCore의 `OpenRuntime` / `OpenCanopy` 류 펌웨어 패치 추상화 — 채택하지 않음. UEFI RuntimeServices를 직접 호출한다. — 근거: 공개 UEFI RuntimeServices만으로 충당 가능하므로 전용 추상화 계층을 두지 않는다.
- AptioMemoryFix 류 memory map hack — 채택하지 않음. firmware가 제공한 memory map을 그대로 신뢰한다. — 근거: memory map 변조는 *공개 명세 기반* 원칙과 어긋나므로 firmware 출력 그대로를 채택한다.

### D5. 내부 handoff 모델과 공개 XNU 인계 ABI

(결정: 2026-09-07 개정 확정 — BP8 및 Boundary B7-1의 질문에 답함.)

**현재 상태:** `nextcore-core/src/handoff.rs`의 `BootArgs` roundtrip은
NextCore 내부 형식의 검증이다. **원하는 상태:** 내부 의미 모델에서 실제
게스트 아키텍처·버전에 맞는 외부 ABI로 검증 가능한 변환을 수행한다.
두 형식은 이름이 비슷해도 동일하지 않으며, 내부 blob을 XNU 구조체로 cast하거나
UEFI entry ABI를 커널 entry ABI로 사용하는 것은 허용된 설계가 아니다.

#### D5-A. 공개 근거와 적용 대상

이번 인터페이스 검토는 Apple 공식 공개 **`xnu-12377.121.6`**, commit
**`ac9718fb1af618d5ce8678d0dc6e8a58f252216f`**를 고정해 읽었다.
[i386 boot.h](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/pexpert/i386/boot.h)는
직접 인계의 외부 표현 근거다. Boundary B7-1에 따라 공개 기술 자료로 분류한다.
**독립 wire encoder 허용 경계:** 공식 공개 ABI에서 확인한 필드 의미·폭·
endianness·크기·버전·offset을 출처와 함께 필요한 범위로 기록하고, 그 외부
표현과 호환되는 byte encoder/decoder를 독립 작성할 수 있다. 이는 헤더 원문·
구조체 선언·Apple 구현 코드를 그대로 복사하거나 격리 분석의 레이아웃을
이식하는 승인과 다르다. 내부 Rust 모델은 별도로 유지하며 host 구조체 cast로
wire 표현을 대신하지 않는다. 독립 adapter의 필드 계약·출처·검증은 Build Plan이
먼저 문서화한다.

- **x86 진입 계층:** 같은 commit의
  [x86_64/start.s](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/x86_64/start.s)는
  초기 진입에 32-bit protected mode, paging 비활성, flat 주소 공간과 EAX의
  인계 포인터를 명시하고 이후 long mode로 전환한다. 이 진입점을 쓸 경우
  x86_64 EFI 호출 상태에서 필요한 실행 전환·포인터 범위·페이지 수명을
  별도로 검증해야 한다. 일반 EFI 함수 호출은 이를 충족하지 않는다.
  뒤의 64-bit `vstart`는 선행 페이지 테이블·stack 상태를 소비하는 내부 단계다.
  Mach-O의 CPU 종류나 thread-state 폭만으로 별도 64-bit 부트 entry가 지원된다고
  판정하지 않는다. EFI mode 필드 역시 CPU entry mode와 구분한다.
- **실제 소비 계층:**
  [i386_init.c](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/i386/i386_init.c)의
  `vstart`는 커널 배치 정보를 사용하고 버전/KC 조건을 처리하며, 페이지
  테이블 초기화 전에 플랫폼 초기화를 호출한다.
  [pe_init.c](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/i386/pe_init.c)는
  전달된 DeviceTree와 video 정보를 읽는다. 따라서 Mach-O 헤더 확인이나
  내부 트리 roundtrip만으로 이 경계를 검증할 수 없다.
- **ARM64 분리:** 같은 commit의
  [arm64/boot.h](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/pexpert/arm64/boot.h)는
  RAM의 물리·가상 배치 등 별도 인계 모델을 정의한다. i386 구조체나 EFI
  진입 전제를 APLS ARM64 경로에 적용하지 않는다.
- **버전 미확인:** 현재 APLS 매체의 27.0/26A5425a와 Darwin 27 문자열은
  `nextcore/VALIDATION.md`의 매체 관측이다. 위 공개 tag와의 ABI 일치 또는
  해당 커널 실행은 미확인이다. x86 대상 매체도 별도 식별·검증해야 한다.

#### D5-B. 표현 범위와 변환 책임

과거의 네 종류는 내부 mock에 충분한 범위였으며 실제 XNU ABI의 상한이 아니다.
위 공개 i386 헤더는 기존 범주 외에 framebuffer, EFI runtime/system table,
descriptor metadata와 버전별 커널 배치 정보도 표현한다. 다음 범위를 허용한다.

- **내부 의미 모델:** UEFI 메모리 맵, 커널 이미지/KC 배치, 인자 문자열,
  ACPI·장치 속성 및 트리, framebuffer, EFI runtime·configuration table,
  대상 ABI 식별과 참조 메모리의 소유권·물리/가상 주소 관계를 표현한다.
  host의 `Vec` 주소나 포인터를 그대로 게스트 주소로 직렬화하지 않는다.
- **외부 ABI adapter:** 대상별로 버전·주소 폭·인자 길이, memory map의
  바이트 크기·descriptor stride/version, 트리 표현과 길이, video 정보,
  kernel/KC 배치 및 EFI runtime/system table 표현을 독립 변환한다.
  내부 요약 기록과 실제 커널이 참조하는 메모리를 구분한다. 모든 필드가
  모든 게스트에서 필수라는 뜻은 아니다.
- **값의 출처와 수명:** 맵·테이블·video 값은 해당 firmware/loader의 실제
  관측에서 얻는다. descriptor 속성을 보존하고, 인계 직전 유효한 맵과
  map key를 확보하며, 참조 페이지가 커널 소비 전에 회수되지 않게 한다.
  EFI runtime 영역과 주소 매핑은 대상 OS의 공개 계약에 맞춰 관리한다.
  GOP protocol 호출의 수명과 framebuffer 메모리의 수명은 다르다.
  [UEFI 2.10A runtime 개요](https://uefi.org/specs/UEFI/2.10_A/02_Overview.html),
  [GOP](https://uefi.org/specs/UEFI/2.10_A/12_Protocols_Console_Support.html)
- **안전한 미지원 표현:** 대상에서 필요한 값·부재 표현·진입 상태를 확인할
  수 없으면 해당 직접 인계를 미지원으로 반환한다. 공개 헤더에 등장하는
  보안 정책, key store, sealed-volume 자료 등의 필드를 임의의 0·합성 값으로
  채우거나 신뢰 검증을 우회하지 않는다. 실제 opaque 자료의 소유·전달은
  선택한 OS loader/플랫폼 계약에 따르며 공개 자산으로 편입하지 않는다.

#### D5-C. 아직 확정되지 않은 구현 계약

대상별 필수/선택 필드, 허용되는 빈 값, KC 배치·재배치, flattened DeviceTree의
구체적 encoding과 필요한 노드, runtime mapping, 보안 자료의 소유권은 실제
대상과 공개 소비 코드를 대조해 Build Plan에서 확정한다. byte offset·상수·전체
필드 열거를 여기서 추정하지 않는다. 검증은 내부 roundtrip, adapter 표현,
firmware/커널 인계 실행을 분리하며 최종 수용은 실제 커널 관측으로 판정한다.

**고정 소스 상세 계약:** `nextcore/artifacts/xnu-entry-contract-20260907.md`에
`xnu-12377-pstart32` 검토 결과를 기록했다. 4096-byte wire 표현, 초기 필드,
VA→PA 변환, `__HIB`·`__TEXT` 및 bootstrap 메모리 조건을 구분한다. 그 파일의
소스 확인·산술 도출·NextCore 제한·실제 이미지 미확인 표기를 구현에서 유지한다.
공개 tag와 macOS 26/27 매체의 ABI 일치는 아직 확인하지 않았다.

**이전 (F) 결론의 범위:** 당시 4종 상한은 mock 단계의 통합 이력으로 보존한다.
본 개정이 그 상한을 대체하며, Build Plan은 이후 본 절의 범위 안에서 대상별
계약을 기록한다. 공개 근거 없는 필드 확장은 계속 Design에 먼저 질의한다.

### D6. macOS 버전 목록 정책: 동적 원칙 + v1 고정 노출 (F 통합)

(결정: 합의 — `OPEN_QUESTION: Design:macOS 버전을 하드코딩할지 동적으로 가져올지`에 답함.)

- 원칙은 *동적 목록*이다. Design 문서는 특정 상용 릴리스 번호·이름의 열거를 박제하지 않으며, wizard는 호스트의 설치 매체·공개 릴리스 식별자가 제공하는 값을 그대로 전달한다.
- 근거: 버전 열거를 Design에 하드코딩하면 릴리스마다 문서·구현이 어긋나므로, Design은 "매체가 준 식별자를 그대로 전달한다"는 원칙만 정의한다.
- 빈 목록·오프라인 등 예외 시 UX 문구는 Prompts 슬롯의 책임이다.

> **(F) Prompts와의 충돌 — 통합 결론 (Design·Prompts 양쪽에 동일 박제):**
> - 층위 결정: **원칙은 동적(본 절 D6), wizard v1 노출은 4종 고정 + 동적
>   확장 여지(Prompts P2 목록·P8).** 두 문장은 상하 관계이지 택일이 아니다 —
>   동적은 *전달 원칙*, 4종 고정은 *v1 노출 집합*이다.
> - 확장 구현 시점: `HOLD: wizard v1 출시 이후 BP 단계표 밖의 별도 단계로
>   수립` — 현 시점 게이트 없음.
> - D6이 Prompts에 위임한 빈 상태·오류 문구는 Prompts P7 (F) 추가분에 박제.
> - 동일 결론이 Prompts P8에 병기되어 있으며, 두 문서 중 한쪽만 바꾸는
>   개정은 금지한다(F).

### D7. 공개 DeviceTree 명세의 범위 (Boundary 질문에 대한 답)

(결정: 합의 — `OPEN_QUESTION: Design:공개 DeviceTree 명세의 범위 정의`에 답함.)

- 내부 DeviceTree 모델은 UEFI·ACPI 공개 규격, IEEE 1275 device-tree 개념,
  공개 OS의 하드웨어 기술 관행으로 표현 가능한 키-값 하드웨어 기술 집합이다.
- **2026-09-07 개정:** XNU에 전달하는 트리는 내부 모델과 별도 외부 ABI다.
  Boundary B7-1의 공식 공개 XNU 소스에서 확인한 형식·소비 요구를 D5의
  아키텍처·버전별 adapter 근거로 사용할 수 있다. 일반 트리나 임의 plist가
  그 flattened 표현과 같다고 가정하지 않는다. 구현 전 정확한 공개 producer/
  consumer와 필요한 노드·값의 출처를 Build Plan에 기록한다.
- 격리 분석에서 얻은 내부 필드·바이너리 레이아웃의 복제·이식은 금지한다.
  공식 공개 인터페이스의 독립 구현과 격리 결과의 코드 이전을 구분한다.
- 허용 출처의 확정 목록(어떤 공개 규격을 인용하는지)은 Boundary 슬롯의 책임이다.

### D8. 격리 자산→NextCore 지식 단위의 정의 (Inventory 질문에 대한 답)

(결정: 합의 — `OPEN_QUESTION: Design:격리 자산에서 NextCore로 이전 가능한 지식 단위의 정의`에 답함.)

- 이전 가능한 지식 단위는 자연어 한 문장으로 표현되는 *필요한 외부 인터페이스* 서술(예: "커널 인계 시 메모리 맵이 필요하다")에 한정한다.
- 코드 줄, 구조체 레이아웃, 상수값·오프셋, 바이너리 추출물의 이전은 금지한다. 이전 시에는 다른 표현으로 재서술하며(Boundary B2 규칙), 출처·원문은 인용하지 않는다.
- 재서술 결과의 메타 기록 형식(한 줄 형식 등)은 Inventory 슬롯의 책임이다.

### D9. 명령어 세트 에뮬레이션 (ISE)

(결정: 목표 합의 — 기존 하드웨어 지원 요구를 유지하고 구현 증거와 분리.)

- **원하는 상태 / CPU 실행 계층:** MacPro1,1 등 구형 x86 하드웨어에서
  대상 macOS가 요구하는 누락 명령어를 실행하도록 한다. XSAVE, AVX/AVX2,
  FMA, SSE4.1/SSE4.2, POPCNT, PCLMULQDQ는 목표 목록이며 전부 지원된다는
  선언이 아니다. 릴리스별 필요한 명령어는 실제 이미지·예외 로그로 확인한다.
- **수행 위치:** 초기 EFI 설정 이후에도 동작하려면 커널 또는 하이퍼바이저가
  실행 상태·예외·메모리 수명을 소유해야 한다. IDT의 예외 전달과 GDT의
  세그먼트 기술자는 서로 다르므로 "IDT/GDT에 트랩 핸들러 등록"으로 묶지 않는다.
  XNU 진입 뒤의 등록 경로와 CPU별 상태 저장은 아직 확정·구현되지 않았다.
- **예외 분류:** 미지원 명령은 `#UD`가 주요 진입점이나, 잘못된 인코딩·OS
  상태 설정도 `#UD` 원인이 될 수 있다. `#GP`를 누락 명령으로 일괄 처리하지
  않는다. CPUID 기능 비트와 OSXSAVE/XCR0 실행 상태를 분리한다.
  [Intel SDM, Vol. 2의 명령별 예외 및 Vol. 3의 예외 처리](https://cdrdv2-public.intel.com/874240/325462-090-sdm-vol-1-2abcd-3abcd-4.pdf)
- **현재 상태 / host 모델:** `nextcore-ise`에는 디코더, 레지스터 모델,
  일부 연산과 `TrapHandler::handle_trap` 순수 함수가 있다. 실제 IDT 설치,
  예외 진입 어셈블리, XNU 컨텍스트 복원 경로는 없다. 메모리 피연산자는
  일부 경로에서 `MemoryUnsupported`로 반환한다. host 단위 테스트로
  Pre-AVX macOS 부팅·완전한 ISA 의미론을 주장하지 않는다.
- **설계상 검증 조건:** 연산 결과뿐 아니라 피연산자 폭, VEX 소스 선택,
  플래그·예외·메모리 접근·상태 저장을 ISA 명세와 대조해야 한다. 이미
  구현된 함수명 또는 테스트 통과만으로 전체 명령군 지원을 노출하지 않는다.
- **공개 출처:** 공개 x86 ISA 명세로 독립 구현한다. 기존 Community payload
  경로는 이식된 구현 또는 Apple 소유 코드의 증거로 취급하지 않는다.
  소유권·이식 가능 여부는 Boundary/Inventory가 해당 자산별로 판정한다.

### D10. GPU 추상화 레이어

(결정: 목표 합의 — 정규 드라이버 규격과 런타임 Metal 지원을 구분.)

- **원하는 상태:** AMD/NVIDIA/Intel 장치에 대한 드라이버를 NextCore 추상화
  레이어 안에 배치하고, 공통 명령·리소스 규격을 통해 게스트가 사용할 수
  있게 한다. 미지원 장치에는 소프트웨어 실행을 제공하고, 가능한 연산은
  메모리 공유·하드웨어 backend로 라우팅한다. 모든 GPU의 지원 완료를
  약속하는 것이 아니라 새 장치를 같은 규격으로 추가하는 확장 목표다.
- **계층 분리:** EFI GOP는 초기 화면, 장치 backend는 메모리·DMA·명령
  제출·동기화, 게스트 드라이버 경계는 OS 장치 연결, Metal은 사용자 공간
  API 계층이다. 공통 Rust 구조체를 `VirtualMetalDevice`라 부르는 것만으로
  macOS에 시스템 `MTLDevice`가 등록되지 않는다.
- **Metal 목표:** 게스트에서 장치 열거, 자원 생성, shader/command 실행,
  fence 완료와 결과 readback이 실제로 성공해야 해당 기능을 지원으로 노출한다.
  화면 출력, 문자열 기반 "Apple GPU" 식별, 하드코딩한 Metal 버전은 이
  검증을 대신하지 못한다. 게스트 연결 방식과 공개 driver/API 범위는
  OPEN_QUESTION으로 Build Plan에 넘긴다.
- **현재 상태 / host 모델:** `nextcore-gpu/src/virtual_device.rs`는 CPU
  `Vec<u8>` 버퍼 복사를 수행한다. `ComputeKernel`, `RenderClear`,
  `PresentSwapchain`은 현재 로그/핸들 확인 경로이며 shader 실행·픽셀
  렌더링·화면 게시의 증거가 없다. `supports_metal()`의 vendor/VRAM 판정과
  `HardwareWrapped` 값은 실제 Metal 또는 GPU 실행 여부의 근거가 아니다.
  `nextcore-apls/src/sgpu.rs`의 요청 수신·명령 변환도 같은 한계를 가진다.
- **Linux 드라이버 선택:** 이전 사용자 요구대로 Linux 드라이버 포팅과
  필요 시 Linux 커널을 backend로 사용하는 방안은 허용된 설계 선택이다.
  Debian rootfs 전체를 기본 의존성으로 만드는 합의는 없다. 포팅 경계·구성
  크기는 Build Plan, 자산 출처·라이선스 분류는 Boundary 슬롯이 맡는다.
- **직접 라우팅 조건:** 메모리 래핑은 장치 명령·DMA 주소 공간·동기화와
  게스트가 기대하는 의미론이 함께 맞을 때만 하드웨어 실행 경로가 된다.
  CPU 버퍼 주소를 반환하는 것만으로 zero-copy 또는 가속을 선언하지 않는다.

### D11. 하드웨어 추상화 레이어 (HAL)

(결정: 목표 합의 — 원본 기술 정보, 변환 계획, 실제 게시·실행을 분리.)

- **원하는 상태 / firmware·가상 장치 계층:** SMBIOS, DeviceTree, PCI,
  ACPI 정보를 명시적인 대상 프로파일로 번역하여 macOS가 사용할 장치 환경을
  제공한다. D3의 기본 firmware SMBIOS 전달 경로와, 별도로 선택한 HAL
  프로파일 변환 경로를 구분한다.
- **현재 상태 / host 모델:** `nextcore-hal`의 SMBIOS 문자열·DeviceTree
  모델·PCI 분류·ACPI 변환 함수가 있다. 현 EFI 진입점은 이들을 호출하여
  firmware configuration table에 게시하거나 PCI 장치를 가상화하지 않는다.
  `recognized`는 로컬 목록과의 일치이며 macOS 드라이버 attach 결과가 아니다.
- **SMBIOS:** 선택한 모델의 기술 정보 변환과 원본 정보 보존을 목표로 한다.
  모든 필드를 임의의 Mac 값으로 바꾸는 것이 지원 조건은 아니다. 게시 후
  게스트 관측값을 확인해야 한다.
- **DeviceTree / ACPI:** 공개 규격으로 표현한 장치 토폴로지와 리소스를
  준비한다. D7의 일반 트리는 XNU가 요구하는 직렬화 ABI와 자동 호환되지
  않으며, AML/테이블의 생성·게시·게스트 해석도 각각 검증한다.
- **PCI:** ID/class 변환만으로 MMIO 레지스터, BAR, IRQ, DMA, 전원 관리의
  동작이 바뀌지 않는다. 실 드라이버 또는 가상 장치 backend가 실제 장치
  의미론을 제공하는 범위에서만 변환을 적용한다.
- **비목표와의 정합:** D4가 제외한 OpenCore 소스·펌웨어 패치 구현은
  가져오지 않는다. 독립 HAL의 공개 인터페이스 기반 변환 목표를 D4의
  "비승계"와 혼동해 제거하지 않는다.

### D12. Apple Silicon Sandbox 통합 (APLS-Sandbox)

(결정: 목표 합의 — Apple Silicon host 경로와 x86 EFI 검증 경로를 분리.)

- **원하는 상태:** `nextcore-apls` 및 `sandbox/vsk/`의 공개 계약을 연결해
  실제 macOS 게스트와 그래픽 작업을 실행한다. 사용자 지정 목표 표기인
  `macOS 27 Golden Gate`는 그대로 추적하되, 실제 매체의 ProductVersion,
  ProductBuildVersion, 커널 아키텍처와 실행 로그가 있어야 지원 판정을 한다.
- **Apple Silicon host / 사용자 공간 계층:** 공식 이름은
  `Virtualization.framework`다. macOS VM은 `VZMacPlatformConfiguration`,
  지원되는 restore image/설치 디스크, `VZMacOSBootLoader` 및
  `VZVirtualMachine`으로 구성한다. 프레임워크 로드는 VM 구성 검증·시작
  완료와 다르다. [Apple: Virtualize macOS on a Mac](https://developer.apple.com/documentation/virtualization/virtualize-macos-on-a-mac)
- **부팅 계층 정정:** 실제 Apple Silicon Mac의 Boot ROM→LLB→iBoot 경로는
  Intel UEFI 부팅과 다르다. APLS host 제어를 같은 EFI 진입점으로 표현하지
  않는다. APLS는 부팅 오케스트레이션·공통 장치 계약을 공유하는 별도 실행
  경로다. AGENTS §0의 EFI 부팅 목표를 이 backend만으로 달성했다고 주장하지
  않는다. [Apple Silicon 부팅](https://support.apple.com/guide/security/boot-process-secac71d5623/web), [Intel Mac 부팅](https://support.apple.com/guide/security/sec5d0fab7c6/web)
- **x86 검증 / EFI·에뮬레이터 계층:** QEMU/OVMF의 x86 EFI 진입 검증과
  Apple Silicon용 macOS 게스트 검증은 서로 다른 시험이다. 아키텍처가 다른
  이미지를 사용하려면 해당 CPU와 기계 모델의 에뮬레이터 경로가 별도로
  필요하다. `native-efi-x86` 상태 출력은 어느 macOS 버전의 부팅 증거도 아니다.
- **현재 상태 / host 모델:** `nextcore-apls`는 launch plan, VF ABI header,
  정책 판정, SGPU 요청 변환, 환경 식별을 제공한다. `guest.rs`의 Apple
  backend는 framework 탐색 코드만 있고 `launch/pause/resume`은
  `AbiPending`을 반환한다. 비지원 host는 `UnsupportedBackend`다.
  Objective-C 클래스 탐색·비동기 start의 실제 Apple host 성공은 미검증이다.
- **현재 상태 / 실제 TCG 실행:** 별도 runner 경로는 Windows→WSL→Python→
  QEMU로 연결됐다. `nextcore/VALIDATION.md`의 실행 기록에서 ARM Stage2
  시작과 firmware panic이 관측됐으며 XNU/userspace/Metal은 미관측이다.
  위 native Apple backend의 미완료와 이 TCG 실행 증거를 혼동하지 않는다.
- **그래픽 수용 조건:** Apple의 VM 화면 설정 API와 NextCore SGPU의 명령
  계약을 분리한다. VM 화면 표시가 된 뒤에도 게스트 안의 Metal 장치 조회와
  실제 렌더/compute 결과를 확인한다. [Apple VM graphics](https://developer.apple.com/documentation/virtualization/graphics)
- **재개 순서의 설계 판단:** 로컬에서 가능한 host 계약·EFI 실행 시험을
  진행하면서 실제 매체·기계 모델·backend 연결을 병렬로 확인한다. 부족한
  backend를 단순히 성공으로 반환하거나 QEMU 시작을 macOS 부팅 성공으로
  취급하지 않는다. 명령·코드·증거 파일 경로는 Build Plan이 기록한다.

### D13. NextCore 제품 정체성과 목표 표시 — 2026-09-08 확정

- 사용자에게 보이는 앱 제목, EFI 화면, CLI 제품 설명과 wizard의 제품명은
  정확히 `NextCore`로 통일한다. Cargo package, 기존 설정 키, bundle identifier,
  import 경로와 serial receipt marker는 호환 식별자이므로 일괄 개명하지 않는다.
- 외부 OpenCore 엔진/원본 자산의 attribution과 기능 출처는 유지한다. 외부
  엔진을 호출하는 기존 wizard의 "OpenCore EFI 생성" 문구는 일반적인 "EFI
  구성 준비"로 바꾸고, 그 바이너리를 NextCore 독립 구현이라고 표시하지 않는다.
- 우선 목표는 사용자가 지정한 `macOS 27 GoldenGate`이며 AMD64↔Apple Silicon
  HAL과 guest Metal을 필수 수용 조건으로 추적한다. 실제 매체 버전/아키텍처와
  완료한 실행 증거가 없으면 목표를 "검증 완료"나 설치 가능한 매체로 가장하지
  않는다. D6/P8의 과거 4종 고정 노출·확장 보류는 이 사용자 결정으로 대체한다.

### D14. 실제 EFI 부팅 선택 화면 — 2026-09-08 확정

착수 시 BOOTX64는 설정의 활성 entry 하나를 바로 실행하며 그래픽 피커가 없었다.
이번 원하는 상태는 실제 UEFI Boot Services 안에서 동작하는 독립 NextCore
피커다. 부팅 대상은 검증한 `Misc.Entries`의 활성 항목이며 현재 chainloader가
지원하는 자기 볼륨의 EFI application만 선택한다. 아직 검색하지 않은 디스크나
설치되지 않은 OS를 타일로 만들어 표시하지 않는다.

- 검은 배경, 상단 NextCore 워드마크, 중앙 OS/entry 이름과 실제 볼륨 레이블을
  가진 타일, 밝은 선택 테두리, 명확한 선택/부팅/취소 키를 제공한다. 좁은 화면은
  표시 타일 수를 줄이고 선택 창을 이동한다. 레이블은 길이·제어문자를 제한한다.
- 좌우/상하 또는 Tab으로 선택, Enter로 해당 항목 실행, Esc로 취소한다.
  선택이 화면과 일치할 때만 index를 caller에 반환한다. 자동 countdown이나
  발견되지 않은 OS의 지원 배지, 장치/Metal 검증 성공 표시는 이번에 추가하지 않는다.
- `Misc.Boot.ShowPicker=true`는 피커를 연다. 누락/false는 기존 단일 entry
  동작을 유지하고 여러 활성 entry는 모호한 설정으로 거부한다. 기존 단일
  `parse_boot_target` 계약은 유지하며 별도 menu parser가 다중 선택을 담당한다.
- GOP의 공개 Blt API로 그리며 raw framebuffer layout을 추정하지 않는다.
  현재 출력 모드를 이용하고 메모리 상한을 둔다. GOP/해상도/메모리 문제가 있으면
  동일 선택·Enter·Esc 동작의 Simple Text Output fallback을 제공한다.
  입력은 SystemTable의 Simple Text Input/WaitForKey를 사용한다.
- 화면 자원과 protocol guard를 반환 전에 정리한다. 피커는 Boot Services를
  종료하거나 child를 직접 호출하지 않는다. 선택 뒤 기존 LoadImage/StartImage
  경로가 실행을 맡고, 취소는 부팅을 수행하지 않는다. ConsoleControl 설치와
  EFI main/Cargo 연결은 Build Plan 소유자가 조정한다.

근거: [UEFI 2.10 Console/GOP/Input](https://uefi.org/specs/UEFI/2.10/12_Protocols_Console_Support.html),
현재 `uefi 0.40.0`의 공개 GOP Blt 및 text input API. 폰트·아이콘·레이아웃은
독립 저작하며 외부 부트 피커 자산을 가져오지 않는다. host 렌더/입력 시험 후
실제 OVMF의 화면 캡처와 키 입력→선택한 child 진입을 같은 실행에서 검증한다.
EFI 피커 성공은 OS 부팅/HAL/Metal 성공과 별도로 기록한다.

2026-09-08 구현 결과: 다중 entry menu parser와 `boot_picker` 순수 렌더러,
UEFI GOP/입력 어댑터가 BOOTX64에 연결됐다. 실제 Q35/TCG OVMF에서 타일 화면,
두 번째 항목의 Enter 실행, Esc 취소, 단일 자동 실행 및 GOP 없는 text fallback의
Enter 실행을 확인했다. 자동 실행은 이전에 무시하던 `Name`도 계속 무시한다.
증거: `nextcore/artifacts/picker-bp21-20260908/README.md`.

## OPEN_QUESTION

(Design 슬롯이 다른 슬롯에 위임하는 항목 — 본 문서 직접 수정 대상 아님.)

### 2026-09-07 재개에서 도출한 미완료

- `OPEN_QUESTION: Build Plan:실제 OS 로더 인계와 macOS 실행 시험에서 EFI 배너/로더 진입/XNU/userspace/Metal의 증거 파일 및 실패 계층을 별도로 기록하라.`
- `OPEN_QUESTION: Build Plan:D9의 커널 또는 하이퍼바이저 예외 소유권과 상태 저장 경로를 결정하고, host ISE 의미론 검증을 런타임 부팅 증거와 구분하라.`
- `OPEN_QUESTION: Build Plan:D10의 guest driver/API 연결과 SGPU software 동작 범위를 확정하고, 로그만 남기는 연산 또는 정적 capability를 실제 실행 성공으로 노출하지 않도록 하라.`
- `OPEN_QUESTION: Build Plan:D12의 Apple host VM 시작 구현과 x86 QEMU/OVMF 시험을 별도 경로로 박제하고, guest 이미지의 실제 아키텍처/빌드 식별자를 기록하라.`
- `OPEN_QUESTION: Boundary:D10에서 허용한 Linux 커널/드라이버 backend의 출처와 포팅·배포 단위 분류를 구체화하라.`
  → RESOLVED-2026-09-07: Boundary B5(e)가 upstream/파일별 조건/패치 출처와
  backend·포팅·firmware/blob 분류를 확정했다. 개별 도입 기록은 Build Plan 책임이다.
- `OPEN_QUESTION: Build Plan:D2-A의 명시 x86_64 child EFI 경로·옵션 계약·실제 LoadImage/StartImage와 반환 처리를 문서화하고, 독립 시험 child로 firmware 서비스 경계를 검증하라.`
- `OPEN_QUESTION: Build Plan:D5/D7 개정에 따라 내부 모델과 대상별 공개 XNU ABI adapter를 분리하고, 공개 source commit·게스트 식별·필수/선택 필드·주소/수명/진입 조건을 구현 전 기록하라.`

위 항목들은 목표를 취소하는 조건이 아니라 다음 구현·검증의 책임 인계다.
아래 (F)는 이전 D1~D8 문서 통합 이력이며, D9~D12 런타임 완료 판정은 아니다.

### 이전 통합 이력

(F) 통합 검증 회수: 당시 아래 6건 전부를 종결했다. 라인은 추적용으로 유지하고
하위에 결속 표기를 붙인다.

- `OPEN_QUESTION: Build Plan:Rust 모듈 트리 — NextCore의 코어 디렉터리 구조`
  → RESOLVED-BY-F: Build Plan BP1이 3-crate + tests 3종 구조를 정본으로
  박제했고 BP6(a)가 D2 1~4단계와의 정합을 닫음으로 확인.
- `OPEN_QUESTION: Build Plan:handoff.rs 필드 목록을 D5 공개 범위에 맞춰 확정하라`
  → HOLD: (F) 상한 확정(D5 4종 = 필드 상한, D5 (F) 대조 결론·Build Plan
  BP7)으로 범위 질의는 종결. *필드 전체 열거*는 문서층에서 중복 박제하지
  않고 단계 6 착수 시 API 스케치로 박제하는 것으로 명시 보류.
  → SUPERSEDED-2026-09-07: 현재 범위는 개정 D5-A~C다. 위 4종 상한은 이전
  mock 단계 결정으로만 남으며, 실제 공개 ABI adapter 계약은 새 Build Plan 질문으로 인계했다.
- `OPEN_QUESTION: Prompts:동적 macOS 목록의 빈 상태·오류 문구를 확정하라`
  → RESOLVED-BY-F: Prompts P7 (F) 추가분에 KO/EN 카피와 "빈 목록을
  노출하지 않는다" 원칙 박제.
- `OPEN_QUESTION: Boundary:공개 DeviceTree 허용 출처 목록을 확정하라`
  → RESOLVED-BY-F: Boundary B6 (F)에 허용 출처 카테고리 목록 박제.
- `OPEN_QUESTION: Boundary:어떤 자산이 격리 폴더에 들어가야 하는지 (Inventory 슬롯 결정)`
  → RESOLVED-BY-F: Boundary B5(a)가 AGENTS §0 + B1 매트릭스 기준으로
  답변 박제(분류 경계) — 자산 *목록* 자체는 Inventory 현 상태 (F)가
  "현시점 빈 목록"으로 박제.
- `OPEN_QUESTION: Inventory:지식 단위 재서술 결과의 메타 한 줄 형식을 확정하라`
  → RESOLVED-BY-F: Inventory I4 (F)에 KB 한 줄 메타 형식 박제.

## 통합 검증 (F)

에이전트 F(통합 검증)가 본 문서의 OPEN_QUESTION 전량을 회수·종결했다.
회수 대조표(질문 → 결론 → 박제 위치):

| 질문 (본 문서) | 결론 | 박제 위치 |
| --- | --- | --- |
| Rust 모듈 트리 | RESOLVED — BP1 정본 | Build Plan BP1/BP6(a) |
| handoff.rs 필드 목록 | HOLD — 상한만 확정, 전체 열거는 단계 6 착수 시 | 본 문서 D5 (F), Build Plan BP7 |
| 동적 목록 빈 상태·오류 문구 | RESOLVED — 카피 박제 | Prompts P7 (F) |
| 공개 DeviceTree 허용 출처 목록 | RESOLVED — 카테고리 목록 박제 | Boundary B6 (F) |
| 격리 폴더 진입 자산 | RESOLVED — 분류 기준 + 빈 목록 박제 | Boundary B5(a), Inventory 현 상태 (F) |
| 지식 단위 메타 한 줄 형식 | RESOLVED — KB 줄 형식 박제 | Inventory I4 (F) |

- 핵심 충돌 조정 1 (D6 × Prompts 버전 목록): **원칙 동적(D6) + v1 노출
  4종 고정·확장 여지(Prompts P8)** — 동일 결론을 D6 (F)와 P8 양쪽에 박제.
- 핵심 충돌 조정 2 (D5 × BP3 단계 6/8 × Boundary B1): 모순 없음 확인,
  잔여 질문("4종 밖 필드")은 D5 (F) 대조 결론대로 "D5 개정 → Build Plan
  개정" 순서로만 처리하기로 확정.
