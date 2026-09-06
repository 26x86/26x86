> **Historical record — preserved unedited.** This document predates the MELLOW
> re-architecture. It is retained because the record of what was known, and when, is itself
> evidence. For the current concept and architecture see [CONCEPT.md](CONCEPT.md) and
> [ARCHITECTURE.md](ARCHITECTURE.md); for what any of it is allowed to claim, see
> [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).

# 7D41 Metal 경로 수정과 검증 범위

작업 기준은 Mellow `f895d89653ea5cad3a534cce46a62d0f59384d71`이다.
이 문서는 이번 로컬 개발본의 `kern_gen11.cpp`, `kern_genx.cpp`,
`DYLDPatches.cpp` 변경을 설명한다. Samsung 750XHD에서 macOS 부팅이나
GPU 실행을 검증했다는 의미가 아니다.

## 실제 구현한 변경

### 제출한 작업과 성공 상태의 일치

기존 `getV142SubmitBlitMode()` 기본값은 1이었다. 이 경로는 GPU 링에 아무
작업도 넣지 않고 `submitBlit()`에서 0을 반환했다. mode 2는 같은 무작업
경로에서 1을 반환했다. 이는 화면 생성 여부와 GPU 연산 성공 여부를 구분할
수 없게 한다. 수정본은 **실제 제출이 없는 경우 `kIOReturnUnsupported`를
반환**한다. 값 3 또는 `-mellowV142orig`만 기존 TGL 제출 함수의 실험 호출을
선택한다. 이전 성공 위장 플래그는 더 이상 성공을 생성하지 않는다.

실험 호출에서는 다음 조건을 확인한다.

- 원본 함수 포인터와 accelerator, blit, vector, task 인자가 존재해야 한다.
- 기존 TGL ABI의 task `+0x298` 컨텍스트와 컨텍스트 `+0xb8` 채널이
  있어야 한다. 없으면 `kIOReturnNotReady`가 된다.
- inherited `routeSel=3`은 미검증 TGL EU 셰이더 경로이므로
  `kIOReturnUnsupported`로 반환한다.
- 수신한 task 객체를 다른 전역 캐시 객체로 바꾸지 않는다. 다른 task의
  컨텍스트를 task `+0x298`에 쓰지 않는다. 전역 캐시의 보유 횟수와 GPU
  주소 공간 소유권을 입증할 수 없기 때문이다.
- 검사를 통과한 호출은 **원래 task로 원본 함수를 한 번 호출**하고 원본의
  성공·실패 값을 그대로 반환한다. 실제 TGL 경로는 원본의 인자 검사를
  포함한 호출 계약을 유지한다.

이 변경이 `routeSel=0..2`의 7D41 하드웨어 실행을 입증하지는 않는다.
해당 ABI 오프셋도 inherited TGL 바이너리의 가정이다. 대상 바이너리의
해시·역어셈블 및 실제 명령 실행 검증이 아직 필요하다.

`barrierSubmission()`도 같은 원칙을 적용했다. 기존 default/hybrid 경로가
barrier를 제출하지 않고 1을 반환하던 코드를 제거했다. 미구현 ordering은
실패 0을 반환한다. 실험적으로 원본을 호출하려면 `mellowV130=2` 또는
`-mellowV130orig`와 기존 `-mellowV130forceorig`를 함께 지정해야 한다.
선택된 경로는 reference 인자와 count/list의 관계를 검사하고, 원래의
queue·accelerator·descriptor·event·list를 한 번 전달한 뒤 원본 결과를
보존한다. 호출 횟수에 따라 일부 barrier를 성공 처리하던 warmup 로직도 없다.
이 실패를 호출자가 어떻게 처리하는지는 macOS에서 확인해야 한다.

### 시작 실패, idle, GuC 상태 보존

`IGAccelDevice::deviceStart()`의 false→true 변환을 제거했고, 동일한 준비
검사를 건너뛰던 `f_devstart` 바이너리 패치도 제거했다. `IntelAccelerator::start()`
진입 시 준비 상태를 지우고, 원본의 성공 반환에서만 준비 상태를 설정한다.
실패 반환 이후에는 뒤에 이어지던 post-start 복구 쓰기를 실행하지 않는다.

`IGScheduler4/5::isGpuIdle()`는 이제 원본 판단을 그대로 반환한다.
`0xfffffffe`를 idle 증거로 취급하던 조건은 `0xffffffff`까지 허용했으며,
이는 잘못된 MMIO 읽기 값과 구분되지 않았다. 링의 head/tail과 하나의 상태
레지스터만으로 특정 command buffer의 완료를 판정해서는 안 된다.

7D41용 GuC 인증·제출 구현이 없는 상태에서 `loadGuCBinary()`가 성공 1을
반환하던 경로도 실패 0으로 바꿨다. 성공값을 반환한다고 host scheduler가
생성되거나 활성화되는 것은 아니다. 실제 TGL은 원본 firmware load 결과를
그대로 사용한다. replacement firmware/signature가 모두 null·0인
`wrapIgBufferWithOptions()`는 payload 없는 dummy-buffer 교체를 하지 않고
원래 인자 그대로 호출한다. PAVP command 4도 원본 오류를 성공으로 바꾸지 않는다.

### Tahoe와 CoreDisplay

기존 CoreDisplay 패치에는 `GetMTLTexture`/`GetMTLCommandQueue`의 null 반환,
`AccessComplete` 전체 무효화, 함수 본문에서 완료 신호 부분으로 직접
점프하는 코드가 있었다. **이 패치들은 수정본에서 제거했다.** 완료 신호만
발생시켜도 텍스처나 GPU 렌더링 결과가 생성되지 않는다.

나머지 inherited DYLD 수정은 `KernelVersion::Sonoma`와 명시적인
`-mellowlegacydyld`를 동시에 요구한다. Tahoe에서는 해당 Sonoma 패턴을
적용하지 않는다. 이는 Sonoma 전체 빌드에 대한 검증도 아니다. 실제
바이너리 확인을 위한 호환성 실험에만 쓰는 제한이다. 번들 경로 관찰 로그는
유지하며, `MTL_BUNDLE_SEEN`은 페이지 검증 이벤트를 보았다는 뜻일 뿐
Metal GPU 실행의 증거가 아니다.

CoreLSKD 두 경로 검사도 수정했다. 기존 `A != path || B != path`는 서로
다른 두 경로에서 항상 참이 되어 두 경로 모두 도달할 수 없었다.
현재는 둘 다 다른 경로일 때만 종료한다.

### FBMemMgr_Init의 커널 패치 경계

`kern_genx.cpp`의 stolen-memory formula 패치는 다음을 검사하는 함수로
분리했다. 현재 Ultra-only 등록 경로에서 이 legacy framebuffer는 등록하지
않지만, 향후 코드를 켰을 때 기존 버그가 다시 활성화되지 않도록 수정했다.

- stolen-size가 0이면 패치하지 않는다. 임의의 최저 할당량을 만들지 않는다.
- image 범위와 HDE64가 요구하는 **32 readable bytes**를 디코드 전에 검사한다.
- `SHL r32, 0x11` 다음에 인접한 같은 레지스터의 `AND r32, 0xfe000000`만
  인정한다. 그룹 opcode, register-only ModRM, 32비트 폭, prefix,
  immediate와 정확한 명령 길이를 검사한다.
- 다른 레지스터, 메모리 피연산자, 16/64비트 폭, 중간 명령, return/branch를
  만났을 때 해당 식을 변형하지 않는다.
- 원본 AND의 길이만큼만 `MOV r32, stolenSize`와 NOP를 넣는다.
  immediate는 바이트 단위로 작성해 비정렬 정수 저장을 피한다.
- kernel-write 활성화가 거절되면 **한 바이트도 쓰지 않는다**. 패치 후에는
  보호 복원을 시도하고 결과를 기록한다. 성공 후 루프를 즉시 종료하므로
  반복 패치와 MOV opcode 누적 변형이 일어나지 않는다.

64-instruction 한도는 탐색 비용 제한이다. 함수의 실제 길이를 확인했다고
주장하지 않는다. 첫 basic block에서 확인되지 않는 변형은 거절한다.

## 실행한 검증

다음 명령은 macOS 없이 실행할 수 있는 host 테스트다.

```sh
python tests/accel_contracts.py --report tests/accel-contracts-result.json
```

결과: **112 native assertion groups 및 5 integration guards 통과**.
실제 production 함수 본문을 추출해 호스트 C++ 컴파일러로 컴파일한다.
실제 upstream HDE64 디코더를 사용하며, kernel API와 accelerator 원본
함수만 mock으로 대체한다. 테스트에는 16개 x86 레지스터 전체의 패치,
거절된 write-enable에서 원본 바이트 보존, 잘린 image, 잘못된 opcode/
피연산자/폭/분기, 원래 task 보존, 원본 반환값 전달, false idle/firmware
상태 보존, barrier의 0/1/2 결과 및 인자 전달, 무제출 barrier 거절이 포함된다.
테스트용 HDE64 원본·라이선스·고정 commit은
`tests/accel_hde/`에 있다.

이 테스트는 **Darwin ABI 검사, kext 로딩, GPU 메모리 접근 또는 Metal
연산 실행 시험이 아니다**. 전체 kext 빌드 결과는 별도 빌드 보고서의 범위를
따른다.

## 아직 구현·입증되지 않은 핵심

1. 7D41의 DMA/GGTT/PPGTT 배치와 GuC firmware 인증·submission, reset,
   interrupt acknowledgement, 실제 fence 값의 순서 보장.
2. 7D41용 EU ISA 명령 생성과 Metal 셰이더 compiler의 연결. GPU ID 변경,
   feature advertisement 또는 성공 반환은 이 기능을 대체하지 않는다.
3. IOKit kernel driver와 Metal 사용자 공간 번들 사이의 matching ABI.
   기존 TGL private object offset 및 scratch-buffer 초기화는 여전히
   inherited 가정이고, 원본 Mellow에는 scratch 초기화를 생략하는 경로가 남아 있다.
4. Tahoe 버전의 IOAcceleratorFamily·CoreDisplay와의 실제 로딩·명령 제출.
5. Linux Xe의 MTL memory model에 따르면 BAR2는 legacy GGTT aperture와
   다르다. 별도 core 수정은 이 매핑을 7D41에 노출하지 않는다. 본 파일들의
   `aperturePtr` 실제 역참조는 null 검사 뒤에 있지만, 이로 인해 건너뛰는
   context repair 경로가 존재하며 그 기능이 완성되었다고 볼 수 없다.

따라서 현재 개발본은 실패 원인을 숨기지 않고 다음 구현을 시험할 수 있게
만든 소스다. 성공 증거는 같은 GPU에서 실행한 compute 출력값과 렌더링
픽셀의 CPU readback 비교, 완료·오류 전파, 반복 실행·reset 이후 재실행,
메모리 수명 및 시스템 안정성 시험을 모두 포함해야 한다.

## 근거

- Apple Metal: [Command Organization and Execution Model](https://developer.apple.com/library/archive/documentation/Miscellaneous/Conceptual/MetalProgrammingGuide/Cmd-Submiss/Cmd-Submiss.html).
  완료 및 오류는 command buffer 수명 주기의 서로 다른 최종 상태다.
- Acidanthera: [WhateverGreen의 DVMT formula 구현](https://github.com/acidanthera/WhateverGreen/blob/master/WhateverGreen/kern_igfx_memory.cpp).
  여기서 알려진 ICL 식을 참고했으며, 수정본은 인접 동일 레지스터만 허용하도록
  범위를 좁혔다. 그 구현의 ICL PCI GGC 읽기를 7D41에 그대로 사용하지 않는다.
- Acidanthera: [고정 HDE64 구현](https://github.com/acidanthera/Lilu/tree/0515f40b7f2a096adc85e832a4c6104fbd07f936/hde).
- Linux Xe: [xe_ttm_stolen_mgr.c](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/xe/xe_ttm_stolen_mgr.c).
  MTL 세대의 BAR2/LMEMBAR에 대한 메모리 모델 근거다.
- [Mellow 원본 고정 소스](https://github.com/NiSeullent/Mellow/tree/f895d89653ea5cad3a534cce46a62d0f59384d71).
  소스 주석의 과거 RPL 실험 결과는 이 Samsung 7D41에서 검증한 증거로
  재사용하지 않았다.
