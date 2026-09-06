> **Historical record — preserved unedited.** This document predates the MELLOW
> re-architecture. It is retained because the record of what was known, and when, is itself
> evidence. For the current concept and architecture see [CONCEPT.md](CONCEPT.md) and
> [ARCHITECTURE.md](ARCHITECTURE.md); for what any of it is allowed to claim, see
> [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).

# Tahoe Metal 사용자 공간 연결 착수

`Userspace/metal_session.py`는 실제 macOS Metal/Objective-C/IOKit C ABI를 호출하는
재사용 가능한 클라이언트 연결 모듈이다. **새로운 Metal 드라이버, CFPlugIn 또는
MTLDevice 구현은 아니다.** 7D41을 지원하는 실제 Metal 장치가 OS에 등록되어 있어야
연결할 수 있다. 존재하지 않는 장치를 만들어 반환하거나 다른 GPU로 대체하지 않는다.

## 구현한 실행 경로

1. x86_64 Tahoe/Darwin25 확인 후 Apple의 실제 시스템 framework를 연다.
2. MTLCopyAllDevices에서 요청한 registryID가 정확히 하나인지 확인한다.
3. IOKit 부모 계층을 따라 PCI provider를 찾고, Intel vendor 및 드라이버가 기록한
   pre-spoof 8086:7D41·00:02.0 식별자를 확인한다. 이 속성은 암호학적 증명은 아니다.
4. 실제 MTLCommandQueue를 만들고 newLibraryWithSource:options:error:로 고정된
   MSL 커널을 컴파일해 MTLComputePipelineState를 생성한다. Apple 컴파일러 경로이며
   IGC OpenCL frontend를 Metal 컴파일러로 바꾸어 부르는 방식이 아니다.
5. 실제 shared MTLBuffer를 할당하고 compute encoder에 입력·출력·인자를 설정한 뒤
   dispatchThreadgroups:threadsPerThreadgroup:와 commit으로 제출한다.
6. 실제 MTLCommandBuffer status가 completed 또는 error가 될 때까지 receipt와
   buffer를 보유한다. 시간 초과에는 자원을 해제하지 않고 재관측할 수 있는 ticket을
   유지한다. 완료 후 nonce를 포함한 전체 출력값을 비교한다.

작업은 최대16개, 각 입력은1~65,536개의 uint32로 제한한다. 핸들에는 세션 식별자를
포함하며 다른 세션·이미 회수한 ticket은 거부한다. Objective-C pool과 호출은 같은
스레드에 한정한다. 미완료 작업이 있으면 close를 거부한다. 제출 수락 여부가 불명확하면
native command를 보유한 receipt를 반환하여 성공이나 취소로 단정하지 않는다.

공개 selector·인자·상태 값은 [Apple metal-cpp의 고정 소스](https://github.com/apple/metal-cpp/tree/27c4382b7151d55a51692cdcb27aaa98752240de)
및 [Metal registryID](https://developer.apple.com/documentation/metal/mtldevice/registryid),
[MSL 라이브러리 컴파일](https://developer.apple.com/documentation/metal/mtldevice/makelibrary(source:options:))을
대조했다. Python ctypes가 호출하는 native ABI와 Metal GPU 실행은 Windows에서
검증할 수 없었으며 **실기 미검증**이다. 테스트에서는 이 경계를 명시적으로 대체한다.

## 호출 예

macOS에서 같은 스레드와 살아 있는 프로세스를 유지하며 다음과 같이 사용한다.
registryID는 기존 metal-probe.swift의 실제 열거 결과에서 지정한다.

```python
from metal_session import MetalSession
session = MetalSession(actual_registry_id)
ticket = session.submit([1, 2, 3, 4], nonce=123456789)
result = session.wait(ticket, timeout=10)
if result['terminal']:
    session.close()
else:
    # Timeout is not cancellation. Keep session/process alive and poll(ticket).
    # close() deliberately refuses unresolved GPU work.
    pass
```

사용자가 중단하여 프로세스를 종료하는 경우 장치의 실제 정지는 OS가 처리해야 한다.
클라이언트가 종료되었다는 사실을 GPU 정지·메모리 회수 성공으로 기록하지 않는다.

## 실제 Apple 번들 조사

공식25G83 InstallAssistant의 선택 ZIP shard를 HTTPS Range로 받아 CRC와 PBZX/XZ
해제 길이를 검사했다. 선택 파일은 실제 YAA record 경계를 따라 추출했다.
`Info.plist`의 principal class는 MTLIGAccelDevice이고 실행 파일 이름은
AppleIntelICLGraphicsMTLDriver다. 번들 버전24.0.5, 표시 버전24.5.8이다.

실제 추출한3,285,040-byte libigdmd.dylib에는 OpenMetricsDevice 및 성능 계측 함수가
있다. **이 보조 라이브러리는 Metal 드라이버 본체가 아니다.** Info.plist와 함께
`Tools/tahoe-umd-evidence.py`로 분석한 결과는 `abi-evidence/intel-umd-partial.json`에
있다. Apple 바이너리는 작업 폴더에만 보존하고 이 개발 패키지에 재배포하지 않는다.

주 실행 파일은 일반 payload의 해당 경로에 없으며 별도 시스템 cryptex 조사 대상으로
남아 있다. x86_64 cryptex 입력은 실제 RIDIFF10 형식이다. 현재 Windows/Linux 경로에서
이를 검증된 전체 이미지로 복구하지 않았고 전체 InstallAssistant 서명도 검증하지 않았다.
따라서 이 자료만으로 ICL plugin을 7D41용으로 패치·설치하지 않는다. IOAccelerator의
private 객체 레이아웃·user-client selector·plugin 초기화·compiler ABI는 여전히
별도 구현·역공학과 실기 검증이 필요하다.

## 검증

`tests/metal_session_tests.py`는 production session 코드16개 테스트를 실행했다.
잘못된 PCI 연결, 입력 범위, 외부 ticket, 명령 상태별 보유, 시간 초과와 늦은 완료,
잘못된 출력, 실패한 GPU 작업, close 차단, thread affinity를 검사한다. 실제 native
submit 메서드의 호출 경계에도 오류를 주입해 commit 수락 불확실 시 receipt 보존과
commit 전 할당 실패 시 회수를 확인했다. 주입한 backend가 native=True라고 주장해도
실기 통과를 반환하지 않는다. 결과는 `validation/metal-session-tests.json`이다.
