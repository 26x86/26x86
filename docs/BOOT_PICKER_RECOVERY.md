# 26x86 부트 피커와 macOS 복구

이 문서는 `Alt/Option` 입력으로 macOS Recovery를 선택하는 경로를 설명합니다.
대상은 `iBoot(AArch64)`의 macOS 게스트이며, iOS·iPadOS 및 기타 모바일 Apple
운영체제는 이 경로에 포함되지 않습니다.

## EFI/OpenCore 계층 — 실제 Intel Mac

참조 설정은 [`integration/opencore/Sample.plist`](../integration/opencore/Sample.plist)입니다.
`Misc -> Boot`에 다음 정책을 고정했습니다.

```text
PollAppleHotKeys = true
ShowPicker       = false
Timeout          = 2
PickerMode       = Builtin
```

따라서 전원을 켠 뒤 2초 동안 Option(Alt)을 누르면 OpenCore의 내장 피커가
표시됩니다. `macOS Recovery` 항목은 해당 APFS 볼륨에 실제 Recovery 환경이
탐지될 때만 나타납니다. `ScanPolicy`, APFS 드라이버와 실제 볼륨 상태가
일치하지 않으면 피커에 항목이 없는 것이 정상이며, 이 참조 plist는 활성 ESP에
자동으로 기록되지 않습니다.

실제 Intel Mac에서 확인해야 할 증거는 다음과 같습니다.

1. 전원 인가 후 2초 안에 Option 키가 입력되었다는 OpenCore 로그
2. 내장 피커에 일반 macOS와 `macOS Recovery`가 함께 표시된 화면
3. Recovery 선택 뒤 해당 APFS Recovery 볼륨의 `boot.efi`가 로드된 로그
4. 복구 환경에서의 디스크 선택 화면

이 중 화면이나 로그를 직접 확인하지 않은 상태는 정적 plist 검사로만
기록합니다.

## VMApple GUI 계층 — 입력 상태 머신과 복구 전송

Windows 또는 macOS GUI의 `Apple Silicon Sandbox` 단계는
`x86/boot_picker.py`의 동일한 2초 정책을 사용합니다.

1. `2초 부트 피커 시작`을 누르면 상태가 `armed`가 됩니다.
2. 브라우저/WebView의 실제 `keydown` 이벤트에서 `Alt` 또는 `Option`을
   받으면 상태가 `picker`로 바뀝니다.
3. `macOS Recovery · _default.ipsw`를 클릭하거나 아래 화살표 후 Enter를
   누르면 `selected`가 되고, 선택 결과와 입력 시각이 브리지에 보존됩니다.
4. `Recovery VM 창 열기`는 이 선택 결과를 `--boot-selection recovery`와
   `--boot-picker-trigger alt-enter`로 VMApple worker에 전달합니다.
5. worker는 QEMU가 복구 소켓을 연 뒤 2초 게이트를 완료하고 나서만 iBSS
   DFU 전송을 시작합니다. reset 뒤 실제 USB descriptor에 bulk OUT endpoint
   4가 나타나지 않으면 `transition-blocked`로 멈춥니다.

상태 머신의 입력 이벤트는 `get_boot_picker_status`, `start_boot_picker`,
`tick_boot_picker`, `boot_picker_key`, `select_boot_entry` HTTP/pywebview
브리지 API로 확인할 수 있습니다. 이 API는 EFI를 쓰거나 macOS 게스트 파일을
변경하지 않습니다.

## Golden Gate 27 설치 판정

현재 저장된 Golden Gate 실험 자산은 원본 AVPBooter/iBSS와 읽기 전용 AUX/root
입력입니다. 새 출력 폴더에는 COW overlay와 `launch.json`만 생성합니다.
따라서 이 기능을 추가한 뒤에도 다음 세 가지가 모두 확인되어야 설치 화면에
도달한 것으로 판정합니다.

```text
signature_acceptance_verified = true
ibec_executed                 = true
xnu_executed                  = true
macos_boot_verified           = true
```

현재 확인된 장치는 `05ac:1227` iBSS DFU이며, reset 후 iBEC bulk endpoint가
광고되지 않습니다. 이 경계에서는 서명 수락, iBEC 실행, XNU 실행, Recovery
UI와 Golden Gate 설치 UI를 추정하지 않습니다. 보고서의
`macos_boot_verified`는 계속 `false`이고, `forced_transition`도 계속
`false`입니다.

## 구성 예시

`config.plist`의 26x86 fragment에는 다음 구조를 사용합니다.

```xml
<key>Venfire</key>
<dict>
  <key>MachineType</key><string>iBoot(AArch64)</string>
  <key>GuestOS</key><string>macOS</string>
  <key>Recovery</key>
  <dict>
    <key>Enabled</key><true/>
    <key>Protocol</key><string>DFU/IPSW</string>
    <key>LocalRecovery</key><dict><key>ImageName</key><string>_default.ipsw</string></dict>
  </dict>
  <key>BootPicker</key>
  <dict>
    <key>Enabled</key><true/>
    <key>DelaySeconds</key><integer>2</integer>
    <key>AltKey</key><string>Alt</string>
    <key>ShowPickerOnAlt</key><true/>
    <key>RecoveryEntry</key><dict><key>Enabled</key><true/></dict>
  </dict>
</dict>
```

`x86.sandbox_config.validate()`는 이 정책을 입력·EFI 경로·SMBIOS 검사보다
먼저 확인하고, 지연 시간이 2초가 아니거나 Alt/Option이 아니거나
`_default.ipsw`가 아니면 실패합니다.
