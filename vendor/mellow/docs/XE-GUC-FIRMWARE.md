> **Historical record — preserved unedited.** Component documentation for the hand-written
> Intel Xe backend, which compiles into the kext but has no call path
> ([Mellow/RuntimeReadiness.hpp:84](../Mellow/RuntimeReadiness.hpp)). Scheduled to move to
> `docs/backends/xe/` in P1. For how these modules map onto the vendor-neutral abstraction
> see [MGAL.md](MGAL.md); for the current architecture see [ARCHITECTURE.md](ARCHITECTURE.md).

# 7D41 GuC firmware DMA 적재·인증 프로토콜

`Mellow/XeGuCFirmware.*`에는 실제 MMIO 적재 프로토콜과 실패 시 메모리 수명 관리가 구현되어 있다. `XeGuCFirmwareIOKit.*`는 실제 IOPCIDevice, BAR0 매핑, IOBufferMemoryDescriptor 및 IODMACommand 동기화에 연결하는 adapter다. **원본 펌웨어를 사용하는 host 시험은 통과했지만, 물리 7D41에서 적재·BootROM 인증·GPU 실행을 시험한 결과는 없다.** 자동 시작 경로에서 모든 선행조건을 충족하는 GGTT/PAT 소유자는 아직 제공되지 않는다. 빈 callback을 성공으로 바꾸지 않는다.

## 고정된 입력과 근거

대상은 물리 `8086:7D41`, BDF `00:02.0`, 실제 GMD_ID가 graphics **12.70**인 main GT다. PCI spoof 후 ID나 제품 이름만으로 이 조건을 충족했다고 판단하지 않는다. IOKit adapter는 PCI command의 MMIO decode·bus master 활성화, PM capability의 PMCSR D0, 유지 중인 GT forcewake도 검사한다. 장치 소유권·reset epoch·quiescence는 동일한 직렬화 영역의 실제 장치 소유자가 제공해야 한다.

입력은 linux-firmware commit `2f2bf38a3d030a083d8b2b1fea2aa0e9b29a48bd`의 원본 `i915/mtl_guc_70.bin`이다. 파일 크기는 320,320 bytes, SHA-256은 `7794f0b6abe5fcd9c6f47035dafe2199f30a6e7d230bd5a53fbf8005a60e5911`이다. 실제 CSS 값은 release **70.53.0**, submission ABI **1.26.0**, CSS 128 bytes, uCode 319,808 bytes, RSA 384 bytes, private data 8,392,704 bytes다. `inspectPinnedFirmware`는 크기·SHA-256·CSS 값을 모두 확인한다. 이는 입력 식별이며 GPU 인증을 대신하지 않는다. 기존 `tests/xe_submission_fetch_firmware.py`, provenance와 `xe_submission_LICENSE.i915`를 재사용한다. 원본 blob은 scratch에만 두었다. [고정 Intel firmware 원본](https://gitlab.com/kernel-firmware/linux-firmware/-/blob/2f2bf38a3d030a083d8b2b1fea2aa0e9b29a48bd/i915/mtl_guc_70.bin)

프로토콜 구현 근거는 Linux commit `4d7d9486c04d917265f64c55bd23b2cc4fe7749c`이다. 아래 주소들은 이 commit에 고정되어 있으며 최신 main branch 동작을 무조건 혼용하지 않는다.

## 구현한 실제 순서

1. 세 region의 소유자·generation·CPU 범위·GGTT 범위·페이지 수를 확인하고 실제 pin/GGTT 예약을 retain한다. firmware는 읽기, ADS/log는 장치 쓰기 용도로 보유한다. 각 region은 최대 64 MiB이고 서로의 CPU/GGTT 범위가 겹치면 거절한다.
2. 원본 firmware를 확인하고 PAT3의 실제 MCR-aware readback 값이 `2`인지 검사한다. 각 GGTT PTE의 값이 해당 region의 retained DMA 페이지와 정확히 일치하는지 읽는다. PTE 설치와 TLB invalidation 완료 증거도 별도로 요구한다.
3. 실제 quiescence 확인 후 `GDRST.GRDOM_GUC`를 쓰고, reset bit 해제(최대 5 ms), MIA reset 상태, DMA idle(최대 100 ms)을 읽는다. 첫 reset 확인 전에는 공유 ADS/log를 덮어쓰지 않는다.
4. WOPCM의 size/offset lock 상태와 기존 배치를 검사한다. 미설정 MTL 배치는 4 MiB, BIOS가 잠근 배치는 Linux와 같은 최대 8 MiB 범위로 검증한다. HuC 예약 + 16 KiB 정렬, 끝의 HW context 36 KiB, GuC reserve/stack 24 KiB를 계산한다. write-once size/offset을 쓴 후 하드웨어가 세운 LOCKED/VALID와 주소를 다시 확인한다. 일부만 잠긴 배치를 추측으로 복구하지 않는다. [WOPCM 배치·초기화 원본](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_wopcm.c)
5. 필요 시 minimal ADS를 생성하고 log를 초기화한 뒤 실제 IODMACommand device synchronization을 한다. scratch 14개 boot parameter, MTL SHIM, doorbell 활성화, ARAT mask를 기록한다.
6. 384-byte RSA는 `UOS_RSA_SCRATCH(0)`에 **RSA의 GGTT 주소**를 쓴다. 64개 scratch slot에 잘라 복사하지 않는다. CSS+uCode 319,936 bytes를 GGTT에서 WOPCM offset `0x2000`으로 DMA한다. `DMA_CTRL` masked START/UOS_MOVE 후 최대 100 ms 동안 실제 START 해제를 기다리고 UOS_MOVE를 해제한다. [GuC 전송 준비·RSA·boot 원본](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_guc.c), [uC DMA 원본](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_uc_fw.c)
7. `GUC_STATUS`에서 AUTH_GOOD, BootROM JUMP_PASSED, uKernel READY 및 reset/halting 해제를 모두 확인한 경우만 `Running`으로 바꾼다. RSA/key/WOPCM 등 알려진 terminal 오류를 구별하고 최대 3초로 제한한다. 단조 시간 역행, all-ones read, I/O 실패도 성공이 되지 않는다. `running(owner, epoch)`는 호출 때 실제 상태를 다시 읽는다. [공개 상태 코드](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/abi/guc_errors_abi.h), [레지스터 정의](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/regs/xe_guc_regs.h)

HuC/GSC 적재·인증은 별도다. 기본 `hucUploadBytes=0`은 이 boot에서 HuC가 제공되지 않았음을 뜻한다. 0이 아닌 값은 소유자가 검증한 HuC upload 크기여야 하며 이 값만으로 HuC 인증이 완료됐다고 보고하지 않는다. PCODE를 통한 unslice 최고 주파수 요청과 SLPC 초기화도 포함하지 않았다. SLPC flag는 켜지 않으며 주파수와 무관하게 bounded boot timeout을 유지한다.

## ADS와 실행 가능 상태의 구분

기본 `HardwareConfig` profile은 공개 minimal ADS 구조를 생성한다. 모든 engine mask는 0, 16×32 mapping table은 invalid instance 32, 정책 DPC 시간은 500,000 µs, 최대 work item은 15다. `DIST_DBS_POPULATED`에서 doorbell 개수를 읽는다. 공개 packed 구조에서 계산한 ADS/policies/system-info offset을 사용하고 private data는 24,576-byte 정렬 prefix 뒤에 둔다. 원본 firmware에는 총 **8,417,280 bytes**의 ADS backing이 필요하다. minimal profile은 GuC boot/hwconfig 단계용이며 LRC 제출을 지원하는 ADS가 아니다. [minimal ADS 및 packed ABI](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_guc_ads.c), [fwif 구조](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_guc_fwif.h)

`Submission` profile은 전체 ADS를 새로 꾸며 만들지 않는다. `fullAdsValid`가 실제 engine masks/mapping, 저장·복구 regsets, golden LRC backing, WA KLV 내용을 검증해야 한다. 이 callback이 없거나 거짓이면 첫 MMIO 쓰기 전에 거절한다. 이 profile의 parameter에는 lite restore, multi-queue 비활성화, 12.70 TSC workaround 및 실제 CCS 존재 시 dual-queue workaround가 들어간다. `submissionProfile()`은 profile 정보다. 최신 hardware health, 활성 CTB, context registration, IRQ 또는 fence 완료를 대신하지 않는다.

## GGTT 및 자원 계약

`Region`은 kernel 내부 전용이며 user-client가 넘기는 임의 주소를 받는 API가 아니다. `retain`은 IOMapper DMA 페이지·GGTT 예약·CPU view의 생존, generation, 정확한 크기, alias 방지, 다른 writer 배제를 보장해야 한다. 검사부터 reset/release까지 같은 sleepable 직렬화 영역을 사용한다. device/MMIO/forcewake/proof objects는 Loader보다 오래 살아 있어야 한다. `retain` 실패는 소유권을 획득하지 않았다는 뜻이고 `release` 실패는 소유권이 남아 있다는 뜻이다.

`verifyGgtt`는 실제 BAR0 `+8 MiB` GSM window에서 각 4 KiB 페이지의 8-byte PTE를 high/low/high로 읽는다. 안정된 PTE가 `DMA address | PRESENT | (PAT3 << 52)`와 정확히 일치해야 한다. DMA 주소는 46-bit/page-aligned로 제한하고 DM/VFID/예상하지 않은 bit는 거절한다. writer lock과 retain 없이 세 번 읽는 것만으로 원자성을 보장하지 않는다. [GGTT window 및 publication 원본](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_ggtt.c), [PTE bit 정의](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/regs/xe_gtt_defs.h)

현재 helper는 GGTT **readback**을 구현한다. 실제 GGTT allocator, 전역 writer lock, PTE qword publication, 해당 GT/media TLB invalidation을 생성하지 않는다. PPGTT `Bound`나 BAR2를 GGTT 매핑으로 취급하지 않는다. main GT의 PAT3는 MCR 접근 대상이므로 `0x480C`를 한 번 평범하게 읽고 검증 완료라고 만들지 않는다. 실제 MCR-aware reader의 `2` 값과 publication proof가 필요하다. [Xe-LPG PAT 설정 원본](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_pat.c)

첫 MMIO 쓰기 이전 실패는 retain한 region을 역순으로 해제한다. 하나라도 MMIO 쓰기를 시도한 뒤에는 write callback이 실패해도 장치가 요청을 봤을 가능성을 인정하고 세 backing을 보존한다. timeout 뒤 늦게 READY가 와도 실패한 loader가 자동으로 살아나지 않는다. `resetAndRelease()`가 실제 reset·MIA reset·DMA idle을 확인해야 backing을 해제한다. 확인 실패나 release 실패는 quarantine 상태로 소유권을 남긴다. 소유자는 그런 loader와 backing을 강제로 파괴하거나 재활용하면 안 된다. Loader는 single-use이며 재시도에는 새로 승인된 reset epoch가 필요하다.

## 검증과 재현

`tests/xe_guc_firmware_test.py`는 production C++ source를 직접 컴파일하고 원본 firmware를 입력으로 사용한다. 테스트 장치·PAT·GGTT·ownership callback은 명시적 emulator이며 실제 하드웨어를 흉내 낸 시험 입력이다. **1,490 assertions 통과**: SHA/CSS, malformed/torn PTE, PAT·publication 거부, WOPCM 배치·부분 lock, 실제 29-write 순서, 각 write의 실패 주입, minimal ADS 값, 22개 terminal 상태, reset/DMA/auth timeout, 경계 시간·시간 역행·정지 clock, 늦은 READY, pin 유지, 부분 release 실패와 DMA idle 미확인 시 해제 금지를 포함한다.

```text
python tests/xe_submission_fetch_firmware.py --output <scratch>/mtl_guc_70.bin
python tests/xe_guc_firmware_test.py --firmware <scratch>/mtl_guc_70.bin --report tests/xe_guc_firmware_results.json
```

결과 JSON에는 검사한 production source와 원본 firmware SHA-256, hardware 미검증 범위를 기록했다. IOKit adapter의 SDK compile 결과는 전체 빌드 담당 보고서에서 별도로 확인한다. Windows에서 GPU register, firmware load, ROM 또는 USB 변경은 실행하지 않았다. 실제 acceptance에는 소유된 7D41/12.70 macOS 환경에서 GGTT/PAT 증거, 마지막 GuC 상태, reset 후 backing 반환 여부, CTB ACK, 실제 context fence, Metal 결과 검증을 각각 수집해야 한다.

공개 Intel 프로토콜 및 ABI의 원래 copyright는 Intel Corporation(2014–2022 및 각 원본 파일의 해당 연도)에 있으며 Linux 파일은 MIT 식별자를 사용한다. 이 문서의 고정 원본 링크가 각 파일의 attribution을 보존한다. 기존 Mellow와 타사 파일의 원래 license는 그대로 적용된다.
