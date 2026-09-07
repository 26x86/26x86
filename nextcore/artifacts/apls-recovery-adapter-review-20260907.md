# BP15 normal recovery adapter 독립 리뷰

작성: 2026-09-07. 계층: Linux supervisor의 프로세스 수명 → Windows/WSL Rust runner의 증거 판정 → CLI 표시/exit. 현재 상태는 정상 recovery adapter 구현 및 합성 검증 완료이며, 원하는 상태는 기존 BP14 진행을 정확히 보존하면서 새 실행의 수거·무결성·부팅 증거를 혼동하지 않는 것이다.

검토 범위는 `x86/recovery_supervisor.py`, `x86/test_recovery_supervisor.py`, `nextcore/crates/nextcore-apls/src/runner.rs`, `nextcore/crates/nextcore-tool/src/apls.rs`다. AGENTS, BP15 및 Boundary B7에 따라 제품 소스는 읽기만 했다. 새 VM, TSS, 네트워크 요청은 0회다. 원문 replay와 상세 receipt는 격리에 보존했고 이 문서에는 일반 메타만 남겼다.

## 판정

**최종 검토 소스에서 미해결 actionable finding은 없다.** 리뷰 중 발견한 출력 경로 P2는 담당자가 수정했고 회귀 검증으로 닫혔다. 이는 코드·합성 실행 계약에 대한 판정이며 새 adapter로 macOS를 실행하거나 부팅을 검증한 결과가 아니다.

- **해결된 P2 — 요청 원문과 canonical output을 혼동.** supervisor는 상대 경로 및 symlink/`..`가 있는 출력 경로를 절대 경로로 확정하지만 기존 Rust 판정은 이를 요청 문자열과 직접 비교했다. 유효한 로컬/WSL 실행이 `runtime=false`로 거부될 수 있었다. 최종 구현은 `requested_output`을 요청 원문과 비교하고, raw launch의 `output`은 envelope의 절대 Linux `output`과 비교한다. 상대 `runs/../result` → canonical `/source/result` 회귀와 누락/잘못된 canonical 경로 거부가 통과했다. 근거: supervisor `supervise()`, Rust `evaluate_recovery_report()` 및 `recovery_correlates_relative_request_with_canonical_linux_output`.
- root가 요청한 **QEMU PID 상관 보완**도 최종 소스에서 확인했다. 런타임 승격은 raw PID가 worker와 다른 양수이고, 관측 inventory의 동일 worker session에서 유일한 PID/starttime으로 기록되며 inventory가 완전할 때만 가능하다. PID 재사용 모호성·다른 session·관측 누락·runtime 미시작은 진행 승격을 거부한다.

## 검증한 계약

| 항목 | 확인 결과 |
| --- | --- |
| 전체 시간 | worker와 cleanup이 같은 monotonic total deadline을 공유한다. CLI는 total이 post duration+5초보다 커야 한다. prehash 20초와 posthash/evidence 20초는 별도이므로 선언된 전체 예산은 total+40초다. phase timeout의 합을 전체 상한으로 표시하지 않는다. |
| 자식 수거 | 새 session, PID/starttime/session 재확인, pidfd signal, subreaper 채택을 사용한다. leader가 먼저 끝나도 남은 session 구성원을 확인한다. 다른 process group의 TERM 무시 자식, 조기 stop, TERM/INT/HUP, 무관한 PID 보존 검증이 통과했다. 최종 보완된 비ASCII·닫는 괄호 process comm의 byte 단위 파싱도 독립 회귀 통과했다. |
| 입력 무결성 | 선언된 원본과 VM JSON의 AUX/root 및 복원 역할을 별도 helper로 전후 해시한다. timeout/불완전 읽기는 unknown이며 변조는 false다. helper 수거 실패도 전체 cleanup 성공으로 숨기지 않는다. |
| 크기·불완전 증거 | stdout/stderr 저장 및 raw launch 읽기는 각각 4 MiB 상한이다. 전체 관측 stdout hash와 저장된 prefix hash/완결 여부를 구분한다. JSON escape 팽창과 envelope 메타 때문에 전송 envelope/Rust 파싱 상한은 8 MiB다. 초과 raw는 제거하면서 complete/identity를 false로 바꾼다. partial JSON, 비유한 수, symlink/FIFO 및 oversize 검증이 통과했다. |
| WSL 및 판정 | WSL launcher 종료만으로 Linux 수거를 인정하지 않는다. envelope/launch identity와 관측된 QEMU PID, cleanup complete/leader reaped/잔여 PID 없음이 필요하다. 전송 소실·누락·잘못된 receipt는 cleanup/boot를 false로 유지한다. |
| 환경·자산 | restore boot args, trace 및 legacy 선택 입력 환경변수를 제거하고 값 전체를 출력하지 않는다. 제품 소스/테스트에서 격리 helper import나 BP14 분석 이식은 없다. raw launch와 raw 오류 문자열은 진단 receipt/명시 `--json`에 보존되므로 공개 배포용 정제 보고서로 취급하지 않는다. |
| 부팅 판정 | Stage2, DFU, 역할 전송, bootx ACK와 XNU/userspace를 분리한다. 같은 실행의 marker/major/순서, handoff claim, 무결성 및 cleanup이 모두 필요하다. 현재 supervisor의 boot 필드는 false로 유지되며 CLI exit 0은 boot verified에만 사용한다. |

명시된 한계도 유지한다. supervisor SIGKILL, session을 의도적으로 벗어난 daemon, blocking kernel syscall 지연은 수거/벽시계 보장 범위 밖이다. Rust의 WSL `wait` 자체가 Linux 외부까지 강제 종료하는 별도 watchdog은 아니다. 이 제한을 실제 Linux cleanup 증거로 대체하지 않는다.

## 저장된 BP14 원문을 이용한 offline 확인

BP14 launch 96,174바이트를 read-only로 읽었다. SHA256은 `0d3eccd9a2fdcbcdacf6ad862fd44b4d4a0e98c4921779143e4abab7a2fa666d`이며 읽기 전후 동일했다. 원문에는 runtime 시작, 복원 역할 5개와 bootx ACK, 이후 firmware panic이 있고 XNU/macOS boot는 false다.

당시 실행에는 새 supervisor의 process inventory가 없다. 따라서 **그 원문을 그대로 감싼 offline CLI replay는 runtime/termination false, exit 2**가 맞다. 기존 관측 기록의 의미는 raw 안에 보존된다.

별도의 **명시적 authored PID 상관 fixture**로 매핑만 검사했을 때는 DFU/iBEC/Stage2/5 roles/bootx/panic이 true로 전달되고 XNU/userspace/macOS boot는 false, CLI exit는 2였다. 이 fixture의 supervisor cleanup·무결성·PID 상관 값은 합성값이며 실제 BP14 supervisor 증거가 아니다. replay 실행기는 JSON 출력만 했고 실제 QEMU/TSS/worker를 호출하지 않았다.

일반 메타 receipt: `nextcore/artifacts/apls-recovery-adapter-review-offline-20260907.json`.

## 최종 targeted 검증

- WSL `python3 -m unittest x86.test_recovery_supervisor -v`: **17/17 PASS**.
- `cargo test -p nextcore-apls runner::tests --offline`: **17/17 PASS**.
- `cargo test -p nextcore-tool apls::tests --offline`: **9/9 PASS**.
- offline CLI replay 2건: 둘 다 기대한 **exit 2**, 부팅 검증 false.

최종 검토 지문:

```text
x86/recovery_supervisor.py 2528fc5270094681ae2e4cf22286b40fbda11c0514f63ffca3f3d6dca74777ba
x86/test_recovery_supervisor.py 7a55ebb84c88d88fc065d16dd273f49aee8684715c5dddad32e561f2f2298d1a
nextcore/crates/nextcore-apls/src/runner.rs 7149a7d1c05292fb8d0914d894aaf3e8b81536962d806fea1524b0d9b08348d7
nextcore/crates/nextcore-tool/src/apls.rs a33439d666b64d1036bf26d10732731fa1cf580c2dccac0bf1dd5fb378429362
```

OPEN_QUESTION: 없음. 새 adapter의 실제 recovery 실행 및 수거 증거는 후속 Build Plan의 명시 실행 범위다.
