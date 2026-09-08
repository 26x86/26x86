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

### BP19. OVMF ACPI/PCI 수집과 HAL 파서의 실제 바이트 연결

현재 상태: 2026-09-08 작업 트리에 `NXHAL` 시험 EFI와 `acpi_raw`/`pci_raw`
파서가 있으나 수집→파서 연결 하네스와 해당 실행 receipt가 없다. MADT/FACP는
선언된 길이 밖의 trailing bytes를 해석할 수 있고 PCI bridge header를 Type 0으로
오해할 수 있다. 기존 Linux handoff 및 모듈 배포 변경은 별도 미커밋 작업이다.

결정(확정): 이번 작업은 x86 UEFI → host HAL 계층에 한정한다. 공개 ACPI 6.6
§5.2와 Linux 공개 `pci_regs.h`의 header layout을 근거로 파서를 보완한다.
SDT header의 checksum 진단 API는 유지하되 typed parser는 잘못된 checksum,
선언 길이 밖의 데이터, 불완전 MADT record를 거부한다. PCI Type 1/2는 현재
`PciDevice`가 선택적인 subsystem ID를 표현하지 못하므로 명시 거부한다.

`NXHAL`은 feature-gated 별도 EFI 시험 도구로 유지한다. EFI memory map의
ACPI reclaim/NVS descriptor가 전체 주소 범위를 포함할 때만 물리 바이트를 읽고,
root signature/checksum/entry width/cap 오류는 실패 처리한다. q35의 bus 0에서
CF8 주소 선택과 CFC 읽기만 수행한다. 장치 config data 쓰기와 AML 실행은 없다.

root는 EFI 수집기와 Python OVMF 하네스를 소유한다. HAL 담당에게 raw parser,
집중 회귀, `examples/inspect_firmware.rs`를 명시 위임한다. 이 example의 입력은
`inspect_firmware <RSDP|SDT|PCI> <binary-file>`, 출력은 성공 시 단일 JSON object,
실패 시 stderr+nonzero다. SDT 종류별 checksum/구조 검사와 PCI decode를 실제
crate API로 수행한다. Python은 JSON을 모으고 raw byte 길이, record count와
RSDP/root pointer 관계를 별도로 검증한다. reviewer는 변경 파일을 읽기만 한다.

완료 기준: fresh ESP/vars에서 BOOTX64가 NXHAL을 chainload하고, RSDP/root와
FACP/APIC/HPET/MCFG 및 하나 이상의 PCI Type 0 header의 정확한 bytes가 HAL
parser를 통과한다. 자연 isa-debug-exit 67, 정상 marker 순서, 입력 원본 pre/post
SHA-256 일치, QEMU 수거가 모두 필요하다. timeout은 cleanup을 포함한 총 상한이며
잘린 dump, forged count, checksum 손상을 성공으로 받아들이지 않는 회귀를 둔다.
실행 command, artifact hash, serial, parser 결과, 실패 이유를 새 receipt에 보존한다.

이 결과는 OVMF 테이블 수집/host 해석 증거다. XNU 인계 provider, 게스트 장치 게시,
사용자 공간, Metal, 물리 하드웨어 및 `macos_boot_verified`는 검증하지 않는다.

공개 근거: [ACPI 6.6](https://uefi.org/specs/ACPI/6.6/05_ACPI_Software_Programming_Model.html),
[Linux PCI header definitions](https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/linux/pci_regs.h).

BP19 결과(확정): 실제 OVMF에서 RSDP+7 SDT+5 PCI header가 13회 HAL inspector를
통과했다. QEMU natural exit 67, 전체 4.3961초, 원본 5개와 EFI 복사본 hash 유지,
소유 process 수거를 확인했다. workspace 280 passed/1 ignored, HAL all-targets
32 passed, Python 30 passed와 독립 검토를 기록했다. 실행 후 typed summary gate
보완은 같은 raw/JSON 13개를 offline 재검증했다. HPET 등의 공통 SDT 검사와
FACP 선택 필드 요약을 전체 장치 ABI 검증으로 확대하지 않는다. 자세한 재현,
source hash와 다음 target-provider blocker는 `nextcore/VALIDATION.md` BP19에 있다.

### BP20. 실제 macOS 부팅 입력 확보와 가속 실행 경로 연결

현재 상태: BP19는 OVMF 수집/host 파서 경계까지다. 사용자는 2026-09-08에
실제 부팅부터 그래픽 가속까지 본래 목적을 수행하도록 지시했다. 현재 로컬
macOS 27.0/26A5425a 매체의 확인된 커널 2개는 ARM64 MH_FILESET이고, 기존
정상 recovery 경로는 bootx 뒤 MMIO decode failure에서 멈춘다. 현재 x86_64
호스트에서 사용할 실제 Intel macOS 입력은 아직 확인되지 않았다.

결정: 원래 ARM64 목표/receipt를 유지하면서 공식 Apple 서버의 Intel recovery
매체를 별도 실행 입력으로 확보한다. 공개 다운로드 도구는 외부 도구로 사용하고
Nextcore 소스 의존성에 편입하지 않는다. 다운로드 도구/매체/추출물은
`_isolated/nextcore/intel-recovery-20260908/`에 두며 원본 해시와 Apple chunklist
검증을 남긴다. Intel 경로 결과는 ARM64 macOS 27 성공으로 바꾸어 기록하지 않는다.
실제 매체의 architecture/version/boot loader/kernel 형식을 확인한 후 대상별
EFI 인계 변경과 fresh COW 실행을 결정한다. 사용자 대상 지정이 도착하면 우선한다.

그래픽은 소프트웨어 렌더 테스트가 아니라 실제 guest API→driver→host GPU
실행과 결과 readback을 요구한다. 새로운 공개 external backend 후보 Reims의
적격성을 host KVM/Vulkan/device enumeration으로 판별한다. 공개 repo라는
이유만으로 reverse-derived implementation을 Nextcore에 복사하지 않으며,
외부 실험 도구와 공개 clean-room crate의 경계를 유지한다. 현재 rate-limit을
재확인하지 않은 과거 기록을 구현 보류 근거로 사용하지 않는다.

완료 판정은 Nextcore EFI 진입, 대상 일치 XNU, userspace, 실제 graphics API
작업 결과를 각각 같은 실행에 연결한다. 매체 확보나 backend probe만으로 완료
처리하지 않는다. ARM unknown MMIO의 임의 응답/alias/firmware patch는 추가하지 않는다.

### BP20 대상 확정 — 사용자 답변 (2026-09-08)

박제된 목표는 **macOS 27 Golden Gate — 실험적 Apple Silicon 대응,
Intel Mac 부분 가속**과 **macOS 26 Tahoe — 네이티브 HAL** 두 경로다.
현재 확보한 26.6.2/25G83 x86_64 복구 매체는 Tahoe 실행 입력으로 사용한다.
ARM64 27.0/26A5425a 입력은 Golden Gate 실험 경로로 유지한다. Intel Tahoe의
부팅이나 WSL host Vulkan 결과를 Golden Gate 대응 또는 guest Metal 완료로
전용하지 않는다. 외부 EFI 도구는 실제 실패 계층을 밝히는 진단용이며,
Tahoe의 Nextcore native HAL 최종 acceptance를 대신하지 않는다.
사용자는 추가 답변에서 **이 컴퓨터에서 계속 개발**하도록 지정했다. 원격/물리
Mac 확보를 선행 조건으로 두지 않고 Windows/WSL, QEMU/OVMF, 실제 host Intel GPU
경로에서 구현과 검증을 계속한다.

### BP20-A — 실제 EFI 로더의 실패 원인 보존

첫 Intel 26.6.2/25G83 원본 `boot.efi` 실행에서 Nextcore의 `StartImage`가
`ABORTED`를 반환했다. FAT에 booter/KC만 복사한 관측이며 HFS volume과 플랫폼
계약이 아직 준비되지 않아 XNU 진입 증거가 아니다. 원본 입력 hash는 유지됐다.
현재 `uefi` 0.40 `start_image` wrapper는 UEFI exit data를 호출자에게 돌려주지
않는다. 표준 UEFI Boot Services ABI만으로 이 데이터를 제한 길이로 읽어
진단하고 `FreePool`로 해제한다. 오류 텍스트와 고정 NEXTCORE marker는 별도
출력하고 제어문자/개행을 escape하여 guest text가 증거 marker를 만들지 못하게
한다. return status는 변경하지 않는다. authored child가 명시적 Exit 데이터와
ABORTED를 반환하는 OVMF 회귀 검증 후 실제 Apple child에 적용한다.

booter 진단 설정은 외부 공개 문서에 따른 VM 전용 NVRAM 사본에서만 적용한다.
원본 OVMF 변수/복구 매체는 수정하지 않는다. 자식 실패 로그를 확보한 후 필요한
filesystem/platform 계약을 결정하며, 오류를 우회해 실행 성공으로 처리하지 않는다.

### BP20-B — Nextcore host GPU의 실제 compute 실행

현재 `ComputePipelineManager::dispatch`는 bytecode를 실행하지 않고 fence를
signal하며, `VirtualMetalDevice`도 capability만으로 HardwareWrapped 이름을
선택한다. 이것은 실제 가속 완료가 아니다. 박제된 구현은 공개 Khronos Vulkan
API 기반의 명시적 `vulkan` 선택 기능과 SPIR-V compute 경로다. public crate는
Mesa/Reims/Apple source 또는 격리 파일을 빌드 의존성으로 사용하지 않는다.
Vulkan loader/ICD는 실행 시 외부 호스트가 제공하고, CPU device fallback을
허용하지 않는 명시 device selector로 실제 장치를 선택한다.

일차 범위는 storage buffer upload, SPIR-V pipeline, bounded dispatch 크기,
compute write→host read memory barrier, fence 완료 및 결과 readback이다.
기존 compute descriptor는 이 기능에 명시 연결하며 지원하지 않는 bytecode,
binding 또는 backend는 실행하지 않고 오류를 반환한다. 성공 fence는 GPU
완료/readback 뒤에만 signal한다. 기본 backend는 미실행을 성공으로 반환하지
않으며 이 동작 변경은 호출 테스트에 반영한다. guest Metal bytecode를
SPIR-V라고 간주하거나 SGPU의 미확정 guest ABI를 임의로 확대하지 않는다.

자원은 Vulkan 수명 규칙에 따라 해제한다. timeout/device-lost 경로에서 진행 중
command가 참조하는 자원을 먼저 파괴하지 않는다. 드라이버 호출 자체는 외부
프로세스 deadline으로도 제한하는 실행 예제를 제공한다. 호스트 driver 호출의
일반적인 무한 정지 가능성을 라이브러리의 짧은 fence timeout만으로 해결했다고
주장하지 않는다. 자체 저작 shader와 256값 결과의 실제 Intel GPU 검증을 public
crate API로 재실행하고, 그 결과는 host GPU 계층에 한정한다.

BP20-B 통합 결정: 기존 `VirtualMetalDevice`/SGPU 경로는 shader나 render target을
등록하지 않으므로 compute/clear/present를 로그만 남기고 완료 처리하지 않는다.
지원하지 않는 명령이 섞인 목록은 host copy를 수행하기 전에 거부한다. 이 모델의
Metal 실행 지원과 SGPU compute 지원은 false이며, public Vulkan manager의
실제 실행 능력을 미연결 guest 경로로 전용하지 않는다. 소프트웨어 buffer copy는
유지하고 overflow 범위를 거부한다. SGPU transport가 오류를 성공 응답으로
바꾸지 않는 회귀 시험을 포함한다.

### BP20-C — Tahoe BootKC의 공개 포맷 준비 검사

현재 실제 Tahoe KC는 기존 standalone MH_EXECUTE 프로필의 입력이 아니며
MH_FILESET·중첩 이미지·chained fixup·local relocation을 포함한다. 기존
`NXKERNEL`의 작은 fixture 범위나 크기 제한만 풀어서 실행하지 않는다.
공식 공개 XNU/dyld의 Mach-O·chained-fixup 헤더 및 XNU bootstrap 소비 코드에
근거한 read-only `KcMetadataInspection`을 별도 core API와 CLI/example로
구현한다. 계약 출처와 source revision은 전용 artifact에 먼저 고정한다.

검사는 outer/nested load command, 파일/VA 범위, entry의 출처, fixup 종류와
local relocation 요구를 구분한다. metadata가 유효해도 relocation/provider가
준비되지 않았으면 `preparation_ready=false`와 구체 사유를 반환한다. 공개 tree
fixture는 자체 저작하고, 실제 KC는 명시적 외부 런타임 입력으로만 사용한다.
이 검사는 native Tahoe handoff의 다음 구현 대상을 좁히며 XNU 실행은 별도다.

### BP20-D — native KC의 실제 메모리 배치·readback

현재 BP20-C는 구조 검사까지이며 실제 커널 컬렉션 바이트를 배치하지 않는다.
다음 구현은 별도 `KcStagingPlan`과 host arena 배치 API/example이다. 가장 낮은
outer VA를 기준으로 한 상대 범위, 실제 Mach-O header VA, outer entry 출처를
각각 보존한다. checked arithmetic과 명시적인 host arena 상한을 적용하고,
outer segment만 copy/zero 대상으로 삼는다. nested member는 같은 outer
메모리를 보는 view이며 따로 copy/zero하여 공유 데이터를 덮지 않는다.

공개 source 계약과 근거는 `nextcore/artifacts/native-kc-next-step-20260908.md`에
먼저 기록한다. 공개 fixture는 자체 저작하며, 실제 Tahoe KC는 격리 경로의 명시적
외부 입력으로만 읽는다. 실제 arena를 할당하고 각 file-backed byte의 copy와
zero-fill/hole readback을 확인하며 원본 입력 해시 전후와 종료 상태를 기록한다.
EFI physical placement, 32-bit entry 주소, classic relocation 및 format 11
chained rebasing은 이 단계에 포함하지 않으며 `preparation_ready=false`다.
XNU의 kernel proper/collection fixup 처리 소유권을 확인하지 않은 전체 chain
선적용은 double-rebase 가능성이 있어 하지 않는다. 호스트 배치 성공을 XNU 실행
또는 native HAL 완료로 기록하지 않는다.

### BP20-E — KC classic/chained 재배치 대상의 읽기 전용 검증

BP20-D에서 실제 arena copy/readback은 통과했다. 다음 단계는 재배치가 쓸 범위를
공개 XNU/dyld consumer와 대조하는 별도 audit API/example이다. 고정 source revision의
계약을 전용 artifact에 먼저 기록하고 자체 저작 fixture로 signed classic displacement,
type/width/PC-relative/external 분류와 format 11의 stride/page/segment 범위·종료·
중복 방문을 검사한다. 파일 범위를 벗어나는 chain, 부족한 cache base, 지원 밖
authentication/type/width 또는 다른 mechanism과 겹치는 write는 명시적으로 기록한다.

실제 KC는 격리된 명시 입력으로 읽기만 하며 decoded 대상 목록은 격리에 보존한다.
공개 결과에는 합계·실패 분류와 원본 hash/종료 증거만 둔다. source와 staged arena에
어떠한 fixup도 적용하지 않고, kernel proper와 XNU 후속 collection consumer의 작업
소유권을 분리한다. 명세로 해소되지 않은 해석은 unsupported로 남기며 target value를
임의 보정하지 않는다. `relocations_applied`와 `preparation_ready`는 계속 false다.

BP20-E page 경계 정정: 고정 dyld producer의 `AppCacheBuilder.cpp`는 fixup의
시작 주소로 page를 분류하며 x86_64의 비정렬 8-byte terminal word가 다음 page에
걸칠 수 있다. 따라서 chain 시작·다음 시작은 원래 page 안에 있어야 하지만,
word 전체의 안전 범위는 owning segment의 file-backed mapping으로 검사한다.
페이지 밖 next, segment/file 밖 word, 겹치는 쓰기는 계속 거부한다. 공개 producer
근거와 자체 저작 경계 시험을 먼저 추가하고 실제 KC를 다시 읽기 전용 검사한다.
동일 제약을 사용하던 BP20-C page-start metadata 검증도 최소 diff로 수정한다.
첫 word 역시 시작의 page 범위와 전체 word의 file/segment 범위를 따로 검증하며,
메타데이터 경로의 첫 terminal straddle과 segment 끝 잘림을 별도 시험한다.

### BP20-F — native KC의 실제 EFI page 소유권과 배치

BP20-D/E의 실제 입력 host 검증 뒤, 동일 `KcStagingPlan`을 UEFI의 실제
AllocatePages/FreePages 소유권과 연결한다. 별도 `LoadedKernelCollection`은 4 GiB
아래의 연속 LoaderData pages를 할당하고, source와의 겹침을 거부한 뒤 outer copy,
zero/hole 및 member view 전체 readback을 수행한다. 메모리맵의 실제 descriptor로
할당 범위를 확인한다. 실패와 정상 반환 모두 Boot Services가 살아 있을 때 전체
pages를 해제하며 해제 결과를 관측한다. 기존 standalone `LoadedKernel`은 유지한다.

명시적 시험 bin `NXKC`와 `kc-staging` feature는 설정에 주어진 파일만 제한 길이로
읽어 이 경로를 실행한다. 자체 fixture와 실제 격리 KC 모두 실제 OVMF에서 검증한다.
Apple 원본·런타임 복사본·raw 출력은 격리에 두며 원본/EFI/firmware hash와 bounded
종료·프로세스 정리를 receipt로 남긴다. 모든 공개 빌드는 격리 파일 없이 가능해야 한다.

여기서 얻는 것은 실제 EFI 물리 메모리의 소유권·배치 증거다. 임의 할당 주소를 XNU
slide/진입 주소로 해석하지 않고 ExitBootServices 또는 KC instruction 실행은 하지
않는다. classic 적용, XNU가 처리할 chained fixup, KC boot_args revision/entry ABI,
platform provider 계약은 별도 조건이며 `preparation_ready=false`를 유지한다.

### BP20-G — KC용 boot_args revision 1 codec

공개 XNU boot.h를 별도 C offsetof probe로 컴파일해 기존 revision 0 필드와
revision 1의 KC header 필드 위치를 대조한다. 기존 standalone encoder를 유지하고,
명시적인 revision 1 encoder에 물리 KC header 범위와 실제 선택 slide 값을 받는다.
header는 저위 kernel 소유 범위 안에 있고 memory map/DT와 겹치지 않아야 한다.
codec은 주어진 slide를 표현할 뿐 CPU 진입용 VA↔PA 대응이나 허용 slide 정책을
만들지 않는다. 이 값들의 실제 생성·수명·KC header 내용은 caller의 별도 책임이다.

고정 consumer는 revision >=1의 nonzero KC header를 초기 physical→virtual 변환한
뒤, firmware가 이미 처리한 kernel proper와 XNU가 처리할 collection chains를
구분한다. 새 codec만으로 fixup 완료나 handoff 준비를 승인하지 않고 기존 EFI 진입
guard도 그대로 둔다. C layout 결과 및 정상/경계/겹침/기존 revision 보존을 검증한다.

### BP20-H — kernel proper classic relocation의 실제 적용

BP20-E/F/G는 대상 범위·EFI 배치·boot_args 표현까지 확인했다. 고정 공개 dyld
producer는 kernel proper에 속한 local unsigned fixup을 classic table로 출력하고
chain tracker에서 제거한다. 공개 XNU는 firmware가 kernel proper를 준비한 뒤
collection chains 및 header/section/symbol 주소를 처리하는 경계를 명시한다.
근거와 제한은 `nextcore/artifacts/kc-classic-relocation-contract-20260908.md`에
기록하며, 이를 따르는 별도 source-bound classic 적용 API/example을 구현한다.

첫 profile은 정확히 하나의 executable member가 있는 fileset의 outer local
dynamic table만 허용한다. type 0, symbol 0, non-external, non-PC-relative,
width 4/8 및 kernel member의 전체 file-backed write 범위를 확인한다. 전체
audit의 오류, 다른 classic table, header/load-command 대상 또는 chain과 겹치는
쓰기는 적용 전에 거부한다. 명시적으로 받은 u32 slide를 원본 word에 더하되
width 범위 밖 덧셈은 거부한다. 이는 wrap을 추정하지 않는 제한된 적용 정책이며
모든 firmware relocation 사례를 지원한다는 주장이 아니다.

계획 전체의 대상·값·자원 검사를 끝낸 뒤, source와 동일함을 검증한 자체 소유
arena에만 적용한다. 변경 word와 나머지 모든 byte를 실제 readback하며 원본,
chained words, Mach-O header/load commands를 유지한다. header 선행 수정이나
할당 주소를 slide로 해석하지 않는다. 결과는 immutable 소유 객체이며 재진입
함수나 전체 handoff 승인 권한을 갖지 않는다. 자체 fixture 경계 시험, no_std
검사 후 실제 KC의 명시적 실험 slide로 host 적용·readback과 해시 보존을 검증한다.
실제 EFI relocation 연결·slide/entry 배치·native XNU/GUI는 별도 조건이다.

### BP20-I — guest 사용자 공간 Metal 실행 probe

외부 reference는 실제 XNU/userspace와 WindowServer 실행까지 관측했지만 guest
GPU 실행은 아직 없다. 공개 Metal·Objective-C runtime API만 호출하는 자체 C
probe를 추가한다. Windows/WSL에서 Mach-O x86_64로 cross-compile하고 실제 guest
실행은 별도 판정한다. public API header에서 enum/NSUInteger/MTLSize ABI를 확인하며,
SDK나 추출 framework를 공개 빌드 입력으로 사용하지 않는다. 최소 linker stub은
호출하는 공개 libSystem 심볼만 선언하고 framework는 정상 dlopen으로 연다.

probe는 실제 MTLDevice identity, shader compilation, compute pipeline과 command
buffer completion을 관측하고 두 입력의 512개 계산값 및 buffer guard를 읽어
검증한다. completion 전에 CPU로 결과를 합성하지 않으며 device/compile/queue/
timeout/readback 실패는 명시적 실패다. process alarm으로 blocking API를 제한한다.
guest 성공은 그 guest API 경로의 compute 증거이며 Reims host의 실제 Intel GPU
selection/submission은 별도 로그로 대조한다. native HAL·완전 Metal conformance·
물리 Mac 검증 또는 전체 macOS boot를 이 probe 하나로 승인하지 않는다.

### BP20-J — 실제 검증된 EFI ConsoleControl provider 연결

같은 직접 EFI 부팅의 control은 ICM NOT_FOUND/ABORTED였으며, 공개 ConsoleControl
계약에 따라 실제 console text mode와 system GOP 존재를 제공한 case는 원본 KC
읽기 및 EXITBS:START까지 진행했다. 별도 진단 hook·원본 화면 증거와 callback
횟수를 보존했다. 이 근거로 Nextcore EFI에 최소 독립 provider를 연결한다.

공개 GUID/함수 ABI만 사용하고 기존 provider가 있으면 재사용한다. 누락된 경우
Boot Services가 살아 있는 소유 범위에 설치하고, child가 반환하면 실제 uninstall
상태를 관측해 소유 메모리의 수명을 보장한다. GetMode는 실제 console mode 및
시스템 GOP 조회를 사용한다. 지원하는 Text 설정은 실제 firmware 동작을 호출하고
미구현 Graphics 전환이나 입력 잠금은 명시적으로 거부한다. 존재/성공을 조작하는
빈 callback이나 전역 Boot Services table hook은 production에 넣지 않는다.

독립 feature와 명시적 호출 경로로 도입하며 자체 EFI callback/lifetime 시험,
기존 provider 보존 및 실제 원본 booter 실행을 검증한다. 이 provider만으로
ExitBootServices 완료·XNU entry·native HAL 전체 완료를 승인하지 않는다. 이후
중단은 실제 CPU/메모리/로그로 별도 원인 계층을 특정한다.

### BP21 — NextCore 제품 브랜딩과 실제 EFI 피커

사용자 2026-09-08 추가 결정: 제품명은 **NextCore**로 통일하고 부트 피커를
반드시 구현한다. Design/Prompts 소유 에이전트에게 해당 시작 문서와 사용자 표시
수정을 명시 위임했다. 외부 구현의 출처·라이선스·과거 실행 증거는 사실대로 유지하며
제품 제목·wizard·CLI 도움말·picker 표시는 NextCore를 사용한다.

현재 단일 target parser는 여러 enabled entry를 거부하고 실제 BOOTX64 피커가 없다.
기존 단일 parser의 의미를 유지한 별도 menu parser와 독립 GOP picker 모듈을
구현한다. 검정 기반 화면의 OS/볼륨 선택 항목, 명확한 선택 표시, 키보드 이동,
Enter 부팅·Esc 취소 및 텍스트 fallback을 제공한다. EFI main의 기존 entry
LoadImage/StartImage와 ConsoleControl 수명 관리는 유지한 채 선택 결과만 연결한다.
제품 이미지 mock만으로 완료하지 않고 자체 EFI target으로 실제 OVMF 화면·입력·
선택된 child 실행과 취소 경로를 검증한다. 소유 파일과 연결 diff는 협업자가 조정한다.

### BP22 — macOS 27 양방향 HAL과 Metal 필수 경로

사용자 추가 결정: **macOS 27 Golden Gate의 AMD64↔Apple Silicon HAL과 Metal
가속은 필수 목표**이며 Tahoe/x86 작업과 병렬로 진행한다. x86 부팅·guest GPU는
서브에이전트가 계속 맡고 root는 현재 ARM firmware 중단 및 실제 host GPU 연결
계약을 다시 확인한다. 현재 PC에서 개발하며 실기기 제공을 선행 조건으로 재요청하지 않는다.

기존 BP16의 미확인 MMIO 의미를 zero-return이나 임의 alias로 대체하지 않는다.
현재 source/device coverage와 원본 입력 역할을 재대조하고 공개 의미가 확인되는
CPU·장치·GPU 요청부터 실제 구현·실행으로 연결한다. AMD64 host↔ARM64 guest와
ARM64 host↔AMD64 guest의 CPU 실행·장치 HAL·GPU API 조건은 각각 판정하며,
한 방향의 성공이나 host Vulkan compute만으로 양방향 macOS/Metal을 승인하지 않는다.
새 구현은 공개 계약 또는 독립 클린룸 근거를 먼저 기록하고, 실제 guest command
completion/readback을 Metal 수용 조건으로 둔다.

진척이 검증되거나 작업이 완료되면 소유 슬롯별로 항상 커밋한다. 공유 index는
root가 조정하며 명시 파일만 stage한다. `_isolated/`와 무관한 기존 변경은 포함하지
않고 force-push는 하지 않는다. 이 추가 요청은 로컬 commit 승인이다.

### BP22-A — Golden Gate ARM64 guest Metal 검증 실행 파일

현재 BP20-I 도구는 Tahoe x86_64 전용이다. 동일한 공개 Metal compute/readback
계약을 Golden Gate ARM64에도 실행할 수 있도록 두 target profile을 명시한다.
기본 Tahoe x86_64/macOS 26 동작을 보존하고 Golden Gate arm64/macOS 27을 추가한다.
Apple의 공개 ARM64 ABI 문서와 고정 Metal-cpp API 선언을 근거로 구조체 인자를
검토하고 Clang의 Objective-C 호출 lowering과 C FFI lowering을 두 아키텍처에서
각각 비교한다. arm64e/PAC 실행 지원은 이 arm64 profile로 승인하지 않는다.

빌드 성공에는 실제 Mach-O CPU type, PIE, LC_BUILD_VERSION의 최소 OS/SDK 및
embedded signature 범위 검사를 요구한다. 다른 아키텍처/최소 OS 실행 파일을
요청 profile 성공으로 기록하지 않는다. 두 파일의 실제 guest command completion,
512개 결과 및 guard readback 전에는 guest Metal verified 상태를 변경하지 않는다.

### BP22-B — ARM firmware fault 시점의 메모리 매핑 관측

BP14의 같은 실패 callback은 unassigned MemoryRegion 경로를 보였으나 전체
FlatView는 reset 시점에만 수집했다. 원본 firmware/media를 새 COW 실행에 공급하고
같은 callback에서 host debugger로 현재 FlatView, 실제 dispatch MemoryRegion,
guest CPU 상태 및 범위가 검증된 작은 RAM window를 읽는다. inferior 함수 호출,
register 수정, 임의 MMIO 응답·alias·원본 변경은 하지 않는다. 원본 hash, PID 수명,
시간/로그 상한 및 정리를 기존 감독 계약으로 보존한다. private 주소·바이트와
분석은 `_isolated/`에만 저장하며 이는 장치 모델 또는 XNU 실행 성공 판정이 아니다.

### BP22-C — 독립 ARM64 XNU boot_args codec

현재 Intel 전용 boot_args를 ARM으로 재사용하지 않는다. 공개 XNU
`ac9718fb1af618d5ce8678d0dc6e8a58f252216f`의 ARM revision 2/version 2 LP64
1152B wire를 별도 `xnu_arm64_boot_args` module에 explicit LE codec로 구현한다.
공개 헤더의 layout을 독립 C offsetof/sizeof로 대조하고 RAM/커널/인자/DT 범위,
정렬·겹침·NUL 종료를 검사한다. x0의 boot_args PA와 wire DT 초기 KVA는 구분한다.
DT KVA는 공개 entry/초기 C 소비 규칙에 따라 virtBase + dtPA - physBase로 계산하며
checked arithmetic을 요구한다. Intel module은 수정하지 않는다.

공개 VMAPPLE 16K profile의 bootstrap mapping 제약과 EL1/MMU-off/DAIF/cache/PAC/
CPU device 요건은 codec과 별도의 준비 조건이다. 실제 Golden Gate 원본 KC는
ARM64E이므로 ordinary arm64 guest probe 빌드가 이 kernel의 PAC 실행을 검증하지
않는다. ARM64 KC의 실제 배치·인증·entry, 대상 27의 ABI 동등성 및 게스트 장치
구현은 이 첫 codec 완료 판정에 포함하지 않는다. 공개 XNU가 담당하는 fileset
chained rebase/PAC 및 header slide를 로더가 미리 중복 적용하지 않는다.

Build Plan 구현 하위 작업을 ARM 계약 담당에게 위임한다. 소유 파일은 별도 ARM64
core module, tests, 필요 lib export와 공개 계약 결과이며 root가 문서/commit을
통합한다. 코드 이후 최소 no_std build와 독립 layout 및 malformed-input 시험을
수행하고 execution-ready/guest Metal 상태는 실제 실행 전 false로 유지한다.

### BP22-D — ARM64 KC 메타데이터와 불변 host staging

현재 KC 검사·staging API는 Intel 전용이다. 공개 Mach-O/ARM thread 구조를
근거로 별도 ARM64 진입 API를 추가하고 기존 x86 기본 API와 rebase/EFI 경로의
CPU gate는 보존한다. 각 header의 raw CPU type/subtype을 보존하여 ARM64E의
capability를 ordinary ARM64로 지우지 않는다. ARM thread는 공개 flavor/count와
명령 크기를 검증하는 명시 subset이며, PC는 4B 정렬과 executable file-backed
outer segment 안의 완전한 4B 범위를 요구한다. member entry를 boot entry로
대체하지 않는다. unknown 형식·불일치·중복·겹침·overflow는 거부한다.

root가 `kernel_collection.rs`, `kc_staging.rs`, 별도 ARM fixture/host example을
소유하고 ARM 계약 담당이 공개 자료와 실제 입력의 형식 일치 여부를 독립 검토한다.
staging은 기존 128MiB 상한과 불변 source borrow를 유지하고 ARM profile의 16KiB
단위 arena 범위를 계산한다. host Vec의 주소·정렬을 guest 물리 메모리로 간주하지
않는다. outer copy/zero-fill/hole 및 모든 member view를 전량 readback하며 원본
KC의 chain/PAC/header/명령 바이트를 적용하거나 수정하지 않는다.

원본 27 입력은 실행 때만 공급하며 주소·원본 분석 결과는 `_isolated/`에 저장한다.
공개 fixture에는 독립 작성한 형식만 사용한다. 실제 staging 완료는 allocation/
mapping/boot_args 연결·인증·ARM64E 실행·guest Metal을 승인하지 않는다. 공개 XNU가
수행하는 chained rebase와 header slide의 소유권은 BP22-C 결정을 유지한다.

### BP23 — 검증된 진척의 원격·조직 동기화

사용자는 진척마다 push하고 조직을 최신화하도록 명시 승인했다. 본체는 PR/CI로,
7개 module은 검증된 source commit의 tracked crate만 fresh export하여 기존 main
이력 위에 새 commit/tag를 추가한다. 기존 tag와 history는 변경하지 않는다.
working-tree의 미검증 변경·격리·runtime artifact는 module 입력이 아니다.

현재 원격 CI는 Linux의 `Tools` 경로 대소문자, QEMU 별도 cwd의 상대 patch 경로,
Python no-build-isolation의 누락 build dependency로 실패했다. 해당 운영 연결을
최소 수정하고 원래 검사 조건을 유지한다. 격리 guard 시험은 실제 index에 금지
경로를 stage하지 않고 독립 git 출력 fixture로 hook의 정상/거부/오류 경로를
실행한다. 실제 tracked tree 검사는 별도로 유지하고 NUL-delimited 이름을 사용한다.
root가 이 CI/guard와 문서 배포 정합을 소유하고 cross-platform/Windows packaging
실패는 x86 담당에게 명시 위임한다. 실패 원인/수정 계약/관련 검증 이후 commit한다.

실제 구조는 tracked Cargo workspace와 독립 module exports이므로 미실행 submodule
전환을 완료로 서술한 배포 문서를 정정한다. 제품 문서의 브랜드·목표·실행 상태를
NextCore와 최신 증거에 맞추고 외부 구현의 실제 출처는 유지한다. 조직 profile은
module publish 담당에게 위임하며 root는 본체 README·wiki·PR을 통합한다.

독립 module 원격 CI는 Tool 테스트가 sibling Core의 fixture를 읽는 결함을 발견했다.
Windows의 대소문자 비구분/인접 clone 때문에 로컬 검증이 이를 놓쳤다. 독립 작성한
동일 fixture를 Tool 테스트 소유 경로로 복사하고 상대 include를 해당 crate 내부로
제한한다. 기존 v0.1.1은 보존하고 Tool v0.1.2로 수정하며, 다음 검증은 Linux의
단일 독립 clone에서 수행한다. 동등 fixture hash와 원격 exact-head CI를 확인한다.

### BP24 — 설치 APFS의 공개 EFI Jumpstart 경로

현재 최종 BP21은 원본 Tahoe Recovery/Terminal까지 검증됐고, 전체 설치의 다음
부팅은 외부 reference가 APFS의 macOS Installer 항목을 읽는 단계다. native EFI도
설치 매체가 가진 filesystem driver를 읽도록 공개 APFS EFI Jumpstart 절차를
독립 구현한다. APFS 전체 filesystem을 복제하거나 원본 driver를 공개 포함하지 않는다.

Build Plan 하위 core parser/합성 시험은 HAL 담당에게 명시 위임했다. 공개 APFS
reference의 block-zero NXSB, checksum, signed physical address, JSDR version과
bounded extent를 검증하고 partition-relative ReadAt로 exact driver bytes만 추출한다.
구조 offset은 독립 C layout과 교차 확인하며 상세 출처/미지원 Fusion 조건은
`nextcore/artifacts/apfs-jumpstart-20260908/contract.md`에서 박제한다.

root는 별도 feature `apfs-jumpstart`의 NXAPFS EFI application과 adapter를 소유한다.
GPT APFS type의 논리 partition 하나를 요구하고 PartitionInfo/BlockIO의 크기와
media ID를 확인한다. DiskIo는 읽기만 수행하며 모든 프로토콜 borrow를 driver
실행 전에 해제한다. 기본 모드는 추출/전량 재읽기 대조다. 명시 load option
`--start-driver`에서만 firmware LoadImage/StartImage를 호출하고 boot-services driver
종류를 검사한다. firmware의 인증 실패·경고를 성공으로 바꾸지 않으며 반환된
실패 image handle을 정리한다. 성공한 resident driver는 source buffer를 빌리지 않고
선택한 controller에만 명시 ConnectController를 호출한다. firmware StartImage
자체는 새로 생성·변경된 handle에 자동 연결을 수행할 수 있으므로 전체 실행의
영향을 해당 controller 하나로 한정했다고 주장하지 않는다.

기존 production BOOTX64/picker와 타 partition은 변경하지 않는다. 먼저 독립 작성
GPT/APFS fixture 및 자체 EFI driver로 실제 OVMF 읽기·실행·거부·정리를 검증한다.
원본 APFS는 installer 담당이 종료 후 지정한 immutable snapshot의 별도 COW에서만
검증한다. 원본 byte·private 로그는 격리하고 host 전후 hash와 firmware/guest 결과를
각각 기록한다. 추출 성공을 mount·설치 OS·guest Metal 성공으로 승격하지 않는다.

### BP24-B — 드라이버가 게시한 APFS 파일시스템 관찰

원본 driver의 StartImage/ConnectController 성공 다음 단계는 실제 OpenVolume과
root directory Read다. 해당 adapter와 순수 metadata parser, 회귀 하네스는 x86
담당에게 명시 위임했으며 먼저 작성한
`nextcore/artifacts/apfs-filesystems-20260908/contract.md`가 입력·제한·판정 계약이다.
root는 코드 검토와 종료된 첫 설치 snapshot의 독립 COW 실행을 담당한다.

새 명시 옵션 `--inspect-filesystems`는 기존 driver 실행 후 선택 APFS partition의
정확한 device-path node 후손만 연다. 256 handles/32 volumes, root 한 단계,
volume당 128/global 512 records, 응답당 4096B/global 1MiB를 제한하고 EOF를 별도
Read로 확인한다. raw protocol lease와 반환 크기 기반 파싱으로 가변 길이 metadata와
DevicePath를 무제한 참조 변환하지 않는다. 파일 쓰기·하위 파일 열기·booter 실행은
이 단계의 동작에 없다. 실제 이름·경로는 격리하고 공개 결과에는 관찰 개수·상태와
원본 hash 유지·종료 증거만 기록한다. 파일시스템 관찰은 설치 OS/Metal 판정과 구분한다.

### BP24-C — 명시 APFS volume의 피커 target 실행

BP24-B는 원본 APFS 볼륨 4개의 root 접근을 실제 확인했다. 다음은 설정 entry의
optional `ApfsVolume` label을 엄격히 검증하고 선택한 APFS 후손 볼륨의 명시
EFI Path를 firmware LoadImage/기존 application lifecycle에 연결하는 단계다.
기존 필드가 없는 entry는 동일 volume 동작을 유지하며 지원 feature가 없는
build에서는 APFS entry를 UNSUPPORTED로 거부한다. 정확한 label 하나만 허용하고
임의의 첫 volume 선택이나 fallback을 하지 않는다.

먼저 작성한 `nextcore/artifacts/apfs-target-20260908/contract.md`가 상세 계약이다.
Core parser/tests는 root, EFI adapter/main 연결·합성 firmware 회귀는 x86 담당에게
명시 위임한다. 원본 실행은 installer 담당이 종료/불변을 확인한 snapshot의 새 COW만
사용한다. 원본 booter 경로는 격리 설정 입력이며 공개 구현에 hard-code하지 않는다.


### BP25 - WSL2 ARM64e boot and real submodule integration (2026-09-08)

Current state: seven crates are copied into the superproject despite independent
module histories. ARM metadata/staging and boot_args are separate; there is no
AArch64 EFI handoff. Guest Metal command execution remains unverified.

DECIDED (current user): work in WSL2, obtain original macOS 27 inputs for an M1
baseline, prioritize ARM boot, develop graphics concurrently, and convert all seven
crates into fully integrated Git submodules. Root owns module integration, build/CI,
and original-input acquisition. ARM EFI agent owns ARM core placement/config, EFI
entry and authored firmware execution tests. ARM recovery agent owns actual PAC
CPU execution checks and reproducible QEMU provisioning. GPU agent owns compute
command dispatch and actual backend/readback validation. Their detailed contracts
are recorded under nextcore/artifacts before implementation. Existing sources,
module histories, firmware authentication and ARM64e PAC semantics are preserved.

The module conversion reuses existing repository histories and preserves active
source edits. Cargo workspace patches select checked-out local modules, while each
standalone module pins remote dependencies. CI recursively initializes all gitlinks
and verifies resolution. No original firmware or private output enters a module.
A recursive fresh clone must resolve the exact module commits before conversion
can be called complete. Root coordinates the index and local commits after tests.

Actual kernel/GUI/Metal acceptance remains tied to guest execution evidence;
authored handoff/PAC payload results are reported as their own layers.

### BP25-A - Corrected target: x86 EFI macOS-specific JIT compatibility layer

The current user clarified that the physical computer is always x86. macOS 27's
ARM build is the input because there is no x86 build for this target. WSL2 is
only the development/build environment. Product execution must begin in x86
EFI and use a macOS-optimized ARM64e-to-x86_64 JIT plus HAL compatibility layer.
A host-OS QEMU process, a physical M1, or an ARM-native EFI application cannot
serve as the target implementation. QEMU and BOOTAA64 may remain reference
validation tools, with their evidence named accordingly.

Root retains submodule integration and provisioning. CPU agent is delegated
preOS ARM64e/PAC architectural semantics and native JIT bridge; boot agent is
delegated ARM image/argument placement into the x86 EFI compatibility runtime;
GPU agent owns no_std display scanout and backend dispatch. Runtime sources
will be owned by the ISE submodule, with explicit EFI and workspace dependencies.
Metal still requires actual hardware command translation and guest completion.

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


## BP25-B — macOS 27 startup ABI and bounded original-input trace

Current: independently authored ARM64e fixtures execute in x86 EFI. The original
M1-baseline kernel collection stages unchanged, but its startup contract must be
established separately. Public XNU `osfmk/arm64/sptm/start_sptm.s` documents a cold
startup selector in x0, traditional boot arguments in x1, and SPTM arguments in
x2. A legacy x0=boot-arguments handoff cannot be assumed for this entry shape.

Decision: the EFI agent owns explicit diagnostic initial-register selection and
bounded original-input tracing. The CPU agent owns generic ARM immediate
arithmetic/condition flags and conditional control flow needed at the observed
first instruction boundary, with independently authored tests. This delegation
reopens those source scopes while module metadata/integration remains root-owned.
Unknown SPTM argument structures and services must not be fabricated or reported
as implemented. Any partial trace must state missing startup prerequisites and
must not be treated as correct macOS cold boot. Raw original instructions and
addresses stay in `_isolated/`; public receipts contain only outcomes and limits.

Reference: https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/arm64/sptm/start_sptm.s

Wanted: establish and test the selected startup ABI, virtual-address translation,
MMU and SPTM interface before advancing to sustained XNU initialization. Synthetic
success and partial original instruction execution remain distinct milestones.


## BP26 — continue original startup and runtime integration

Current: the original macOS 27 prefix retires four instructions in x86 EFI,
then stops at a standard thread-pointer system register. Submodules are locally
committed and independently linked; remote publication remains a separate pending
action. Continued implementation does not depend on publication.

Decision and delegation: the CPU agent owns ISE thread/context system registers,
architectural state and their native/reference ABI consistency, with public ISA
semantics and independently authored tests. The EFI/Core agent owns reproducible
original-prefix tracing and explicit boot prerequisites; it may add a separate
bounded firmware DeviceTree-template parser, preserving the strict runtime parser
and unresolved template state. Unknown platform values must remain explicit.
The GPU agent owns the GPU module's guest-command submission boundary: inspect
and extend existing bounded queues/adapters rather than duplicate them, connect
supported compute commands to the validated backend, and reject unsupported
operations explicitly. Root owns translation/memory integration review, submodule
revision propagation, metadata, provisioning and final regression validation.

Wanted: replace the observed standard-register boundary, observe the next actual
original instruction boundary, and improve independently testable memory and GPU
interfaces without claiming SPTM services, runtime device-tree resolution, XNU
boot or macOS Metal completion prematurely. Original code and private coordinates
remain under `_isolated/`; only public interface implementations and independently
authored fixtures enter module commits. No source copies return to the parent.


BP26-A decisions: root owns `ISE/runtime/preos/src/mmu.rs` to correct distinct
TG0/TG1 architectural granule encodings, validate disabled translation-table walks,
and retain deterministic failures for unsupported regimes. CPU source changes
outside that file remain delegated. Arm's Cortex-A73 TRM TCR_EL1 table and Arm's
Memory Management guide specify distinct TG1 and TG0 encodings; synthetic table
walks will establish lower/upper 4 KiB and 16 KiB behavior and rejection cases.
GPU agent is explicitly delegated the existing APLS SGPU codec move into GPU,
with APLS re-exporting the same public types. This is ownership consolidation of
the existing wire format, with bounded counts/lengths and compute submission
through the existing executor, not introduction of a parallel command protocol.
