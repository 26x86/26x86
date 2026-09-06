> **Historical record — preserved unedited.** This document predates the MELLOW
> re-architecture. It is retained because the record of what was known, and when, is itself
> evidence. For the current concept and architecture see [CONCEPT.md](CONCEPT.md) and
> [ARCHITECTURE.md](ARCHITECTURE.md); for what any of it is allowed to claim, see
> [EVIDENCE-POLICY.md](EVIDENCE-POLICY.md).

# 0.4.1 부팅·GPU 검증 절차

현재 판정은 **7D41 Metal 가속 미완성 / 실기 부팅·설치 미검증**이다.
GuC·VM·IRQ 모듈은 존재하지만 실제 장치를 하나의 수명과 reset epoch로 관리하는
native backend owner가 아직 없다. 공개 Metal 클라이언트는 이미 등록된 MTLDevice를
사용하며, Tahoe용 Metal 사용자 공간 드라이버를 생성하지 않는다.

## 설치와 부팅

SanDisk `MACINSMS` USB의 현재 구성은 Mellow 활성화 실험 프로필이다.
`-mellowtahoe -MellowDebug -mellowtglwithgfx mellow-dmc=skip`을 유지한다.
WhateverGreen은 비활성화되어 있다. `mellow-dmc=skip`은 인증된 DMC 적재 결과가 아니다.
`profiles/gpu-baseline-safe.plist`에는 `-igfxvesa` 비교 프로필을 보존한다.

OpenCore → XNU → Recovery → SSD 설치 → 설치된 macOS 부팅을 각각 확인한다.
현재 Apple Recovery는 온라인 설치 매체이므로 Recovery에서 작동하는 네트워크가 필요하다.
기존 Windows 디스크 전체를 지우지 말고 설치 대상으로 정한 공간을 확인한다.
기존의 OpenCore schema, kext 파일, AML checksum 검사는 이 단계를 대신하지 않는다.

Recovery의 Terminal에서 다음을 실행하면 Python이나 Xcode 없이 정보를 수집한다.
`Diagnostics` 상위 폴더는 USB에 준비되어 있다. 두 번째 실행에는 새 폴더 이름을 쓴다.

```sh
sh /Volumes/MACINSMS/Diagnostics/Tools/collect-boot-evidence.sh recovery /Volumes/MACINSMS/Diagnostics/recovery-first
```

설치한 OS로 부팅한 뒤에는 다음을 실행한다.

```sh
sh /Volumes/MACINSMS/Diagnostics/Tools/collect-boot-evidence.sh installed /Volumes/MACINSMS/Diagnostics/installed-first
```

수집기는 OS build, boot session, root/APFS volume, kext, PCI, framebuffer,
accelerator, USB/NVMe/network, 설치 로그와 GPU 관련 로그를 보존한다. 명령별 실패와
30초 제한 시간을 기록한다. 수집 성공은 설치나 가속 성공 판정이 아니다.
OpenCore 단계에서 멈춘 경우 USB 루트의 `opencore-*.txt`와 `SysReport`를 보존한다.
XNU에 도달하기 전에는 이 shell 수집기를 실행할 수 없다.

## A. Compute와 B. offscreen render

전체 개발 패키지에서 Python 3과 Xcode command-line tools가 있는 macOS로 실행한다.
먼저 장치를 열거하고 물리 8086:7D41에 연결되는 registry ID를 확인한다.

```sh
python3 Tools/metal-run.py --output evidence/enumeration.json
python3 Tools/metal-run.py --compute 0xREGISTRY_ID --output evidence/compute-render.json
```

`0xREGISTRY_ID`는 열거된 실제 값으로 바꾼다. 열거만으로는 PASS가 나오지 않는다.
Compute의 첫 네 입력 `[1,2,3,4]`는 GPU MSL kernel에서 `x*7+3`을 계산하여
`[10,17,24,31]`과 대조한다. 나머지 입력과 nonce는 매번 바뀌며 초기 출력도
기대값과 다르게 만든다. Render는 private texture에 그린 뒤 GPU blit으로 공유
메모리에 읽고 모든 픽셀과 해시를 비교한다. CPU는 기대값 계산과 비교만 한다.
선택 장치와 PCI ancestry, 명령의 장치, 완료 상태와 GPU timestamp도 확인한다.

## C. 반복 제출

```sh
python3 Userspace/mellow_acceptance.py --registry-id 0xREGISTRY_ID --iterations 10000 --output evidence/stress-first
```

첫 실패에서 추가 제출을 멈추고 JSONL을 즉시 보존한다. Timeout이면 최대 60초
추가 drain을 시도하며 미완료 버퍼를 `close()`로 해제하지 않는다. 프로세스 종료가
GPU 취소를 보증하지 않으므로 그 경우 실패 및 미완료 상태를 기록한다.
1000회 미만은 장기 제출 테스트 PASS가 아니다.

이 도구로 관찰하지 못하는 reset/page-fault/hardware-fence/panic 수치는 `null`이다.
로그에 오류가 안 보인다는 이유로 0을 만들지 않는다. 스트레스 통과도 공개 Metal
compute의 제한된 근거이며 GuC 인증·실기 IRQ/fence·WindowServer 사용의 증거가 필요하다.
화면 출력, `Metal: Supported`, WindowServer 프로세스 존재만으로 최종 PASS를 내리지 않는다.

## OS·루트패치 경계

현재 완성되고 검증된 7D41용 Metal root patch는 없다. TGL 이름이 붙은 드라이버의
실제 존재·출처·버전·호환성부터 설치 OS에서 확인해야 한다. Recovery 이미지에서
조사한 ICL Metal bundle metadata와 helper dylib는 완전한 TGL Metal 드라이버가 아니다.
루트패치 완료나 부팅 성공을 만들기 위해 드라이버 attach 또는 fence 결과를 조작하지 않는다.
ROM/UEFI 변경은 실기 로그가 해당 계층의 구체적 문제를 가리킬 때 검토한다.
