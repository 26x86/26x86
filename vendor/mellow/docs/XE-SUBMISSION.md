> **Historical record — preserved unedited.** Component documentation for the hand-written
> Intel Xe backend, which compiles into the kext but has no call path
> ([Mellow/RuntimeReadiness.hpp:84](../Mellow/RuntimeReadiness.hpp)). Scheduled to move to
> `docs/backends/xe/` in P1. For how these modules map onto the vendor-neutral abstraction
> see [MGAL.md](MGAL.md); for the current architecture see [ARCHITECTURE.md](ARCHITECTURE.md).

# 7D41 GuC firmware·submission·fence 구현

이번 구현은 실제 실행 가능한 C++ 소프트웨어 계층이다. **7D41 하드웨어에
firmware를 적재하거나 GPU 명령을 실행한 결과는 아니다.** 하드웨어 adapter가
없는 경우 명시적으로 `UnsupportedBackend`를 반환한다. 이미지를 파싱한
것을 인증 성공으로, interrupt가 도착한 것을 작업 완료로 바꾸지 않는다.

## 확인한 정확한 플랫폼과 firmware

고정 Linux 소스 `4d7d9486c04d917265f64c55bd23b2cc4fe7749c`에서 `8086:7D41`은
`INTEL_ARL_U_IDS`이다. `xe_pci.c`는 ARL 전체를 `mtl_desc`에 연결한다.
따라서 ARL-U라는 제품 계열과 MTL 기반 드라이버 descriptor를 함께 기록한다.
해당 descriptor의 graphics/media IP는 **GMD_ID를 실제로 읽어 결정**한다.
PCI ID만으로 정확한 graphics IP와 stepping을 입증했다고 주장하지 않는다.

이 Linux 버전의 MTL GuC 선택 파일은 `i915/mtl_guc_70.bin`이며 권장 release는
70.53.0이다. `guc_read_css_info()`의 최소 허용 release는 70.29.2이다.
권장 minor보다 낮다는 것과 지원 major/minimum을 위반한다는 것은 구분했다.
동일 계열의 HuC는 `mtl_huc_gsc.bin`, GSC는 `mtl_gsc_1.bin`이며 이를 TGL
GuC 이미지로 대체하지 않았다.

정식 linux-firmware 저장소의 commit
`2f2bf38a3d030a083d8b2b1fea2aa0e9b29a48bd`에서 실제 GuC 파일을 내려받아
다음 값을 확인했다.

- 파일 크기: **320,320 bytes**
- SHA-256: `7794f0b6abe5fcd9c6f47035dafe2199f30a6e7d230bd5a53fbf8005a60e5911`
- 실제 CSS release: **70.53.0**
- 실제 CSS submission ABI: **1.26.0**
- uCode: **319,808 bytes**, RSA 영역: **384 bytes**
- CSS private-data 요구 크기: **8,392,704 bytes**
- 상태: **parsed-not-authenticated**, hardware authentication: **false**

원본 blob은 작업용 `work/`에만 보관했다. 결과물에는 고정 출처·해시·실제
parser 결과·원본 license 및 재다운로드 도구가 들어 있다. 이 metadata
파싱은 공개 CSS 구조의 길이·버전 필드를 읽은 것으로 firmware disassembly가
아니다. Intel license는 unmodified binary 재배포 조건과 별도 limited patent
license를 포함하며 원문은 `tests/xe_submission_LICENSE.i915`에 보존했다.

## 실제 구현한 코드

### XeFirmware: 공개 CSS 구조 파서

`parseGuCCss(data, length, info)`는 128-byte CSS header와 uCode/RSA 경계를
검증한다. 모든 DWORD 길이의 합·차·바이트 변환을 64비트로 계산해 정수
wraparound와 unsigned underflow를 피한다. header보다 작은 total size,
빈 uCode/RSA, 잘린 payload, 잘못된 header 길이 식을 거절한다. 비정렬
포인터를 구조체로 cast하지 않고 little-endian 바이트를 조합한다.

공개 CSS 규격에 따라 modulus/exponent는 header 길이에 표시되어 있으나
실제 파일에는 생략될 수 있다. 필수 구성인 header·uCode·RSA가 파일 안에
존재해야 한다. 버전과 device-info valid bit, security-info valid bit,
private-data 크기는 metadata로만 반환한다. **RSA 서명 검사, device
authentication, firmware upload를 수행하는 함수는 없다.**

### XeSubmission: 고정 크기 queue와 자원 수명

`SubmissionQueue(owner, context, backend, engine)`은 최대 32개 job,
job당 최대 64 DWORD와 8개 resource를 보관한다. 동적 할당을 하지 않으며
입력 명령·resource metadata를 내부 snapshot으로 복사한 뒤 검사한다.
caller가 이후 입력 배열을 바꿔도 이미 받아들인 snapshot은 바뀌지 않는다.

공개 API는 다음과 같다.

- `activate(info)`: firmware metadata와 adapter의 실제 readiness 결과를
  확인한다. device/GMD identity, DMA, page tables, GuC authentication,
  context registration, IRQ, coherent fence, submission ABI의 8개
  prerequisite가 모두 필요하다. 하나라도 빠지면 준비 상태가 되지 않는다.
- `submit(...)`: 명령 whitelist와 owner/mapping 범위를 검사하고 resource를
  retain한다. 일부 retain이 실패하면 앞서 확보한 자원만 역순으로 반환한다.
  backend가 완전 거절하면 자원을 반환하고 fence 번호를 소비하지 않는다.
- `onInterrupt(epoch, now)`: interrupt 자체에 완료값을 부여하지 않는다.
  backend에서 acquire-ordered hardware fence를 읽고 owner·context·engine·
  generation 일치, 기존 관측값보다 뒤인지, 실제 제출 범위 안인지 확인한다.
- `expire(now)`: deadline 이후 job을 `TimedOut`으로 바꾸지만 **DMA용
  resource를 해제하지 않는다**. timeout은 GPU가 메모리에 더 이상 접근하지
  않는다는 증거가 아니기 때문이다.
- `reset(now)`: adapter가 해당 queue의 DMA 중단과 IRQ/deferred callback
  배출을 확인한 경우에만 자원을 해제하고 generation을 증가시킨다.
  quiesce 실패 시 이전 자원과 generation을 유지한다.
- `query(token)`, `retire(token)`: 결과를 조회하고 더 이상 GPU가 보유하지
  않는 terminal job만 회수한다.

`BackendAcceptance::Unknown`은 제출 명령을 hardware가 받았는지 불확실한
경우다. 성공이나 거절로 추정하지 않고 자원을 보유한 채 reset을 요구한다.
timeout/unknown 이후 실제 늦은 fence를 관측하면 자원은 해제할 수 있지만
이미 결정된 결과를 성공으로 바꾸지 않는다. 중복 interrupt는 이중 release를
일으키지 않고, reset 이전 interrupt는 generation 검사에서 거절된다.

32비트 hardware sequence가 최대값에 도달하면 재사용하지 않는다.
`SequenceExhausted`를 반환하고 확인된 quiesce/reset 이후 새 generation에서
1부터 시작한다. 비교의 half-range 가정을 깨뜨리는 무검증 wrap은 없다.

### 명령 검증의 정확한 범위

Linux Xe의 `xe_mi_commands.h`에서 확인한 `MI_NOOP=0x00000000`,
`MI_BATCH_BUFFER_END=0x05000000`만 bootstrap stream에서 허용한다.
END는 마지막 DWORD여야 하며 없는 END, END 뒤 명령, 옵션 비트가 추가된
미검증 변형, register write, nested batch, 기타 opcode는 모두 거절한다.

이는 완전한 compute command parser가 아니다. 별도 Intel ocloc 작업에서
얻은 **7D41용 ELF/Zebin과 SPIR-V는 GPU ring packet이 아니며 이 함수에
제출할 수 없다**. ELF를 명령 스트림으로 해석하여 register를 쓰는 동작은
추가하지 않았다.

## 메모리 계층과의 연결 계약

`Resource.id`와 `mappingGeneration`은 `XeMemory::Handle`의 slot/generation을
식별한다. 이는 queue reset generation과 **다른 수명 주기**다. adapter는
`id=slot+1`, `mappingGeneration=handle.generation`으로 변환한 뒤
`VirtualMemory::inspect(owner, handle)`로 실재 allocation을 확인해야 한다.
caller가 넣은 `pinned=true`만 신뢰해서는 안 된다.

backend `retain`은 owner와 handle, 실제 `Bound` 상태, address/bytes를
확인하고 `retainUse`를 사용해야 한다. backend `release`는 검증된
terminal event에서 `releaseUse`를 호출한다. 그러면 timeout/unknown 동안
`activeUses`가 유지되어 VM의 reclaim을 막는다. 제출 전에 나중에 완료되지
않을 가짜 fence를 `recordUse`에 기록하는 우회는 필요하지 않다.

VM과 queue는 **공통 소유권 규칙 아래 직렬화**해야 한다. DMA pin/unpin과
IODMACommand prepare는 sleep 가능한 client context에서 수행하며 command-gate
action이나 interrupt context 안에서 실행하지 않는다. 대기 가능한 DMA 작업과
queue의 소유권 변경을 조정하여 retain/submit과 VM retire 사이의 원자성을 유지한다.
retain과 submit 사이 retire, callback 재진입, hardware가 아직 snapshot을
참조할 때 객체 파괴를 허용하지 않는다. 객체 크기가 크므로 kernel stack에
두지 않는다. 수명 종료 전에 성공한 quiesce/reset이 필요하다. 이 구현은
lock-free 또는 interrupt-thread-safe 컨테이너라고 주장하지 않는다.

## 남은 실제 hardware adapter

기본 `unavailableSubmissionBackend()`는 모든 callback이 비어 있으므로
activation/submission을 거절한다. 테스트 mock이 readiness flags와 fence를
돌려주는 것을 production adapter에 복사하면 안 된다. production 연결에는
다음 동작을 실제로 구현·검증해야 한다.

1. 읽은 GMD_ID/stepping과 GT·engine 정보를 바탕으로 한 backend 선택.
2. DMA pin과 실제 PPGTT/GGTT bind, PAT/cache 속성 및 TLB invalidate 완료.
3. WOPCM 및 GuC private-data 배치, boot parameters, firmware DMA upload,
   장치가 보고하는 RSA/auth/ready 상태 확인.
4. GuC submission ABI 1.26과 일치하는 CTB/context registration 및 실제 queue
   transport. command snapshot의 DMA mapping·fence emission·doorbell.
5. platform-specific IRQ 읽기·acknowledge와 coherent fence read barrier.
6. timeout/reset에서 해당 실행 context가 완전히 멈추고 callback이 배출됐다는
   증거, 재시작 시 정확한 memory/firmware/context 재등록.

MMIO 주소를 추측하거나 TGL object offset을 이 계층에 복사하지 않았다.
현재 시스템에서 GuC 인증이나 NOOP batch 실행도 확인하지 못했다. Metal
사용자 공간 ABI, compiler/runtime 및 화면 합성은 별도의 미완성 계층이다.

## 재현 가능한 시험

```sh
python tests/xe_submission_fetch_firmware.py --output work/mtl_guc_70.bin
python tests/xe_submission_test.py --firmware work/mtl_guc_70.bin --report tests/xe_submission_result.json
```

실제 `XeFirmware.cpp`와 `XeSubmission.cpp`를 호스트 C++ 컴파일러로
컴파일했고 **269 assertion groups**가 통과했다. firmware parser는 위
정식 blob에서도 실행했다. 시험은 truncated/overflow header, old/new
version, opcode 거절, 8개 readiness prerequisite, 부분 retain rollback,
불확실한 제출, owner/context/engine mismatch, acquire 없이 온 fence,
역행·미래·중복 sequence, timeout 뒤 late IRQ, 실패한 quiesce, reset 후
stale IRQ, queue capacity, 32비트 마지막 sequence와 새 generation을 포함한다.
실제 hardware callback은 전부 host mock임을 결과 JSON에 명시했다.

## 고정 1차 출처

- [PCI ID 계열](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/include/drm/intel/pciids.h)
  및 [ARL→MTL descriptor/GMD_ID](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_pci.c)
- [firmware 선택과 CSS validation](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_uc_fw.c)
  및 [공개 CSS ABI](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/abi/uc_fw_abi.h)
- [Xe hardware fence 구현](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_hw_fence.c)
  및 [MI command encoding](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/instructions/xe_mi_commands.h)
- [정식 고정 firmware](https://gitlab.com/kernel-firmware/linux-firmware/-/blob/2f2bf38a3d030a083d8b2b1fea2aa0e9b29a48bd/i915/mtl_guc_70.bin)
  및 [license 원문](https://gitlab.com/kernel-firmware/linux-firmware/-/blob/2f2bf38a3d030a083d8b2b1fea2aa0e9b29a48bd/LICENSES/LICENSE.i915)

위 source semantics를 참고해 portable state machine을 새로 구현했다.
Linux Xe driver 전체를 Darwin에 포팅했다는 의미가 아니다.
