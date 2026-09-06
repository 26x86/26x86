# Mellow platform decisions — RFC 001

Status: reviewed architecture decisions; implementation and hardware acceptance remain separate.
Date: 2026-09-06. Scope: application API, shader translation, execution providers, Darwin GPU ports.

## 한글 요약과 문서 우선순위

Mellow의 방향은 **Metal 요청 → Mellow 객체/명령 그래프/MIR → 검증된 GL·CL 또는 native backend**다.
기존 GPU 드라이버가 제공하는 GL·CL을 이용하면 일부 Metal 워크로드를 먼저 실행할 수 있다.
이 사실은 Metal 2/3 전체 기능 동등성이나 미지원 GPU의 macOS 드라이버 완성을 뜻하지 않는다.
첫 제품 경계는 Mellow를 명시적으로 선택한 앱의 off-screen compute/render다.
시스템 Metal 장치 등록, IOAccelerator, WindowServer, scanout은 각각 별도 승인 관문을 둔다.

이 RFC는 [CONCEPT](CONCEPT.md), [AIR-ABI](AIR-ABI.md),
[WORKLOAD-RUNTIME](WORKLOAD-RUNTIME.md), [ARCHITECTURE](ARCHITECTURE.md)의 설계 전제를 정정한다.
해당 초안의 단정과 충돌하면 이 문서의 결정 및 실제 실험 기록을 따른다.
`DECIDED`는 설계 선택이며 `IMPLEMENTED`, `GPU_PASS`, `SYSTEM_PASS`와 다른 상태다.
문서 추가, 컴파일 성공, 인터페이스 이름 일치는 위 실행 상태를 자동 승격하지 않는다.

## D01 — 지원 단위는 버전 이름이 아니라 관찰 가능한 계약

Metal의 GPU family별 기능과 한계가 다르므로 `Metal 2` 또는 `Metal 3` 한 문자열로
지원 범위를 광고하지 않는다. API/셰이더/메모리/동기화 요구를 각각 capability로 관리한다.
Apple의 [Metal feature tables](https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf)를
입력 명세로 사용하며, 표의 해당 family 필수 조건 전체를 충족하기 전에는 그 family를 반환하지 않는다.
일부 기능 통과를 `supportsFamily(Mac2)=true`나 `supportsFamily(Metal3)=true`로 표현하지 않는다.

초기 프로필 `mellow.offscreen.v1`의 계약은 다음과 같다.

- compute: 32-bit 정수/부동소수점, 명시적 buffer binding, 고정 threadgroup, bounds가 검증된 접근.
- render: vertex/fragment, 단일 RGBA8 target, 명시적 viewport, 제한된 depth/blend 설정.
- transfer: 명시적 buffer copy와 허용된 pixel format의 upload/readback.
- synchronization: 단일 provider queue에서 명령 순서와 완료 후 CPU 가시성.
- 제외: argument-buffer tier 광고, sparse/residency API, mesh shader, ray tracing, tile shader,
  dynamic library, indirect command buffer, 임의 format reinterpretation, cross-provider alias.

제외 기능은 문서에만 적지 않고 object 생성·pipeline 생성·command validation에서 거절한다.
하위 API에 비슷한 이름이 존재한다는 이유만으로 capability를 활성화하지 않는다.

## D02 — GL/CL 기판의 제약을 번역기 계약에 포함

Host GL baseline은 실제 생성한 4.1 core context와 조회한 extension/limit 집합이다.
GL 4.1 core에는 GL 4.3 compute/SSBO 기능이 포함되지 않는다. compute는 별도 CL 경로를 사용한다.
texture/image 접근, atomics, subgroup, resource indexing, precision, memory ordering은
각각 의미 보존을 입증해야 하며 GL/CL 버전 숫자만으로 Metal 의미를 만족시킬 수 없다.
명세 기준: [OpenGL 4.1](https://registry.khronos.org/OpenGL/specs/gl/glspec41.core.pdf),
[OpenGL 4.3](https://registry.khronos.org/OpenGL/specs/gl/glspec43.core.pdf),
[Metal Shading Language](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf).

Host CL은 실행 장치가 GPU인지와 실제 언어/extension 지원을 조회한다.
CL 1.2만 있는 장치에 SPIR-V IL 로딩이 있다고 가정하지 않는다.
초기 선택은 제한된 MIR → OpenCL C source lowering이며 실제 compiler build log를 저장한다.
SPIR-V 경로는 해당 provider가 지원하는 IL 확장/버전을 입증한 뒤 별도 adapter로 추가한다.
Rusticl은 OpenCL 기판 후보이지 Darwin winsys·kernel driver가 이미 있다는 증거가 아니다.
[Mesa Rusticl documentation](https://docs.mesa3d.org/rusticl.html).

Host GL renderer의 accelerated flag, CL device type, vendor/device 식별자를 admission에 사용한다.
소프트웨어 renderer 또는 확인할 수 없는 장치는 GPU acceptance에서 제외한다.
Apple API가 deprecated라는 사실과 현재 장치에서 동작한다는 사실도 따로 기록한다.
[Apple OpenGL capabilities guidance](https://developer.apple.com/library/archive/documentation/GraphicsImaging/Conceptual/OpenGL-MacProgGuide/opengl_api_versions/opengl_api_versions.html).

## D03 — AIR 발견을 독립 MSL 컴파일러 API의 증거로 사용하지 않음

`MTLCompiler`, `MTLAirEntry`, relocation class, GPUCompiler dylib 이름 발견은 조사 단서다.
그 이름만으로 호출 ABI, public standalone entry point, 출력 schema, 재배포 권한,
하드웨어 없는 환경에서의 runtime MSL 컴파일 성공을 확정할 수 없다.
relocation class 이름을 native Intel ZEBIN relocation 규칙과 동일시하지 않는다.
`newLibraryWithSource:`를 호출할 기존 정상 Metal device도 없는 경우를 설계에 포함한다.

Apple이 문서화한 SDK 경로는 `.metal` → `.air` → `.metallib`이다.
이는 AIR를 모든 stock LLVM 버전에서 읽을 수 있다거나 임의 metallib에 동일한 AIR가
항상 남아 있다는 보장이 아니다.
[Apple Metal tools](https://developer.apple.com/library/archive/documentation/Miscellaneous/Conceptual/MetalProgrammingGuide/Dev-Technique/Dev-Technique.html).

첫 입력 adapter는 사용자가 설치한 SDK로 생성한 **정확히 버전이 기록된 `.air` corpus**다.
SDK 실행 위치는 빌드 머신일 수 있으며, GPU 없는 대상 macOS에서 compiler를 찾는 데 의존하지 않는다.
`.metallib` ingestion은 별도 container adapter로 취급하고 bounds/format/metadata 검사부터 통과시킨다.
runtime MSL은 두 선택지 중 검증된 것만 활성화한다.

1. 지원 조건·입출력·권한이 확인된 SDK compiler adapter를 명시적으로 설정한다.
2. 명시한 MSL 부분집합용 frontend를 별도로 작성하고 source corpus로 검증한다.

private compiler 호출은 기본 경로에 포함하지 않는다. 연구 adapter가 생겨도 build별 실험 범위다.
Apple compiler 바이너리 대신 compiler 식별자, 입력 hash, 생성 명령, 출력 hash를 보관한다.
AIR adapter key는 `{SDK build, tool version, target triple, language version, dialect schema}`다.
알 수 없는 intrinsic/metadata/address-space/bitcode record는 typed compile error로 종료한다.
현재 문서에 설명되지 않은 값을 추측하여 device code로 전달하지 않는다.

## D04 — Mellow 객체 모델과 MIR를 독립 경계로 고정

논리 흐름은 다음과 같다. 각 화살표는 versioned adapter와 검증 결과를 갖는다.

```text
Opt-in application
  → Mellow Metal-facing objects + validated descriptors
  → command/resource graph + shader MIR
  → provider-specific lowering + verified capability intersection
  → host GL / host CL / future native submission
  → completion evidence + output readback
```

MIR는 backend-neutral이라는 이름보다 명시적인 실행 의미가 중요하다.
필수 필드는 stage/entry point, scalar widths, address spaces, binding indices,
resource access ranges, threadgroup requirements, barrier scope, atomic ordering,
texture format/sample semantics, math flags와 source location이다.
fast-math, NaN, denormal, overflow 차이는 자동 완화하지 않고 compile policy에 넣는다.
lowering 전후 verifier가 capability와 resource layout 계약을 검사한다.
GLSL/CL C/native instruction 선택은 MIR 검증 후 수행한다.

cache key에는 AIR input hash, adapter/MIR schema, compiler revision/options,
provider/driver build, device feature set, specialization 값, layout signature를 넣는다.
shader source hash 하나로 다른 GPU·SDK·driver 결과를 재사용하지 않는다.
실패한 compiler 결과와 capability 거절도 원인 코드를 보존하되 성공 binary로 캐시하지 않는다.

## D05 — resource 소유권과 hazard graph를 routing보다 먼저 구현

장치 생성 시 provider와 물리 장치를 고정한다. 같은 Mellow device가 command buffer마다
임의 GPU로 바뀌지 않는다. 여러 provider를 쓰는 앱은 별도 device/resource domain을 만든다.
초기 버전에서 GL/CL 혼합 command buffer와 암묵적 migration은 거절한다.
명시적 export/import·copy가 지원될 때만 provider 경계를 넘는다.

모든 resource는 `{owner_device, provider, handle, generation, size, access, format}`을 갖는다.
host pointer, GPU VA, buffer object handle, IOSurface ID를 서로 대체 가능한 주소로 취급하지 않는다.
suballocation과 texture view는 parent allocation 및 겹치는 byte/subresource 범위를 유지한다.
CPU mapping 시점과 GPU 사용 기간이 겹치면 허용된 coherent 계약이나 명시적 동기화를 요구한다.
`shared`/`managed`/`private` storage mode는 provider가 보장하는 경우에만 제공한다.

graph validation은 RAW/WAR/WAW, alias, queue dependency, readback visibility를 검사한다.
완료 상태는 `encoded → validated → submitted → completed|failed|cancelled`만 허용한다.
host-side enqueue 반환을 `completed`로 바꾸지 않는다.
실제 provider fence/event를 관찰하고 필요한 cache flush/invalidate 이후 completion을 전달한다.
submit 실패는 뒤의 dependent node도 실패시키며 중간 결과를 성공 output으로 반환하지 않는다.

IOSurface는 공유 object일 뿐 모든 API·GPU 사이의 무복사/동기화 보장이 아니다.
format, stride, plane, lifetime, device residency 및 import/export sync 계약을 별도로 검사한다.
초기 off-screen 경로는 explicit readback이 기준이고 zero-copy는 독립 성능 기능이다.

## D06 — 앱 opt-in과 시스템 graphics integration은 별도 제품 경계

첫 호스트 API는 명시적 Mellow device factory 또는 앱에 연결한 shim이다.
앱은 반환된 object를 지원 부분집합에서 사용하며 실패를 명시적으로 처리한다.
Objective-C protocol 구현만으로 모든 Metal consumer, validation layer, binary app이
해당 object를 수용한다고 단정하지 않는다. 사용할 selector와 object lifetime도 시험한다.

symbol interposition은 개발용 opt-in process 실험으로 한정한다.
protected/hardened process, code signing, library validation, framework 내부 private 호출 때문에
시스템 전체 `MTLCreateSystemDefaultDevice` 대체를 보장하는 배포 전략으로 삼지 않는다.
[Apple library validation](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.cs.disable-library-validation).

시스템 경로는 별도 `system-integration` 실험 track으로 관리한다.
정확한 macOS build에서 IOAccelerator/IOUserClient selector·structure·ownership·error ABI,
user-space device factory, bundle loading, shared memory 및 notification ABI를 기록해야 한다.
`MetalPluginClassName`이나 `MTLIOAccelDevice` 이름 발견만으로 이 계약이 완성되지 않는다.
WindowServer/CoreAnimation 채택은 별도 프로세스 관찰과 GPU workload 증거가 필요하다.
scanout에는 connector/EDID, modeset, display memory, vblank, pageflip, hotplug, sleep/wake가 추가된다.
compute/render PASS가 framebuffer·display·WindowServer PASS로 전파되지 않는다.

## D07 — MELLOWKPI는 함수명 치환기가 아닌 의미 보존 계층

Linux DRM은 allocation, reservation, VM, scheduler, fence의 수명과 동시성 규약을 공유한다.
동일한 C signature를 XNU 함수로 치환해도 규약이 같아지지 않는다.
[DRM memory management](https://docs.kernel.org/gpu/drm-mm.html),
[DRM UAPI](https://docs.kernel.org/gpu/drm-uapi.html)를 계약 조사 시작점으로 고정한다.

Darwin adapter는 적어도 다음 계약을 개별 구현·시험한다.

- memory: pin/unpin, DMA/IOMMU mapping, alignment, physical scatter/gather, cache mode,
  CPU/GPU visibility, page lifetime, eviction 시 미완료 작업의 처리.
- VM: GPU VA allocation, bind/unbind completion, TLB invalidation, permission,
  fault attribution, teardown과 실행의 경합, IOMMU 주소와 GPU VA의 구별.
- IRQ: handler admission, source acknowledgement, masking, deferred work,
  interrupt context에서 허용되는 lock/allocation, teardown 중 재진입 차단.
- fence: queue-local monotonic timeline, atomic state transition, callback lifetime,
  wait cancellation, timeout/reset error propagation, context 소멸과 대기자의 경합.
- scheduler/reset: firmware 인증 후 queue 활성화, submission validation,
  watchdog, reset epoch, stale completion 거절, 영향을 받은 모든 client의 실패 통지.
- concurrency: lock ordering, sleepable/atomic context, refcount/RCU 대체 의미,
  workqueue drain, MMIO ordering, posted write 확인, CPU memory barrier 종류.

MELLOW-UAPI는 `{abi_version, struct_size, handle_generation, capability_epoch}`를 포함한다.
사용자 포인터·길이·정렬·권한을 검증하고 kernel pointer나 무제한 MMIO를 노출하지 않는다.
DRM ioctl 이름을 재사용해도 Mesa winsys가 요구하는 semantics가 같다는 검증은 별도다.
reset은 epoch를 증가시키며 이전 epoch의 GPU fence가 새 작업을 완료시키지 못하게 한다.
GPU reset을 성공 fence로 숨기거나 CPU로 output을 채워 GPU completion으로 보고하지 않는다.

## D08 — backport factory의 산출물은 검토 가능한 포팅 recipe

`mellow-port`는 다음 pipeline을 목표로 한다. 아래 단계와 schema는 계획된 인터페이스다.

```text
Pinned source + dependency closure + per-file license
  → compiler AST/type/config analysis + effect inventory
  → capability requirements + semantic contract gaps
  → reviewed transformation recipe + handwritten platform bindings
  → compile/link + contract tests + differential tests
  → firmware/device admission + hardware acceptance
  → reproducible backend package + provenance + unresolved gaps
```

첫 기준 backend는 사람이 검토한 하나의 device/backend 조합이다.
그 backend를 동일한 hash/의미로 재생성한 뒤 인접 revision/device intake를 자동화한다.
새 API, lock context, memory model, firmware protocol이 발견되면 gap으로 중단한다.
자동화가 할 일은 누락을 찾고 반복 가능한 변경을 적용하는 것이며 unknown을 stub으로 숨기지 않는다.
text substitution으로 register table을 옮기는 단계와 실행 가능한 driver port를 구분한다.
Linux Backports의 Linux 신버전→구버전 지원을 Darwin 포팅 완성의 선례로 간주하지 않는다.
[Linux Backports scope](https://backports.docs.kernel.org/).

recipe 필수 항목: upstream commit, source hashes, build config, dependency graph,
SPDX/notice records, selected adapter family, firmware contract, applied transformations,
manual patch hashes, capability exclusions, test inputs/results, target OS/kernel build.
현재 `upstream-pins.json`에 파일 몇 개가 기록되어 있다는 사실은 전체 closure 분석 완료가 아니다.
revision 갱신은 semantic diff와 contract 재시험을 발생시킨다. zero-touch universal import는 목표 계약이 아니다.

## D09 — NVIDIA·AMD backend 선택과 licensing을 입력에서 고정

NVIDIA 경로는 두 후보를 명시적으로 분리한다.
`nouveau-nvk`는 Mesa NVK/Nouveau winsys 및 해당 DRM/firmware 계약을 대상으로 한다.
`nvidia-rm`은 NVIDIA open kernel modules의 RM/UAPI와 matching firmware/userspace 계약을 대상으로 한다.
NVK/Nouveau를 NVIDIA RM kernel UAPI의 교체 가능한 userspace로 가정하지 않는다.
adapter 변경은 backend 교체이며 memory, synchronization, compiler, firmware 검증을 다시 요구한다.
[Mesa NVK](https://docs.mesa3d.org/drivers/nvk.html),
[Mesa Nouveau sources](https://gitlab.freedesktop.org/mesa/mesa/-/tree/main/src/nouveau).

NVIDIA pinned README는 kernel modules에 대응 release의 GSP firmware와 userspace를 요구한다.
Linux용 userspace ELF를 Darwin에서 그대로 사용할 수 있다는 뜻도 아니다.
Nouveau용 firmware 추출 도구의 존재 역시 NVIDIA RM UAPI와 Nouveau UAPI의 동등성 증거가 아니다.
[Pinned NVIDIA README, e4a5faa](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/e4a5faa2567f28c8eabe0ebb6422b6d0abcf37eb/README.md).

AMD는 `amdgpu_drv.c`의 허용적 notice를 DRM·TTM·scheduler·Linux 공통 코드 전체에 확장하지 않는다.
해당 파일은 여러 DRM/Linux header와 amdgpu 하위 시스템에 의존한다.
closure별 GPL/dual-license/permissive 조건과 결합 경계를 분리해 기록한다.
[Pinned amdgpu entry point, 0d9ff90](https://github.com/torvalds/linux/blob/0d9ff90a5422cc7509258aaaba1e7481df4d332a/drivers/gpu/drm/amd/amdgpu/amdgpu_drv.c).

기존 repository [LICENSE](../LICENSE)의 Thou Shalt Not Profit License를 보존한다.
수입한 파일의 license, copyright, NOTICE와 원본 출처를 보존하며 MIT로 일괄 재표기하지 않는다.
새 backend를 결합·배포할 수 있는지는 해당 closure의 조건 검토 결과에 따라 결정한다.
GPL code와 기존 license의 결합 문제가 미해결이면 그 결합 artifact의 배포 관문을 닫는다.
이를 해결했다고 주장하기 위해 디렉터리만 분리하거나 새로운 이름을 붙이지 않는다.
[NVIDIA pinned COPYING](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/e4a5faa2567f28c8eabe0ebb6422b6d0abcf37eb/COPYING).

## Acceptance gates — 구현 순서와 실패 판정

G0, provenance/admission: SDK·driver·GPU·firmware·source hash·license closure를 고정한다.
unknown provider, CPU renderer, 다른 GPU로의 조용한 routing은 GPU acceptance 실패다.

G1, shader corpus: known-source AIR, scalar/vector, layout, address-space, barrier,
integer edge cases, float tolerance, malformed/truncated input, unknown intrinsic를 포함한다.
정수는 exact 비교, float은 항목별 명시된 tolerance/NaN 정책으로 oracle과 비교한다.
positive corpus뿐 아니라 unsupported feature를 정확한 단계·오류로 거절하는 negative corpus도 통과한다.

G2, resource graph: alias RAW/WAR/WAW, early release, out-of-range binding,
simultaneous CPU/GPU access, queue dependency, failed submit, stale handles를 시험한다.
GL↔CL 공유가 미구현이면 거절 결과를 검사한다. 우연히 맞은 최종 buffer만으로 hazard PASS를 주지 않는다.

G3, host GPU vertical slice: opt-in 앱→Mellow objects→AIR/MIR→provider GPU 실행을 연결한다.
compute `[1,2,3,4]*7+3` readback과 off-screen pattern render를 서로 독립적으로 통과한다.
매번 무작위 seed·guard region·입출력 hash를 기록하고 CPU reference 결과는 별도 provenance로 표시한다.
command ID, selected device, compiler artifact, provider event/fence, output을 같은 record에 묶는다.

G4, native backend: real allocation/VM bind→firmware authentication→queue→IRQ/fence→readback을 입증한다.
누락 IRQ, fault, timeout, reset, cancel, client death를 주입해 bounded teardown과 epoch 처리를 검증한다.
MMIO/firmware status와 fence provenance를 보존하고 소프트웨어 counter 증가만으로 GPU 실행을 판정하지 않는다.
10,000 command buffer 반복에서 timeout/reset/page fault/fence mismatch를 집계한다.
의도한 fault test와 정상 workload 결과를 분리하며 누락 counter는 0이 아니라 unavailable이다.

G5, application compatibility: 선택한 앱/SDK/API subset별 selector와 rendering 결과를 검증한다.
G6, system ABI: 정확한 Tahoe build에서 device enumeration, IOAccel round trip와
WindowServer/CoreAnimation의 실제 GPU 사용을 확인한다. G5 결과로 G6를 건너뛰지 않는다.
G7, display: modeset→scanout→vblank/pageflip→hotplug→sleep/wake를 실기에서 확인한다.
headless compute PASS와 외부 화면 사진 한 장은 display 안정성 PASS의 대체 증거가 아니다.

각 gate 결과에는 `PASS|FAIL|NOT_RUN`, environment, input/output hashes, evidence path,
unsupported set, reset epoch, failure reason을 기록한다. 이 RFC 자체는 어느 gate도 통과시키지 않는다.
