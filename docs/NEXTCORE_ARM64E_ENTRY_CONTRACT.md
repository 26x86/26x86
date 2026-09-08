# BP31 — macOS 27 M1 정상 진입 입력 계약 재검증

2026-09-09. 읽기 전용 감사. 저장소·모듈·원본 이미지·실행 설정은 변경하지
않았고 새 원본 실행도 하지 않았다. 이미 보관한 전체 IPSW, 추출물, 이전
진입점 조사와 공개 Apple/XNU 자료를 재사용했다. 이 문서에는 공개 인터페이스와
관측의 일반화된 결론만 담는다. 상세 원본 관측의 파일 위치는 별도 비공개
색인에 분리했다.

**현재 선택한 M1/j274 커널과 outer LC_UNIXTHREAD를 유지한다. 정상 부팅
준비는 SPTM 계열 handoff를 기준으로 진행하되, 현재의 불완전한 prefix
진단을 정상 handoff로 승격하지 않는다.** 비-SPTM 커널로 바꿔야 한다는
근거는 발견되지 않았다. 정확한 macOS 27의 boot_args/SPTM wire layout과
살아 있는 메모리·서비스 상태는 여전히 확정되지 않았다.

## 1. 실제 입력 선택에서 확인한 것

전체 복원 이미지의 BuildManifest와 기존 추출본이 byte-exact로 일치했다.
M1/j274에 대응하는 설치·업데이트·일반 macOS identity 세 개가 모두 현재
선택한 같은 KC, DT, iBoot 구성 요소를 지정한다. 세 identity에는 대상별
SPTM과 TXM 구성 요소도 있으며 실제 ZIP member가 존재한다. 이 다섯 구성
요소의 ZIP member SHA-384가 각 identity의 Digest와 모두 일치했다. KC/DT/
iBoot 추출물의 SHA-256와 기존 raw derivative 해시도 유지됐다.

이는 **대상 선택과 바이트 provenance**의 검증이다. ZIP CRC나 manifest
digest 일치는 Apple 신뢰 사슬·개인화 서명·부트 정책 검증을 대신하지 않는다.
기존 전체 IPSW SHA-256 영수증을 재사용했으며 이번에 전체 파일 해시를 다시
계산하거나 자산을 재다운로드하지 않았다. Manifest의 구성 요소 존재만으로
SPTM 서비스가 실행 중이거나 올바른 초기 CPU 상태가 존재한다고 추론하지 않는다.

공식 Apple SoC 표는 2026-01-28 기준으로 M1에는 PPL, M2 이상에는 SPTM을
표시한다. 이 표는 특정 macOS 27 복원 빌드의 구성 요소 선택 규칙이나 XNU
진입 ABI를 정의하지 않는다. 실제 대상 manifest와 실행 이미지의 관측을
버리고 칩 이름만으로 비-SPTM 경로를 강제할 근거로 사용해서는 안 된다.
이번 결과 또한 구형 하드웨어의 모든 SPTM 보안 특성에 관한 새 보증은 아니다.
[Apple SoC security](https://support.apple.com/guide/security/apple-soc-security-sec87716a080/web).

## 2. entry 선택과 SPTM/PPL 분기는 서로 다른 문제다

독립적인 Mach-O 명령 파싱에서 outer LC_UNIXTHREAD는 하나였고, 그 PC는
유일한 실행 가능한 file-backed segment 안에 있었다. 이전 parser의 선택과
정확히 일치했다. 이 이미지에는 이번 검증에 쓸 시작 심볼 증거가 없으므로
심볼 일치로 입증했다고 보고하지 않는다.

공개 Apple KC builder는 정적 커널의 thread command를 outer 컬렉션에
복사하고 segment slide를 반영한다. LC_FILESET_ENTRY는 내부 이미지의
위치·ID를 기록하며 별도의 정상 부팅 PC 선택 지시가 아니다. 내부 Mach-O의
PC가 다르다는 이유로 outer entry를 교체할 수 없다.
[Apple KC builder](https://github.com/apple-oss-distributions/dyld/blob/fd8d0c4d52320ebf64db34f3cb280310d905c5ae/kernel-collection-builder/AppCacheBuilder.cpp#L4843),
[Mach-O load commands](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/EXTERNAL_HEADERS/mach-o/loader.h).

공개 XNU에서 SPTM과 PPL 경로의 핵심 선택은 **빌드 구성**이다.
`config_sptm`은 SPTM startup/init을 선택하고, `config_pmap_ppl`은 별도의
startup/init을 선택한다. MASTER는 둘을 상호 배타적으로 사용하도록 설명한다.
SPTM entry 안에서 x0를 비교하는 분기는 SPTM 대 비-SPTM 선택이 아니라
cold/warm/secondary/hibernate/panic 같은 진입 이유를 구분한다.
[XNU ARM64 source selection](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/conf/files.arm64#L14),
[XNU configuration](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/config/MASTER#L320).

따라서 현재 대상의 SPTM 관련 패키지 선택과 이전의 entry-family 관측은 서로
일관된다. 정확한 대상 layout·보호 regime까지 확정했다는 의미는 아니다.
다른 칩용 KC, embedded entry 또는 legacy x0=boot_args 호출로 바꾸는 실험은
이번 감사의 결론이 아니다.

## 3. 정상 진입에 필요한 데이터와 실행 상태

공개 SPTM startup의 일반 부팅 호출은 x0에 진입 이유, x1에 iBoot 부트 인자,
x2에 SPTM bootstrap 인자를 받는다. panic 진입은 같은 레지스터를 다른 의미로
사용한다. SPTM이 XNU를 호출하고 처음에는 boot 실행 segment만 실행 가능하게
두며, XNU의 fixup 이후 권한 전환 서비스를 수행한다. 현재 x2=0 진단은 이
계약을 제공하지 않는다.
[SPTM startup ABI](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm64/sptm/start_sptm.s#L35).

SPTM bootstrap은 단순한 firmware blob이 아니다. 공개 XNU는 실제 root table,
physical aperture, bootstrap stacks, 공유 metadata, 사용 가능한 RAM 경계와
feature 일관성을 소비한다. SPTM이 이미 페이지를 사용했으므로 첫 자유 PA를
iBoot의 topOfKernelData와 별도로 받는다. 표와 scratch 공간을 0으로 채운
구조체로는 이 상태가 생기지 않는다.
[SPTM initialization](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm64/sptm/arm_init_sptm.c#L673).

| 정상 입력 계약 | 공급자와 검증할 일치 관계 | 현재 공백 |
| --- | --- | --- |
| 대상 구성 요소 묶음 | 선택 identity, KC/DT/monitor/trust 자료의 provenance와 명시한 부트 목적 | 바이트 선택은 확인; 실제 정책·신뢰 서비스는 별도 |
| 버전이 고정된 boot_args | 정확한 target layout, 실제 RAM 범위, DT 포인터/크기, 영상 backing, boot flags | 현재 codec의 공개 profile을 macOS 27 ABI로 보증하지 못함 |
| SPTM bootstrap | 살아 있는 allocator/MMU/page ownership 및 서비스가 만든 포인터와 범위 | target layout와 전체 live-state producer 미구현 |
| 초기 CPU·주소 공간 | 실제 entry VA, arguments와 stack 접근성, 레지스터/번역/PAC 상태, segment 권한 | M=0 bounded JIT는 정상 SPTM mappings를 입증하지 않음 |
| runtime DT | 실제 provider의 기기·메모리·부트 자료와 template 처리 결과 | 48개 template 미해결, 동적 runtime 입력도 별도 필요 |
| root filesystem·부트 정책 | 실제 storage, SSV/신뢰 자료, 정책과 선택한 OS의 일치 | KC prefix만으로 공급되지 않음 |

Apple은 iBoot가 AuxKC와 SSV 등 선택한 OS의 검증 및 로딩에 관여한다고
설명한다. 설치 패키지에서 KC를 고르는 작업과, 실제로 커널이 마운트할 볼륨·
신뢰 자료·부트 정책을 공급하는 작업은 별개다.
[Apple silicon boot process](https://support.apple.com/guide/security/boot-process-secac71d5623/web).

### boot_args profile의 추가 주의점

현재 Nextcore codec는 명시적으로 고정한 공개 XNU profile의 1024-byte
command line과 1152-byte LP64 구조를 구현한다. 그 profile의 공식 헤더에는
command-line 크기가 직접 정의돼 있다. 별도로 조사한 공개 XNU revision은
그 크기를 외부 iBoot ABI 헤더의 매크로에서 가져온다. Revision/Version의
숫자가 같더라도 모든 tail offset과 전체 크기를 자동으로 동일하다고 볼 수 없다.
이번 감사는 실제 macOS 27 크기가 달라졌다고 단정하지 않는다. 생산용 encoder를
연결하기 전에 **target에 맞는 헤더/ABI 근거와 독립 layout probe**가 필요하다는
의미다. 기존 SPTM SDK layout 차이 조사도 같은 이유로 참고 profile일 뿐이다.
[현재 codec의 공개 profile](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/pexpert/pexpert/arm64/boot.h),
[외부 iBoot ABI를 사용하는 공개 헤더](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/pexpert/pexpert/arm64/boot.h).

## 4. 48개 template과 runtime DT는 같은 완료 조건이 아니다

기존 firmware DT 원본과 통계 영수증의 해시를 다시 확인했다. 338개 node,
4289개 property 중 48개가 template이며 모두 기존 분석과 일치한다. private
inventory에서 이들은 제조·기기 identity, 네트워크 식별자와 주변 장치 calibration
성격을 포함한다. RAM·CPU provider 하나로 모두 해소할 수 있는 값들이 아니다.
실제 표현식과 기기별 값은 공개 코드나 이 문서에 옮기지 않았다.

또한 template을 해소하는 것만으로 runtime DT가 완성되지 않는다. 공개 XNU는
실제 DRAM과 커널 관리 메모리를 구분하며, 부트 인자의 DT 포인터·길이로 tree를
초기화한다. firmware가 런타임에 채운 메모리·영상·부트 정보를 소비한다. 현재
진단용 최소 DRAM tree는 전체 원본 runtime tree를 대체하는 정상 플랫폼 증거가
아니다.
[Platform initialization](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/pexpert/arm/pe_init.c#L383).

XNU runtime parser는 property 길이 전체를 경계 검증과 다음 property 계산에
사용한다. firmware template flag를 단순히 지우거나 표현식을 그대로 문자열
값으로 전달해서 성공으로 처리하면 안 된다. Nextcore의 현재 분리된 firmware
parser와 엄격한 runtime validator는 유지할 필요가 있다.
[XNU runtime DT parser](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/pexpert/gen/device_tree.c#L64).

## 5. 다음 구현 가능한 한정 작업

다음 데이터 작업은 **provider 결과를 받아 새 runtime DT를 만드는 독립적인
transactional materializer**로 좁힐 수 있다. 이미 있는 `firmware_dt`의
구조화된 입력을 사용하고 template 표현식은 계속 불투명하게 유지한다.

1. 각 unresolved property를 원본 hash와 안정적인 node/property 식별자로
   묶고, 공급자는 출처와 실제 값의 byte 형식을 명시한다. 임의 expression
   interpreter나 누락값의 0 대체는 만들지 않는다.
2. 변경하지 않는 literal은 보존한다. 공급자가 없는 template이나 중복·충돌
   입력이 하나라도 있으면 새 tree를 커널용으로 내보내지 않고 전체 미해결
   목록을 반환한다. 실패 시 원본과 출력 대상 메모리는 그대로 남겨야 한다.
3. 실제 MemoryService의 RAM/할당 snapshot에서 DRAM 및 예약 영역 자료를
   생성한다. 같은 snapshot으로 boot_args와 DT를 검증해 포인터·길이·범위가
   서로 다른 수작업 상수에서 나오지 않게 한다. 아직 없는 기기 backing을
   제공한 것으로 광고하지 않는다.
4. 독립 fixture에서 nested template, padding, 길이 변경, 중복, 공급자 누락,
   overflow, 잘못된 출처 hash를 검증한다. 성공 출력은 기존 runtime parser로
   다시 검사한다. 실제 x86 EFI의 authored ARM consumer가 MemoryService를
   통해 생성한 DT와 그 메모리 범위를 읽고 예상 값을 되돌리는 시험을 둔다.
5. 현재 원본은 실제 provider가 준비되지 않은 항목을 여전히 unresolved로
   보고해야 한다. 이 구현의 acceptance는 올바른 데이터 생성·거부·guest
   가시성이다. 정상 macOS boot acceptance나 target SPTM ABI 확정이 아니다.

이 작업은 BP30 메모리 provider와 이어지고, SPTM/PPL 양쪽에 필요한 공통
데이터 경로를 제공한다. 다음 실행 상태 작업은 여전히 native MMU와 정확한
초기 mapping·권한 계약이다. target ABI 근거가 확보된 뒤에만 살아 있는
메모리/서비스 snapshot으로 SPTM bootstrap encoder를 연결할 수 있다.

## 남은 명시적 미확인 항목

- macOS 27 대상 boot_args 및 SPTM bootstrap의 정확한 wire layout과 version.
- 해당 firmware가 실제로 공급한 초기 CPU/번역/PAC 상태와 monitor 서비스.
- 원본 DT의 제조·네트워크·calibration 값을 제공할 실제 backing과 동적 부트 자료.
- root storage, 정책·신뢰 자료, 정상 커널 초기화·사용자 공간·안정성 및 Metal.

현재 결과는 입력 선택 오류를 확인한 것이 아니라, 올바른 패키지를 골랐어도
정상 handoff에는 별도의 live-state producer가 필요하다는 계약을 구체화한 것이다.
