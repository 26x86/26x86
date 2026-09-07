# APLS normal recovery adapter 조사 및 제안 계약

작성: 2026-09-07. 계층: Windows/WSL 호스트 실행 조정 → Python recovery worker → QEMU ARM64 guest. 이 문서는 BP15 결정을 위한 읽기 전용 조사 결과다. 아래 제안은 아직 Build Plan에 합의된 구현 계약이 아니다. 코드·시작 문서·Apple 입력은 수정하지 않았고 새 VM/TSS 요청은 실행하지 않았다.

현재 상태: BP13/14의 정상 recovery는 `python -m x86 vmapple run` 경로다. 현재 Rust `RunnerBackend::Tcg`는 `run-tcg`만 호출하므로 정상 recovery에 필요한 live TSS/DFU/iBEC/restore 역할 입력을 전달하지 못한다. 원하는 상태는 같은 recovery 작업을 명시적인 Nextcore 실행 모드로 제공하면서, 전체 실행 상한·자식 수거·원본 무결성·게스트 진행 증거를 각각 반환하는 것이다.

## 1. 결론과 실제 근거

- **`--transition-timeout 20 --restore-timeout 30 --duration 10`은 전체 60초 상한이 아니다.** 별도 personalization/DFU/전환/전달/Stage2 대기 시간이 있고, `duration`은 그 단계들이 끝난 뒤부터 시작한다. Rust의 현재 `child.wait()`에는 상한이 없다.
- legacy Python은 잡힌 예외에서 직접 소유 QEMU를 terminate → wait 5초 → kill → wait 5초로 수거한다. 그러나 worker의 SIGTERM/SIGKILL/WSL 전송 단절을 처리하는 전체 process-group 감독 계약은 없다.
- normal report는 `schema="26x86.vmapple-gui/1"`, `runtime_started`를 사용하며 top-level `engine`이 없다. 기존 Rust TCG evaluator가 요구하는 `26x86.vmapple-tcg/1`, `qemu-vmapple-tcg`, `tcg_runtime_started`와 다르다.
- normal CLI는 `error is None`이면 exit 0이다. 이는 연구 프로토콜 실행 결과이며 macOS boot 판정이 아니다. 기존 BP13 보존 결과는 worker exit 0, QEMU exit 0, Stage2 prompt/5종 restore/bootx ACK 확인, **Darwin/userspace 없음 및 macOS boot false**를 함께 기록한다.
- 현재 normal recovery의 post 단계는 panic 관측만 갱신한다. `xnu_executed`는 false로 시작하고 recovery 성공 경로에서 UART XNU/userspace 파서로 갱신되지 않는다. `iboot_xnu_handoff.valid=true`는 보고서 내부 일관성이고, `claims.macos_boot_verified=true`와 다르다. 최소 adapter가 이 빠진 증거를 만들어서는 안 된다.

근거: `x86/cli.py:621-675`, `x86/vmapple.py:2702-2764,2916-3188`, `x86/iboot_handoff.py:170-183,335-370`, `nextcore/crates/nextcore-apls/src/runner.rs:59-85,177-227,315,362-492`. 실제 보존 결과: `nextcore/artifacts/apls-restore-contract-20260907/normal-recovery-optional-rpc-observation.json`(42.693초, outer_timeout=false, 원본 13개 동일, PID 수거). 이번 조사에서 그 런타임을 재실행하지 않았다.

## 2. 기존 normal CLI의 정확한 입력 계약

BP13의 재현 입력은 `normal-recovery-optional-rpc-invocation.json`에 argv 배열로 남아 있다. shell 문장으로 재조립하지 않고 항목 단위로 전달해야 한다. 기본 normal entry는 다음 구조다. 아래 `<...>`는 계약상 경로 자리이며 실행 명령을 수행한 기록이 아니다.

```text
<python> -m x86 vmapple run
  --target 27
  --qemu <qemu-system-aarch64> --qemu-img <qemu-img>
  --firmware <AVPBooter> --vm-json <macosvm.json>
  --boot-selection recovery --no-boot-picker
  --memory-mib 4096 --smp 2 --display none
  --build-manifest <BuildManifest.plist> --tss-helper <local-helper>
  --original-ibss <unchanged-iBSS.im4p>
  --original-ibec <unchanged-iBEC.im4p>
  --live-personalize --restore-chain --restore-role-dir <role-directory>
  --transition-timeout 20 --restore-timeout 30 --duration 10
  --output <new-Linux-output-directory> --research-only --json
  [--optional-rpc-unavailable]
```

- `--target`: 26 또는 27. 현재 BP13/14 관측은 27/26A5425a/ARM64 입력이다. x86_64 authored EFI probe와 혼동하지 않는다.
- `--vm-json`: hardware model/ECID/원본 AUX/root를 한 bundle에서 해결한다. 별도 `--aux`, `--root`, `--uuid`, `--aux-offset`는 충돌 검사 대상이므로 최소 adapter에서 함께 노출할 필요가 없다. 내부 AUX offset은 bundle metadata에서 정해진다.
- `--firmware`: 정상 recovery는 AVPBooter에서 DFU를 시작한다. `run-tcg --firmware-kind iboot-stage2`의 raw Stage2 entry와 교환하면 안 된다. normal `run`에는 `--firmware-kind`와 `--observation-timeout` 옵션이 없다.
- live mode는 BuildManifest, TSS helper, original iBSS, original iBEC가 모두 필요하다. 입력 파일은 로컬에 이미 존재해야 한다. helper는 `subprocess.run([helper, identity_plist, parameters_plist, optional "local-policy"])`로 호출된다.
- `--restore-chain`은 `--live-personalize`를 요구한다. 역할 디렉터리에 `RestoreTrustCache.im4p`, `RestoreRamDisk.im4p`, `RestoreDeviceTree.im4p`, `RestoreKernelCache.im4p`가 필수이고 `RestoreLogo.im4p`는 있으면 사용한다. CLI에는 `restore_extra_commands` 옵션이 없으며 최소 adapter에도 추가하지 않는다.
- `--memory-mib`: normal 경로 512..1048576, `--smp`: 1..32. 기존 Rust raw-TCG 허용 범위 128..262144 및 1..255를 그대로 복사하면 normal worker와 불일치한다.
- `--transition-timeout`, `--restore-timeout`: 유한 양수 ≤3600초. `--duration`: 주어지면 유한 양수 ≤86400초이나 생략하면 post 대기가 무기한일 수 있다. adapter에는 양수 duration을 필수로 둔다.
- `--boot-selection` 기본 recovery, boot picker 기본 on/2초다. BP13은 `--no-boot-picker`로 실행했다. adapter는 결정한 값을 명시하고 receipt에 보존한다.
- `--research-only`는 필수. `--optional-rpc-unavailable`는 명시 실험 옵션이며 기본 off를 유지한다. `--research-stage2` 및 `--research-graphics`는 BP13 입력에 없고 기본 off다.
- 현재 normal parser는 여러 `X86_VMAPLE_*` 환경 기본값을 읽는다. 또한 `VENFIRE_RESTORE_BOOT_ARGS`는 restore 명령을, `VENFIRE_EXTRA_TRACE`는 trace 구성을 바꾼다. 최소 adapter는 이 두 값과 legacy optional-input 환경값을 지우거나 검증된 명시 값으로 고정하고 effective 값/사용 여부를 receipt에 기록해야 한다. 특히 상속된 AUX/root seed나 legacy iBEC가 숨은 입력이 되어서는 안 된다. 임의 환경 전체를 receipt로 덤프하지 않는다.
- restore 기본 boot-args는 `rd=md0 nand-enable-reformat=1 -progress -restore`다. 이는 restore 매체 역할의 명령이며 설치 완료 증거가 아니다. 별도 변경 없이 기본값을 고정하는 것이 BP13 재현 범위다.

근거: `x86/cli.py:905-1009`, `x86/vmapple.py:2359-2603`, `x86/vmapple_restore.py:42-60,243-360`, `x86/vmapple_personalization.py:223-231`.

## 3. 단계별 시간과 stop 지원의 실제 범위

아래 시간은 각 단계의 현재 동작 설명이다. 합산한 값을 strict 전체 wall-clock 상한으로 사용할 수 없다.

1. QEMU capability probes는 각 15초이며 여러 번 순차 호출한다. QEMU startup 전에 storage 진단과 파일 해시가 수행된다. qcow2 두 개 생성은 각각 30초 subprocess timeout을 가진다. 이 시간은 transition/restore/duration에 포함되지 않는다(`vmapple.py:585-622,1453-1478,2643-2691`).
2. QEMU 시작 뒤 recovery socket은 별도 30초, picker는 켜져 있으면 2초다(`2776-2795`).
3. iBSS live personalization은 새 `now + transition_timeout`을 받는다. helper encode와 HTTPS ticket 및 nonce 재확인이 그 단계 안에 있다(`2916-2930`).
4. iBSS upload는 `send_dfu_file()`의 **별도 기본 300초**를 사용한다. caller가 transition_timeout을 넘기지 않는다. initial probe/개별 USB 제어는 transport timeout을 사용한다(`2936-2942`, `1730-1777`).
5. DFU→iBEC endpoint 관측은 다시 transition_timeout을 받는다. probe의 여러 control 요청은 개별 timeout을 재설정하며 loop deadline을 완전히 공유하지 않는다(`1972-2000`).
6. iBEC+LocalPolicy personalization은 다시 `now + transition_timeout`을 받는다. 그 후 configuration/LocalPolicy/iBEC/go도 별도 `recovery_deadline=now+transition_timeout`을 만들고, Stage2 prompt는 다시 `min(transition_timeout,300)`을 기다린다(`2947-2984`).
7. restore timeout은 역할 파일 읽기/정규화/래핑/해시 **뒤에서** 시작한다. transfer마다 남은 시간과 socket timeout을 사용한다. 파일 읽기·최종 해시는 해당 transfer/restore timeout 바깥이다(`vmapple_restore.py:255-300,370-378`, `vmapple.py:1830-1864`).
8. `duration` deadline은 위 처리가 끝난 다음 `now + duration`으로 설정된다. `(output / "stop").exists()`도 이 final loop에서만 확인한다. 따라서 early TSS, DFU, Stage2, restore 대기를 stop 파일로 즉시 취소할 수 없다(`3090-3104`). Stage2 panic/marker timeout은 별도로 바로 QEMU cleanup에 진입한다(`2993-3017`).
9. terminate/kill 대기와 source 재해시·report 기록은 추가 시간이다(`1879-1969,3182-3187`).

TSS helper timeout 자체는 전달된다(`vmapple_personalization.py:254-255`). Python은 `subprocess.run(timeout=...)` 만료 시 해당 자식을 kill 후 wait하지만 프로세스 생성 시간까지 엄격한 상한을 보장하지 않는다. [Python subprocess 문서](https://docs.python.org/3/library/subprocess.html#subprocess.run)

HTTPS의 `open(timeout=_time_left(deadline))` 후 `response.read(MAX_TSS_BYTES+1)`에는 전체 monotonic deadline을 다시 확인하는 루프가 없다(`262-265`). 이 timeout은 연결 같은 blocking operation에 대한 값이므로 전체 네트워크 왕복을 강제로 중단하는 전역 watchdog으로 볼 수 없다. [Python urllib.request 문서](https://docs.python.org/3/library/urllib.request.html#urllib.request.urlopen)

따라서 **전체 worker 상한은 legacy의 phase timer와 별도로 필요**하다. 기존 BP13 diagnostic `observe-recovery.py:186-201`은 Linux에서 `start_new_session=True`인 worker를 생성하고 75초 후 owned group에 TERM, 필요 시 KILL을 보낸다. 이것은 `x86 vmapple run`이나 현재 Rust runner에 내장된 기능이 아니다. diagnostic script는 QMP pause/trace도 추가하므로 그대로 제품 adapter의 worker로 재사용할 이유가 없다.

## 4. 종료 및 WSL 실패 계약

현재 보장:

- Python이 처리하는 normal 예외/KeyboardInterrupt는 `except BaseException`으로 들어가 `_terminate_process(process)`를 호출한다. 해당 **직접 QEMU 자식**의 returncode, complete, forced, terminate/kill/wait 오류를 기록한다(`vmapple.py:1879-1942,3189-3225`).
- 복원 후 보존한 USB transport는 `finally`에서 닫고 passive drain thread를 최대 1초 join한다. recovery socket 파일도 지운다(`1515-1527,3264-3272`).
- recovery 예외는 `launch.json`에 부분 report를 남긴 뒤 다시 raise한다. CLI stdout에는 `{ok:false,error:...,macos_boot_verified:false}`만 나올 수 있으므로 stdout만 읽으면 이미 시작한 QEMU/PID/cleanup/input receipt를 잃는다(`3189-3263`, `cli.py:664-673`).

현재 미보장:

- normal QEMU `Popen`에는 별도 session/group 설정이 없다. worker에도 SIGTERM handler, parent-death handler, 전체 deadline이 없다. 기본적인 프로세스 종료는 Python exception cleanup 경로와 같지 않으며 SIGKILL은 처리할 수 없다. [Python signal 문서](https://docs.python.org/3/library/signal.html#signal.SIGKILL)
- Rust는 Windows `wsl.exe` PID를 저장하고 `child.wait()` 결과를 받는다. 그 Windows PID가 종료됐다고 Linux QEMU/TSS 자식의 종료가 증명되지는 않는다. `wait()` 오류나 WSL 연결 상실에 대한 Linux cleanup 재확인도 없다(`runner.rs:251-264,302-328`).
- `_terminate_process()`는 process tree 전체가 아니라 주어진 Popen 자식 하나를 정리한다. TSS helper가 다른 자식을 만드는 경우까지 기존 helper timeout이 수거한다고 단정할 수 없다.
- 기존 diagnostic wrapper의 TERM 후 KILL 판단도 worker `wait()`만 기준이다. worker만 먼저 종료되고 같은 그룹의 자식이 TERM을 무시하면 KILL 단계가 생략될 수 있다. BP13 실제 run의 수거 성공과 이 일반 실패 경로의 보장은 별개다.

BP15 최소 제안:

- Linux/WSL 안의 supervisor가 **worker를 spawn하기 전부터** 단일 monotonic 전체 deadline을 소유한다. capability helper/QEMU/TSS helper는 그 worker가 시작한 한 owned session/process group에 속한다. 별도 cancellation/cleanup grace는 짧고 유한하게 기록한다. phase deadline을 리셋해도 전체 deadline은 연장하지 않는다.
- stop 요청은 supervisor가 모든 phase에서 감시하고, 우선 협조적 중지 후 bounded grace를 지나면 owned group TERM→KILL로 수거한다. worker가 먼저 종료됐어도 잔여 그룹을 확인한다. 정상 종료·예외·timeout·cancel 모두 같은 잔여 자식 확인 경로를 탄다. 무관한 QEMU 프로세스에 이름 기반 kill을 하지 않는다.
- Rust의 WSL launcher PID, Linux supervisor/worker PID, QEMU PID와 각 수거 상태를 분리한다. Linux-side deadline/cleanup을 Windows wrapper 생존만으로 대체하지 않는다. WSL 재접속/상태 읽기가 실패하면 `guest_process_terminated=false` 또는 명시 unknown 상태이며 성공으로 치환하지 않는다.
- 원본 파일은 supervisor가 미리 확정한 입력 manifest로 최종 재해시한다. worker 강제 종료로 legacy final hashing이 실행되지 않았으면 그 결과를 복구하거나 `input_integrity=false/unknown`으로 남긴다. 재해시 자체의 상한도 별도 명시한다.
- Linux output은 새 경로이고 원본 bundle 바깥이어야 한다. worker의 새 COW session을 계속 사용한다. Linux supervisor가 bounded `launch.json` 읽기를 담당하므로 `/tmp/...`를 Windows `Path`로 읽으려 하지 않는다.
- raw worker stdout/stderr, `launch.json`은 변형 없이 해당 연구 runtime에 보존하고 hash/path/완결 여부를 envelope로 반환한다. 부분 report에 `returncode`가 남아 있거나 stdout JSON이 유효하다는 이유만으로 cleanup 완료를 추정하지 않는다.

`start_new_session=True`는 POSIX에서 setsid를 호출한다. TERM/KILL이 지정 자식 하나를 대상으로 하는 Popen API와 process-group 감독은 다른 범위다. [Python subprocess 문서](https://docs.python.org/3/library/subprocess.html#popen-constructor)

## 5. 최소 Rust/CLI 입출력 제안

이름은 BP15에서 확정한다. 논리적으로 기존 native/raw-TCG와 구분되는 **TCG recovery variant**가 필요하다. 예를 들어 `RunnerBackend::TcgRecovery` / CLI `--backend tcg-recovery`처럼 명시하고, 기존 두 경로는 그대로 둔다. AVPBooter를 선택했다는 이유만으로 자동 recovery로 바꾸지 않는다.

요청에 필요한 항목:

- 기존 공통 host(local Linux 또는 WSL distribution/python), repository, vm_json, output, host_receipt_dir, target, research_only.
- qemu, qemu_img, AVPBooter firmware, memory_mib, smp.
- build_manifest, tss_helper, original_ibss, original_ibec, restore_role_dir.
- transition_timeout_secs, restore_timeout_secs, **total_timeout_secs**, 양수 post duration. 기존 `observation_timeout_secs`를 normal argv에 전달하지 않는다. `duration_secs`를 재사용하면 “restore 처리 후 관측 시간”이라는 모드별 의미를 문서/receipt에 명시한다.
- live_personalize=true, restore_chain=true, boot_selection=recovery, display=none을 이 variant에서 고정하면 최소 입력 surface가 된다. BP13 재현을 위해 boot picker 설정도 명시한다. optional_rpc_unavailable는 별도 명시 false 기본값이다.
- 위 필드들은 argv 원소 또는 검증된 structured request로 전달한다. shell interpolation이나 arbitrary command/extra QEMU arguments는 필요하지 않다. Python의 기존 parser/transport/restore 구현을 호출하고 protocol을 Rust에 복제하지 않는다.

반환 envelope는 raw `26x86.vmapple-gui/1` report의 schema를 바꾸지 않고 감싼다. 추천 필드는 request identity, worker exit/completed, total deadline/cancel 사유, Linux child cleanup, source integrity, worker report path/hash/completeness, recovery_progress, boot claims다. Rust `RunOutcome`의 현재 `report`에 원문을 보존하고 다음 분리 정보를 추가하거나 내부 구조로 둔다.

- `guest_runtime_started`: 일치하는 request identity 및 raw recovery schema/boot_mode/target/machine_type/guest_os와 `runtime_started=true`; supervisor가 기록한 해당 QEMU PID와 결합한다. raw report에 없는 `engine`/`tcg_runtime_started`를 주입해 기존 TCG identity 검사를 통과시키지 않는다. envelope 자체 engine은 `qemu-vmapple-recovery`처럼 구분 가능하다.
- `guest_process_terminated`: supervisor의 동일 QEMU/owned-group 종료 확인. raw `process_cleanup.complete`, `returncode`, `termination`은 보존하되 단독 판단을 피한다. 자연 종료는 process_cleanup이 없을 수 있다.
- `recovery_progress.dfu_upload_completed`: `dfu_upload.transfer_complete`; endpoint ready는 `transition.state=="ibec-ready"`로 별도 기록한다.
- `recovery_progress.stage2_banner_observed`/`stage2_prompt_observed`: 각각 `stage2.stage2_serial_started`와 `stage2.observed`, 대응 byte offset/marker를 보존한다. banner와 prompt를 같은 단계로 합치지 않는다.
- `recovery_progress.restore_sequence_sent`/`bootx_acknowledged`: `restore_chain.sequence_sent`, `restore_chain.bootx_acknowledged`, 해당 input_integrity와 실제 역할 step count를 함께 반환한다. top-level restore_chain_completed만으로 누락된 ACK를 채우지 않는다.
- TSS ticket/payload preservation, firmware panic, worker error, transition_blocker, handoff_blockers는 독립 증거다. raw report 내부의 private 경로/긴 로그를 사용자 화면에 모두 출력할 필요는 없다.
- **현재 worker에 대한 최소 adapter는 XNU/userspace/macOS boot 미검증을 유지한다.** 추후 같은 실행의 UART parser가 연결되면 명시적으로 XNU marker+major, 뒤따르는 userspace marker, causal handoff claims, request target 일치, input integrity, cleanup 완료와 raw positive boot claim을 모두 요구한다. 기존 evaluator의 인식 marker/offset 검사를 약화하지 않는다.
- CLI exit 0은 기존 Nextcore와 같이 macos_boot_verified일 때만. 연구 진행 완료라도 boot false이면 exit 2로 반환하며 `completed-unverified` 등으로 표시한다. Python worker exit 0은 원문 exit 정보로만 보존한다. 설치/Metal/실기 Mac 검증은 false다.

최소 검증 항목은 argv/identity/schema, 부분 launch report 복구, 단계별 false-positive 방지, total deadline 중 helper/worker stall 및 worker-first-exit 후 잔여 자식 수거, stop의 early phase 취소, WSL transport 실패 시 cleanup unknown 유지다. authored stalled worker/child는 감독 경계 단위 테스트에 사용할 수 있으나 실제 recovery boot 성공 증거는 아니다. 실제 다음 recovery 실행은 root가 한 담당자에게만 위임해야 한다.

## 6. OPEN_QUESTION / BP15 결정 항목

- `OPEN_QUESTION: Build Plan: TCG recovery variant/CLI 이름과 supervisor 배치 파일을 확정한다. 현재 Rust wait만으로 bounded라는 주석은 새 recovery에 적용할 수 없다.`
- `OPEN_QUESTION: Build Plan: 전체 deadline, cleanup grace, 원본 재해시 예산 및 cancel/WSL 단절 관측 방식을 수치로 고정한다. BP13의 20/30/10 phase 값은 전체60초 계약이 아니다.`
- `OPEN_QUESTION: Build Plan: 최소 노출은 현재 미검증 recovery 진행만 반환할지, 같은-run post-restore UART observer까지 포함할지 결정한다. 후자의 경우 별도 marker/target/순서 acceptance가 필요하다.`

## 7. 조사 시점 파일 지문

아래 SHA256은 조사한 공개 소스/메타 문서의 지문이며 Apple payload 내용이 아니다. 다른 에이전트 변경으로 이후 달라질 수 있다.

```text
x86/cli.py 9015523160cf0d1cc470aedb0124d32c55054aed644e8aecfeadbad17d41d475
x86/vmapple.py 584256d8ef11c5d3007edf141cc034c2033eeda75e0b5619e2e156dad2b62bdd
x86/vmapple_personalization.py 5a79060d7dfba41198ca2f7bbbbd64d0b175f5c1eca7ecf48c31fce6d1ce2df7
x86/vmapple_restore.py a3ad1c907ef2c4f43cad1a62e640efeeedd24e291da1f2c99f296598c3bc8b8f
x86/boot_evidence.py 6fe20a5f9e376992ff3c486459922683a8f37b8cb43edc1ef4fcdee58857014d
x86/iboot_handoff.py 7a589f93c5971a864e60e3403c58ed86e44cfdbc2c6ab09530b2c6e567f7c116
nextcore/crates/nextcore-apls/src/runner.rs 5636d1244a8743ac89ca0d7fec4733be969e21da0deee7f97cc7a69016db87a6
nextcore/artifacts/apls-restore-contract-20260907/observe-recovery.py 23a073d091a4ff75c8b5ef79e27a6ecb4f3d683e2b0f3e7ffa24ba93b54b8e6f
nextcore/artifacts/apls-restore-contract-20260907/normal-recovery-optional-rpc-invocation.json 9ae4edc6d6b70b913be840115cecb75e860ee5c4b7458092789a9e4bc73c5a1b
nextcore/artifacts/apls-restore-contract-20260907/normal-recovery-optional-rpc-observation.json 0d1f809226973e59dbb6a95c678c94c118b07ed057febe2e36ff67982804389e
```
