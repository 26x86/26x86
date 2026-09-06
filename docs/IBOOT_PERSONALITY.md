# iBoot(AArch64) Personality 범위

이 문서는 **사용자 공간 설정 검증 계층**과 **VMApple 복구 실행 계층**의
정책을 고정한다. EFI JIT, AIC 장치 모델, USB transport의 구현 상태나 Apple
서명 검증 결과를 대신하지 않는다.

## 대상 게스트

`iBoot(AArch64)`는 macOS 게스트 실행을 위한 MachineType이다. Venfire 내부
명칭은 유지하고 26x86의 사용자 화면과 산출물에서는 26x86을 제품명으로
사용한다.

```text
iBoot(AArch64)
 ├─ macOS     → Supported
 ├─ iOS       → Unsupported
 └─ iPadOS    → Unsupported
```

정책 검증기는 tvOS, watchOS, visionOS 등 모바일 Apple 운영체제와 알 수 없는
OS 이름도 거부한다. 지원 값은 `macOS` 하나이며, 대상 릴리스는 현재
`macOS 26 Tahoe`와 `macOS 27 Golden Gate`이다. 이 값은 실행 범위이며 실제
부팅 성공을 의미하지 않는다.

## 복구 범위

이 Personality가 구현 대상으로 삼는 복구 인터페이스는 macOS에 필요한
DFU/IPSW 경로다.

```json
{
  "Venfire": {
    "MachineType": "iBoot(AArch64)",
    "GuestOS": "macOS",
    "Recovery": {
      "Enabled": true,
      "Protocol": "DFU/IPSW",
      "LocalRecovery": {
        "ImageName": "_default.ipsw"
      }
    }
  }
}
```

`_default.ipsw`는 Local Recovery의 기본 파일명이다. 소스 검색·IPSW
검증·대상 System Storage 매핑은 EFI/Recovery 구현의 후속 단계이며, 이
정책 모듈은 이름과 게스트 범위만 확인한다. iOS/iPadOS 이미지가 파일명이나
바이트를 바꾸어 들어오는 것을 허용하는 우회 경로는 없다.

## 검증 순서

1. `MachineType`, `GuestOS`, 복구 프로토콜과 `_default.ipsw` 이름을 순수
   정책 함수가 검사한다.
2. 범위를 통과한 경우에만 QEMU/WSLg 실행 파일과 caller-supplied firmware,
   iBSS, AUX/root를 확인한다.
3. 그 다음에만 COW storage와 VMApple process를 만들고 실제 USB descriptor를
   읽는다.
4. reset 뒤 bulk OUT endpoint 4가 실제로 광고된 경우에만 iBEC 전송을
   시도한다. 이 조건이 충족되지 않으면 `transition-blocked`로 보존하고
   강제 전환하지 않는다.

모바일 게스트 요청은 1단계에서 `VF_GUEST_SCOPE_VIOLATION`으로 끝나므로
DFU block, QEMU process, 기존 ESP/guest image 쓰기가 발생하지 않는다.
Fastboot는 iBoot Personality의 복구 프로토콜이 아니며
`VF_RECOVERY_SCOPE_VIOLATION`으로 거부한다. 일반 Venfire MachineType
목록(U-Boot, EFI 등)은 이 문서의 iBoot 범위를 자동으로 확장하지 않는다.

## 확인 명령

입력 파일이나 USB를 건드리지 않고 정책만 확인한다.

```sh
python3 -m x86 personality validate --guest-os macOS --target 27 \
  --recovery-protocol DFU/IPSW --recovery-image-name _default.ipsw
```

거부 예:

```sh
python3 -m x86 personality validate --guest-os iPadOS
# exit 2, policy_error.code = VF_GUEST_SCOPE_VIOLATION
```

실제 VMApple 결과의 `machine_type`, `guest_os_policy`, `recovery_scope`도
같은 정책 결과를 기록한다. 현재 Golden Gate GUI 실험은 iBSS DFU 전송,
reset 뒤 실제 `05ac:1281` iBEC recovery 재열거, bulk endpoint 4,
LocalPolicy/iBEC 전송과 `go` acknowledgement, Stage2 prompt 및 restore-role
전송까지 확인했다. 이후 iBoot가 XNU 이전에 패닉했으므로
`signature_acceptance_verified`, `xnu_executed`, `macos_boot_verified`와
설치 UI 증거는 계속 `false`다. 이 경계에서 전환을 강제하지 않는다.
