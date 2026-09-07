# Nextcore 작업 지시서 (Build Plan Slot)

## 책임

Nextcore의 *어떻게*를 박제한다 — Rust 모듈 구조, 단계별 구현 순서, 검증,
의존성, 빌드 산출물. *무엇*과 *왜*는 Design 슬롯의 영역이다.

## 현재 상태

- BP1~BP5 모두 박제된 결정으로 채워짐 (이전 세션의 골격에서 확장).

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
    - 게이트 자동화: `cargo check --workspace && cargo test --workspace --no-run`
    - 완료 기준: 빈 crate 셋업이 host + UEFI 양쪽 타깃에서 컴파일 통과.
    - 기대 출력: `cargo check` 종료 코드 0, `cargo test --no-run`에서 전 crate 빌드 성공 로그.
    - Pass: `cargo check --workspace` 종료 코드가 0이다.
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

## OPEN_QUESTION

- `OPEN_QUESTION: Design:handoff 자료 구조의 *공개 명세*가 정확히 어디까지 정의되는지`
  — Build Plan은 BP3 단계 6/7을 *공개 DeviceTree + 공개 Mach-O + EFI Handoff
  컨벤션*에 한정해 구현. Design이 *어디까지*를 *공개 명세의 범위*로 인정할지
  박제해 주면 BP3 단계 6/7의 필드 셋이 그에 맞춰 확정됨.
- `OPEN_QUESTION: Prompts:Step 3 카피의 호스트 OS별 분기 문구 반영`
- `OPEN_QUESTION: Boundary:격리 자산에 들어가는 Mach-O / ACPI 명세 문서는 어떤 수준까지 허용되는지`
  — Build Plan은 BP3 단계 8의 mock 환경 명세로 *공개 명세로 표현 가능한
    범위*를 한 번 더 박제함. Boundary가 격리 폴더 운영 규칙을 확정해 주면
    BP3 단계 7의 `goblin`/`aml` 사용 범위도 그에 맞춰 조정됨.

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