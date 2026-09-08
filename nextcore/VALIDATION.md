## BP34 dynamic-MMU integration checkpoint — 2026-09-09

ISE0d722886 and EFIed9ba255 are merged module heads. Standalone canonical builds
pass, including debug NXAPFS, conditional13/stage1108/DT8/dynamic6 and strict
capture readers. Separate immutable bundles preserve actual Arm6, native C/Rust6
comparison and authored EFI6 with a separately compiled omission negative.
The parent adds native/control/actual-EFI/reader/captured-comparison CI gates;
Fresh recursive750bda20 passes53commands: workspace502/Python149/GUI25, reference98/service44, actualEFI200 plus6separateCLI, strict DT28/dynamic30 controls, native capturedArm6 and13comparator regressions. Existing Clippy warnings remain. Full receipts are in artifacts/integration-bp34-20260909. Final canonical network verification and CI precede parent merge.
The earlier BP33 runtime/proofs are retained. No normal OS or guest Metal claim.

## BP33 owned-memory integration checkpoint — 2026-09-09

Final pins are Core147f4c4, EFI7e7a08b and Tool4bb09da. Core's UEFI-only software
SHA-256 selection corrects the actual debug LLVM failure exposed by the unchanged
NXAPFS all-features build. Core PR5 is merged; its fresh standalone tests and real
debug/release firmware code generation pass. Corrected canonical EFI passes debug NXAPFS and conditional13/stage1108/DT8.
Fresh recursivee0351bd passes47commands,502workspace/149Python/25GUI,194actualEFI
and6separateCLI,98reference/39service/119Vulkan plus native/oracle/package checks.
Core no-default232+3doctests and28DT reader controls pass. Clippy warnings remain.
Full receipts: [integration-bp33-20260909](artifacts/integration-bp33-20260909/README.md).

The original authored8-case DT capture and separate compiled wrong-mapping
failure are unchanged. Reader review corrected report-envelope and host-u64
omissions;28 malformed controls reject. Evidence is in
[guest-memory-dt-20260909](artifacts/guest-memory-dt-20260909/README.md).
The first recursive30a8e2e run stopped after a QEMU terminate/kill wait timeout
in the direct-bypass harness; no complete-suite pass is attributed to it.
Normal macOS boot, EFI GPU and guest Metal remain unverified.

## BP32 implementation checkpoint — 2026-09-09

ISE720d7c6 has passed final standalone source tests and module PR6 CI; it is
merged as91721d0. EFI8d53dd2 pins it for both native sources and the Rust service.
Fresh parentdf60198b passed41commands:476workspace/149Python/25GUI/98reference,
186actualEFI plus6CLI rejections, native/Arm/Vulkan/package regressions. Final
EFIf3f7938 changes only docs/metadata from tested8d53dd2 and passed module CI;
final parent network checkout/CI is required before merge. Clippy warnings remain
visible. Full receipts are in artifacts/integration-bp32-20260909.
Historical authored native/EFI and independent Arm replay evidence retain their
own provenance in artifacts/arm-stage1-{native,oracle,service-comparison}-20260909.
The capture overlay distinguishes32 completion-state fetch comparisons from
actual target-state evidence. Normal macOS boot and guest Metal remain unverified.

# NextCore 재개 검증 — 2026-09-09

2026-09-07 작업의 통합 설명과 artifact index는
`artifacts/NEXTCORE_SESSION_REPORT_20260907.md`에 있다.

## BP31 — 조건부 비교 명령어

[새 재귀 통합 결과](artifacts/integration-bp31-20260909/README.md): baseline8bcf5c52에서
workspace476/Python149/GUI25/참조93, 실제 x86 EFI78개 및 별도 CLI6개 통과.
f38a2c30의 provider 필수 판정은 별도13개 성공/실제 우회 거부1개로 추가 검증했다.
이후 최종 CI에서는 새 통합 바이너리에 필수 provider 판정을 적용한다.

ISE0aabf085의 CCMP/CCMN reg/imm5 및32/64-bit 구현과 EFI7495633 연결을 각각
모듈 PR #5로 병합했다. 독립 ISE 클론의 native34264경우/137070assertions,
참조93개, Arm3668개와 native/provider/PAC/MMU 회귀 검사가 통과했다.
새 standalone EFI는 빈 Cargo cache에서 정식 의존성으로 빌드됐고 실제 combined
바이너리에서13개 authored 조건부 비교 사례가 통과했다.
[역사적 실행과 원본 aggregate](artifacts/arm-conditional-compare-20260909/README.md)는
별도 source/binary/hash로 보존한다. 원본은최대4096명령/1205blocks 예산으로 종료했다.
현재 소스를 받는 상위 EFI runner는 runtime hash와 실제 결과를 다시 기록하며,
기존65개 실제 EFI 사례에13개 조건부 비교 실행을 더한다. 상위 재귀 통합은 별도 검증한다.

## BP30 — 실제 EFI 메모리 서비스와 서브모듈 연결

[새 재귀 통합 검증](artifacts/integration-bp30-20260909/README.md)은 구현 commit
`ea0a62e8`에서476개 workspace,149개 Python,25개 GUI,91개 참조,158개 ARM 오류 대조와
실제 x86 EFI65개/별도 CLI 거부6개를 통과했다. native/provider/ABI, Vulkan119개,
no_std 빌드, 펌웨어 패키징과 Clippy도 통과했다. 최종 증거 커밋은 별도 원격 검증한다.

별도 no_std 서비스는 ISE 모듈의 정식 Git 소스로 유지한다. native C 진입은 guest RAM
포인터를 받지 않고, 모든 fetch/scalar/pair 접근을 Rust 콜백으로 전달한다. 요청/응답/결과는
80/80/192-byte ABI이며, 쌍 전체 범위를 검사한 뒤에만 메모리를 수정한다. 지원하지 않는
backing과 callback 오류를 실제 guest abort로 꾸미지 않는다. 기존 직접 실행 경로와
native SCTLR.M 차단은 유지한다.

- [초기 실제 EFI provider 검증](artifacts/arm-memory-provider-20260909/README.md):
  23개 일반·경계 사례, 실제 callback 오류1개와 direct 우회 음성 대조군.
- [합쳐진 EFI의 독립 canonical 빌드와 재실행](artifacts/arm-memory-provider-combined-20260909/README.md):
  빈 Cargo Git cache, 부모 patch 없이 정식 원격 의존성/보조 패키지를 해석하고5개 빌드
  및 같은 실제 실행 경계를 검증했다. 별도 변형 오류 바이너리를 정상 빌드와 구분한다.
- [명시적 진단 예산](artifacts/arm-tiered-trace-20260909/README.md): 기본64/8 API를
  유지하고 opt-in만256/1024/4096을 허용한다. 원본은98명령/14blocks 뒤 CCMP에서 멈췄다.
  이 원본 실행은 역사적 scalar/tiered 바이너리로 분리돼 있다.

상위 runner는 기존 직접 경로39개와 별도로 provider23개, 실제 tiered2개 및 직접 우회1개,
CLI 거부6개를 재현한다. 임의 child exit1만으로 음성 대조를 성공 처리하지 않으며 실제
실패 receipt와 입력 hash를 검사한다. 최종 상위 commit의 새 재귀 검증 기록은 별도로 남긴다.
정상 macOS 부팅, native MMU, 사용 가능한 데스크톱과 guest Metal은 아직 미완료다.

## BP29 최신 검증 — x86 EFI의 ARM64e scalar 메모리

BP28 상위 PR #10과 변경된 5개 모듈 PR #2는 모두 main에 병합됐다.
BP29 ISE는 정수 scalar 13종과 상세 MMU 실패 API를 구현했다. 기존 walker의
비정상 VA 분류와 cold/cached 실패 주소 차이도 독립 ARM 대조로 수정했다.
새 독립 ISE 클론에서 package 26개·참조 91개 테스트, native scalar 106,496경우/
426,981assertions, 기존 PAC/IRQ/pair/C↔Rust ABI 검증이 통과했다. AT/PAR 118개와
실제 EL1 abort 40개의 원래 제어값·페이지테이블을 실제 Rust walker에 전달해
158개 결과와 오류 대조군까지 일치했다. 자세한 결과와 재현기는 ISE 모듈의
`tools/mmu_fault_levels`에 있다. native SCTLR.M은 아직 허용하지 않는다.

[실제 x86 EFI scalar 증거](artifacts/arm-scalar-memory-20260909/README.md)는
11개 자체 작성 입력으로 정수 13종, Device/SP 정렬과 unsupported 처리를 검증한다.
고의로 부호 확장을 잘못 실행한 입력도 실제 EFI 결과에서 거부했다. 이 EFI는
원래 고정 scalar 커밋8b09f876으로 빌드했고, 통합 ISE33fea9f의 연결 소스12개가
동일하다는 대조를 별도로 보존한다. 통합 커밋d45b107d의 EFI도 새 빌드·재실행으로39개 authored 검사를 통과했다.
[전체 통합 결과](artifacts/integration-bp29-20260909/README.md)는472개 workspace
테스트,91개 참조 테스트,158개 실제 ARM 입력 대조와 각 실행 명령을 보존한다.
원본 macOS27 진입 진단은 47명령에서64명령/12native blocks로 진행했고,
설정된 진단 예산 때문에 정지했다. 이 지점이 미지원 명령이라는 주장은 하지 않는다.
[원본 aggregate 결과](artifacts/arm-original-prefix-bp29-20260909/results.json)에는
원본 바이트나 실행 좌표가 없다.

정상 macOS 부팅·사용 가능한 데스크톱·게스트 Metal은 미완료다. BP30에서는
JIT의 Rust 메모리 서비스 연결과 별도 명시 opt-in 진단 예산 확장을 진행한다.
아래 내용은 이전 검증의 역사이며 현재 구현/호스트 상태는 이 BP29 요약을 따른다.

## 현재 상태와 원하는 상태

첨부 세션의 우선순위인 APLS 실행과 QEMU/OVMF 검증을 병렬로 이어서 실제
프로세스/펌웨어까지 연결했다. 외부 reference와 native NextCore production EFI
provider 경로 모두 실제 Tahoe XNU, userspace와 읽을 수 있는 Recovery GUI를 확인했다.
native 경로의 restore-datapartition panic은 VM RAM 조건을 수정해 통과했다. 자체 KC loader 진입,
전체 native HAL, macOS 전체 부팅과 Metal은 아직 완료되지 않았다.
`docs/NEXTCORE_BUILD_PLAN.md`의 각 BP가 실행 계약이며 해당 시점의 진척은 아래 BP21/BP22에 보존한다.

## BP21/BP22 최신 통합 — 2026-09-08

- **최종 BP21 → 실제 Tahoe Terminal 통합**: 보관된 최종 EFI `8d29af21…0e96`를
  재빌드 없이 사용해 GOP 피커→Enter→기존 Shell/HFS helper→원본 booter→언어 선택→
  Recovery Utilities→Terminal을 실제 조작했다. `uname -a`와 `sw_vers`는 x86_64
  Darwin 25.6.0/macOS 26.6.2/25G83을 출력했다. QEMU 329.1601초에 QMP quit 뒤
  자연 exit0, 전체 감독 344.0045초, 잔여 프로세스 0이다. 기존 9개 입력과 모든
  신규 실행 입력의 전후 hash가 일치하고 ESP 차이는 BOOTX64/config뿐이다.
  [결과](artifacts/picker-native-recovery-20260908/result.json)와
  [자체 피커 화면](artifacts/picker-native-recovery-20260908/picker.png)을 보존했다.
  전체 설치 OS·native HAL·guest Metal은 이 복구 세션의 수용 범위에 포함하지 않는다.
- **EFI 피커·브랜딩**: GOP dark/mint tile, 동일 volume의 명시 EFI 항목,
  방향키/Tab/Home/End·Enter·Esc 및 text fallback을 구현했다. 실제 OVMF에서
  두 번째 child와 UTF16 load options, 취소, 기존 auto boot, GOP 없는 fallback을
  검증했다. core 153개 및 독립 crate 복사 153개, Python policy 28개 통과.
  최종 EFI SHA256 `8d29af2199999967145cd23145401c342294288366d17b6fcebc6bf02df00e96`.
  공개 이미지 `resources/branding/nextcore-picker.png`는 실제 OVMF 화면이다.
  제품 표기는 NextCore로 통일했고 외부 부품의 실제 이름/출처/라이선스는 보존했다.
- **Tahoe native 복구 GUI**: 이전 2GiB VM이 2.5GiB tmpfs 요청을 충족하지 못한
  로그를 근거로 RAM만 8GiB로 올려 launchd/WindowServer까지 진행했다. SMC 추가 뒤
  no-USB 화면은 210초에도 입력 pairing 안내였고 텍스트는 정상이다. USB keyboard/
  tablet만 추가한 fresh COW에서는 언어 선택→Recovery 메뉴와 실제 입력이 통과했다.
  이는 기존 BP20-J EFI를 사용한 조건 대조이며 새 BP21 EFI 직접 macOS 검증과
  섞지 않는다. 원본·COW·QMP 수명 증거는 `_isolated/nextcore/native-userspace-recovery-20260908/`.
- **실제 guest Metal 실행**: 외부 reference의 Tahoe 26.6.2/25G83 Recovery Terminal에서
  13,136B x86 probe가 start→no-metal-device를 기록하고 exit1로 종료했다. guest가
  실행 파일을 새 파일로 복사했고 host 전체 SHA256이
  `eae69343a05e096eb2299b6c92e3a15a15b20123d9b23eac346e56cd6e50791b`와 일치했다.
  전체 NDJSON/exit/version/파일 readback은 격리에 있다. Metal device·compute·readback
  성공은 false다. 공식 full installer 검증 후 전체 OS/driver 경로를 진행 중이다.
- **BP22-C ARM64 boot_args**: 공개 XNU의 별도 1152B LE wire, checked PA/KVA·DRAM·DT·
  NUL/overlap 검사와 15개 tests를 구현했다. 실제 C LP64 sizeof/offsetof와 Darwin ARM64
  compile, no_std 통과. [공개 계약](artifacts/arm64-boot-args-contract-20260908/README.md).
- **BP22-D ARM64/ARM64E KC**: 명시 CPU/subtype·단일 ARM thread subset·4B entry 범위를
  검사하고 Intel 기본 API를 유지한다. 16KiB span의 host staging은 outer 소유 byte와
  모든 member view를 전량 대조하며 chain/PAC를 적용하지 않는다. 실제 27 원본
  81,002,496B/7 outer segments/216 headers/1,096 views, 중복 view 비교 총
  3,463,261,621B가 6.594초에 통과했다. 원본과 실행 도구 hash 전후가 같다.
  원본 주소·metadata는 격리에 보존한다. host 배치는 guest 물리 배치나 진입이 아니다.

사용자는 검증된 진척의 로컬 commit과 push·원격/조직 최신화를 승인했다.
본체는 PR/CI, 독립 모듈은 기존 history와 release tag를 보존하는 방식으로 반영한다.

재개 시 존재하던 7-crate workspace와 dirty 변경을 보존했다. 초기 실행 당시의
로컬 제외 정책과 달리 현재 Nextcore 소스는 Git 추적 대상이며 `nextcore/target/`과
`nextcore/artifacts/`는 제외된다. BP19에서는 추적 정책을 변경하지 않았다.

## BP24 APFS Jumpstart 실행 (2026-09-08)

공개 APFS 형식의 bounded read-only parser를 추가했다. 23개 합성 경계·손상 입력
검사, 독립 C의 24 offsets/4 checksum vectors, UEFI no_std 및 소유 코드의 strict
검사가 통과했다. 명시 NXAPFS helper는 기본 추출/전량 재읽기와 `--start-driver`를
분리하며 기존 BOOTX64/picker 동작을 유지한다.

실제 OVMF 6개 경우에서 기본 모드, 자체 resident driver, application 거부,
NXSB/JSDR checksum 오류와 중복 APFS를 검증했다. 전체 guest-visible disk와 ESP
readback, QMP 자연 exit0 및 process cleanup이 모두 통과했다. 증거 변조를 거부하는
Python 9개 검사도 통과했다. [합성 runtime receipt](artifacts/apfs-ovmf-20260908/result.json).

완료된 첫 설치 snapshot을 각각 새 COW로 열어 원본 APFS driver **745,080B**를
전량 추출·재읽기했다. 다음 실행에서는 실제 driver StartImage와 ConnectController가
SUCCESS를 반환했고 NextCore parent도 console lease를 해제하고 SUCCESS로 돌아왔다.
전체 60.6816초(실행 supervisor 4.1393초), 원본 9개 hash와 ESP 파일 유지,
QMP exit0/잔여 process0을 확인했다. [원본 실행 결과](artifacts/apfs-firmware-20260908/original-apfs-result.json).
드라이버 원본 byte는 공개에 넣지 않았으며 root 열기·설치 OS·Metal은 별도 단계다.

PR #7의 exact head `8f21c876757dc571c4e09b36a779e6239dec15a1`에서 전체 원격 CI와
신규 `apfs-firmware` run `34200621847`이 통과했다. 이 CI는 EFI를 다시 빌드하고
6개 합성 OVMF를 실제 실행한다. main `65d1e85`로 merge했고 관련 module 배포를 진행한다.

### BP24-B 실제 APFS root 관찰

명시 `--inspect-filesystems`의 NXAPFS r1 `1e63c89b…ec725`를 완료된 첫 설치 snapshot의
별도 COW에서 실행했다. SFS 6개 중 선택한 APFS partition의 정확한 node 후손 4개를
열어 root GetInfo와 전체 root Read/EOF를 확인했다. 4 records/8 Read 호출,
metadata 응답 17,240B이며 모든 root Close·protocol Close·parent cleanup/return이
SUCCESS다. supervisor 2.8096초, 전후 검증 포함 56.3239초, QMP 자연 exit0와
잔여 process0, 입력 9개 SHA256와 ESP 파일 유지가 통과했다.
[공개 집계 결과](artifacts/apfs-filesystems-20260908/original-result.json)에 정확한
binary·격리 receipt hash를 기록했다. 원본 파일명/volume ID/경로·로그는 격리한다.
이는 APFS 파일시스템 접근 성공이며 APFS에서 booter 실행·설치 OS/Metal 성공은 아니다.

PR #8의 exact head `c6ac2c6ea34e24dfebb419de00af2638e58554a2`에서 전체 CI와
`apfs-firmware` run `34202928667`이 통과한 뒤 main `416926c`로 merge했다.
이 원격 firmware 검사는 7개 실제 authored OVMF와 순수 parser/C layout을 실행했다.
다음 BP24-C는 설정의 명시 `ApfsVolume`을 실제 picker load 경로와 연결하는 작업이다.

## BP23 원격 동기화 (2026-09-08)

후속 APFS module release는 고정 main `65d1e85`에서 Core/EFI v0.1.2와 Tool
v0.1.3을 게시했다. 독립 Linux single-parent clone의 전후 gate와 exact-head
main/tag CI 모두 통과했고 기존 tag를 보존했다. Core 203 tests/APFS 23/no_std,
EFI all-feature check/NXAPFS 실제 link, Tool 17 passed/1 ignored다. 변경 없는
GPU/HAL/ISE/APLS는 v0.1.1을 유지한다. 조직 profile `440e6a9`의 원격 byte readback과
7개 repository 최종 ref audit도 통과했다.
[후속 release receipt](artifacts/module-release-apfs-20260908/release-receipt.json)를
보존한다. 해당 고정 release에는 이후 BP24-B 파일시스템 관찰 변경이 들어 있지 않다.

PR #5의 head `ee04ddad4d7cbba8033df1d48082a513b931e43d`에서 모든 원격 검사가
통과한 뒤 main `06262cb970ef482415493e9f5f9a32c05476dc9c`로 squash merge했다.
Pages run `34197153249`의 build/deploy도 성공했다. 실제 배포 페이지 검사에서
홈 버튼 3개와 제외된 wiki Home 링크의 404를 확인해 수정했다. PR #6은 전체
CI 통과 후 main `1cf2b989ecbb36773fc33b8b96ae91b7e2d33cca`로 반영했고 Pages
run `34199199279`도 성공했다. 실제 배포의 4개 진입 페이지 title/버튼 URL과
47개 내부 페이지·asset의 HTTP 200을 확인했다.
[배포 readback](artifacts/docs-publish-qa-20260908/live-deployed.json)을 보존했다.

독립 module 6개는 v0.1.1, Tool은 v0.1.2로 게시했고 최신 7개 모두 원격 main/tag
일치, 게시 전후 fresh-clone gate, exact-head GitHub CI를 확인했다. 최초 Tool
v0.1.1의 실패와 태그는 보존한다. 수정판은 sibling checkout이 없는 Linux 단독
clone에서 실제 all-target 검사를 통과했다. 조직 profile `4e446a4`의 NextCore
브랜딩과 release link도 원격 API readback을 마쳤다.
[release receipt](artifacts/module-release-v011-20260908/release-receipt.json)에
각 source/parent/tag/CI와 보존한 실패를 기록했다. guest Metal 상태는 변하지 않는다.

## BP20 대상별 실제 실행 (2026-09-08)

사용자 확정 목표: **macOS 27 Golden Gate — AMD64↔Apple Silicon HAL,
Metal 가속 필수**, **macOS 26 Tahoe — 네이티브 HAL**. 현재 어느 경로도
XNU/userspace/Metal 전체 수용 조건을 통과하지 않았다.

사용자는 실기기 접근 대신 이 컴퓨터에서 개발을 계속하도록 지정했다. 현재 WSL의
VT-x와 설치된 KVM 모듈을 확인한 뒤 `kvm_intel`을 적재하고 기존 developer 사용자에게만
`/dev/kvm` 접근 ACL을 주었다. 재부팅 없이 **KVM API 12, query-kvm enabled=true,
실제 OVMF Shell 실행**을 확인했다. 3.1837초, QMP quit의 정상 exit 0, 원본 firmware
해시 유지 및 프로세스 회수를 확인했다. 이전 `/dev/kvm` 부재만으로 이 PC의 KVM을
불가능으로 분류한 판단은 정정한다. 상세는 `artifacts/local-kvm-20260908/README.md`다.

### EFI 로더 및 Tahoe 입력

- Apple 공식 복구 다운로드를 chunklist 검증한 결과 실제 입력은
  **macOS 26.6.2 / 25G83, x86_64**다. 960,530,321-byte BaseSystem DMG,
  실제 PE32+ EFI application과 67,584,000-byte MH_FILESET BootKC를 확인했다.
  상세 메타는 `artifacts/boot-media-candidates-20260908.md`에 있다.
- 실제 booter를 Nextcore가 `LoadImage`/`StartImage`한 첫 실행은 `ABORTED`로
  반환했다. HFS 전체 복구 볼륨을 fresh COW로 제공하고 외부 UEFI Shell/HFS
  드라이버로 비교해도 초기 booter 설정 조회가 `NOT_FOUND`로 실패했다.
  파일 복사만의 문제로 단정하지 않으며 XNU 전 boot/platform 계약이 미충족이다.
- Shell 출력 리다이렉션으로 실제 Apple child의 전체 콘솔을 격리 보존했다.
  Apple 원문 로그·화면·매체는 `_isolated/nextcore/intel-recovery-20260908`에만
  있고, 공개 결과는 `artifacts/tahoe-efi-observation-20260908.json`이다.
  6개 시도의 원본 입력 hash가 모두 유지됐다. 두 초기 관측의 2 MiB screenshot
  cap/host SIGXFSZ 및 read-only IDE 거절도 실패로 기록했다.

### Tahoe 외부 reference의 실제 XNU 실행

Nextcore→외부 OpenShell/OpenCore 1.0.7→서명 검증된 복구 DMG 경로에서 CPU0의
CPL0 실행 위치를 정지 관측했다. **185.40초의 PC 256바이트가 원본 KC의 kernel
member executable segment와 유일하게 일치**했고 후속 관측도 같은 trap 상태였다.
실행은 298.05초의 제한 종료와 원본 해시 유지, 프로세스 회수로 끝났다. 이 결과는
`external_reference_xnu_executed=true`이며 native Nextcore provider 완료와 구분한다.

실제 panic stack은 type 13 #GP이고 fault 위치는 시간 초기화의 MSR 읽기다.
공개 XNU/QEMU 코드의 VMM 주파수 전달 조건을 확인한 뒤 host CPUID invariant TSC와
`Haswell-v4,vendor=GenuineIntel,invtsc=on,enforce=on` KVM/OVMF probe를 검증했다.
probe는 3.2948초에 정상 QMP 종료했고 원본 해시가 유지됐다. 추정 주파수, kernel
patch 또는 host `ignore_msrs` 변경은 사용하지 않았다.

정확한 initial NVRAM의 `-v serial=3 serialbaud=115200 debug=0xA`를 실제 booter가
소비한 후속 실행은 커널 배치 요청이 EFI ACPI NVS/BootServicesData와 겹쳐 XNU 전
멈췄다. 242.7352초에 QMP로 종료하고 입력 해시/정리를 확인했다.

동일조건 fresh 재시도는 배치 및 이전 TSC #GP를 통과했다. 185.35초에 실제 kernel
PC 256바이트를 다시 원본과 매칭했고, 다음 MCA 초기화의 Haswell pre-C0 stepping
거부 패닉을 확인했다. QOM의 실제 frequency는 3,264,001,000 Hz, CPU identity는
family 6/model 60/stepping 1이었다. 이 값은 VM 속성 관측이며 guest의 frequency
출력과 구분한다. 실행은 298.03초에 정리됐고 원본 해시가 유지됐다. 공개 MCA
consumer의 stepping >=3 조건에 따라 `stepping=3`만 추가한 다음 실행을 진행한다.

stepping 3 실행에서는 **launchd PID 1, recoveryosd의 실제 복구 작업 실행과 세션
초기화**가 관측됐다. `external_reference_userspace_verified=true`다. 뒤이어
AppleIntelMCEReporter 115.0이 CMCI 부재를 보고하고 PID 0에서 page fault를 냈다.
원본 BaseSystem KC와 대조한 backtrace/레지스터는 controller 초기화 실패 후 정리
경로의 null 기반 읽기와 일치했다. 실행은 298.06초 제한 종료/정리됐고 입력은
변하지 않았다. 화면은 커널 콘솔이므로 GUI·guest Metal은 미검증이다.

읽기 전용 KVM ioctl은 최대 32 banks와 `supported_mcg_cap=0x9000500`을 반환해
CMCI 지원을 확인했다. QEMU 기본 MCG_CAP은 이를 노출하지 않는다. 격리된 QEMU의
default-off `x-cmci` 구현은 실제 guest CTL2 write/read 및 자체 KVM guest의 CMCI
인터럽트 전달을 통과했다. TCG/미지원 CPU/LAPIC 조건은 거부하고 migration을 막는다.

동일 signed recovery에 적용한 다음 실행은 **이전 CMCI/MCEReporter 패닉을 통과**했다.
원본 XNU의 CMCI consumer와 실제 반환 저장값, idle PC 256바이트 일치를 확인했고
launchd PID 1, recoveryosd PID 65, WindowServer PID 81이 실행됐다. 298.0839초
제한 종료와 원본 hash/정리를 확인했다. 마지막 1280×800 화면은 검정이므로 GUI와
Metal 성공은 아니다. AHCI Port 2 abort는 같은 토폴로지의 정지 QMP 열거에서
자동 생성된 빈 `ide-cd`에 대응했고 원본 복구 디스크는 Port 1이었다.
상세 계약·증거는 `artifacts/tahoe-cmci-contract-20260908.md`와 signed-DMG 결과다.

native booter의 초기 설정 조회 실패도 별도 대조했다. 공개 HW_BID 길이/속성과
firmware feature 변수의 실제 readback을 맞춰도 초기 실패는 유지됐다. 외부 reference는
DataHub record publication과 SMBIOS replacement를 둘 다 꺼도 초기 image-load 경계를
통과했다. 기존 OVMF SMBIOS와 다른 protocol/provider는 남아 있으므로 native provider
구현의 인과 근거를 계속 좁힌다.

추가 실제 LocateProtocol 관측에서 마지막 누락은 공개 EFI ConsoleControl이었다.
고정 FAT 디스크의 제어군과 실제 Text/system GOP 정보를 제공한 case를 비교했다.
출력 리다이렉션을 제거한 case 화면은 원본 KC 읽기 성공과 **EXITBS:START**를
보였고 동일 무제공 제어군은 초기 ICM/ABORTED로 반환했다. GetMode 1회 SUCCESS,
SetMode/LockStdIn 호출 0회다. 진단 hook은 production에 넣지 않으며 BP20-J의
독립 provider로 연결했다. 이 초기 A/B의 범위는 EXITBS:START이며 이후 production
경로의 XNU/초기 userspace 결과는 아래 BP20-J가 갱신한다.

공개 증거는 `artifacts/tahoe-signed-dmg-selection-20260908.md`,
`artifacts/tahoe-vmm-frequency-contract-20260908.md`,
`artifacts/local-kvm-invtsc-20260908/report.json`,
`artifacts/efi-platform-next-step-20260908.md`다. 원본 CPU bytes, 주소, stack,
Apple 로그와 매체는 격리 receipt에만 있다. native HAL, macOS 전체 부팅과 guest Metal은 false다.

### BP20-A StartImage 종료 데이터

`uefi` wrapper가 버리던 표준 UEFI ExitData를 Nextcore에서 제한 길이로 읽고
escape하며 FreePool로 해제한다. 반환 status는 그대로 유지한다. 실제 Apple
child에 적용한 결과는 **ABORTED, exit data 0 bytes/null**이었다.

- release EFI build 성공, 자체 저작 child의 실제 OVMF **8/8** 통과.
  정상/오류 반환, null/빈 문자열, 제어문자, 긴 문자열, binary suffix를 포함한다.
- 독립 검토에서 발견한 하네스의 비정상 QEMU 종료 허용과 deadline 시 receipt
  유실을 수정했다. 집중 테스트 **7/7**, 기존 raw/receipt 최종 재검증 **8/8**,
  각각의 SIGXFSZ 변조 **8/8 거부**. 이 변경 뒤 VM을 중복 실행하지 않았다.
- 최종 EFI SHA-256:
  `24933c66f5f1028054fef319232a4cd7faa306c4827c6e090d8a9f5e47a7233d`.
  `artifacts/exit-data-bp20a-20260908/build-receipt.json`,
  `final-ovmf/report.json`, `harness-review-revalidation.json`이 증거다.
- `tools/verify_exit_data_ovmf.py --efi <BOOTX64.efi> --child <NXTEST.efi>
  --output <fresh-dir>`로 재현한다. 정상 child도 firmware로 돌아오므로 QEMU의
  bounded stop을 자연 종료로 주장하지 않는다.

### BP20-B 실제 host GPU와 외부 게스트 장치

공식 Mesa 25.2.8의 dzn을 전역 설치 없이 빌드하고 WSL D3D12를 통해
**Intel 8086:7D41 integrated GPU**를 선택했다. 공개 Nextcore
`ComputePipelineManager::with_vulkan`로 서로 다른 두 입력 세트를 upload/dispatch하고
**512개 결과**가 모두 일치했다. offset 16의 buffer view 앞뒤 보호 영역 유지와
실제 Vulkan fence 완료 후 readback, 프로세스 자연 종료 0을 확인했다. CPU
llvmpipe fallback은 사용하지 않았다. 이 결과는 Vulkan 전 기능 적합성이나
macOS Metal 성공을 뜻하지 않는다.

binding 불일치, LocalSize 불일치, 잘못된 SPIR-V 명령 3종은 host buffer 변경이나
가짜 fence 완료 없이 거부됐다. 별도 잘못된 device selector 실행도 CPU fallback
없이 exit 1로 끝났다. 성공/오류 dispatch 실행은 0.5098초였고 원본 입력 해시와
프로세스 정리를 확인했다. 공개 API는 optional `vulkan` feature이며 standalone
crate 빌드가 격리 파일에 의존하지 않는다. 증거는
`artifacts/vulkan-manager-bp20b-20260908/build-receipt.json`, `final-runtime/report.json`이다.

기본 compute backend와 미연결 VirtualMetalDevice/SGPU는 미실행 명령을 성공으로
반환하지 않도록 고쳤다. SGPU의 shader/clear/present는 지원되지 않으며 전체 명령
목록을 검증한 뒤 software copy만 수행한다. 부분 copy와 성공 응답이 생성되지 않는
transport 회귀 검증을 추가했다. 실제 Vulkan manager API와 별도 경로임을 유지한다.

외부 Reims QEMU 11.1.0에서도 TCG/shared memfd/OVMF를 실제 실행해 PCI 자원
배정과 GOP 공존을 확인했다. Vulkan 초기화는 guest draw 시 수행되는 구조여서
이 펌웨어 실행에서는 dzn/D3D12가 열리지 않았다. guest driver/Metal 작업 제출은
아직 미검증이다. 상세 명령·해시는 `artifacts/graphics-runtime-path-20260908.md`.
독립 Vulkan 코드 검토에서는 추가 확정 결함을 발견하지 못했다. fence timeout 시
진행 중 객체/loader를 보존하며 driver 호출 전체 deadline은 외부 supervisor가 맡는다.

### BP20-C native Tahoe KC 준비 검사

공개 XNU/dyld 포맷에 근거한 별도 core `inspect_kernel_collection` API와
`inspect_kc` example을 구현했다. 실제 67,584,000-byte 입력을 읽기 전용으로
검사했고 **204개 member, 621개 outer segment, format 11 chained fixup,
65,260개 local relocation**을 확인했다. outer entry와 nested kernel entry를
혼동하지 않으며 outer LC_MAIN은 지원 밖으로 거부한다.

이 검사는 파일/VA/명령/section/fixup 시작점 범위와 메타데이터만 검사한다.
placement, classic relocation, chained rebasing, platform provider 및 entry ABI가
남으므로 `preparation_ready=false`다. NXKERNEL 입력 제한과 실행 guard는 유지했다.
자체 저작 KC 경계 테스트 16/16, 전체 core 87/87와 no_std check를 통과했다.
전체 strict clippy는 기존 파일의 두 lint 종류 때문에 실패했고, 해당 기존 lint만
허용한 검사에서는 새 코드 경고가 없었다. 계약은
`artifacts/kc-metadata-contract-20260908.md`, 실제 KC 상세는 격리 receipt에 보존했다.

### BP20-D 실제 native KC 메모리 배치

별도 `KcStagingPlan`이 source를 immutable borrow로 묶고 outer segment만 복사한다.
호스트의 **67,584,000-byte arena**에 67,575,808바이트를 복사하고 8,192바이트의
hole을 zero/readback했다. 실제 입력의 outer zero-tail은 0이며, 자체 fixture에서는
tail·unaligned range·공유 member tail·잘못된 범위·변조를 별도로 검증했다.

620개 nonempty outer mapping, 204개 member header와 826개 member segment view가
일치했다. 공유 linkedit 때문에 member 비교량 2,679,621,441바이트는 중복 포함이며
고유 메모리 크기가 아니다. release example은 **0.84초, 자연 exit 0**, 원본 입력과
실행 파일 해시 유지 및 프로세스 회수를 확인했다. core all-targets **98 passed**와
no_std UEFI check를 통과했다. 공개 근거는
`artifacts/kc-staging-bp20d-20260908/build-receipt.json`, 실제 입력 receipt는
`_isolated/nextcore/kc-staging-bp20d-20260908/final-runtime/report.json`이다.

이 결과는 호스트 배치다. EFI physical placement, relocation 적용, XNU/native HAL
실행은 false이며 BP20-E에서 classic/chained 대상의 읽기 전용 검증을 이어간다.

### BP20-E 실제 KC 재배치 대상 검사

새 read-only audit는 **classic 65,260개와 format 11 chain 401,606개**, 합계
**466,866개**의 전체 쓰기 범위를 확인했다. 1,201개 chain이 모두 종료했고 중복
쓰기·미지원 encoding·외부 cache·범위 오류는 0개였다. 원본과 실행 파일 hash가
유지됐고 실제 release example은 9.1556초에 자연 exit 0, 전체 receipt는 13.0375초에
완료됐다. 실행 파일 SHA-256은
`60988fa5474ccf79384eaee6246287d135d20889ca80a75a425cc221a1fc7467`이다.

초기 검사의 페이지 경계 오류 5개는 원본 이상이 아니었다. 공개 dyld producer가
시작 주소로 page를 분류하므로 마지막 비정렬 8-byte word가 다음 page에 걸칠 수
있었다. 시작/다음 시작의 page 범위와 word 전체의 segment/file 범위를 분리해
검사하도록 고쳤고, metadata의 첫 word 경계에도 같은 수정을 적용했다. 자체 저작
single/successor straddle, 잘린 segment, page 밖 next와 겹침 회귀를 통과했다.

core **120 passed**, focused audit/metadata **38 passed**, no_std UEFI 및 모든 기존
EFI bin check가 통과했다. 공개 build/source/aggregate 근거는
`artifacts/kc-fixup-audit-bp20e-20260908/build-receipt.json`, 독립 통합 검사는
`artifacts/bp20e-integration-20260908/report.json`이다. 실제 decoded 목록은 격리에만
있다. 재배치 적용·실행 소유권·EFI 배치·준비 완료는 이 검사만으로 승인하지 않는다.

### BP20-F 실제 EFI KC page 소유권과 배치

새 `LoadedKernelCollection`과 명시적 `NXKC` bin이 같은 staging plan을 실제
UEFI AllocatePages/FreePages에 연결했다. 실제 Tahoe 입력을 **16,500 LoaderData
pages = 67,584,000바이트**에 배치하고 전체 arena, 204개 header와 826개 member view를
readback했다. 이후 FreePages SUCCESS와 다른 할당 전 ConventionalMemory coverage를
확인했다. source와 destination의 비중첩, raw memory-map stride/range/중복·hole도 검사한다.

실제 Q35/TCG OVMF는 **10.7938초에 자연 exit 87**, 전체 검증은 12.5301초였다.
원본 입력·EFI·firmware 및 복사본 hash가 같고 프로세스 정리가 완료됐다. 별도 자체
fixture와 destination 손상→실제 readback 거부→RAII drop 시험도 통과했다. host gate는
explicit/drop 모두 FreePages 및 직후 memory-map 결과가 SUCCESS일 때만 승인한다.

NXKC SHA-256은 `5e2fc6be99c60ea8a76d5a72d0c3a2f95bfc155e7c7b86554e0ea2897189a6b3`.
공개 계약·코드·fixture 근거는 `artifacts/kc-efi-staging-contract-20260908.md`와
`artifacts/kc-efi-staging-bp20f-20260908/`, 실제 입력 receipt는
`_isolated/nextcore/kc-efi-staging-bp20f-20260908/actual-ovmf/report.json`에 있다.
이 결과는 실제 EFI physical staging이다. KC 진입 주소/slide를 추정하거나 instruction을
실행하지 않았고 ExitBootServices, fixup 적용, native HAL 완료 판정은 그대로 보류했다.

### BP20-G KC boot_args revision 1

별도 `encode_fileset_boot_args`가 실제 caller가 준 physical header 범위와 slide를
version 2/revision 1로 기록한다. header 전체가 낮은 kernel 소유 범위 안에 있고
map/DT와 겹치지 않는지 검사한다. 기존 revision 0 encoder와 EFI 진입 guard는 유지한다.
주소 배치나 slide 정책, fixup 적용과 provider 준비는 이 codec의 검증 범위 밖이다.

고정 공개 XNU boot.h를 수정 없이 별도 C11 offsetof probe로 컴파일·실행해 크기
4096, slide offset 1108, KC header offset 1256을 확인했다. 기존 Rust 공통 필드도
C offset과 일치했다. 경계/전체 extent/가상주소 거부/기존 revision 보존을 포함해
boot_args **14 passed**, 전체 core **124 passed**, no_std UEFI check가 통과했다.
소스 해시는 전후 같으며 독립 코드 검토에서 추가 결함은 발견하지 못했다.
`artifacts/kc-bootargs-contract-20260908.md`,
`artifacts/kc-bootargs-bp20g-20260908/report.json`이 근거다.

### BP20-H 실제 kernel proper classic 적용

공개 dyld producer/XNU consumer 계약을 고정한 별도 source-bound API가 outer
local unsigned width4/8 classic만 처리한다. 명시적 실험 slide `0x200000`으로 실제
KC의 **65,260 words(4-byte 14, 8-byte 65,246)**를 자체 소유 host arena에 적용했다.
write 522,024 bytes와 non-target 67,061,976 bytes 전체의 volatile readback이
일치했다. 401,606 chain words와 205 headers/load-command 범위를 보존했다.
width 밖 덧셈은 지원 밖으로 거부하며 allocation 주소를 slide로 삼지 않는다.

18개 신규 경계/손상 시험을 포함한 **core 142 tests**, no_std UEFI 검사 통과.
실제 child는 0.6766초에 natural exit 0, 전체 1.5503초이며 원본/실행파일/core
source hash 유지와 프로세스 정리를 확인했다. EFI의 classic 적용이나 실제 runtime
slide 선택은 아직 아니다. 근거는 `artifacts/kc-classic-relocation-contract-20260908.md`,
결과와 build receipt는 `artifacts/kc-classic-rebase-bp20h-20260908/`에 있다.

### BP20-I guest Metal 실행 도구

`tools/metal_compute_probe.c`는 공개 Metal API의 실제 shader/pipeline 생성과 두
command completion 뒤 512개 값·입력·guard를 읽는 독립 guest probe다. 90초 alarm과
command별 제한을 가지며 CPU fallback은 없다. 공개 header의 enum/NSUInteger/MTLSize
ABI를 대조했고 WSL Clang/LLD로 **x86_64 Mach-O PIE 13,136 bytes**를 빌드했다.
엄격한 C 컴파일·link·load-command 검사는 통과했으며 실제 guest 실행은 아직 없다.
`artifacts/guest-metal-probe-bp20i-20260908/build-r4/build-receipt.json`에 저장했다.
첫 inspector PATH 누락과 lazy binder link 실패는 이전 실패 receipt로 보존했다.
독립 검토에서 발견한 source 후검증 read failure/compile timeout의 receipt 손실을
수정하고 두 오류 주입 regression을 통과했다. 실제 guest 실행 증거는 아니다.

외부 Reims+CMCI는 고정 publisher source의 display 통합과 별도 opt-in CMCI를
QEMU 11.1에 빌드했다. configure/compile 0, 실제 guest MSR default·CTL2 readback,
TCG/family/MCA 거부를 다시 확인했다. 11.1은 userspace APIC를 CMCI 검사 전에
거부하므로 이전 8.2의 오류문구 기대와 달랐으며, 원본 실패 receipt와 실제 거부
판정을 별도로 남겼다. 이 빌드·probe는 아직 Reims Vulkan/guest Metal 실행 증거가
아니다. 모든 외부 source/build와 guest 입력은 격리에 보존한다.

### BP20-J production EFI ConsoleControl → 원본 XNU/초기 userspace

공개 protocol과 실제 EFI Text/GOP 상태를 연결하는 선택적 ConsoleControl provider를
구현했다. 기존 instance는 재사용하고 새 instance는 child 반환 후 정확히 uninstall한
뒤 해제한다. callback code가 firmware에 남아 있으면 부모 image가 반환하지 않는다.
실제 OVMF 17 checks, 성공/ABORTED child의 반환 상태와 자원 수명 모두 통과했다.
새 모듈/EFI clippy는 기존 core lint만 제외하고 통과했으며 disabled feature도 빌드됐다.

실측 Haswell/invariant TSC/stepping 3/CMCI profile에서 **NextCore production EFI
provider → 원본 Tahoe booter → XNU → launchd PID 1**에 도달했다. 같은 실행의
CPU0 PC 256B가 원본 KC executable segment에 유일하게 일치하고 linked VA +
실제 collection slide = PC를 확인했다. dmpstore의 12B boot-args/속성과 실제
booter/kernel의 `-v serial=3` 출력도 일치한다. corrected run은 22.0017초 자연
종료, 원본 hash 유지, process cleanup 정상이다. 앞선 HMP filename quoting 실패는
관측 실패로 별도 보존했으며 PC readback 근거로 쓰지 않았다.

다음 원인 계층은 **사용자 공간**이다. launchd의 `restore-datapartition` task가
exit(1) 후 userspace panic을 일으킨다. 이 경로에는 외부 OpenCore 및 diagnostic
provider/table hook이 없지만 EFI Shell/HFS helpers와 원본 Apple booter는 있다.
자체 KC loader 진입, 전체 native HAL/복구 GUI/macOS boot/Metal은 아직 아니다.
공개 계약은 `artifacts/efi-console-control-contract-20260908.md`, authored receipt는
`artifacts/efi-console-control-20260908/runs/final/report.json`이며 원본 CPU/Apple
로그/디스크와 같은 실행의 대응 자료는 격리된 `native-console-result.json`에 있다.

### BP22-A Golden Gate ARM64 guest Metal probe

동일 공개 Metal API probe를 `--target golden-gate-arm64`로 빌드했다. 실제
Clang18 엄격한 C compile, Darwin LLD link, objdump inspection 및 CPU/PIE/
LC_BUILD_VERSION 검사 통과: macOS 27 arm64, 33,776B,
SHA256 `8589a3db81a91f36770b1bfbad191162fb9b931e75a4853d472a3c7e5f682a5a`.
기본 Tahoe x86_64 재빌드는 13,136B 및 기존 SHA256
`eae69343a05e096eb2299b6c92e3a15a15b20123d9b23eac346e56cd6e50791b` 그대로다.
다른 CPU/OS, 잘린 command table, signature 겹침을 거부하는 검증을 포함해
도구 regression 8개가 통과했다. 독립 ABI 검토는 실제 Objective-C 호출과 C FFI
호출의 Clang18 ARM64 lowering이 일치함을 확인했다. 검토에서 찾은 arm64e subtype
오인 승인도 exact subtype/capability 검사로 수정했다. 최종 ARM64 r2 바이너리는
같은 hash이며 receipt는
`artifacts/guest-metal-probe-bp22a-20260908/{arm64-r2,x86_64-r1}/build-receipt.json`.
빌드 산출물에 embedded signature가 있다는 것은 guest 실행/정책 수용 증거가
아니다. 두 target 모두 guest_executed/guest_metal_verified=false를 유지한다.

### BP22-B ARM firmware fault-time 관측

원본 macOS 27.0/26A5425a recovery 입력으로 같은 4-byte read/decode failure를
재현하고 **실패 callback 시점**의 실제 dispatch 대상이 unassigned이며 현재
FlatView 16개 영역 모두 해당 접근을 덮지 않음을 확인했다. guest PC와 작은
실제 RAM window도 같은 중단과 대응한다. r1의 GDB Int128 변환 실패는 관측 실패로
보존했고 QEMU의 선언된 16B 정수 저장소를 읽는 r2에서 해결했다.

추가 r3에서는 같은 callback에 도달한 순간의 serial 파일을 먼저 읽었다.
그 시점에는 panic/double-panic 출력이 없었고 detach 후 panic이 나타났으므로
이미 출력된 panic을 뒤늦게 본 것으로 간주하지 않는다. 이 관측은 MMIO 장치의
정상 반환값을 정의하지 않는다. r2는 62.640초, r3는 54.286초에 제한 관측을
마쳤고 13개 원본 입력과 관측 도구/QEMU hash 유지, PID 회수/cleanup이 통과했다.
raw trace는 압축 보존 후 원본 hash로 역검증했다. guest/device state 수정은 없고
ARM XNU/userspace/Metal은 false다. private 원본/주소/바이트/trace/결과는
`_isolated/nextcore/arm-fault-time-20260908-r{1,2,3}/`에만 남긴다.

현재 primary source delta 조사에서도 해당 device의 공개 read/reset/side-effect
계약이 충족되지 않았다. 동시에 공개 XNU ARM64 entry/boot_args에서 직접 인계
경로의 별도 ABI 계약을 작성한다. firmware 장치 모델을 추정하여 성공시킨 것으로
표시하거나 이 결과를 NextCore 자체 kernel entry 성공으로 사용하지 않는다.

### BP20 통합 검증

`cargo test --locked --workspace --exclude nextcore-efi --all-targets --features
nextcore-gpu/vulkan`은 **308 passed, 1 ignored**였다. 별도 기본 feature GPU/APLS는
**143 passed**, 모든 EFI bin의 UEFI target check와 core no_std UEFI check가 통과했다.
ignored 항목은 외부 EFI fixture가 필요한 기존 패키징 시험이다. 당시 소스 해시 전후는
같았고 로그와 명령은 `artifacts/bp20-integration-20260908/report.json`에 보존했다.
이 통합 검증 뒤 추가한 BP20-D/E/G는 위의 별도 후속 검사로 기록한다.
BP20-F/G 통합 뒤 모든 EFI bin을 `kc-staging`까지 함께 활성화한 UEFI check도
통과했고 선택한 소스 해시가 유지됐다: `artifacts/bp20fg-integration-20260908/report.json`.

## BP19 OVMF → HAL 실제 바이트 연결 (2026-09-08)

현재 상태: **실제 BOOTX64 → NXHAL chainload, ACPI 수집과 host HAL 파서 연결 통과**.
원하는 다음 상태는 대상 XNU에 필요한 플랫폼 provider와 게스트 관측의 연결이며,
이번 결과는 그 provider 또는 운영체제 부팅 성공을 대신하지 않는다.

가설과 변경: 기존 raw parser의 선언 길이 밖 읽기와 PCI header layout 오해를
수정하고, 합성 fixture 외에 실제 OVMF가 제공하는 동일 bytes도 해석할 수 있는지
확인했다. `NXHAL`은 ACPI reclaim/NVS descriptor가 전체 범위를 포함할 때만
읽는다. RSDP/root 검사, 읽기 거부 5종, bus 0 PCI config 읽기는 별도 시험 EFI에서
수행한다. ACPI typed parser는 checksum/선언 길이/불완전 MADT record를 거부하고,
PCI decoder는 multifunction bit를 허용하는 Type 0만 지원한다.

실행 결과(QEMU 8.2.2, q35/TCG/SMM off, Nehalem, 256 MiB, 1 CPU):

- RSDP 1개와 SDT **7개**(XSDT/FACP/APIC/HPET/MCFG/WAET/BGRT), PCI Type 0
  header **5개**를 실제 수집하고 13회 Rust inspector 호출이 모두 통과했다.
- RSDP→XSDT→6개 child pointer, raw 길이/checksum/count와 JSON 결과가 일치했다.
  MADT는 LAPIC 1, IOAPIC 1, interrupt override 5, NMI 1의 8개 record다.
  MCFG는 allocation 1개다. FACP는 선택 필드 요약이며 HPET/WAET/BGRT는 공통
  SDT header/checksum만 검사했다. AML, HPET register, PCI BAR/IRQ/DMA는 미검증이다.
- QEMU가 **3.9851초에 exit 67로 자연 종료**, 전체 하네스 **4.3961초**였다.
  60초 deadline 미초과, harness stop=false, process group/adopted child 잔존 없음.
- 원본 입력 5개(BOOTX64/NXHAL/inspector/OVMF code/OVMF vars)와 두 EFI 복사본의
  pre/post SHA-256 일치. vars 복사본의 guest 변경은 별도로 기록했다.

검증: Rust workspace **280 passed, 1 ignored**(별도 EFI fixture 필요), HAL
all-targets **32 passed**(workspace와 중복 포함), HAL clippy 경고 0, UEFI target
check 및 BOOTX64/NXHAL release build 통과. Python 하네스 최종 **30 passed**에는
잘린 dump, 잘못된 pointer/count/schema, checksum, crash 오판, timeout/TERM 무시,
leader exit와 `setsid` 이탈 child 수거가 포함된다. 기존 ISE 및 feature 미사용
NXKERNEL 경고는 이번 변경의 실패가 아니다.

독립 검토에서 파서 JSON 불일치 승인, PCI parser crash의 unsupported 오인,
다른 session으로 이탈한 child 수거 누락을 고쳤다. 실제 OVMF 실행 후에는 typed
summary gate만 추가 보완했으며, 원본 실행 receipt를 보존하고 **같은 13개 raw와
stdout를 최종 gate로 offline 재검증**했다. VM은 반복 실행하지 않았다.
별도 독립 readback에서 원본/13 raw hashes, 같은 UID의 QEMU 잔존 없음과 실제
수집 bytes를 손상시킨 4종(checksum/truncation/FACP declared length/PCI Type 1)의
실제 inspector exit 1 거부를 확인했다. 첫 readback helper의 진단 문자열 불일치와
다른 UID `/proc` 접근 오류는 관측 실패로 보존하고 검사 범위를 수정했다.

파일 근거:

- `artifacts/hal-ovmf-bp19-20260908/`: report/command/serial/raw, 당시 하네스 소스.
  report SHA-256 `693c038ec3fcf0606ec1dde78049cd2386a840211c2dfce6058ca5646fbc109e`.
- `artifacts/hal-build-20260908/`: 실행 EFI, workspace log, toolchain,
  `independent-readback.json`과 재현 helper 및 첫 관측 실패 원본.
- `artifacts/hal-continuation-review-20260908.md`,
  `artifacts/hal-firmware-review-20260908.md`: 구현/독립 검토.
- 실행 하네스 SHA-256 `57b0d9cf5ce746364c75912115aea94a415e9d092fd03ab68738976fdd633add`,
  최종 gate SHA-256 `c6e8abac1bf9a2574d15a1b138d615c8adb41f1b1ac5302ca4296700fd17553b`.

재현(`nextcore/`, Windows에서 UEFI build, WSL에서 host inspector/build/run):

```text
cargo build -p nextcore-efi --target x86_64-unknown-uefi --release --bin BOOTX64
cargo build -p nextcore-efi --target x86_64-unknown-uefi --release --bin NXHAL --features hal-tables
cargo build -p nextcore-hal --example inspect_firmware --target-dir /tmp/nextcore-hal-bp19-target-20260908
python3 tools/verify_hal_ovmf.py --efi target/x86_64-unknown-uefi/release/BOOTX64.efi --hal target/x86_64-unknown-uefi/release/NXHAL.efi --inspector /tmp/nextcore-hal-bp19-target-20260908/debug/examples/inspect_firmware --output /tmp/nextcore-hal-ovmf-NEW --timeout 60
python3 -m unittest discover -s tools -p test_verify_hal_ovmf.py -v
```

BOOTX64 SHA-256 `2b354c28dda5b673d318782063439853bea795a19aac8044af06157054c9dd1f`,
NXHAL `065158fdcd8872f92ca9e9be4b242f7c057b59a99ba65cf272365fd5965c2e99`.
`xnu_executed`, userspace, `macos_boot_verified`, Metal, physical hardware는 모두
미검증이다. 다음 blocker는 실제 x86_64 target kernel과 그 ABI에 맞는 플랫폼/DT/
runtime provider다. 현재 raw parser를 곧바로 게스트 장치 게시로 부르지 않는다.

## 확인된 구현과 근거

1. **사용자 공간 / EFI 패키징**: `nextcore-tool build`와 `install-usb`가
   `NXC0` 더미를 만들던 경로를 제거했다. 명시 `--efi`의 AMD64 PE32+ EFI
   application 구조를 검증하고, 입력 검증 후 새 파일로 복사·읽기 비교한다.
   기존 출력/self-copy/hardlink 원본은 덮어쓰지 않는다.
   최종 번들은 `artifacts/efi-bundle-20260907/EFI/`에 있다.
2. **UEFI Boot Services / 파일 I/O**: 실제 EFI가 자기 부팅 볼륨에서
   `\EFI\OC\config.plist`를 읽는다. 1..1,048,576바이트만 허용하고 부분
   읽기/EOF를 처리한다. 표준 Serial I/O에 EFI 진입과 읽기 결과를 기록한다.
   BP9에서 no_std XML `Misc.Entries` 파서를 연결했다. 0개/복수 선택과
   XML/경로/상한 오류를 구분하며 UCS-2 경로와 UTF-16 옵션을 검증한다.
   같은 볼륨의 명시 application을 `LoadImage→StartImage`로 실행하고,
   자가 참조와 resident driver를 거부한다. 부모는 ExitBootServices를 먼저
   호출하지 않는다. BP11에서 별도 NXKERNEL의 공개 ABI 준비와 CPU 진입
   프로브를 추가했다. 실제 XNU 운영체제 인계 완료와는 구분한다.
3. **APLS 호스트 실행**: Rust `RunnerRequest`와 `nextcore-tool apls run`이
   명시한 native/local 또는 TCG/WSL worker를 실행하고 종료를 회수한다.
   요청/명령/PID/stdout/stderr/adapter receipt를 새 디렉터리에 보존한다.
   실제 Windows→WSL→Python→QEMU→ARM firmware 실행을 확인했다.
4. **QEMU 관측**: log backend에서 `-trace file=`가 `-D`를 덮는 결함을
   수정했다. 공용 `qemu.debug.log`에서 CPU와 PSCI 증거를 각각 읽으며 큰
   파일은 head/tail 범위와 byte offset을 기록한다. 원본 로그는 유지하고
   1 MiB 합계 sample을 별도로 남긴다.

## BP9 현재 실행 결과

- Rust workspace **135 passed, 1 ignored**. 최신 로그는
  `artifacts/workspace-chainload-final-tests-20260907.log`.
- ignored 실제 EFI 복사 통합 시험은 별도 **1 passed**:
  `artifacts/compiled-chainload-copy-tests-20260907.log`.
- core **37 passed**, no-default 파서 **12 passed**와 no_std UEFI target check
  통과. `artifacts/boot-config-review-20260907.md`에서 독립 검토 결과 확인.
- EFI release build, host check, 패키징 모두 통과. 배포용 파일은
  `artifacts/efi-chainload-bundle-20260907/EFI/BOOT/BOOTX64.EFI`이며 빌드본과
  SHA-256 `b4082331c5f8ed0f9cfa84b5bd4e9c61b0c08f42baba7e6c4c750a431cce37e8`
  가 일치한다.
- 최종 번들로 실제 OVMF **12/12 passed**. 설정 없음/빈 파일/상한/잘못된 XML,
  0개 target/대상 파일 누락/자가 참조, child 정상·오류 반환, 빈 옵션과
  한글·보충 문자 UTF-16LE 전달, resident driver 실행 전 거부를 확인했다.
  `artifacts/ovmf-chainload-final-20260907/report.json` 및 독립 재해시·프로세스
  확인 `independent-readback.json`에 기록. 원본 5개 해시 유지, QEMU 모두 종료.
  **이 결과는 EFI application 인계이며 XNU/macOS/Metal 성공이 아니다.**
- 독립 리뷰 2건을 수정했다: resident driver 반환 뒤 LoadOptions 수명,
  core에서 허용하지만 UEFI CString16이 거부하는 non-BMP 경로. 해당 수정 후
  실행/파서 시험을 다시 통과했다. `artifacts/efi-chainload-review-20260907.md`.
- 요청한 실행 절차를 `nextcore-boot-engineering` 개인 스킬과 재사용 프롬프트로
  저장했다. 구조 검증과 독립 시나리오 3건을 통과했고, 로그의 동일 실행 출처
  및 매체 역할/실행 버전 구분을 보강했다. `artifacts/skill-review-20260907.md`.

## BP10 정상 AVP entry 관측

같은 macOS 27.0 / 26A5425a 원본의 AVPBooter를 현재 fixture에 사용한 관측을
완료했다. 실행 상한은 20초였고 실제 0.605초 후 게스트가 PSCI_SYSTEM_RESET을
요청해 `-no-reboot`인 QEMU가 종료했다. AUX 읽기 33회는 모두 성공했고 root
I/O와 UART 출력, XNU/userspace는 없었다. 정상 entry에서도 부팅 상태 또는
입력 레이아웃의 내부 판단은 아직 규명되지 않았다. reset을 부팅 성공이나
호스트 오류로 표시하지 않는다. 원본 4개 pre/post hash 일치, 대상 PID 종료.

`artifacts/apls-diagnosis-20260907/avp27-observation.json`에서 공개 MMIO/ARM
exception/PSCI 관측을 확인할 수 있다. normalized command는 firmware 경로,
research-stage2 모드 및 진단 `exec` logging 유무가 달랐다. AVP worker는
translation-block logging을 켜지 않았으므로 TB count를 비교하지 않는다.
전량 230,557바이트의 예외/장치/PSCI 로그를 스캔했고 원본을 보존했다.

`input-candidates.md`의 좁은 기존 입력 조사에서는 초기화된 native VM tuple을
확인하지 못했다. 설명형 identity, reused AUX 및 추출 RestoreRamDisk/OS 이미지의
역할을 설치 완료 디스크와 구분한다. 이 결과를 바탕으로 같은 모델의 정상
restore chain 또는 실제 provisioning 결과가 생성하는 boot-state를 확인하는
것이 다음 작업이다. 펌웨어/원본 매체를 수정한 실험은 없다.

## BP11 공개 XNU ABI와 실제 EFI 메모리 배치

- 공개 XNU `xnu-12377.121.6`의 진입 소스와 wire layout을 고정했다.
  `artifacts/xnu-entry-contract-20260907.md`에 출처와 소비자 검증이 있다.
  EFI64인 boot_args와 32비트 pstart 진입 모드를 구분하며, 이 버전이 현재
  ARM 복원 이미지와 일치한다고 주장하지 않는다.
- `macho_image` no_std 파서, `LoadedKernel`의 실제 AllocateAddress/복사/
  zero-fill/readback, 4096-byte boot_args encoder, bounded flattened DT codec을
  구현했다. 원본 plan을 재파싱해 일치시킨 뒤 배치하며 VA→PA 변환은 명시
  `xnu-12377-pstart32` 프로필만 담당한다. LC_MAIN은 generic parser가 지원해도
  이 프로필에서는 실행 전 거부한다.
- `NXKERNEL.EFI`는 `Nextcore/Kernel`의 Profile/Path/Arguments를 읽고
  standalone x86_64 Mach-O를 정확한 저위 물리 주소에 배치한다. 기본 빌드는
  `PROVIDERS_PENDING`으로 반환한다. `kernel-probe` feature는 자체 작성
  fixture의 EBS/최종 메모리 맵/ABI/CPU 전환 시험용이며 배포 기본값이 아니다.
  NMI는 CLI로 차단되지 않는다. 현재 전환 계약은 SMM off와 NMI 주입이 없는
  통제된 QEMU q35에 한정하며 실제 하드웨어 NMI 전환을 검증했다고 보지 않는다.
- core **71 passed**, host workspace **169 passed, 1 ignored**.
  `artifacts/workspace-kernel-handoff-tests-20260907.log`.
  실제 EFI 복사 ignored test는 별도 **1 passed**:
  `artifacts/compiled-kernel-efi-copy-tests-20260907.log`.
  default/probe EFI target release 빌드 모두 통과했다.
- 기존 EFI application 회귀는 새 parser/build로 **12/12 OVMF passed**.
  `artifacts/ovmf-kernel-parser-regression-final-20260907/report.json`과
  `independent-readback.json`에 원본 5개 재해시 일치와 child 종료를 기록했다.
  첫 DrvFS 출력 시험은 serial polling의 `OSError 61`로 호스트 관측이 중단돼
  성공으로 세지 않았다. 해당 child는 finally에서 수거됐고 WSL `/tmp`의
  새 출력으로 실행한 위 12건이 완료된 근거다.
- 독립 검토에서 발견한 LC_MAIN 진입 종류 누락을 수정했다.
  `artifacts/kernel-handoff-review-20260907.md`.
- 새 커널 경로의 실제 OVMF 시험 **8/8 passed**: 정상 자체 probe 1건과
  production provider gate, truncated/FILESET/profile/LC_MAIN/표식 누락 거부,
  guest의 DATA 손상 검출 7건이다. 정상 경로는 정확한 물리 배치
  base=0x100000/entry=0x101000 뒤 EBS를 통과하고, CPU 상태/boot_args/
  전달 map/140-byte fixture DT/DATA 전체/BSS 전체를 guest가 검사했다.
  1.906초 후 QEMU가 debug-exit **33**으로 자연 종료했으며 하네스 kill이 아니다.
  DATA 손상은 loader의 source readback 후 독립 guest 검사에서 FAIL_DATA와
  자연 종료 **35**로 검출돼 성공 마커만 출력하는 시험이 아님을 확인했다.
  일반 DT 순회나 운영체제 필수 노드 충분성을 이 fixture로 검증하지 않는다.
- 증거는 `artifacts/ovmf-kernel-positive-20260907/report.json`과
  `artifacts/ovmf-kernel-negatives-20260907/report.json`. 루트가 입력 8개의
  hash를 독립 재확인하고 잔존 QEMU가 없음을 확인했다:
  `artifacts/kernel-probe-independent-readback-20260907.json`.
  이 결과는 **EFI→자체 32비트 프로브 실행**이며 XNU/macOS/Metal=false다.

## BP12~BP13 정상 복원 경로의 전진 경계

BP12는 현재 AVP27/VM JSON/AUX/root를 유지한 정상 DFU recovery 관측이다.
matching manifest의 iBSS/iBEC와 정상 personalization으로 Stage2 banner까지
진행했으나 prompt 전 DataAbort로 종료됐다. AUX79 read/3 write 및 root2 read는
모두 성공했다. ASR 부재나 root 쓰기 실패를 이 실패의 원인으로 단정하지 않는다.

BP13은 같은 명령과 원본 입력에 기존 default-off optional RPC adapter 하나만
켠 비교다. 이 adapter는 원래 completion/result를 보존하며 성공을 합성하지 않는다.
Stage2 prompt, restore role **5종**, `bootx` ACK까지 진행됐다. AUX117 read/3 write,
root2 read, optional RPC request1/completion unchanged1을 전량 trace에서 확인했다.
bootx 전후 PC가 바뀌었고 실행 블록 259,145개를 관측했으나 firmware panic이
남았으며 Darwin/userspace는 관측하지 못했다. macOS boot=false다.

BP14의 같은-event host callback 관측에서 VA=PA, 4-byte `MMU_DATA_LOAD`,
mmu_idx 0, `MEMTX_DECODE_ERROR`를 확인했다. 실제 실행의 QMP flatview 25개
범위에도 PA mapping이 없었다. 따라서 최초 실패는 bootx 뒤 decode되지 않은
물리 read로 좁혀졌다. 장치 정체와 올바른 register contract는 여전히 미확정이며
임의 zero-return 장치나 펌웨어 패치는 추가하지 않았다.

BP12 15.671초, BP13 42.693초로 각각 실행 상한 내였다. 원본 13개 hash 유지와
대상 프로세스 종료를 루트가 독립 재확인했다. 공개 결과는
`artifacts/apls-restore-contract-20260907/`의 comparison/observation/full-trace-counts
및 `independent-readback.json`이며 raw register/trace/ticket은 격리 경로에 유지했다.
초기 bounded sample count와 별도 전량 count를 혼합하지 않는다.

BP14 재시도는 Stage2 prompt, 복원 5종, bootx ACK 뒤 동일 firmware panic을
재현했고 XNU/userspace/macOS는 false다. debugger는 일치 event 1건만 읽고
guest/device 값을 바꾸지 않은 채 detach했다. 총 44.469초, 원본 13개 hash
동일, worker/wrapper/QEMU/GDB 잔존 0이다. 첫 시도의 GDB argv 오류는 guest/TSS/
DFU 실행 0인 실패로 별도 보존했고, 두 번째 시도 전 복합 argv round-trip과
descendant cleanup 합성 시험을 통과했다. 공개 근거는
`artifacts/apls-restore-contract-20260907/bp14-same-event-transaction.json`,
`normal-recovery-translation-b-observation.json`, `bp14b-argv-roundtrip.json`이다.
정확한 주소·레지스터·debugger 원문은 `_isolated/`에만 있다.

실제 RestoreDeviceTree의 bus range를 적용한 읽기 전용 조사에서는 BP14 fault를
포함하는 `reg` node가 하나 있었다. 비교 입력에서는 일치 node가 없었다. 그러나
그 node를 구현할 공개 장치 interface/register contract는 찾지 못했으므로 장치
정체는 미확정이고 모델 응답도 추가하지 않았다. 공개 요약은
`artifacts/apls-restore-contract-20260907/bp14-device-contract-survey.json`이다.

## BP15 Nextcore 정상 recovery adapter

Rust APLS에 명시 `tcg-recovery` backend를 추가하고 기존 Python normal recovery를
Linux supervisor로 감쌌다. supervisor는 새 session의 worker/descendant를
monotonic deadline 안에서 수거하고, VM JSON이 지정한 AUX/root를 포함한 원본
입력의 pre/post hash를 비교한다. raw QEMU PID는 같은 session에서 실제 관측한
유일한 PID/starttime과 일치해야 runtime 근거가 된다. 요청 output 원문과
canonical worker output을 분리하여 상대 경로도 안전하게 검증한다.

합성/독립 검증은 Python supervisor **17 passed**, Rust runner **17 passed**,
CLI **9 passed**다. 기존 `x86.test_vmapple_tcg`와 함께 실행한 Python 회귀는
**40 passed**다. 독립 리뷰는
`artifacts/apls-recovery-adapter-review-20260907.md`에 있으며 미해결 finding은
없다. 저장된 BP14 report는 당시 PID ledger가 없으므로 strict offline 판정에서
runtime/boot=false를 유지했다.

최종 host workspace 회귀는 **169 passed, 1 ignored**이고 `cargo check
--workspace --exclude nextcore-efi`도 통과했다. 기존 `nextcore-ise`의 unused 경고
4건은 실패가 아니며 이번 BP15 소유 파일의 변경 사항이 아니다. 로그는
`artifacts/workspace-tests-bp15-20260907.log`와
`artifacts/python-recovery-tests-20260907.log`에 보존했다.

새 adapter를 통한 실제 정상 recovery 1회는 48.365초에 Nextcore exit **2**로
끝났다. DFU, iBEC endpoint, Stage2 banner/prompt, 복원 역할 **5종**, sequence와
`bootx` ACK를 확인한 뒤 firmware panic이 발생했다. supervisor는 raw QEMU PID의
same-session 상관=true, cleanup complete=true, remaining PID 0, deadline 미초과,
입력 15개 pre/post hash 일치를 기록했다. XNU/userspace/목표 커널 major는
관측되지 않았고 macOS boot=false다. 결과는
`artifacts/apls-supervised-recovery-result-20260907.md`, 전체 host receipt는
`artifacts/apls-supervised-recovery-host-20260907/`에 있다.
독립 요약과 receipt hash는
`artifacts/apls-supervised-recovery-independent-check-20260907.json`에 있다.

## BP16 공개 MMIO 계약 조사

세 갈래 독립 조사 결과는 모두 **HOLD**다. pinned VMApple machine에는 QEMU
PL031이 이미 존재하지만 그 mapping은 선택 DeviceTree node 범위와 겹치지 않는다.
선택 compatible은 ARM/PL031 binding과 일치하지 않고 role 속성이 없으며 문제
read의 상대 offset도 PL031 정상 register/ID coverage 밖이다. PL031 alias는
bad-offset fallback을 정상 장치 응답으로 오인하게 되므로 추가하지 않았다.

Linux/OpenBSD의 Apple SMC RTC/NVMEM은 다른 transport다. Apple Virtualization의
Mac hardware model/AUX는 opaque platform state이고 custom Virtio와 공개 GPU MMIO
API는 host-supplied device의 선례지만 이번 장치의 register, reset, 반환값과
side effect를 정의하지 않는다. reset 시점 CPU system flatview 16개와 고정 machine
map의 noncoverage, same-event `MEMTX_DECODE_ERROR`를 분리했으며 reset snapshot을
fault 순간 snapshot으로 표현하지 않았다. 코드 수정과 추가 VM 실행은 없다.

공개 근거:

- `artifacts/apls-restore-contract-20260907/bp16-public-contract-survey.md`
- `artifacts/apls-restore-contract-20260907/bp16-public-contract-survey.json`
- `artifacts/apls-restore-contract-20260907/bp16-qemu-coverage-review.md`
- `artifacts/apls-restore-contract-20260907/bp16-qemu-coverage-review.json`
- `artifacts/apls-restore-contract-20260907/bp16-host-interface-survey.md`
- `artifacts/apls-restore-contract-20260907/bp16-host-interface-survey.json`

정확한 주소, node 원문과 offset은 `_isolated/`의 private receipt에만 있다.

## BP8 실행 이력

- Rust host 회귀: **123 passed, 1 ignored**.
  `artifacts/workspace-tests-20260907.log`.
- 실제 컴파일 EFI를 사용하는 ignored 통합 시험을 별도로 명시 실행:
  **1 passed**. `artifacts/compiled-efi-copy-tests-20260907.log`.
- Python TCG/boot-evidence 회귀: **32 passed, 1 skipped**.
  Windows PATH의 QEMU probe만 제외됐으며 실제 QEMU는 WSL에서 별도 실행했다.
  `artifacts/python-evidence-tests-20260907.log`.
- host check와 UEFI target check 모두 통과:
  `artifacts/host-check-20260907.log`, `artifacts/uefi-check-20260907.log`.
  최초 `cargo check --workspace`는 Windows target에 no_std EFI까지 포함해
  unwind 오류를 냈다. host/firmware target을 분리한 명령이 올바른 게이트다.
- 실제 EFI release 빌드: `target/x86_64-unknown-uefi/release/BOOTX64.efi`.
  당시 번들 복사본과 SHA-256가 동일했다. 현재 BP9 바이너리는 후속 결과를 본다.
- 패키징한 EFI의 OVMF 실행: **4/4 passed** (설정 읽기, 누락, 빈 파일,
  상한 초과). EFI/config/OVMF code/OVMF vars 원본 4개 해시 유지.
  `artifacts/ovmf-bundle-20260907/report.json`.
- 직접 작성한 AArch64 프로그램의 VMApple TCG 보정 시험: **passed**.
  QMP에서 X0가 0→42로 변했고 PC가 입력 프로그램 내 다음 명령으로 이동했다.
  이는 CPU 에뮬레이터 실행 증거이며 macOS 실행 증거가 아니다.
  `artifacts/cpu-probe-20260907/report.json`.
- 최종 APLS CLI 실매체 실행:
  `artifacts/apls-trace-fixed-20260907/adapter.json`.
  worker/guest 시작과 종료를 확인했고 원본 AUX/firmware/root/VM JSON 4개를
  독립 재해시해 일치했다(`readback.json`). QEMU PID도 종료됐다.
  UART에 Stage2 시작 후 펌웨어 panic이 있다. 수정된 추적에서 Stage2 실행
  관측=true, 4 MiB 샘플 내 실행 블록 54,188개, 원본 로그 27,482,713바이트다.
  XNU/userspace/목표 커널 런타임/Metal은 미관측이며 macOS boot=false다.
- optional-RPC 단일 변수 비교 실행:
  `artifacts/apls-optional-rpc-20260907/comparison.json`.
  새 출력 경로를 제외하면 기존 명령에 해당 옵션만 추가했다. UART 417바이트가
  기준 실행과 동일하고 Stage2 이후 panic 경계도 그대로다. 원본 4개 해시와
  프로세스 종료를 독립 확인했다. 따라서 해당 옵션은 기본값으로 채택하지 않는다.

입력 매체의 BuildManifest 메타데이터는 ProductVersion=27.0,
ProductBuildVersion=26A5425a다. 원본 kernel payload를 읽기 전용으로 확인한
공개 버전 문자열은 `Darwin Kernel Version 27.0.0`이다. 파일 내부 버전은
실제 XNU가 실행됐다는 의미가 아니며 runtime target-match는 계속 false다.

## 재현 명령

`nextcore/` 디렉터리에서:

```powershell
cargo check --workspace --exclude nextcore-efi
cargo check -p nextcore-efi --target x86_64-unknown-uefi
cargo test --workspace --exclude nextcore-efi
cargo build -p nextcore-efi --target x86_64-unknown-uefi --release
cargo build -p nextcore-efi --target x86_64-unknown-uefi --release --features test-child
cargo build -p nextcore-efi --target x86_64-unknown-uefi --release --bin NXKERNEL --features kernel-probe
$env:NEXTCORE_TEST_EFI=(Resolve-Path target/x86_64-unknown-uefi/release/BOOTX64.efi).Path
cargo test -p nextcore-tool compiled_efi_is_copied_without_changes -- --ignored
cargo run -p nextcore-tool -- build --plist tests/sample.plist --efi target/x86_64-unknown-uefi/release/BOOTX64.efi --out <새-출력-디렉터리>
cargo run -p nextcore-tool -- apls run --help
```

OVMF 시험은 WSL에서 `python3 nextcore/tools/verify_ovmf.py --efi <실제-EFI>
--child <자체작성-NXTEST.EFI> --config <활성-entry가-없는-config.plist>
--output <새-디렉터리>`로 실행한다. NXTEST는 시험 전용 feature로 빌드하며
일반 배포 번들에는 포함하지 않는다. 구체적인 QEMU
명령과 모든 펌웨어 입력 hash는 각 실행 디렉터리의 command.json/report.json에
있다. APLS의 정확한 명령은 해당 host receipt의 request.json/invocation.json에
있으며, output과 host-receipt-dir은 매번 새 경로를 사용한다.

커널 경로의 전체 8건은 `nextcore/`를 WSL cwd로 하여 아래처럼 실행한다.
기본 빌드와 `kernel-probe` 빌드는 별도 파일로 보존한 뒤 전달한다.

```bash
python3 tools/verify_kernel_ovmf.py \
  --efi artifacts/kernel-probe-build-20260907/BOOTX64.efi \
  --kernel-probe artifacts/kernel-probe-build-20260907/NXKERNEL-probe.efi \
  --kernel-default artifacts/kernel-probe-build-20260907/NXKERNEL-default.efi \
  --output /tmp/nextcore-kernel-ovmf-new-run
```

실행 도구가 자체 작성 assembly에서 fixture를 빌드하며 Apple 입력은 사용하지 않는다.
출력 경로가 이미 있으면 덮어쓰지 않는다. 위 예시 경로도 재실행 때는 새 이름을 쓴다.

`apls run` 종료 코드 0은 검증된 macOS 부팅, 2는 미검증 관측 또는 CLI 인자
오류, 1은 adapter/setup 오류다. worker 종료 코드와 QEMU 종료 코드는 별개다.

## GPU 추상화 계층 확장 (2026-09-07)

Design D10의 host 그래픽 레이어를 "host 데이터 모델/명령 의미론 검증" 범위 안에서
확장했다. 실제 Metal/GPU 실행은 아니며 이번 변경으로 `macos_boot_verified`는
계속 `false`다.

새 모듈 (전부 `nextcore-gpu/src/`):

- `framebuffer.rs` — LinearFramebuffer(BGRA8/RGBA8/BGRX8, stride, dirty
  tracking, clear/set/get/fill_rect/blit)와 DoubleBuffer. UEFI GOP 선형
  프레임버퍼 패턴 대응.
- `texture.rs` — TextureManager(텍스처 생성/업로드/다운로드/삭제, 포맷
  RGBA8/BGRA8/RGBA16F/RGBA32F/Depth, 2D bilinear/nearest sampling,
  SamplerDescriptor, clamp/repeat/mirror 주소 모드).
- `sync.rs` — GpuSyncManager(fence/세마포어/이벤트, signal/wait/timeout/reset).
  GPU async 경계용 프리미티브.
- `render_pipeline.rs` — RenderPipeline/Descriptor, VertexInputState,
  Depth/Stencil/Blend/Rasterizer state, Viewport/Scissor. 공개 GPU pipeline
  state 모델.
- `command_executor.rs` — RecordedCommandBuffer와 GpuCommand(draw/indexed/
  instanced, bound 상태, render pass clear, texture copy, viewport).
  execute()가 framebuffer clear와 draw call 기록을 수행한다. `execute_with_rasterizer`
  는 slot 0의 vertex/index buffer에서 `SOFTWARE_RENDER_VERTEX_STRIDE`(52바이트:
  position+color+tex_coord+normal) 인터리브 정점을 해석해 SoftwareRasterizer로
  실제 삼각형 래스터화까지 수행하고, render pass 시작 시 depth buffer를
  프레임버퍼 크기로 재할당·초기화한다. `decode_software_vertex`는 공개 API다.
- `compute.rs` — ComputePipelineManager(storage buffer, dispatch, fence
  signal). software compute 디스패치의 host 모델.
- `rasterizer.rs` — SoftwareRasterizer(NDC→screen, barycentric, depth
  buffer, line rasterization)와 Vertex/Vec2/Vec3/Vec4/Color 및 blend 함수.

검증: `nextcore-gpu`는 기존 10건 + 신규 81건 = **91 passed**. clippy 0건.
전체 workspace `cargo test`도 통과. 신규 테스트 파일은 `tests/gpu_framebuffer.rs`,
`gpu_texture.rs`, `gpu_sync.rs`, `gpu_pipeline.rs`, `gpu_raster.rs`,
`gpu_executor.rs`, `gpu_compute.rs`, `gpu_render_path.rs`. 통합 경로
`gpu_render_path.rs`는 clear→Draw/DrawIndexed→SoftwareRasterizer 래스터화→
DoubleBuffer swap→front 표시까지 한 흐름으로 검증한다.

다음 blocker: D10"게스트 연결 방식과 공개 driver/API 범위". 현재 로그/핸들 확인과
호스트 렌더 모델은 host 단위 테스트로만 검증됐다. 실제 graphics driver/Metal
runtime acceptance는 XNU/userspace 부팅 뒤의 별도 관측이다. 이번 확장은
"호스트 모델의 명령 의미론"이며 GPU 가속 완료로 표시하지 않는다.

## 남은 구현과 다음 근거

- **ARM firmware→XNU**: BP14는 정상 복원과 root 읽기, bootx ACK 뒤의
  최초 실패를 매핑되지 않은 물리 4-byte data read로 확정했다. 장치 정체와
  공개 register contract를 확인하기 전에는 모델 응답을 구현하지 않는다.
  raw Stage2의 이전 무효 비교를 정상 복원 결과와 섞지 않는다.
  설명형 identity/reused AUX/RestoreRamDisk는 설치 완료 native VM bundle로
  확인되지 않았으며 bootx ACK도 XNU 성공을 대신하지 않는다.
- **native Apple Silicon**: VF native worker 연결 코드는 있지만 이 Windows
  호스트에서는 실행 검증하지 못했다. TCG 결과를 native VF 성공으로 부르지 않는다.
- **x86 UEFI→XNU**: 실제 메모리 배치와 공개 boot_args/DT codec, 명시 pstart32
  프로필을 구현했다. 실제 목표 이미지의 버전·KC 형식, 필요한 entropy/platform/
  runtime/DT provider 및 초기 allocator backing을 충족해야 XNU를 실행할 수 있다.
  자체 프로브 실행은 이러한 macOS acceptance를 대신하지 않는다.
  인벤토리와 `artifacts/extracted`의 좁은 조사에서 확인한 실제 raw kernel 2개는
  모두 ARM64 MH_FILESET이며 x86_64 XNU 후보는 없었다. kernel 입력 11개 hash는
  기존 receipt와 일치했다. 공개 tag `xnu-12377.121.6`의 동일 x86 바이너리도
  미확인이다. 이 결론은 전체 디스크/IPSW 내부 조사로 확대하지 않는다:
  `artifacts/x86-kernel-candidate-survey-20260907.json`.
- **ISE / HAL / GPU**: host 데이터 모델/명령 의미론 검증과 XNU 예외 소유권,
  실제 장치 게시, guest GPU driver/API 연결 및 Metal 실행을 구분한다.
  D9~D12의 목표는 유지되며 런타임 성공으로 표시하지 않았다.

## OPEN_QUESTION

- `OPEN_QUESTION: Build Plan: ARM guest 펌웨어 panic이 요구하는 플랫폼/입력 조건을 다음 실행에서 구체적으로 검증한다.`
- Design D2-A/D5-A~C에서 중간 EFI 인계와 내부 모델/공개 XNU ABI adapter
  경계가 확정됐다. 실제 대상별 wire contract/진입 코드는 후속 구현 대상이다.

위 미완료가 남아 있으므로 활성 목표는 완료 처리하지 않는다.
