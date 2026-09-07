# iBoot → XNU handoff contract

이 문서는 **Apple boot-chain 증거 검증 계층**이다. EFI/preOS 장치 모델,
QEMU VMApple TCG 프로세스, USB/iBoot transport, XNU 자체를 구현하는 문서가
아니며, 실행 로그의 단계가 실제로 인과적으로 연결되었는지를 판정한다.

## 왜 별도 계약이 필요한가

다음 이벤트는 각각 유효한 연구 증거지만 서로 대체할 수 없다.

```text
iBSS DFU
  → iBEC bulk upload / Stage2 prompt
  → restore roles / bootx acknowledgement
  → XNU entry
  → macOS userspace
```

특히 `05ac:1281` 재열거, bulk OUT endpoint 4, iBEC `go`, `bootx`
acknowledgement, TSS `STATUS=0`, LocalPolicy 전송 또는 QEMU 프로세스 종료는
그 자체로 서명 수락이나 XNU 실행을 의미하지 않는다. iBoot가 `bootx` 뒤에
패닉하면 최종 상태는 XNU 이전의 `blocked`다.

`x86/iboot_handoff.py`의 `verify_handoff_report()`는 다음을 강제한다.

- `iBoot(AArch64)`와 macOS 26/27 범위만 허용한다.
- 직접 AVPBooter 경로와 DFU 복구 경로를 구분한다. 직접 경로는 DFU를
  거치지 않아도 되지만 `direct_boot.requested=true`와
  `dfu_entered=false`를 요구한다.
- XNU/사용자 공간 플래그만 믿지 않고 로그 marker와 byte offset을 요구한다.
  XNU는 Darwin marker와 요청된 kernel major가 모두 있어야 한다.
- `macos_boot_verified=true`를 입력한 보고서가 단계·marker·target major·입력
  무결성 조건을 모두 만족하지 못하면 오류로 거부한다.
- `signature_acceptance_verified=true`에는 게스트가 실제로 수락했다는
  별도 acknowledgement, method, source가 필요하다. TSS 티켓 수신·payload
  보존·전송 ACK를 서명 수락으로 승격하지 않는다.
- 보고서는 읽기만 하며 QEMU, USB, firmware, AUX/root를 열거나 변경하지 않는다.

## 확인 명령

저장된 런처 보고서에 대해 오프라인 검증을 실행한다.

```sh
python3 sandbox/efi/verify_iboot_xnu_handoff.py \
  /path/to/output/report.json --target-major 27
```

복구 역할/`bootx` 체인을 반드시 요구하려면 다음을 사용한다.

```sh
python3 sandbox/efi/verify_iboot_xnu_handoff.py \
  /path/to/output/report.json \
  --target-major 27 --require-recovery-chain
```

종료 코드 `0`은 **보고서가 내부적으로 일관됨**을 뜻한다. 단계가 XNU
이전에서 막힌 일관된 보고서도 종료 코드 `0`일 수 있으며, JSON의
`claims.macos_boot_verified`는 `false`로 남는다. 종료 코드 `2`는 malformed
scope 또는 불가능한 양성 boot/signature claim이다.

합성 fixture가 모든 marker를 가지고 `verified`가 될 수는 있지만 이는
검증기의 논리 테스트일 뿐 실제 Apple 서명, 원본 iBoot, XNU 또는 macOS
userspace 실행 증거가 아니다. 실제 호환성 판정에는 해당 실행의 원본
UART/transport 로그, 변경되지 않은 입력 해시, guest acceptance 증거와
Apple Silicon native 실행 결과가 별도로 필요하다.
