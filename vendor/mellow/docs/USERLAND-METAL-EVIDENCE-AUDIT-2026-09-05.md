> **Historical record — preserved unedited.** This document predates the MELLOW
> re-architecture. It is retained because the record of what was known, and when, is itself
> evidence. For the current concept and architecture see [CONCEPT.md](CONCEPT.md) and
> [ARCHITECTURE.md](ARCHITECTURE.md); for what any of it is allowed to claim, see
> [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).

# 7D41 Metal 사용자 공간 증거 감사 (2026-09-05)

## 결론

현재 사용자 공간 코드는 **이미 OS가 등록한 `MTLDevice`를 시험하는 클라이언트**다.
7D41용 Metal 사용자 공간 드라이버를 등록하거나 Tahoe의 사설 IOAccelerator ABI를
구현하지 않는다. 이 감사에서 계산·오프스크린 렌더 판정의 오탐 경로를 줄였지만,
Samsung 750XHD 실기에서 실행한 증거가 없으므로 7D41 Metal 가속 성공으로 판정하지 않는다.

## 이번에 좁힌 성공 조건

### 재사용 Python 세션

`Userspace/metal_session.py`의 계산 셰이더는 요청한 acceptance A를 실행한다.

```text
output[i] = input[i] * 7 + 3 (UInt32 wrap)
[1, 2, 3, 4] -> [10, 17, 24, 31]
```

nonce는 결과 공식을 바꾸지 않는다. 별도 GPU buffer에
`nonce ^ 0x7d410003`을 기록하므로, 고정 출력이나 이전 실행의 buffer가 새 제출로
오인되는 경로를 막는다. 매 제출마다 출력 buffer 전체를 CSPRNG 바이트로 새로 채우고
초기·예상·실제 SHA-256을 보존한다. `MTLCommandBufferStatus.completed`만으로는 통과하지
않으며 예상 전체 출력, 출력 변화, nonce witness를 모두 확인한다.

장치 귀속은 다음 조건을 모두 요구한다.

1. `MTLCopyAllDevices()`에 요청 registryID가 정확히 한 번 있어야 한다.
2. 그 ID의 IOService 조상을 따라간 `IOPCIDevice`가 Intel이어야 한다.
3. Mellow가 PCI config를 spoof 전에 읽어 게시한 물리 식별자가
   `8086:7D41`, BDF `00:02.0`이어야 한다.
4. 현재 노출 ID는 물리 `7D41` 또는 Mellow의 TGL 호환 ID `9A49`만 허용한다.
5. software/SwiftShader/llvmpipe/softpipe 이름은 거부한다.
6. 생성한 command queue와 command buffer의 `device.registryID`를 다시 읽어 같은 ID인지
   확인한다.
7. 완료 뒤 PCI 계층과 물리 식별자를 다시 읽어 제출 전 값과 같은지 확인한다.
8. Apple이 GPU 완료 후 제공한다고 문서화한 `GPUStartTime`/`GPUEndTime`이 0이 아니고
   순서가 유효해야 한다.

이 조건의 제한도 명시한다. Mellow가 게시한 IORegistry 속성은 암호학적 attestation이
아니다. 공개 Metal 완료·timestamp·buffer 결과는 선택한 `MTLDevice`에서 GPU 작업이
완료됐다는 강한 사용자 공간 증거지만, Mellow 내부의 실제 IRQ acknowledgement와
hardware fence가 맞았다는 독립 증거는 아니다.

모든 `poll()`/`wait()` 결과는 schema 2의 같은 필드를 낸다.

```text
terminal, status, timed_out, resources_retained
output, output_matches, output_changed, nonce_witness_matches
device_chain_matches, gpu_timing_recorded, native_metal_command_completed
public_metal_target_compute_verified, native_metal_executed, target_probe_passed
hardware_irq_fence_verified, cpu_fallback_excluded_by_hardware_evidence, evidence
```

마지막 두 hardware 필드는 이 클라이언트만 실행해서는 항상 `false`다. 주입한 test
backend는 자신이 native라고 주장해도 `target_probe_passed`를 만들 수 없다.

호출 수명은 다음과 같다.

```python
session = MetalSession(registry_id)
ticket = session.submit([1, 2, 3, 4], nonce)
result = session.wait(ticket, timeout=10)
if not result["terminal"]:
    result = session.poll(ticket)  # 같은 owning thread에서 terminal까지 재관측
session.close()                    # pending ticket이 하나라도 있으면 거부
```

Metal 공개 API에는 commit된 command buffer를 안전하게 취소하는 동작이 없다. 따라서
`cancel(ticket)`은 명시적으로 `Unavailable`을 낸다. timeout은 취소나 GPU 메모리 회수
성공이 아니며, ticket·buffer·session을 유지해 terminal 상태를 다시 읽어야 한다.

### Swift compute + render probe

`Tools/metal-probe.swift`와 `Tools/metal-run.py`는 schema 3 JSONL 증거를 사용한다.

- 계산 입력은 nonce로 재현 가능하되 첫 네 값은 항상 `[1,2,3,4]`다.
- Python evaluator가 4,096개 입력·초기 poison·예상 A 결과를 독립 재생성하여 세 SHA-256을
  대조한다.
- 실제 결과의 첫 네 값, 전체 예상 hash, 별도 nonce witness, queue/command registryID,
  GPU timestamp를 모두 확인한다.
- 렌더 B는 private RGBA8 texture에 full-screen 빨강 triangle을 그리고 shared buffer로
  blit한다. 4×4 RGBA `[255,0,0,255]`와 256-byte row stride의 untouched `0xA5` padding을
  합친 알려진 SHA-256은
  `7f8f467143b62cef24e8b429a733a6b2fbf67d6a828dd02f74d7353bce78d6fb`이다.
  Swift probe와 Python evaluator가 이 값을 각각 계산·검사한다.
- 열거만 한 실행, 중복·순서 변경 stage, schema/registry 불일치, software device 이름,
  변조된 challenge hash, 0 timestamp, 다른 command device, render hash 불일치는 실패다.
- `completed`는 범위를 `public Metal compute and offscreen render only`로 고정하고
  stress, hardware IRQ/fence, WindowServer, 전체 Metal conformance는 `false`로 남긴다.

## 검증 결과와 범위

Windows host에서 다음 검사를 실행했다.

```text
python -m py_compile Userspace/metal_session.py Tools/metal-run.py
python tests/metal_session_tests.py
python tests/metal_evidence_tests.py
```

- session 수명·귀속·완료 gate: 19 test methods 통과
- JSONL 증거·known offscreen hash·Mach-O/Intel container negative gate: 15 test methods 통과
- `git diff --check`: 통과

이 환경에는 `swiftc`, Metal.framework, Tahoe x86_64 runtime 및 7D41 실기가 없다.
따라서 Swift native compile, MSL compile, command 제출, texture readback, GPU timestamp,
GuC 인증, IRQ/fence, reset/page-fault, 수천 회 stress 및 WindowServer는 실행하지 않았다.

## 공개 원문과 확인된 경계

### 확인됨

- Apple은 [`MTLDevice`](https://developer.apple.com/documentation/metal/mtldevice)를 앱이
  사용하는 GPU의 주 인터페이스로 정의하고, 각 instance가 GPU 하나를 나타낸다고 설명한다.
  [`MTLCopyAllDevices`](https://developer.apple.com/documentation/metal/mtlcopyalldevices%28%29)는
  시스템의 모든 Metal GPU device instance를 반환한다.
- Apple의 [`registryID`](https://developer.apple.com/documentation/metal/mtldevice/registryid)는
  task 사이에서도 같은 GPU를 식별할 수 있는 전역 ID다.
- Apple은 [`MTLCommandQueue.device`](https://developer.apple.com/documentation/metal/mtlcommandqueue/device)가
  queue가 제출할 수 있는 GPU를 정하고,
  [`MTLCommandBuffer.device`](https://developer.apple.com/documentation/metal/mtlcommandbuffer/1442995-device)가
  command buffer를 간접 소유한 GPU라고 문서화한다.
- Apple은 [`GPUStartTime`](https://developer.apple.com/documentation/metal/mtlcommandbuffer/gpustarttime)과
  [`GPUEndTime`](https://developer.apple.com/documentation/metal/mtlcommandbuffer/gpuendtime)이 GPU 완료
  전에는 `0.0`이고 완료 뒤 GPU 실행 시간을 나타낸다고 설명한다.
- 현재 WhateverGreen은
  [`kern_igfx.cpp`](https://github.com/acidanthera/WhateverGreen/blob/master/WhateverGreen/kern_igfx.cpp)에서
  Ice Lake에는 AppleIntelICL stack을 선택하지만 Rocket Lake, Alder Lake, Raptor Lake,
  Arrow Lake는 `gPlatformGraphicsSupported = false`로 처리한다.
- 현재 Mellow의
  [공개 README](https://github.com/NiSeullent/Mellow/blob/main/README.md)는 `8086:7D41`을
  `0x9A49`로 spoof하고 Apple TGL framebuffer/HW/MTL stack에 연결하는 실험 설계를 설명하면서,
  Xe-LPG가 macOS에서 지원되지 않고 boot, display, Metal 및 안정성을 보장하지 않는다고 명시한다.
- Apple의 오래된 IOKit graphics family 문서는
  [graphics acceleration이 user-space module과 kernel driver의 hardware-specific code를
  함께 요구할 수 있고 표준 구현 방식이 없다고 설명](https://developer.apple.com/library/archive/documentation/DeviceDrivers/Conceptual/IOKitFundamentals/Families_Ref/Families_Ref.html)한다.
  Apple의 XNU README도
  [PrivateHeaders는 Apple 내부 개발 전용](https://github.com/apple-oss-distributions/xnu/blob/main/README.md)이라고
  명시한다.
- 이 저장소의 `abi-evidence/intel-umd-partial.json`은 확보한 Tahoe ICL 자료의 범위를
  `Actual bundle metadata and helper Mach-O analysis, not a complete Intel Metal plugin`으로
  고정한다. 확인한 bundle metadata는 `com.apple.driver.AppleIntelICLGraphicsMTLDriver`,
  principal class `MTLIGAccelDevice`, declared executable `AppleIntelICLGraphicsMTLDriver`를
  가리키지만, 실제로 분석한 Mach-O는 helper인 `libigdmd.dylib`뿐이다.
  `main_executable_acquired`, `private_plugin_abi_verified`, `plugin_loaded`, `metal_executed`는
  모두 `false`이며 helper는 사설 `IOAccelerator.framework`에 의존한다. 즉 현재 로컬 자료에서
  정확히 빠진 사용자 공간 부분은 **선언된 Metal plugin 주 실행 파일, Tahoe 사설 ABI 적합성,
  실제 plugin load 및 7D41 명령 실행 증거**다.
- Apple의 [macOS Tahoe 26 Software License Agreement](https://www.apple.com/legal/sla/docs/macOSTahoe.pdf)는
  Apple-branded system용 라이선스임을 밝히고, 제2.J항에서 non-Apple-branded computer에
  설치·실행하거나 타인에게 그렇게 하도록 하는 행위와 별도 허가 없는 재배포를 제한한다.
  제4.B항은 Apple Software 구성요소를 bundle에서 분리해 standalone으로 배포할 수 없다고
  명시한다. 따라서 공개 EFI/release에 Apple proprietary TGL/ICL graphics binary를 넣는
  배포 권한은 확인되지 않았으며 이 감사 결과로 그러한 권한을 만들 수 없다.
- Apple의 [Tahoe 호환 목록](https://support.apple.com/en-la/122867)에 남은 2020년 13-inch
  Intel MacBook Pro는 Apple 사양상
  [10세대 Intel CPU와 Intel Iris Plus](https://support.apple.com/en-ca/111339)다.

### 이 원문으로부터의 추론

- Tahoe의 공개 Metal API는 이미 존재하는 GPU device를 고르고 사용하는 API다. 공개 문서에서
  제3자 앱이나 일반 kext가 새 Intel `MTLDevice` backend를 등록하는 지원 API는 확인되지 않았다.
  따라서 이 Python/Swift 클라이언트는 누락된 7D41 UMD/compiler/plugin을 만들어 주지 못한다.
- Apple의 Tahoe 지원 Mac과 현재 WhateverGreen의 플랫폼 분기상 Apple이 공개적으로 지원한
  마지막 Intel iGPU 세대는 Ice Lake로 보는 것이 타당하다. 이는 Apple이 "Arrow Lake를 절대
  지원한 적 없다"고 직접 적은 문장이 아니라 호환 모델·사양·오픈소스 패처의 결합 추론이다.
- Apple 공식 사이트와 Apple OSS에서 `AppleIntelTGLGraphics*` public payload를 확인하지 못했다.
  커뮤니티가 사용하는 TGL bundle은 공개 Mellow의 외부 선행조건이며, 공식 Apple 배포 출처와
  재배포 권리를 이 감사에서 검증하지 못했다. 따라서 해당 proprietary binary를 EFI나 공개
  release에 포함하는 경로를 성공 조건으로 간주하지 않는다.
- OCLP가 설명하는 root patch는 기존 지원 GPU의 kext, Metal bundle, compiler/framework를
  [세대별 묶음으로 복원](https://github.com/dortania/OpenCore-Legacy-Patcher/blob/main/docs/PATCHEXPLAIN.md)한다.
  공개 Tahoe 계획도 [Intel Broadwell/Skylake 이하의 legacy graphics](https://github.com/dortania/OpenCore-Legacy-Patcher/issues/1167)를
  열거한다. 7D41용 새 KMD/UMD/compiler가 없는 상태에서 spoof나 root patch만으로 해당 기능을
  합성할 수 있다는 근거는 아니다.

## 전체 가속 판정에 아직 필요한 증거

1. 같은 부팅에서 Mellow가 기록한 물리 `8086:7D41` 및 정확한 KEXT/Apple bundle hash.
2. acceptance A와 known-hash offscreen B의 native 결과 원본 JSONL.
3. 최소 1,000회 이상의 제출에서 timeout, GPU reset, page fault, fence mismatch가 0이라는
   독립 kernel/OS log와 backend counter.
4. GuC firmware identity·인증, 실제 context submission, IRQ acknowledgement 및 fence advance를
   같은 challenge/command에 연결한 증거.
5. WindowServer가 바로 그 registryID의 GPU surface를 실제 화면에 합성하고 sleep/wake/reset 뒤
   다시 실행하는 증거.

이 항목을 한 부팅의 서명·hash·시간 축으로 결합하기 전에는 `Mellow 7D41 Metal acceleration`
PASS를 만들지 않는다.
