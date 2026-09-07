# BP14 host observation wrapper review

계층은 호스트 debugger/process lifecycle이다. 현재 BP14 private wrapper,
GDB command, outer runner의 구조를 읽었다. 원하는 상태는 공개 callback의
대상 실패 인자를 한 번 읽고 detach한 다음, 정해진 시간 안에 소유한 QEMU와
debugger를 종료·수거하는 것이다. 실제 guest 실행이나 관측 값 검증은 이
리뷰가 수행하지 않는다. precise 주소·register·ticket·원문 관측 값은 기록하지 않는다.

## 검토 중 발견과 상태

1. **P2 / source 수정 확인 — JSON 저장 경쟁으로 cleanup 중단 가능.** 초기
   debugger receipt는 직접 truncate/write했고 wrapper는 예외 처리 없이 읽었다.
   저장 중인 JSON을 읽으면 main/finally의 reap 함수가 예외로 끝나 후속 정리를
   건너뛸 수 있었다. GDB의 같은 directory temp+replace 및 wrapper의 JSON/
   I/O 오류 처리, 이미 reap한 상태의 조기 반환을 다시 읽어 수정 확인했다.
   source 수정만 확인했으며 이 경쟁을 runtime에서 주입한 것은 아니다.
2. **P2 / 수정·합성 검사 확인 — leader 종료가 descendant 종료를 보장하지 않음.**
   초기 outer runner는 timeout 후 group에 TERM을 보내고 leader의 wait가 다시
   timeout일 때만 KILL했다. leader가 먼저 종료하면 살아 있는 descendant가
   있어도 escalation을 건너뛴다. group/소유 descendant의 잔존 확인과 cleanup을
   leader 상태와 분리해야 한다. 후속 private lifecycle 모듈은 별도 process
   group도 포함하는 소유 session을 열거하고, leader 종료와 무관하게 TERM/KILL과
   adopted waitpid를 수행한다. 아래 합성 기록으로 수정 경로도 확인했다.
3. **시간 계약 정합 / 수정 확인.** 초기 outer의 90초 wait 뒤 TERM grace 3초와 KILL
   wait 3초는 총 90초 상한이 아니다. 전체 deadline 안에 cleanup 시간을 예약하고
   잔존 확인까지 마치는 것으로 조정했다. 후속 모듈은 absolute90 안에 cleanup
   4초를 예약하고 잔존/기한 결과를 명시 기록한다. child wrapper는 57초 관측 뒤
   짧은 TERM/KILL/wait 예산을 두어 60초 목표 안에 정리하려는 구조다.

## 확인한 구조

- capability 호출은 QMP 실행 인자가 없으면 원래 QEMU로 exec하며 argv를 그대로
  전달한다. 따라서 --version의 stdout/exit를 별도로 합성하지 않는다. 실제
   passthrough 비교 결과도 후속 preflight 파일에서 stdout/returncode 일치 및
   debugger state 미생성을 확인했다.
- wrapper가 먼저 PR_SET_CHILD_SUBREAPER를 설정하고 GDB를 child로 시작한다.
  GDB가 inferior를 시작하므로 ptrace policy를 바꾸는 attach 우회가 없다.
  GDB 종료 후 입양한 inferior는 waitpid로 수거하며, GDB가 먼저 수거한 경우도
  별도 상태로 구분한다. 이는 [Linux subreaper 계약](https://www.man7.org/linux/man-pages/man2/PR_SET_CHILD_SUBREAPER.2const.html)에 부합한다.
- GDB는 공개 callback의 target-matching 조건을 검사해 첫 일치에서 읽기를
  끝내고 breakpoint 삭제/detach로 진행한다. 명시 guest memory/register 쓰기,
  callback 반환값 변경, inferior function call 또는 guest 분기 수정은 없다.
  대상 인자가 unavailable이면 오류로 기록하고 계속 성공으로 표시하지 않는다.
  host ASLR 비활성화도 요청하지 않는다.
- wrapper의 TERM/INT/HUP handler는 종료 요청을 기록하고 소유 identity가 확인된
  QEMU에 TERM으로 정규화해 전달한 뒤 필요하면 KILL한다. 같은 signal 번호를
  그대로 전달하는 구현은 아니다. PID/starttime/executable/runtime 조건을 확인해
  다른 프로세스에 signal을 보내는 범위를 제한한다.
- 상세 debugger output과 receipt는 private 경로에만 저장한다. 관측 metadata를
  읽을 때 public summary는 별도 whitelist로 선별해야 하며, 이번 보고서는 그
  원문이나 실제 인자 값을 복사하지 않는다.

검토 근거: AGENTS.md와 Build Plan BP14, private source의 process/control flow,
[Python subprocess 문서](https://docs.python.org/3/library/subprocess.html),
[GDB detach 문서](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Attach.html).
소스 변경·새 guest 실행·ptrace 정책 변경은 하지 않았다. 미해결 항목은 root와
실행 담당에게 즉시 전달했다.

## 후속 lifecycle 및 합성 근거 확인

`bp14_lifecycle.py`의 소유 session 검사, signal 직전 session/starttime 재확인,
outer subreaper 설정, leader 종료와 무관한 finally cleanup을 읽었다. 새 helper가
실제 runner의 `start_new_session=True` Popen과 absolute deadline에 연결된 것도
확인했다.

- `bp14-static-preflight.json`: Python/GDB Python AST 검사, --version stdout/
  returncode 동일, debugger state 미생성, ptrace policy 미변경, atomic write/
  transient read 처리 및 source/DWARF callback signature 대조 결과가 기록돼 있다.
  이 preflight 시점의 guest run count는 0이다.
- `bp14-cleanup-synthetic-test.json`: leader가 먼저 정상 종료하고 다른 PG에 있는
  child가 TERM을 무시하는 합성 조건에서 KILL/adopted reap, 잔존 0, 기한 내 종료를
  기록한다. elapsed=0.288초이며 실제 guest 실행을 포함하지 않는다.

**남은 범위:** wrapper 자체의 TERM/INT/HUP 처리는 확인했지만 outer runner의
직접 SIGTERM/SIGHUP에는 Python handler가 없다. 이 경우 OS 기본 종료가 Python
finally를 실행하지 않으므로 outer의 cleanup/forwarding을 보장하지 않는다.
SIGINT의 기본 KeyboardInterrupt는 해당 finally를 거친다. root와 실행 담당에게
이 차이를 전달했다. 현재 승인된 관측을 중단시키는 요청은 하지 않았으며, 직접
outer-TERM/HUP 지원은 아직 검증했다고 표시하지 않는다.

공개 callback 관측의 성공 여부, detach 이후 실제 QEMU 수거 및 원본 13개 hash
보존은 실제 실행 담당의 후속 결과로 판단한다. 이 리뷰는 그 관측 값이나 private
GDB 출력 파일을 읽거나 공개 결과에 복사하지 않았다.
