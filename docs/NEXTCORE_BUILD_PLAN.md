# Nextcore 작업 지시서 (Build Plan Slot)

## 책임

Nextcore의 *어떻게*를 박제한다 — Rust 모듈 구조, 단계별 구현 순서, 검증,
의존성, 빌드 산출물. *무엇*과 *왜*는 Design 슬롯의 영역이다.

## 현재 상태

- 2026-09-07 재개: 실제 workspace는 core/efi/tool/ise/gpu/hal/apls 7개 crate다.
  재개 당시 103 host 테스트를 재검증했고, `NXC0` 더미는 실제 EFI 이미지
  검증/복사로 교체했다. EFI는 부팅 볼륨의 config 파일을 제한된 크기로 읽고
  Serial I/O로 상태를 출력한다. UEFI→XNU 인계는 아직 구현되지 않았다.
  APLS host adapter/CLI가 실제 WSL→QEMU→ARM firmware를 실행했으며,
  Stage2 시작 후 XNU 이전 panic까지 관측했다. BP8~BP9 실행 계약을 적용한다.
- BP1~BP7은 최초 3-crate 설계/문서 통합 이력이다. 현재 파일 수, std/no_std
  지원, 의존성과 실행 근거는 BP8~BP9 및 `nextcore/VALIDATION.md`가 우선한다.
  BP9에서 core의 std 기능을 분리하고 no_std XML boot_config를 EFI에 연결했다.
  실제 동일 볼륨의 명시 EFI application 인계를 구현했다. 직접 XNU 인계는 미완료다.
  EFI는 `uefi 0.40`의 helpers/allocator를 사용하며 이전 uefi-services 및
  중복 allocator 의존성을 제거했다.
- BP1~BP5 모두 박제된 결정으로 채워짐 (이전 세션의 골격에서 확장).
- (F) 통합 검증 — 본 문서 OPEN_QUESTION 3건 전부 종결(RESOLVED 3, BP7에
  내부 HOLD 1건 포함). BP7 신설. BP3.9 × Prompts P4 (F) 분기 카피 정합 확인.

## 원하는 상태

- Rust workspace / crate 구조가 박제된다.
- 단계별 구현 순서가 *각 단계마다 검증 게이트*와 함께 박제된다.
- 의존성 목록 (UEFI, plist, ACPI, kext 포맷 등)이 명시된다.
- 빌드 산출물 (EFI binary, 디렉터리 구조)이 명시된다.

## 결정 항목

### BP1. Rust 모듈 구조

```
nextcore/
├── Cargo.toml                 # workspace 루트
├── crates/
│   ├── nextcore-efi/          # UEFI binary (no_std, x86_64-unknown-uefi)
│   │   └── src/
│   │       ├── main.rs        # UEFI entry point  —  pub fn efi_main(image: Handle, st: *mut SystemTable) -> Status
│   │       ├── boot.rs        # Boot Services 추상화  —  pub struct BootServices; impl { locate_handle, alloc_pages, open_protocol }
│   │       ├── runtime.rs     # Runtime Services 추상화  —  pub struct RuntimeServices; impl { set_variable, get_variable, reset }
│   │       └── console.rs     # UEFI console (ConOut)  —  pub struct Console; impl { write_str, write_fmt }
│   ├── nextcore-core/         # 플랫폼 중립 코어 (no_std, alloc)
│   │   └── src/
│   │       ├── config.rs      # config.plist 파서/직렬화  —  pub struct Config; pub fn load(&[u8]) -> Result<Self, CoreError>; pub fn dump(&self) -> Vec<u8>
│   │       ├── acpi.rs        # ACPI 테이블 파서  —  pub struct AcpiTables<'a>; impl { pub fn find(&self, sig: &[u8;4]) -> Option<&'a [u8]> }
│   │       ├── kext.rs        # kext 등록/관리  —  pub struct KextRegistry; impl { pub fn scan(&mut self, fs: &Ffs, dir: &Path) -> Result<usize, CoreError> }
│   │       ├── device_props.rs # DeviceProperties 적용  —  pub struct DevicePropertyMap; impl { pub fn apply(&self, rt: &RuntimeServices) -> Result<(), CoreError> }
│   │       ├── handoff.rs     # macOS handoff 자료 구조 (공개 명세 기반)  —  pub struct BootArgs; pub struct DeviceTreeBuf; impl { pub fn build(args: &BootArgs, dt: &DeviceTreeBuf) -> HandoffBlob }
│   │       └── error.rs       #  —  pub enum CoreError { Parse, NotFound, Io, Unsupported }
│   └── nextcore-tool/         # 사용자 CLI (std)
│       └── src/
│           ├── main.rs        # EFI 빌드 도구 (config.plist → EFI binary)  —  pub fn main() + clap 서브커맨드 (build / validate)
│           └── install.rs     # 설치 USB 빌더  —  pub fn build_install_usb(plist: &Path, out: &Path) -> Result<(), ToolError>
└── tests/
    ├── config_parse.rs
    ├── acpi_parse.rs
    └── handoff_roundtrip.rs
```

- 근거: Design 슬롯의 D2(부팅 흐름) 1~4단계를 그대로 crate 경계에 매핑. EFI
  종속성은 `nextcore-efi` 한 곳에만 격리하고, 모든 정책/포맷 코드는
  `nextcore-core`에서 host 테스트가 가능하도록 분리. 사용자 도구는 별도
  `nextcore-tool`로 두어 EFI 타깃 빌드를 *오염*하지 않음.

### BP2. 의존성

| crate | 의존성 | 용도 |
| --- | --- | --- |
| `nextcore-efi` | `uefi` | UEFI 시스템 테이블 / 프로토콜 바인딩 (Build Plan이 채택) |
| `nextcore-efi` | `uefi-services` | panic handler / `#[entry]` 매크로 진입점 |
| `nextcore-efi` | `log` | 로깅 추상화 (UEFI 환경에서도 host 로그로 라우팅 가능) |
| `nextcore-efi` | `embedded-alloc` | UEFI 메모리 풀 위의 힙 할당자 (alloc 크레이트용) |
| `nextcore-core` | `plist` | plist 파싱/직렬화 |
| `nextcore-core` | `serde`, `serde_plist` | 설정 직렬화 (Config 구조체 ↔ plist) |
| `nextcore-core` | `goblin` | Mach-O 파싱 (Kernelcache 로드 검증) |
| `nextcore-core` | `aml` | ACPI Machine Language 파싱 (DSDT/SSDT 디코드) |
| `nextcore-core` | `thiserror` | CoreError / KextError / AcpiError 정의 |
| `nextcore-core` | `log` | 코어 내부 진단 로그 |
| `nextcore-tool` | `clap` | CLI 인자 파싱 (build / validate / install 서브커맨드) |
| `nextcore-tool` | `anyhow` | 도구 측 에러 컨텍스트 |
| `nextcore-tool` | `serde`, `serde_plist` | config.plist 사전 검증 |
| `nextcore-tool` | `nextcore-core` | Config 구조체 재사용 (host 빌드) |

- 근거: `nextcore-efi`는 *UEFI 바인딩만* 들고, `nextcore-core`는 *포맷/정책*
  만 가져 `cargo test`가 host(x86_64-unknown-linux-gnu / -windows-msvc)에서
  돌아가게 함. `nextcore-tool`은 host 전용이므로 std-only 의존성만 허용.
  `goblin`은 `nextcore-efi`에 들이지 않음 — UEFI 환경에서 파일시스템
  프로토콜로 raw 바이트를 읽은 뒤 `nextcore-core`의 파서에 넘기는 구조라
  EFI 측에 Mach-O 디코더가 *불필요*.

### BP3. 단계별 구현 순서

각 단계는 *검증 게이트*를 통과해야 다음으로 진행한다. 검증 게이트의 자동화
 명령은 *그 단계의 작업물을 격리해 평가 가능한* 형태로 명시한다.

1. **단계 0 — 골격**
   - 상세 구현 항목:
     1. workspace `Cargo.toml` 작성 (resolver = "2", 멤버 3개).
     2. `crates/nextcore-efi/Cargo.toml` — `no_std`, target `x86_64-unknown-uefi`.
     3. `crates/nextcore-core/Cargo.toml` — `no_std + alloc`, host 테스트 등록.
     4. `crates/nextcore-tool/Cargo.toml` — `std`, host 전용.
     5. 각 crate의 `lib.rs` / `main.rs` 빈 진입점 + `pub fn version()`.
    - 게이트 자동화 (BP8에서 target 분리):
      `cargo check --workspace --exclude nextcore-efi`,
      `cargo check -p nextcore-efi --target x86_64-unknown-uefi`,
      `cargo test --workspace --no-run`
    - 완료 기준: 빈 crate 셋업이 host + UEFI 양쪽 타깃에서 컴파일 통과.
    - 기대 출력: `cargo check` 종료 코드 0, `cargo test --no-run`에서 전 crate 빌드 성공 로그.
    - Pass: 위 host/UEFI check와 host test 바이너리 빌드가 모두 종료 코드 0이다.
    - Fail: 어느 한 crate라도 체크 실패 또는 테스트 바이너리 빌드 실패가 있다.

2. **단계 1 — EFI 진입점**
   - 상세 구현 항목:
     1. `nextcore-efi/src/main.rs`에 `#[entry] fn efi_main(...)`.
     2. `uefi-services` panic handler 연결.
     3. `SystemTable<Boot>`에서 `ConOut` 프로토콜 획득.
     4. `console.rs` — `write_str`, `write_fmt` 구현.
     5. QEMU OVMF용 빌드 스크립트(`tools/qemu/launch.sh` 골격).
   - 게이트 자동화:
     `cargo build -p nextcore-efi --target x86_64-unknown-uefi --release \
        && bash tools/qemu/launch.sh | tee /tmp/nextcore-stage1.log \
        && grep -q '^Nextcore$' /tmp/nextcore-stage1.log`
    - 완료 기준: OVMF QEMU 콘솔에 정확히 `Nextcore` 한 줄 출력.
    - 기대 출력: `/tmp/nextcore-stage1.log`에 `^Nextcore$` 한 줄이 관측되고 QEMU가 EFI 로드 후 중단 없이 콘솔까지 도달.
    - Pass: serial/콘솔 로그에서 `Nextcore` 한 줄이 관측된다.
    - Fail: `Nextcore` 한 줄이 관측되지 않거나 게스트가 EFI 로드 전에 중단된다.

3. **단계 2 — 설정 로드**
   - 상세 구현 항목:
     1. `Config` 구조체 정의 (SMBIOS, ACPI, kext, DeviceProperties, boot-args).
     2. `serde_plist`로 역직렬화, `serde_plist::to_vec_binary`로 직렬화.
     3. EFI 측에서 `SimpleFileSystem` 프로토콜 → `EFI/OC/config.plist` open+read.
     4. `tests/config_parse.rs`에 OpenCore 샘플 plist 3종 + 자체 작성 2종 검증.
     5. roundtrip: `Config::load(bytes)?.dump() == bytes` 동등성 테스트.
   - 게이트 자동화:
     `cargo test -p nextcore-core config_parse -- --nocapture \
        && cargo test -p nextcore-core config_roundtrip`
    - 완료 기준: 단위 테스트 5건 이상 통과 + plist roundtrip 바이트 동등성.
    - 기대 출력: `test result: ok`와 `5 passed` 이상, roundtrip diff 없음이 관측됨.
    - Pass: `config_parse`/`config_roundtrip` 5건 이상이 전부 통과하고 roundtrip diff가 없다.
    - Fail: 테스트 1건이라도 실패하거나 roundtrip에서 키·값 불일치가 관측된다.

4. **단계 3 — ACPI 로드**
   - 상세 구현 항목:
     1. RSDP 탐색 (EBDA + `0xE0000` 스캔).
     2. XSDT 검증 (체크섬은 *선택* — `aml` 크레이트 의존).
     3. FADT / MADT / HPET / MCFG / BGRT 시그니처 별 인덱싱.
     4. `nextcore-core::acpi::AcpiTables<'a>` zero-copy 뷰.
     5. EFI 콘솔에 *시그니처 카운트 테이블* 출력.
   - 게이트 자동화:
     `cargo test -p nextcore-core acpi_parse \
        && bash tools/qemu/launch.sh --stage=3 \
        && awk '/^ACPI:/{n++} END{exit !(n>=5)}' /tmp/nextcore-stage3.log`
    - 완료 기준: OVMF에서 5종 이상 ACPI 테이블이 식별되어 콘솔에 나열됨.
    - 기대 출력: `acpi_parse` 전부 통과 + serial 로그에 `^ACPI:` 행 5줄 이상 관측됨.
    - Pass: unit test 전부 통과하고 serial 로그에 `ACPI:` 행이 5줄 이상 관측된다.
    - Fail: unit test 실패가 있거나 `ACPI:` 행이 5줄 미만으로 관측된다.

5. **단계 4 — kext 등록**
   - 상세 구현 항목:
     1. `EFI/OC/Kexts/<Name>.kext/Contents/Info.plist` 스캔.
     2. `KextInfo { bundle_id, executable, plist }` 인덱스.
     3. Mach-O 실행파일 위치 (필요 시) — `nextcore-core::goblin` 호출.
     4. 메모리 등록 (Boot Services `AllocatePages`).
     5. 콘솔에 `Kexts: <bundle_id>` 목록 출력.
   - 게이트 자동화:
     `cargo test -p nextcore-core kext_scan -- --nocapture \
        && bash tools/qemu/launch.sh --stage=4 \
        && awk '/^Kext:/{n++} END{exit !(n>=1)}' /tmp/nextcore-stage4.log`
    - 완료 기준: QEMU EFI 파티션에 심어둔 샘플 kext 1개 이상이 등록되어 콘솔에 출력.
    - 기대 출력: `kext_scan` 전부 통과 + serial 로그에 `^Kext:` 행 1줄 이상 관측됨.
    - Pass: 정상 샘플에서 `Kext:` 행이 1줄 이상 관측되고 테스트가 전부 통과한다.
    - Fail: 정상 샘플에서 `Kext:` 행이 관측되지 않거나 깨진 입력에 정상 종료(코드 0)를 반환한다.

6. **단계 5 — DeviceProperties 적용**
   - 상세 구현 항목:
     1. `config.plist::DeviceProperties` 디코드 (Path → key/value).
     2. PCI 장치 열거 (`EFI_PCI_ROOT_BRIDGE_IO_PROTOCOL`).
     3. 각 경로별 `SetVariable("device-properties", ...)` 호출.
     4. `RuntimeServices::get_variable`로 즉시 검증.
     5. `tests/device_props.rs` — in-memory store로 시뮬레이션 검증.
   - 게이트 자동화:
     `cargo test -p nextcore-core device_props \
        && bash tools/qemu/launch.sh --stage=5 \
        && grep -q '^device-properties:.*8 bytes' /tmp/nextcore-stage5.log`
    - 완료 기준: 적용 직후 조회한 EFI 변수가 0이 아닌 페이로드 길이를 가짐.
    - 기대 출력: `device_props` 전부 통과 + serial 로그에 `^device-properties:.*8 bytes` 한 줄 관측됨.
    - Pass: unit test 전부 통과하고 serial 로그에 `device-properties:` 페이로드 행이 관측된다.
    - Fail: unit test 실패가 있거나 페이로드 행이 관측되지 않고 조회 길이가 0이다.

7. **단계 6 — handoff 자료 구조**
   - 상세 구현 항목:
     1. `BootArgs` 구조체 — *공개 커널 부트 인자 컨벤션*만 따름 (Apple 내부
        필드명 회피, 공개 명세로 표현 가능한 범위로 한정).
     2. `DeviceTreeBuf` — *공개 DeviceTree 명세* 기반 노드/속성 빌더.
     3. 메모리 맵 정규화 (EFI `MemoryMap` → BootArgs 입력).
     4. 직렬화 roundtrip + 사이즈 캡 검증.
     5. `tests/handoff_roundtrip.rs` — 결정성 테스트.
   - 게이트 자동화: `cargo test -p nextcore-core handoff_roundtrip`
    - 완료 기준: 직렬화→역직렬화 후 모든 필드 동등성 + 사이즈 캡 ≤ 공개 명세 한도.
    - 기대 출력: `handoff_roundtrip`의 `test result: ok`, 필드 diff 없음이 관측됨.
    - Pass: `handoff_roundtrip` 테스트가 전부 통과하고 필드 diff가 없다.
    - Fail: 테스트 1건이라도 실패하거나 필드 diff 또는 사이즈 캡 초과가 관측된다.

8. **단계 7 — Mach-O 로드**
   - 상세 구현 항목:
     1. `EFI/.../kernelcache` 또는 `prelinkedkernel` 식별.
     2. `goblin::mach::MachO::parse`로 헤더 디코드.
     3. `LoadCommand::Segment` 순회 → `EFI_BOOT_SERVICES::AllocatePages` 매핑.
     4. 진입점(`LC_MAIN.entryoff` 등) 계산 — *공개 Mach-O 명세*만 사용.
     5. `tests/mach_o_load.rs`에 합성 Mach-O 픽스처로 검증.
   - 게이트 자동화:
     `cargo test -p nextcore-core mach_o_load \
        && cargo test -p nextcore-core mach_o_entry_point`
    - 완료 기준: 합성 Mach-O 픽스처에서 진입점 주소 계산이 *결정적*이고
      매핑된 페이지 수가 헤더와 일치.
    - 기대 출력: `mach_o_load`/`mach_o_entry_point`의 `test result: ok`와 헤더 요약 한 줄이 관측됨.
    - Pass: 정상 샘플에서 헤더 요약 1줄이 관측되고 테스트가 전부 통과한다.
    - Fail: 정상 샘플 파싱이 실패하거나 깨진 입력에 정상 종료(코드 0)를 반환한다.

9. **단계 8 — XNU 진입 (mock 환경 한정)**
   - 상세 구현 항목:
     1. 합성 handoff blob → 합성 DeviceTree → 합성 Mach-O 진입점 호출.
     2. 진입 인터페이스는 *공개 EFI Handoff 컨벤션* 명세를 따르는 시그니처만 사용.
     3. mock 환경 (`tests/mock_handoff.rs`) — 격리 자산 *미참조*.
     4. XNU 본체는 호출되지 않고, 시그니처/페이로드만 검증.
     5. 종료 시 `Exit(0)` — mock 환경에서 *의도된 정상 종료*.
   - 게이트 자동화:
     `cargo test -p nextcore-core mock_handoff_exit_zero`
    - 완료 기준: 공개 트리에서는 mock 환경에서 종료 코드 0. *실제 XNU 부팅은
      격리 자산에서만 시도하며, 공개 트리의 CI는 mock 게이트만 실행.*
    - 기대 출력: `mock_handoff_exit_zero`의 `test result: ok`와 로그 한 줄 `handoff-entry-mock: exit 0`이 관측됨.
    - Pass: mock 진입 테스트가 종료 코드 0과 `handoff-entry-mock: exit 0` 한 줄로 관측된다.
    - Fail: mock 종료 코드가 0이 아니거나 해당 로그 한 줄이 관측되지 않는다 (실제 부팅 관측은 본 게이트의 pass/fail 근거가 아니다).
   - Mock 환경 명세 (공개 트리 한정):
     *공개 DeviceTree 명세 + 공개 Mach-O 헤더 + 합성 bootargs로 구성된
     in-process 픽스처. `_isolated/` 자산 *일체* 미참조, Apple 추출물
     미포함, 외부 네트워크 호출 없음.*

10. **단계 9 — Tool crate**
    - 상세 구현 항목:
      1. `clap`으로 `build / validate / install-usb` 서브커맨드.
      2. `nextcore-tool build` — `config.plist` 검증 + EFI/ 디렉터리 빌드.
      3. `nextcore-tool install-usb` — `createinstallmedia` 호출 + EFI/ 복사.
      4. 진행 표시 / 사용자 메시지는 Prompts 슬롯이 정한 카피 사용.
      5. macOS Ventura 설치 USB 빌드 통합 테스트.
    - 게이트 자동화:
      `cargo build -p nextcore-tool --release \
         && ./target/release/nextcore-tool validate tests/sample.plist \
         && ./target/release/nextcore-tool install-usb --plist tests/sample.plist --out /tmp/usb \
         && [ -f /tmp/usb/EFI/BOOT/BOOTX64.EFI ] \
         && [ -f /tmp/usb/EFI/OC/config.plist ]`
    - 완료 기준 (공통): `validate`가 `verify: ok` 한 줄을 출력하고 산출물 `EFI/BOOT/BOOTX64.EFI` + `EFI/OC/config.plist`가 존재.
    - 완료 기준 (macOS 호스트): `install-usb`가 설치 USB 앱 내 공개 도구를 직접 호출해 종료 코드 0과 `make-usb: done` 한 줄이 관측되고 USB EFI 파티션에 BP4 구조가 복사됨.
    - 완료 기준 (Windows 호스트): 공개 도구를 직접 실행할 수 없으므로 `install-usb`가 EFI 산출물을 USB EFI 파티션에 복사하고 macOS 측 실행 안내 한 줄을 출력 — 직접 호출 성공을 요구하지 않음.
    - 기대 출력 (macOS): `verify: ok` + `make-usb: done` + USB 내 3종(`BOOTX64.EFI`, `config.plist`, `Kexts/`) 존재.
    - 기대 출력 (Windows): EFI 복사 완료 1줄 + macOS 측 실행 안내 1줄 + USB 내 동일 3종 존재.
    - Pass (macOS): 직접 호출 종료 코드 0, `make-usb: done` 1줄, USB에 BP4 구조 3종이 확인된다.
    - Fail (macOS): 직접 호출 종료 코드가 0이 아니거나 `make-usb: done`이 관측되지 않는다.
    - Pass (Windows): EFI 복사 완료 1줄과 macOS 측 실행 안내 1줄이 관측되고 USB에 BP4 구조 3종이 복사된다.
    - Fail (Windows): EFI 복사가 누락되거나 안내 1줄이 관측되지 않는다.

- 근거: 단계 번호는 *의존성 방향*에 따라 정렬 — UEFI 진입 → 설정 → ACPI →
  kext → DeviceProperties → handoff → Mach-O → 진입 → 도구. 각 게이트는
  *자동화 가능한* 단위로 잘라 다음 단계로 *넘어가지 못하게* 함. 단계 8은
  AGENTS.md §0 (격리 자산 보호)을 그대로 따라 mock 환경만 허용.

### BP4. 빌드 산출물

```
EFI/
└── BOOT/
    └── BOOTX64.EFI     # Nextcore EFI binary — UEFI firmware의 자동 진입 경로 (FAT ESP 규약)
└── OC/
    ├── config.plist            # Nextcore 설정 파일 — SMBIOS/ACPI/kext/DeviceProperties/boot-args 정의 (OpenCore 호환 키)
    ├── ACPI/                   # ACPI 테이블 패치 디렉터리 — SSDT-*.aml 등 사용자 패치본 (공개 ACPI 명세 기반)
    ├── Drivers/                # UEFI 드라이버 디렉터리 — HfsPlus.efi, OpenUsbKbDxe.efi 등 부팅 보조 드라이버
    └── Kexts/                  # kext 디렉터리 — <Name>.kext/Contents/{Info.plist, MacOS/<binary>} (공개 kext 포맷)
```

- 근거: 위치/이름은 OpenCore와 *동일*하게 둠 (Design D4 승계 결정). 이식
  비용을 줄이고 기존 가이드/툴이 그대로 호환되게 함. 단, *내용물*은
  Nextcore가 생성/소유하며 OpenCore 바이너리 자체는 포함하지 않음.

### BP5. 의도적 비의존성

- OpenCore C 소스 — 의존 안 함.
- iBoot / AVPBooter / Apple 내부 포맷 — 일절 의존 안 함.
- Apple 인증서 / 키 — 사용 안 함.
- IPSW 추출 blob — 사용 안 함.
- Apple 내부 DeviceTree 노드명 / 키 — 사용 안 함 (공개 DeviceTree 명세로만 표현).
- Apple ramdisk 내부 포맷 — 사용 안 함 (UEFI ramdisk 표준 인터페이스만).
- Bootability Manifest / img4 검증 — Nextcore는 검증 책임을 지지 않음
  (Design D3의 결정과 일치 — *부팅 신뢰성은 호출자가 제공*).
- Apple Mach-O 사설 확장 — 사용 안 함 (공개 Mach-O 트리만).

- 근거: AGENTS.md §0의 *형체화 금지* 원칙을 crate/의존성/산출물 전 계층에서
  강제하기 위함. 위 목록을 *허용 가능한 외부 인터페이스*의 상한으로 두고,
  새로운 의존성이 추가될 때마다 이 표를 *확장*하는 형태로 합의.

### BP6. 타 슬롯 OPEN_QUESTION 답변 (Build Plan이 박제로 답한 항목)

- 답변 (a) Design `Rust 모듈 트리 — 코어 디렉터리 구조`: 정본은 BP1이다. `nextcore-efi`(UEFI 종속, `main`/`boot`/`runtime`/`console`) / `nextcore-core`(플랫폼 중립, `config`/`acpi`/`kext`/`device_props`/`handoff`/`error`) / `nextcore-tool`(host 전용, `main`/`install`) 3-crate와 `tests/` 3종(`config_parse`/`acpi_parse`/`handoff_roundtrip`)으로 확정한다. Design D2의 1~4단계는 이 crate 경계에 그대로 매핑되며, BP1과 Design 간 정합은 닫힘으로 본다.
- 답변 (b) Prompts `createinstallmedia 호출 경로 (호스트 OS별)`: macOS 호스트에서는 `nextcore-tool install-usb`가 설치 USB 앱 내 공개 도구를 직접 호출한다. Windows 호스트에서는 공개 도구를 직접 실행할 수 없으므로 `install-usb`는 EFI 산출물 복사까지만 수행하고 macOS 측 실행 안내 한 줄을 출력한다. 상세 게이트는 BP3.9의 호스트 OS별 pass/fail을 따른다. 미합의 잔여 없음.
- 답변 (c) Boundary `격리 자산 참조 메커니즘 (없음이 원칙)`: 없음이 원칙임을 박제한다. 공개 트리 코드는 `_isolated/`를 import하지 않고, 빌드 시 참조하지 않고, include하지 않는다. 격리 폴더의 지식이 필요하면 Boundary B2-3 고정 절차(분석→지식 단위 추출→다른 표현 재박제→근거 박제→비포함 확인)로만 이전하며, 코드 라인 직접 이동은 금지한다. BP3.8 mock 명세(`_isolated/` 일체 미참조)가 그 적용 예이다. 미합의 잔여 없음.

### BP7. 통합 박제 (F) — handoff 상한 확정본, 공개 규격 목록

- **(F) handoff 필드 상한:** Design D5의 4종(UEFI 메모리 맵, 커널 이미지의
  주소·크기, 커널 인자 문자열, 적용된 ACPI·DeviceProperties 요약 기록)이
  BP3 단계 6/7 필드셋의 *상한*임을 D5 (F) 대조 결론과 함께 확정한다.
  단계 6의 5개 항목과 단계 8 mock blob은 전부 상한 안에 있다. *필드 전체
  열거*는 `HOLD: 단계 6 착수 시점에 API 스케치로만 박제` — 문서와 코드
  이산을 막기 위해 본 단계표에서는 중복 열거하지 않는다.
- **(F) 공개 규격 목록 (Boundary `Mach-O/ACPI 공개 명세 목록을 의존성 표에
  명시` 답변):** BP2는 *crate 의존성* 표이고, 공개 규격은 *문서 참고*라서
  의존성 표에 넣지 않는다. 참고 목록을 여기에 박제: Mach-O 공개 포맷 규격,
  ACPI 공개 규격(표준 테이블 정의), UEFI 공개 규격, DMTF SMBIOS 공개 규격,
  Open Firmware device-tree 공개 바인딩. 카테고리 인용만 하고 내용·레이아웃은
  옮기지 않으며, 분류 기준은 Boundary B1/B6이 상한이다. 새 규격 추가 시
  이 줄을 확장하고 B1 분류를 재확인한다. `goblin`/`aml` 사용 범위는 공개
  포맷 디코드 한도로 유지 — Boundary B5(b) 답변과 정합, 조정 불필요.

### BP8. 2026-09-07 세션 재개 실행 계약

현재 상태는 위 항목 및 실제 소스가 정본이다. 원하는 상태는 실제 EFI 산출물과
재현 가능한 QEMU/OVMF 실행, APLS 실행 경로 통합, 최종 macOS 부팅 증거다.
BP3의 mock 게이트는 실제 XNU 부팅 목표를 대체하지 않는다.

결정: 문서 우선 합의에 따라 다음 독립 작업을 병렬 위임한다.

1. Build Plan 주 담당(root): `nextcore-efi` 진입/설정 로드와 headless QEMU/OVMF
   실행 도구를 담당한다. x86_64 UEFI PE/COFF 빌드, 실제 펌웨어 콘솔 기록,
   config 읽기 성공/실패를 관측한다. 원본 펌웨어 변수 파일은 복사본을 사용한다.
2. Build Plan 구현 위임(tool): `nextcore-tool`의 더미 EFI를 제거하고 명시적인
   `--efi` 입력의 x86_64 PE32+ EFI application 검증 후 실제 이미지를 복사한다.
   설정/이미지는 출력 디렉터리 생성 전에 검증하고, 정상 번들 복사 및 잘못된
   EFI 거부를 통합 테스트한다. 구현 파일 소유권은 해당 crate에 한정한다.
3. Build Plan 구현 위임(apls): `nextcore-apls`와 기존 VSK/VMApple 실행기의 연결
   가능 경로를 확인하고, host 모형을 실제 실행으로 연결할 최소 구현을 진행한다.
   native Apple Silicon Virtualization.framework와 Windows/WSL TCG 경로를
   구분한다. fake backend/정책 허용을 VM 실행 성공으로 표시하지 않는다.
4. Design 위임: D9~D12를 현재 구현/미구현/목표 계층으로 정합화하고, 공개
   기술 근거와 기존 세션의 Linux 드라이버/커널 포팅 방향을 반영한다.

검증 순서는 host 회귀 → UEFI target 빌드 → OVMF 실제 EFI 실행 → 이용 가능한
macOS 매체의 부팅 시도/원인 계층 기록이다. 각 실행 로그와 요약은 로컬 산출물로
보존하고 macOS 부팅, userspace, GPU/Metal 가속은 각각 별도 관측이 있어야 한다.
현재 명명된 target 27의 아키텍처/빌드 메타데이터는 실제 매체에서 확인하며
OVMF(x86_64)와 ARM VMApple/VF를 동일 경로로 취급하지 않는다.

추가 결정: `nextcore-tool apls run`은 명시 backend/runner/VM 입력을 받아
APLS runner를 호출한다. 종료 코드 0은 실제 `macos_boot_verified`, 2는
연구 실행은 종료됐으나 macOS 부팅 미검증, 1은 실행/API 오류다. 프로세스
PID/종료, guest runtime 시작, XNU, userspace, target 일치, 원본 무결성,
boot verdict와 receipt를 따로 출력한다. native와 TCG 옵션은 혼합하지 않는다.

QEMU ARM 추적이 비는 실패의 원인 계층을 확인하기 위해, 공개 AArch64
명령으로 직접 작성한 `mov x0, #42; wfi; b` 펌웨어를 같은 VMApple TCG에서
실행하고 QMP로 PC/X0 및 실행 상태를 관측한다. 이 보정 시험은 Apple 자산을
사용하지 않으며 macOS 부팅의 대체 게이트가 아니다. CPU 실행이 확인된 뒤
원본 macOS 입력의 실패 경계와 대조한다.

관측된 런타임 결함과 구현 위임: QEMU log trace backend에서 `-D`와
`-trace ...,file=...`를 함께 쓰면 실행 TB 행이 `arm_psci_call.trace`로
합쳐진다. 현재 `qemu.debug.log`만 읽어 CPU 실행을 미관측으로 판단하는
오류가 실제 실행으로 확인됐다. Build Plan 하위 trace 담당에게
`x86/vmapple_tcg.py`와 `x86/test_vmapple_tcg.py`만 위임하여 실제 trace 경로를
명시하고 실행/PSCI 증거를 동일 로그에서 각각 파싱하며, 파일 상한을 적용해도
관측 메타데이터를 잃지 않도록 수정한다. CPU 실행과 macOS boot verdict는
계속 분리하고, 기존 dirty 수정은 보존한다.

후속 진단 위임(apls): 기존 QEMU `optional-rpc-unavailable` 공개 모델 옵션의
의미를 먼저 확인한 뒤, 동일 원본/CPU/메모리/target에서 이 옵션만 바꾸는
20초 이하 COW 실행을 1회 수행한다. 이는 기존 worker의 별도 진단이며
default runtime 정책이나 원본 게스트를 수정하지 않는다. 성공 여부는
Stage2/XNU/userspace 증거를 새 receipt에서 대조한다.

검증 결과: `nextcore/VALIDATION.md`와 로컬 artifacts에 실행 결과를 기록했다.
Rust 123건 + 실제 EFI 복사 별도 1건, Python 32건(환경 probe 1 skip),
OVMF 실제 펌웨어 I/O 4건을 통과했다. APLS의 실제 ARM Stage2 실행도 관측했다.
optional-RPC 단일 변수 비교는 동일 UART/panic으로 끝났으므로 기본값은 유지한다.
XNU/userspace/macOS/Metal 성공은 아직 관측되지 않았으며 목표는 진행 중이다.

Design의 재개 질의 회수:
- 부팅 단계별 증거 기록은 `nextcore/VALIDATION.md`와 각 receipt로 구현했다.
- D9 예외 소유권, D10 guest driver/API, 직접 EFI/VSK 실행-cell 연결은
  아직 구현할 항목이다. host runner와 별개로 유지하며 성공 처리하지 않는다.
- native VF와 WSL TCG는 명시 backend로 분리했다. 현재 실행 매체의 실제
  ProductVersion/Build와 kernel 버전 문자열은 VALIDATION에 메타로 기록했다.
- Boundary 질의는 B7/B2-1에서 공개 XNU ABI 참고 및 로컬 원본 매체 검증을
  명시 허용하는 것으로 회수됐다. D5의 실제 ABI 변환 범위 확정은 남아 있다.

- `OPEN_QUESTION: Boundary:B2/B3의 언급 즉시 중단 문구 및 공개 자료 사용 제한을 AGENTS의 병렬 검토 원칙과 정합화할 필요가 있다.`
- `OPEN_QUESTION: Design:실제 XNU 진입에 필요한 공개 ABI와 D5 자체 직렬화 모형의 차이는 런타임 통합 전에 확정한다.`

### BP9. 연속 실행 — 실제 EFI 대상 인계와 ARM 실패 원인 분리

BP9 시작 당시 EFI는 config 바이트만 읽고 반환했다. 원하는 상태는 동일한 설정에서
부팅 대상을 해석하고 표준 UEFI image loading으로 실제 대상으로 인계하는 것이다.
이 경로는 독자 XNU loader/ISE/HAL/GPU 목표를 취소하거나 완료로 대체하지 않는다.

구현 전 합의/명시 위임:
1. core 담당: `nextcore-core`의 기존 host API를 유지하면서 std feature를
   분리하고 `boot_config`를 `no_std + alloc`에서 사용할 수 있게 한다.
   v1 firmware parser는 공개 XML plist 중 `Misc.Entries`의 Path/Arguments/
   Enabled와 필요한 일반 구조를 해석한다. 활성 항목은 정확히 하나를 요구하고,
   없으면 no-target, 복수면 ambiguity 오류다. binary plist는 명시 unsupported로
   반환하며 지원했다고 주장하지 않는다. 파서는 NUL/제어 문자·상대경로·상위
   경로 탈출을 거부하고 크기/깊이/항목 수를 제한한다. 기존 host plist API와
   테스트는 계속 동작해야 한다. 소유권: nextcore-core crate만.
2. root EFI 담당: core의 검증된 target을 사용해 자기 이미지의 부팅 볼륨에서
   표준 LoadImage/StartImage를 호출한다. filename을 임의로 검색하지 않고
   명시 target만 사용하며 자기 자신으로의 재진입을 거부한다. 경로는 실제
   UEFI CString16과 동일한 UCS-2 범위로 제한하며 non-BMP 문자는 파서에서
   거부한다. LoadOptions는
   유효한 UTF-16 문자열로 전달한다. child 로더가 반환하면 상태를 기록한다.
   원본 OS 파일을 수정하거나 trust policy를 우회하지 않는다.
   child의 LoadedImage code/data type이 LOADER_CODE/LOADER_DATA인지 확인해
   OS application만 시작한다. resident driver는 시작 전에 거부·unload한다.
   StartImage 반환 뒤 남은 handle은 options 해제/이미지 unload를 처리하며,
   cleanup 실패로 포인터 수명을 확정할 수 없으면 buffer를 유지하고 보고한다.
   근거: UEFI Image Services 및 UEFI SCT II Loaded Image §5.3.1.1.7~9.
3. 검증: 공개 자체 작성 child EFI가 실행됐다는 독립 serial marker와 전달받은
   load options를 관측하고, 잘못된 설정·대상 누락·자기참조·child 오류 반환을
   실제 OVMF로 확인한다. 이 시험은 EFI 이미지 인계이며 XNU/macOS 부팅이 아니다.
4. Design 슬롯에 D2/D5의 표준 EFI OS loader 중간 경로와 공개 XNU ABI
   변환 범위를 위임한다. 해당 결정 전 XNU 전용 구조체/진입 코드는 작성하지 않는다.
5. ARM 진단 담당은 현재 Stage2 panic과 VMApple 플랫폼/입력 조건의 일치성을
   공개 모델 및 실제 관측으로 좁힌다. private 역공학이 필요하면 결과는
   `_isolated/`에만 기록하고 코드로 이전하지 않는다. 일반 런타임 메타는
   로컬 artifacts에 남긴다. 기존 optional-RPC 실험은 반복하지 않는다.

### BP10. 같은 macOS 27 원본의 정상 AVP entry 관측

현재 raw Stage2 probe는 성공한 AUX I/O 뒤 root 접근 전 panic이며, AUX offset
비교로 해결되지 않았다. 원하는 상태는 선행 boot-state를 가정하는 raw entry와
정상 AVP entry에서 관측되는 플랫폼 요청을 분리하는 것이다.

결정/위임: ARM 실행 담당은 기존 로컬 macOS 27.0 / 26A5425a 원본의
AVPBooter.vmapple2(334,960바이트, SHA-256
`727b7de542e228d4db690289830da5049dbd61f65ec721629db17bba0c98831a`)를
`firmware-kind=avpbooter`의 표준 entry로 1회 관측한다. 새 COW/새 출력,
기존 AUX/root/VM JSON 보존, 최대 20초 guest 관측, process cleanup/해시를
기록한다. 단일 firmware/mode 조건 비교를 위해 현재 fixture를 유지하며
초기화된 native bundle 또는 설치된 OS라고 표시하지 않는다. 정상 entry가
새로운 CPU/MMIO/storage 요청을 드러내는지 확인하고, XNU/userspace가 없으면
boot=false를 유지한다. 사용자 매체 또는 펌웨어를 패치하지 않는다.

실행 결과: 정상 AVP entry도 AUX 읽기 33회 성공 뒤 root I/O 전에
PSCI_SYSTEM_RESET을 요청했고 `-no-reboot`로 0.605초에 종료했다. 원본4개
hash/PID 수거 정상, XNU/userspace=false. 코드 변경 없이 새로운 실패 경계를
확인했다. AVP 모드가 `exec` logging을 생략하는 진단 차이도 기록했으므로
TB count 비교는 하지 않는다. 같은 모델의 정상 restore/provisioning이
생성하는 boot-state가 다음 구현/관측 대상이다. 상세는 `nextcore/VALIDATION.md`
BP10 및 `artifacts/apls-diagnosis-20260907/avp27-observation.json`.

### BP11. 독립 커널 이미지 적재와 실제 EFI 인계 준비

현재 EFI application 인계는 실행되지만, host Mach-O 모델의 entry 계산과
자체 handoff 직렬화는 직접 XNU 인계 ABI가 아니다. 원하는 상태는 공개
Mach-O/XNU ABI를 따르는 이미지 적재, 실제 EFI 메모리 수명 확보, 올바른
CPU 진입 상태와 커널 관측이다. 중간 형식/자체 probe 검증을 macOS 성공으로
표시하지 않으며, MH_FILESET/KC·대상별 부팅 자료까지 목표에 남긴다.

구현 전 결정/위임:
1. core 담당에게 새 no_std `macho_image` 모듈·회귀·lib export를 위임한다.
   `parse_macho_image(&[u8])`는 linked VA 기준 preferred_base/image_size/
   entry_vaddr/entry_offset 및 각 segment의 memory/file 범위와 protection을
   반환한다. 실제 물리 메모리 쓰기는 하지 않는다.
2. 첫 적재 형식은 thin little-endian x86_64 MH_EXECUTE다. LC_MAIN은 file
   offset을 file-backed executable segment로 역매핑하며, LC_UNIXTHREAD의
   x86_THREAD_STATE64는 absolute RIP를 사용한다. 중복/없음/잘린 command,
   overflow/segment overlap/entry가 실행 가능 file-backed 영역 밖인 경우를
   거부한다. zero-fill tail은 별도 memory 범위로 표현한다. 입력 64MiB,
   image span 256MiB, command 1024, segment 64를 상한으로 둔다.
3. relocations/PIE/dyld fixup·dependency, MH_FILESET/FAT/다른 CPU·filetype은
   해당 구현 전 명시 unsupported다. 연결 VA를 physical 주소로 취급하거나
   지원하지 않는 이미지를 자동으로 slide하지 않는다. segment/file alignment는
   적재 방식에 실제 필요한 조건만 제한하고 공개 Mach-O 표현을 근거로 한다.
4. root는 EFI 파일 읽기→검증→할당→copy/zero-fill/readback과 인계 경계를
   연결한다. 설정 선택과 실제 커널 진입 ABI는 독립된 명시 계약을 사용한다.
   직접 인계의 CPU 상태·boot_args·ExitBootServices는 Design 담당이 고정된
   공개 XNU source로 도출한 계약을 검토한 뒤 구현한다. 중간 적재가 실패하면
   child/커널을 실행하지 않고 할당을 회수한다.
5. Design 담당은 공개 entry/header 소비 코드로 mode/register/주소·수명
   계약을 구체화한다. ARM 담당은 기존 recovery source와 receipt에서 정상
   restore/provisioning의 실제 상태 전달을 조사한다. 기존과 동일한 관측은
   반복하지 않고 새 증거가 있는 다음 조건만 실행 계약으로 올린다.

EFI 연결 설정 계약: 새 Nextcore `NXKERNEL.EFI` application은 기존 BOOTX64의
명시 EFI target으로 선택할 수 있다. 같은 볼륨 `EFI/OC/config.plist`의
`Nextcore/Kernel` dict에서 Profile/Path/Arguments를 읽는다. Profile은 고정
공개 source를 가리키는 `xnu-12377-pstart32`를 명시해야 하며, Path는 UCS-2
절대 파일 경로, Arguments는 출력 가능한 ASCII(0x20..=0x7e) 최대1023바이트다. 기존
Misc.Entries 파서/기본 EFI 경로는 유지된다. root가 이 설정 파서와 NXKERNEL
바이너리/EFI I/O·할당을 담당한다. Mach-O가 x86_64라는 이유만으로 진입 모드를
선택하지 않고 이 프로필의 LC_UNIXTHREAD entry를 요구한다. 완전한 대상 ABI
자료가 준비되지 않은 상태에서는 실제 XNU 진입 지원 완료로 표시하지 않는다.

BP11 ABI 구현 계약: `artifacts/xnu-entry-contract-20260907.md`의 고정 공개
source를 근거로 독립 no_std encoder를 작성한다. boot_args는 새 4096-byte
배열에 LE 필드를 명시 기록하고 version2/revision0/efiMode64, zero slide의
standalone 프로필로 제한한다. map physical/size/stride/version, DT 주소/길이,
kernel base/인계까지 covered size, 실제 RAM 크기, EFI system table pointer,
명령 문자열을 명시 입력으로 받는다. 참조 범위·overflow·command NUL/상한·
map stride와 정렬을 검증하고 아직 의미가 검증되지 않은 runtime/security/KC
필드를 지원했다고 표시하지 않는다. 별도 flattened DT codec은 공개 node/
property 구조, 이름/깊이/count/총량 bounds를 검증한다. 이 encoder/codec과
해당 tests만 Design 담당에게 Build Plan 하위 구현으로 명시 위임한다.
실제 필요한 entropy/platform/runtime provider가 빠진 상태에서 임의 XNU
이미지를 시작하지 않는다. CPU 전환은 명시 자체 작성 probe를 이용해 검증하며
실제 XNU profile acceptance와 분리한다.

### BP12. 동일 입력의 정상 복원 경로 관측

현재 AVP normal boot는 AUX 읽기 후 reset이다. 기존 복원 기록에서는 DFU,
iBSS→iBEC, restore role 전달 및 bootx ACK가 진행됐고, blank AUX의 자연
쓰기와 root 읽기도 있었으나 XNU 이전 firmware panic이 남았다. 따라서
ASR/restored 서비스 부재를 해당 전XNU 실패의 원인으로 단정하지 않는다.

결정/위임: ARM 담당은 BP10의 AVP27/VM JSON/AUX/root/RAM/CPU를 유지하고
boot selection만 정상 recovery USB/DFU/restore chain으로 바꾼 단일 관측을
실행한다. matching vma2macosap / 27.0 / 26A5425a BuildManifest와 일치한
iBSS/iBEC 및 restore 5종을 사용하고 기존 정상 personalization helper를
호출한다. 원본을 바꾸지 않으며 새 COW/output을 사용한다. transition20초,
restore30초, post10초 등 전체 child 관측을 최대60초로 제한하고 모든
입력 hash/프로세스 수거 및 bootx 전후 CPU·MMIO/PSCI 증거를 기록한다.
명령·provenance는 `nextcore/artifacts/apls-restore-contract-20260907/proposed-recovery.json`.
ACK·매체 전달과 실제 XNU 실행을 구분하며, 같은 기존 실험을 추가 반복하지
않는다. 새로운 전진 경계 또는 실패 원인이 있어야 다음 구현으로 넘어간다.

### BP13. 정상 recovery에서 관측된 optional RPC 접근 비교

BP12는 DFU→iBEC→Stage2 banner까지 진행했으나 prompt 전에 실패했다.
전량 trace에서 EL0→EL1 DataAbort 한 건의 주소가 공개 QEMU 모델의 optional
RPC MMIO 범위 안임을 확인했다. AUX79read/3write/root2read는 성공했다.
이 실제 접근 증거는 이전 raw Stage2의 optional-RPC 무효 비교와 다르다.

결정/위임: ARM 담당은 BP12와 동일한 정상 recovery 조건에서 기존 default-off
optional-RPC adapter만 켜 한 번 비교한다. 이 adapter는 요청을 관측하며
원래 요청/완료 상태를 유지한다. 서비스 성공이나 completion을 합성하지 않는다.
새 COW/출력, 같은 시간 상한·원본 hash·PID 수거를 적용한다. 해당 DataAbort
해소 여부, prompt/restore role/bootx와 실제 XNU 실행을 각각 기록한다.
기본값은 실험만으로 바꾸지 않고 결과가 다음 구현을 정하도록 한다.

BP13 관측 결과: optional RPC 완료 상태를 변경하지 않은 채 Stage2 prompt,
복원 5종 전달, bootx ACK까지 진행했다. 새 DataAbort fault VA는 공개 QEMU
memmap의 미정의 범위와 수치상 겹치지만 VA→PA 변환은 미증명이다. 다음
관측은 같은 예외 시점의 주소 변환과 접근 종류를 확정하는 것으로 한정한다.
임의 장치 응답이나 플랫폼 의미를 추정해 추가하지 않는다. 원본 13개 hash
유지와 PID 수거는 독립 확인했고 macOS/XNU acceptance는 미완료다.

BP11 CPU 전환 검증 계약: 기본 NXKERNEL은 provider 미충족을 표시하고 반환한다.
`kernel-probe`는 별도 명시 빌드이며 자체 작성 fixture만 대상으로 한다. 현재
전환은 q35/SMM off/1CPU/워치독 없음/NMI 주입 없음의 통제된 OVMF에 한정한다.
CLI가 NMI를 차단하지 않으므로 실제 하드웨어에는 별도 IDT/NMI 계약이 필요하다.
프로브의 CPU/메모리 검사와 운영체제의 플랫폼·엔트로피·runtime 충분성은 별도다.

### BP14. 동일 DataAbort의 VA와 PA를 호스트 transaction 경계에서 식별

현재 BP13의 보존 trace/QMP에는 같은 이벤트의 MMU 변환 상태가 없다.
공개 syndrome 정의로 읽기 방향 synchronous external DataAbort,
S1PTW=false, ISV=false까지만 확인돼 접근 폭과 변환 stage를 추정하지 않는다.
디버그 심볼이 있는 현재 QEMU와 WSL gdb를 이용한 좁은 관측을 ARM 담당에게
명시 위임한다. 원하는 상태는 같은 guest access의 VA/PA/size/type/mmu_idx/
MemTxResult를 공개 QEMU `arm_cpu_do_transaction_failed` 함수 인자에서
읽기만 하고 기존 fault VA와 동일 이벤트인지 판정하는 것이다.

기존 BP13 입력·adapter·restore 조건을 유지하며 새 COW/output을 사용한다.
host debugger는 기존 연구 guest의 해당 실패 callback을 한 번 관측한 뒤
분리/계속하며 값이나 실행 분기를 바꾸지 않는다. 최대 child60초, debugger를
포함한 소유 process group90초로 한정하고 원본13개 재해시/프로세스 수거를
확인한다. precise address/register 값과 debugger 원문은 `_isolated/` 또는
동일 비공개 runtime에만 남기며 공개 결과는 매핑 관계/접근 분류/단계 메타뿐이다.
환경 정책 때문에 attach가 불가하면 시스템 ptrace 정책을 바꾸지 않는다.
관측을 위해 펌웨어/게스트 명령이나 unknown device 응답을 수정하지 않는다.

BP14 관측 결과: 첫 시도는 GDB argv의 JSON 전달 오류로 guest 실행 전에
종료됐고, 원본 hash와 모든 자식 수거를 확인한 실패 receipt로 보존했다.
JSON·공백·쉼표·백슬래시·따옴표 argv round-trip과 leader-first descendant
수거 합성 시험을 통과한 뒤 새 COW/output으로 한 번 재시도했다. 같은 BP13
fault 이벤트에서 VA와 PA가 같았고 4-byte `MMU_DATA_LOAD`, core mmu_idx 0,
`MEMTX_DECODE_ERROR`를 확인했다. 실행 시 QMP flatview 25개 범위에도 해당 PA
mapping이 없었다. 따라서 현재 최초 실패는 bootx 뒤 실제 물리 주소 공간의
decode되지 않은 4-byte read다. 장치 정체는 여전히 미확정이며 주소 gap에
임의 응답을 추가하지 않는다. Stage2 prompt/복원 5종/bootx ACK 뒤 같은
firmware panic이고 XNU/macOS는 미관측이다. 원본 13개 hash와 debugger/QEMU/
worker 수거는 독립 확인했다.

### BP15. 정상 recovery의 Nextcore APLS adapter 통합

현재 `nextcore-apls::RunnerRequest`의 TCG variant는 raw Stage2/AVP worker만
호출하고, BP12~BP14의 정상 `vmapple run` 입력과 `26x86.vmapple-gui/1`
report를 표현하지 못한다. legacy normal worker의 단계별 timeout은 여러 번
재시작되고 DFU 기본 300초 및 helper/file I/O가 별도이므로 전체 실행 상한이
아니다. Windows의 `wsl.exe` leader 종료도 Linux QEMU/TSS descendant 수거를
증명하지 않는다.

결정: 명시 `TcgRecovery` backend를 추가한다. qemu/qemu-img/AVPBooter,
VM JSON, BuildManifest, TSS helper, 원본 iBSS/iBEC, restore role directory,
RAM/CPU와 transition/restore/post/total timeout을 구조화된 입력으로 받는다.
recovery boot, picker off, live personalization, restore chain과 display none은
이 variant의 고정 계약이다. optional RPC unavailable adapter는 별도 bool이며
기본 false다. 상속된 restore/trace/legacy input 환경값은 제거하고 effective
값만 receipt에 기록한다.

Linux supervisor는 worker를 새 session/process group에서 실행하고 worker와
cleanup의 단일 monotonic deadline 안에 cooperative stop, TERM, KILL과
descendant wait를 끝낸다. worker leader가 먼저 끝나도 owned descendant를
확인한다. 입력 pre/post hash와 evidence 저장은 각각 별도 20초 budget을 가지며
전체 supervisor 상한은 `total_timeout + 40초`다. hash timeout/오류는 integrity
unknown이고 boot acceptance를 거부한다.
Windows Rust는 supervisor envelope를 읽으며 WSL 연결 종료만으로 Linux child
cleanup을 true로 만들지 않는다. raw launch report는 hash/path/completeness와
함께 보존한다. normal schema의 runtime/progress 필드를 기존 raw-TCG schema로
위조하지 않는다.

반환 상태는 guest runtime, DFU/iBEC/Stage2 prompt, restore 5종, bootx ACK,
firmware panic, XNU marker/major, userspace, input integrity, deadline/cancel과
process cleanup을 분리한다. Python worker exit 0 또는 bootx ACK는 boot 성공이
아니다. 실제 같은-run XNU+target+userspace+integrity+cleanup 근거가 없으면
Nextcore CLI는 completed-unverified/exit 2를 유지한다. 구현과 회귀는
`artifacts/apls-recovery-adapter-contract-20260907.md`의 최소 contract를 따른다.

BP15 구현 결과: `x86.recovery_supervisor`와 Rust `TcgRecovery` backend를
연결했다. supervisor는 raw report의 QEMU PID를 같은 Linux session에서 실제
관측한 유일한 PID/starttime과 상관시키며, 누락·불일치·PID 재사용이면 runtime과
상위 진행/boot 증거를 승격하지 않는다. 요청 output 원문과 canonical worker
output도 별도로 검증한다. Python 17건, Rust runner 17건, CLI 9건과 저장된 BP14
report의 offline 판정을 독립 검토했고 미해결 finding은 없다.

새 adapter의 실제 정상 recovery 1회는 48.365초에 exit 2로 종료됐다. DFU,
iBEC endpoint, Stage2 banner/prompt, 복원 5종, sequence, bootx ACK를 관측한 뒤
firmware panic이 발생했다. QEMU PID의 same-session 상관, cooperative stop,
leader/descendant 수거, 15개 입력의 pre/post hash 일치와 deadline 미초과를
확인했다. XNU와 userspace 근거는 없고 `macos_boot_verified=false`다. 공개 결과는
`nextcore/artifacts/apls-supervised-recovery-result-20260907.md`와 host receipt에
보존한다.

### BP16. bootx 뒤 unmapped MMIO node의 공개 계약 판별

현재 상태: BP14의 same-event transaction은 DeviceTree bus range 적용 뒤 실제
복구 입력의 `reg` node 하나에 포함된다. 비교 DeviceTree에는 일치 node가 없고,
현재 QEMU flatview에는 해당 범위가 없다. 이 사실은 node의 존재와 decode gap만
확인하며 장치 종류, register 의미, read side effect 또는 reset state를 확정하지
않는다.

결정: 공개 upstream 소스, 공개 하드웨어/펌웨어 문서 또는 독립 클린룸 구현에서
node compatible/role과 해당 access 폭·offset·반환 의미를 함께 확인한다. 단순
DeviceTree 명칭, 문자열, 인접 주소 또는 다른 SoC의 유사 장치는 구현 근거가
아니다. 후보마다 출처, 대상 SoC/model 일치, register coverage, access semantics,
현재 QEMU 모델 coverage를 표로 남긴다. 공개 계약을 찾지 못하면 HOLD로 기록하고
zero-return MMIO, 임의 RAM alias, panic skip 또는 firmware patch를 추가하지 않는다.

검증 게이트: 공개 계약이 확인된 경우에도 먼저 최소 read-only 모델과 한 번의
same-event 관측으로 `MEMTX_DECODE_ERROR` 해소 및 다음 PC/exception을 비교한다.
복구 진행, XNU marker/major, userspace와 macOS boot는 계속 별도 상태다. 정확한
주소·node 원문·비공개 trace는 `_isolated/`에만 둔다.

BP16 조사 결과: pinned VMApple machine은 QEMU PL031을 이미 생성하지만 그
mapping과 선택 DeviceTree node 범위는 겹치지 않는다. 선택 node의 compatible은
표준 PL031/ARM binding과 일치하지 않고 role 속성이 없으며, 문제 read의 상대
offset도 PL031의 정상 register/ID coverage 밖이다. Linux/OpenBSD의 Apple SMC
RTC/NVMEM transport, Apple Virtualization의 opaque Mac platform state, custom
Virtio 및 GPU용 MMIO forwarding도 이번 node의 register/reset/side-effect 계약을
제공하지 않는다. 따라서 구현은 HOLD다. 공개 근거는
`bp16-public-contract-survey`, `bp16-qemu-coverage-review`,
`bp16-host-interface-survey` 문서/JSON에 나누어 보존했다.

### BP17. 실제 실행 호스트 적격성 판별

현재 상태: x86 UEFI probe는 authored guest에서만 통과했고, ARM TCG recovery는
`bootx` ACK 뒤 firmware MMIO decode failure에서 멈춘다. 둘 다 macOS boot 증거가
아니다. BP16의 공개 contract HOLD를 임의 모델로 우회할 수 없으므로, native Apple
Silicon/macOS 실행 경로가 있는지도 별도 판정한다.

결정: 2026-09-07에 현재 Windows host와 등록 원격 두 대를 로그인 없이 변경하지
않는 명령으로 확인했다. 현재 host는 Samsung x64 PC / Windows 11 x64이고,
`zuzunza` 및 `koreaidc2`는 모두 `x86_64` Linux였다. 따라서 이 세 환경에는
Virtualization.framework로 ARM macOS guest를 실행할 적격 host가 없다.

검증 게이트: native Apple Silicon macOS host가 제공되면, Windows TCG 결과와
분리된 새 receipt에서 host architecture, supported macOS runtime, VM boot marker,
XNU marker, userspace marker를 순서대로 판정한다. 그 전에는 현재 TCG panic을
macOS boot 또는 장치 구현 성공으로 승격하지 않는다.

### BP18. Nextcore 모듈 저장소 배포

현재 상태: Nextcore workspace에는 `core`, `efi`, `gpu`, `hal`, `ise`, `apls`,
`tool`의 일곱 Rust crate가 있고, 루트 저장소 배포만 완료됐다. 기존 VenFire
배포처럼 모듈 소비자는 각 계층의 소스, 의존 관계, source commit 및 tag를 독립
저장소에서 확인할 수 있어야 한다.

결정: 공개 tracked source만 fresh export directory로 복사하고 각 저장소에 독립
Git 초기 commit, `26x86-Nextcore-<Module>-v0.1.0` tag, `repository.json`,
sha256 file inventory 및 CI를 생성한다. 외부 모듈 의존은 상대 path 대신 해당
GitHub 저장소와 초기 tag로 고정한다. 배포 순서는 leaf `Core`/`GPU`/`HAL`/`ISE`,
그 다음 `APLS`/`EFI`, 마지막 `Tool`이다. `_isolated/`, artifacts, target 및
비공개 입력은 export 대상이 아니다.

검증 게이트: export 전 source path가 tracked crate tree인지 확인하고, 각 export의
metadata와 inventory를 검토한다. public repository 생성 뒤 branch/tag push를
확인하고, clone한 독립 tree에서 module별 Cargo test 또는 EFI target check가
통과해야 배포 성공으로 기록한다.

## OPEN_QUESTION

- BP9 연속 실행 결정: Design D2-A는 표준 EFI application 중간 경로를 허용했고,
  D5-A~C는 과거 4종 handoff 상한을 내부 모델/대상별 공개 XNU ABI adapter로
  분리했다. 따라서 아래 과거 RESOLVED-BY-F의 4종 상한은 현재 구현 제약이 아니다.
  아직 구현되지 않은 대상별 wire layout/필수 필드/주소 수명은 공개 자료와
  실제 대상 버전을 고정한 별도 계약으로 구현한다.
- `OPEN_QUESTION: Build Plan: ARM 연구 입력의 AUX/identity/매체 역할과 정상 boot/restore entry가 일치하는 기존 후보를 확인한다. AUX offset 0 비교는 동일 panic이므로 기본값 변경 근거가 아니다.`

- `OPEN_QUESTION: Design:handoff 자료 구조의 *공개 명세*가 정확히 어디까지 정의되는지`
  — Build Plan은 BP3 단계 6/7을 *공개 DeviceTree + 공개 Mach-O + EFI Handoff
  컨벤션*에 한정해 구현. Design이 *어디까지*를 *공개 명세의 범위*로 인정할지
  박제해 주면 BP3 단계 6/7의 필드 셋이 그에 맞춰 확정됨.
  → RESOLVED-BY-F: Design D5 4종 = 상한으로 확정(D5 (F) 대조 결론, 본 문서
  BP7). 필드 전체 열거는 BP7의 내부 HOLD로 이관.
- `OPEN_QUESTION: Prompts:Step 3 카피의 호스트 OS별 분기 문구 반영`
  → RESOLVED-BY-F: Prompts P4에 (F) macOS/Windows 분기 카피 박제 —
  BP3.9·BP6(b)와 3자 정합 닫힘.
- `OPEN_QUESTION: Boundary:격리 자산에 들어가는 Mach-O / ACPI 명세 문서는 어떤 수준까지 허용되는지`
  — Build Plan은 BP3 단계 8의 mock 환경 명세로 *공개 명세로 표현 가능한
    범위*를 한 번 더 박제함. Boundary가 격리 폴더 운영 규칙을 확정해 주면
    BP3 단계 7의 `goblin`/`aml` 사용 범위도 그에 맞춰 조정됨.
  → RESOLVED-BY-F: Boundary B5(b)가 "공개 명세 수준만 공개 트리 허용"으로
  박제했고 B6 (F)가 허용 출처 목록을 추가 박제. `goblin`/`aml`은 공개
  포맷 디코드 한도 그대로 유지(BP7 (F)) — 조정할 차이 없음.

## 해소 메모 (Build Plan이 박제로 답한 항목)

- `RESOLVED-BY-BP1: Design:Rust 모듈 트리 — Nextcore의 코어 디렉터리 구조`
  — Design이 Build Plan에 보낸 OPEN_QUESTION. BP1에서 `nextcore-efi`,
  `nextcore-core`, `nextcore-tool` 3-crate 구조와 모듈별 공개 인터페이스를
  박제해 해소. 상세 답변은 BP6(a).
- `RESOLVED-BY-BP6b: Prompts:createinstallmedia 호출 경로 (호스트 OS별)`
  — Prompts가 Build Plan에 보낸 OPEN_QUESTION. BP6(b)와 BP3.9 호스트 OS별
  게이트로 박제해 해소.
- `RESOLVED-BY-BP6c: Boundary:격리 자산 참조 메커니즘 (없음이 원칙)`
  — Boundary가 Build Plan에 보낸 OPEN_QUESTION. BP6(c)로 박제해 해소
  (없음이 원칙, B2-3 절차로만 지식 이전).
- `ACCEPTED-FROM-PROMPTS: Prompts:사용자 메시지 카피의 한국어/영어 비율`
  — Prompts 슬롯이 박제 결정(한국어 우선, 영어 보조 병기)했으므로 Build Plan은
  BP3.9 `install-usb` 진행 표시/안내 문구에 그 비율을 그대로 따른다. 미합의 없음.

## 통합 검증 (F)

| 질문 (본 문서) | 결론 | 박제 위치 |
| --- | --- | --- |
| handoff 공개 명세의 어디까지 | RESOLVED (내부 HOLD: 필드 전체 열거) | Design D5 (F), 본 문서 BP7 |
| Step 3 카피 OS별 분기 | RESOLVED — 분기 카피 박제 | Prompts P4 (F) |
| 격리 Mach-O/ACPI 허용 수준 | RESOLVED — 공개 명세 수준만 허용 | Boundary B5(b), B6 (F) |

- 타 슬롯이 본 문서에 던져 이미 해소된 항목 재확인: Boundary `격리 자산
  참조 메커니즘` → BP6(c) 박제 유지(F 확인), Boundary `공개 규격 목록
  의존성 표 명시` → BP7 (F)로 회수, Design `handoff.rs 필드 목록` →
  D5 (F)·BP7 (F)로 상한 확정 후 HOLD 이관.
- BP3.9(호스트 OS별 게이트) × BP6(b)(호출 경로) × Prompts P4 (F)(분기
  카피): 세 문서 정합 닫힘. macOS 버전 목록 원칙(D6/P8)과 단계 9의
  고정 목록 검증은 상하 관계로 정리 — 구현은 BP3.9 그대로, 확장 시점은
  D6 (F)의 HOLD를 따른다.
