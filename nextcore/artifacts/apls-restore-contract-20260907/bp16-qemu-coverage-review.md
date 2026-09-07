# BP16 B — QEMU 장치 등록 및 범위 대조

작성: 2026-09-07. 계층: QEMU 호스트의 장치 생성·MemoryRegion 연결 → ARM 게스트의 물리 주소 decode. 조사 범위는 저장된 관측과 로컬 소스이며 새 VM·TSS·네트워크 요청과 코드 수정은 없다.

현재 상태: BP14 same-event의 4바이트 읽기는 부모 bus translation을 적용한 private 복원 DeviceTree 노드 하나의 범위 안에 있다. pinned/base machine map, 현재 machine map, 저장된 CPU system flatview에는 그 노드 범위와 겹치는 영역이 없다. 원하는 상태는 실제 장치의 공개 binding과 해당 register 의미를 확인해 구현 여부를 결정하는 것이다.

결정: **등록·주소 범위의 불일치는 확인했으며 장치 정체와 반환 의미는 HOLD다.** 기존 모델에 임의 alias를 추가하거나 빈 MMIO를 만들 근거는 확보하지 않았다. 정밀 주소, private 노드 이름·속성 원문과 레지스터 값은 이 문서와 JSON에 포함하지 않았다.

## 관측과 소스의 시점

- 로컬 QEMU: `/tmp/26x86-vmapple-tcg-build-0907b/qemu`, base commit `ff1d2d19d7e24893e2012d879f8e73077e17b9bd`. worktree에는 연구 변경이 있다. base machine SHA256은 `2e7f872746da5183e745dcb7b2bb2137b76716f4abeae0a0b78921402a05384a`, 현재 machine SHA256은 `6fcd457542de1b2e65bf68e75380d686df489bd5a57b13e10e8f863f49fe2fef`다. 로컬 변경을 upstream 구현으로 표시하지 않았다.
- debugger의 VA/PA·폭·응답은 **동일 fault 이벤트**의 관측이다. 이에 반해 `info mtree -f`는 private observer의 `label == 'reset'` 경로에서 저장됐다. **fault 순간의 추가 flatview를 관측한 것은 아니다.**
- 저장본에는 여러 주소 공간의 영역이 총 25개 있다. CPU 두 개와 `memory`가 공유하는 system flatview의 **16개 영역만** CPU 물리 주소 판정에 사용했다. 별도 virtio PCI 설정 공간과 I/O 공간을 CPU mapping으로 합치지 않았다.
- system reset-view의 16개 영역은 접근 전체와 private 노드 전체 범위 모두를 덮지 않는다. base 16개·현재 17개의 선언 map도 접근을 덮지 않으며 현재 선언 map 전체가 노드 범위와 겹치지 않는다. 실제 RAM 크기와 연구 alias는 선언의 RAM placeholder 크기 대신 reset-view의 실제 범위로 추가 대조했다.
- fault 시점의 동적 flatview는 미관측이다. 고정 sysbus 연결, PCI aperture, RAM alias에 대한 소스 범위 대조와 reset snapshot 대조를 same-event snapshot이라고 합쳐 표현하지 않는다.

## 장치 등록 경로별 gap matrix

`겹침 없음`은 private 노드 범위와의 비교이며 장치 정체의 부정·긍정 판정은 아니다. 상세 boolean과 지문은 함께 저장한 `bp16-qemu-coverage-review.json`의 13개 행에 있다.

| 공개 모델 종류 | 현재 생성·연결 경로 | 기록된 실행 | 노드 범위 coverage |
| --- | --- | --- | --- |
| Firmware RAM | `vmapple_firmware_init`, machine source 354–385 | RAM 영역 존재 | 겹침 없음 |
| Configuration RAM | `create_cfg`, source 192–220; `cfg.c` MMIO 등록 | RAM 영역 존재 | 겹침 없음 |
| Optional RPC MMIO | cfg의 두 번째 영역; 명시 unavailable 옵션으로 활성화 | I/O 영역 존재 | 겹침 없음 |
| GIC distributor/redistributor | `create_gic`, source 253–301 | 두 영역 존재 | 겹침 없음 |
| UART | `create_uart`, source 304–317 | PL011 영역 존재 | 겹침 없음 |
| RTC | `create_rtc`, source 319–325, 호출 590 | **PL031 영역 존재** | **기존 RTC mapping과 불일치** |
| GPIO | `create_gpio_devices`, source 334–352 | PL061 영역 존재 | 겹침 없음 |
| Panic notification | `create_pvpanic`, source 181–190 | 영역 존재 | 겹침 없음 |
| Storage backdoor | `create_bdif`, source 148–179 | 영역 존재 | 겹침 없음 |
| AES banks | `create_aes`, source 236–246; `aes.c` 553–556 | 두 영역 존재 | 겹침 없음 |
| PCI apertures | `create_pcie`, source 387–447 | ECAM/MMIO container 존재 | 전체 aperture도 겹침 없음 |
| PV graphics/surface MMIO | source 222–234, 조건 분기 586–588 | headless이며 graphics 생성 생략 | 선언된 두 범위도 겹침 없음 |
| Main RAM/research alias | source 564–580 | 같은 RAM backing의 두 영역 존재 | 실제 두 범위도 겹침 없음 |

**PL031 모델이 없거나 VMApple에서 생성되지 않는다는 설명은 잘못이다.** 현재 `create_rtc()`는 `sysbus_create_simple("pl031", ...)`를 호출하고 machine 초기화가 이를 실행한다. reset flatview도 실제 PL031 영역을 보여 준다. 그러나 이 사실로 private 노드를 RTC로 식별하거나 다른 위치의 PL031 alias를 승인할 수는 없다.

VMApple 초기화는 고정 `create_*` 호출과 명시적인 `sysbus_mmio_map`/`memory_region_add_subregion` 연결을 사용한다. 이 경로에는 복원 DeviceTree의 각 노드를 순회해 QEMU 장치를 자동 생성하는 binding 단계가 없다. `bootinfo.skip_dtb_autoload = true`도 확인했다. 따라서 guest에 노드가 존재하는 것과 host에서 해당 장치를 연결하는 것은 별도 계약이다. 그래픽 활성화나 RAM alias 확장은 이번 범위 비교에서 수리가 뒷받침된 후보가 아니다.

## MEMTX_DECODE_ERROR의 해석

`include/exec/memattrs.h:89`의 명칭만으로 장치 정체를 판정할 수 없다. `system/memory.c:1367–1406`은 accepts, 정렬 및 폭을 검사하고, `memory_region_dispatch_read()`의 1446–1448은 그 검사가 실패해도 `MEMTX_DECODE_ERROR`를 반환한다. unassigned 영역뿐 아니라 이미 있는 영역에서 거부된 접근도 이 응답을 낼 수 있다.

이번 결론은 응답 코드 하나가 아니라 **same-event PA/폭**, **CPU reset flatview의 noncoverage**, **고정 장치·alias·PCI aperture의 소스 대조**를 분리해 결합한 것이다. 실제 fault 순간의 flatview 또는 MemoryRegion identity를 새로 읽었다고 주장하지 않는다.

## 구현 전에 필요한 공개 계약

1. 버전이 고정된 공개 출처, 대상 SoC/model 적용 범위, compatible/role과 구체 장치의 binding.
2. bus address/size cell 및 부모 translation, MMIO 전체 범위와 bank·alias·mirror 규칙.
3. 관측된 register offset의 정의, 허용 폭·정렬·endianness, 접근 privilege/security 속성 및 fault 의미.
4. reset 값과 순서, clock/power 가용성, read 반환 의미와 side effect, 쓰기 제한 및 미정의 register 처리.
5. 관련된 경우 interrupt·timer·DMA 상호작용과 QEMU realization/mapping 수명.
6. 독립 register 회귀와 한 번의 후속 same-event 관측에 사용할 성공/실패 조건.

이 필드들이 확인될 때까지 zero-return MMIO, 임의 RAM alias, panic skip 또는 firmware patch를 구현하지 않는다. 복원 진행, XNU 실행, userspace, macOS 부팅은 계속 별도 판정이며 이 조사는 새 부팅 성공 근거를 추가하지 않는다.

## 근거 위치와 검증

네트워크 없이 로컬 git blob과 현재 worktree를 읽었다. 아래는 같은 pin의 공식 참조 위치이며 이번 검토에서 새로 다운로드한 것은 아니다.

- [QEMU VMApple machine](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/vmapple/vmapple.c)
- [QEMU PL031](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/rtc/pl031.c)
- [MemoryRegion dispatch](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/system/memory.c)
- [Memory transaction result definitions](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/include/exec/memattrs.h)

최종 계산에서 읽은 소스·private 증거의 pre/post bytes가 일치했다. JSON은 source 지문, snapshot 시점, coverage boolean, 필요한 계약 필드만 보존한다. 제품 코드, 기존 관측, 시작 문서, Git staged 영역은 수정하지 않았다.
