# BP16 공개 장치 계약 조사 A

작성: 2026-09-07. 계층: 공개 QEMU 장치 모델과 게스트 MMIO 인터페이스. 현재 상태는 BP14의 동일 fault access가 실제 복원 DeviceTree의 한 node 범위에 포함되지만 현재 QEMU system view에 대응 mapping이 없는 것이다. 원하는 상태는 그 node의 compatible과 접근 offset·폭·반환 의미를 함께 뒷받침하는 공개 계약을 확보하는 것이다.

**판정: HOLD. 검토한 1차 소스에서 일치하는 계약을 찾지 못했다.** 선택된 DeviceTree 원본 해시는 이전 receipt와 동일하다. 그 node의 compatible은 PL031과 일치하지 않으며 별도 role 속성도 없다. 정확한 주소, offset, node/compatible 원문 및 상세 비교는 `_isolated/nextcore/apls-panic-20260907/bp16-public-contract-private.json`에만 기록했다.

## 후보별 판정

| 공개 후보 | 대상/compatible 대조 | register·접근 의미 | 현재 모델 및 결정 |
| --- | --- | --- | --- |
| QEMU VMApple의 PL031 | 현재 VMApple가 실제로 instantiate하는 공개 장치이지만 선택된 node의 compatible과 불일치 | 관측된 상대 access는 PL031의 명명된 register 및 ID register coverage 밖이다. `pl031_read()`의 bad-offset fallback에 해당한다. | 기존 PL031 범위는 선택된 node 범위와 겹치지 않는다. 그곳으로 alias하는 구현 근거가 아니다. HOLD. |
| Linux Apple SMC RTC | binding은 `apple,smc-rtc`이며 선택된 compatible과 불일치 | SMC를 통해 counter를 읽고 NVMEM offset을 합성하는 인터페이스다. 선택된 가상 장치의 직접 MMIO load 반환값·read side effect·reset state를 정의하지 않는다. | transport 불일치로 제외. |
| OpenBSD Apple SMC | `apple,smc`/해당 SoC SMC binding과 하위 RTC 경로 | SMC key read와 NVMEM offset을 사용하는 시간 조회다. 같은 MMIO offset/폭의 계약으로 전용할 수 없다. | transport 불일치로 제외. |
| Apple 공개 XNU platform expert | 검토한 ARM 초기화/식별 소스에서 선택된 exact identity token의 binding을 찾지 못했다. | CPU/timebase·platform 초기화 정보는 있으나 선택된 MMIO read의 의미를 확인할 계약은 없다. | 검토한 두 파일의 범위에서 불일치. Apple 공개 소스 전체의 부재를 주장하지 않는다. |
| Asahi m1n1 | 고정 tree의 전체 경로 목록에서 RTC/VMApple 이름을 가진 구현 경로 0개 | 파일명 조사만으로 코드 내부 구현 부재를 증명하지 않는다. | 추가 matching contract를 확보하지 못한 보조 메타다. |

QEMU PL031의 잘못된 offset에서 반환하는 fallback 값은 선택된 장치가 요구하는 정상 응답이라는 증거가 아니다. 단일 read 폭이 처리 가능하다는 사실도 compatible·register·상태 의미의 일치를 대신하지 못한다. 따라서 PL031 alias, zero-return MMIO, 임의 RAM mapping 또는 guest patch를 추가하지 않는다. 이 HOLD는 BP16의 장치 모델 구현 게이트에 한정된다.

## 확인한 1차 소스

- **QEMU commit `ff1d2d19d7e24893e2012d879f8e73077e17b9bd`**: [VMApple machine](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/vmapple/vmapple.c)의 `memmap`/`create_rtc()`와 [PL031 구현](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/rtc/pl031.c)의 register 정의, `pl031_read()`, `MemoryRegionOps`를 읽었다. 기존 PL031의 public contract가 선택된 node에 자동 적용되지는 않는다.
- **Linux tag `v6.19-rc7`**: [Apple SMC RTC binding](https://github.com/torvalds/linux/blob/v6.19-rc7/Documentation/devicetree/bindings/rtc/apple%2Csmc-rtc.yaml)과 [Asahi 기여 RTC driver](https://github.com/torvalds/linux/blob/v6.19-rc7/drivers/rtc/rtc-macsmc.c)의 `macsmc_rtc_get_time()`을 대조했다. 이 공개 구현은 SMC counter와 NVMEM의 조합이며 이번 가상 장치 MMIO 계약과 다르다.
- **OpenBSD commit `8da35e4bf6afbf16c87dcd7a1fb460782b5682b6`**: [aplsmc.c](https://github.com/openbsd/src/blob/8da35e4bf6afbf16c87dcd7a1fb460782b5682b6/sys/arch/arm64/dev/aplsmc.c)의 compatible 검사 및 `aplsmc_gettime()`을 읽었다. SMC/NVMEM 경로가 확인되며 선택된 직접 MMIO read 계약은 아니다.
- **Apple XNU commit `f6217f891ac0bb64f3d375211650a4c1ff8ca1ea`**: [pe_identify_machine.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/pexpert/arm/pe_identify_machine.c), [pe_init.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/pexpert/arm/pe_init.c). 공개 ARM platform 초기화와 clock/timebase 정보의 범위를 확인했다.
- **Asahi m1n1 tree `940439b9a407fbfc499bea933269219f3f62d4c7`**: [공식 저장소 tree API](https://api.github.com/repos/AsahiLinux/m1n1/git/trees/940439b9a407fbfc499bea933269219f3f62d4c7?recursive=1). 응답은 truncated=false이며 경로 조사에만 사용했다.

위 pinned 파일 7개를 실제 읽고 각각 SHA256을 메타 JSON에 기록했다. ARM PL031 TRM의 웹 본문과 추가 Linux PL031 binding은 이번 열람에서 확보되지 않아 그 내용에 의존하지 않았다. 검색에 나타난 추출 DeviceTree gist와 사용자 부팅 로그는 primary register contract로 채택하지 않았다.

## 산출물과 남은 게이트

`bp16-public-contract-survey.json`은 compatible 일치, register coverage, source revision/hash 및 판정을 담는다. 공개 파일에는 private 주소·node 원문이 없음을 검사했다. 새 VM 실행과 제품 소스 수정은 모두 0회다. 현재 QEMU mapping/flatview 독립 대조는 병렬 조사 B의 receipt와 함께 읽는다.

재개에 필요한 것은 선택된 compatible에 대한 공개 driver binding과 해당 read의 반환값·폭·부작용·reset state를 설명하는 계약이다. 현재 판정은 `supported_public_contract_found=false`, `device_identity_verified=false`이며 XNU/userspace/macOS 부팅 증거로 승격하지 않는다.

OPEN_QUESTION: Build Plan: matching public device contract를 확보하기 전까지 BP16 모델 구현은 HOLD로 유지한다.
