# BP14 same-event translation result — 2026-09-07

Current state: BP13 reached the Stage2 prompt, transferred five restore roles
and received `bootx` ACK, then encountered a firmware Data Abort. Its fault VA
only numerically overlapped a gap in the public physical map. Desired state:
read the actual VA/PA/access/MMU/result arguments of that same failed QEMU
transaction without changing the guest, a device result or the source media.

## Confirmed boundary

The successful BP14 observation captured exactly one matching callback in
the public `arm_cpu_do_transaction_failed` function. All requested arguments
were available. The actual VA and PA were equal for this access: CPU 0 made
a four-byte `MMU_DATA_LOAD`, with core `mmu_idx=0` and result
`MEMTX_DECODE_ERROR`. The translated PA matches no region in the captured
runtime flatview; its 25 range rows were parsed and checked. It also matches
no declared region in the current VMApple map. Thus this event is now
localized to a physical-address decode gap in this QEMU model, beyond BP13's
VA-only comparison. **The expected device and its behavior remain unknown.**

The public callback signature and implementation are at
`target/arm/tcg/tlb_helper.c:316`. `include/exec/memattrs.h:89` defines this
result as an address decode failure, distinct from a device error or denied
access. `target/arm/mmuidx.h:142` and `target/arm/internals.h:1019` map core
index zero to A-profile E10_0. Its documented TLB regime combines EL0 access
through EL1&0 stage 1+2; this index does not prove that each translation stage
was enabled. Those enable bits were not separately observed.

GDB detached immediately after the one matching event. No guest register,
instruction, firmware byte, device return value or execution branch was
modified. Live iBSS/iBEC and LocalPolicy requests succeeded, original payloads
were preserved, and the guest again reached the Stage2 prompt, five restore
roles and `bootx` ACK. It subsequently emitted a firmware panic. Darwin and
userspace markers remain absent; **macOS boot is not verified**.

Precise addresses, registers, callback arguments and debugger output remain
private. The public receipt contains only mapping relationships, access
categories, phase outcomes and public-source pointers. No speculative device
response or ASR implementation follows from this result.

## Two attempts, one actual guest observation

Attempt 1 (`normal-recovery-translation-observation.json`) stopped in QEMU
argument parsing before QMP, TSS, DFU or guest execution. GDB's shell-escaped
`--args` string was used after disabling its matching startup-shell behavior,
which changed the JSON blockdev argument. Trace and UART were empty;
callback count was zero. This was an observation-wrapper failure, not a new
guest failure. Outer time was 6.614 seconds; QEMU returned 1 and worker 2.
The original helper sources and hashes are preserved in the private
`bp14-attempt-1` snapshot and `bp14-static-preflight.json`.

Before attempt 2, a synthetic inferior confirmed exact argument round-trip
for JSON, spaces in paths, commas, backslashes and mixed quotes using GDB's
standard `--args` and matching startup behavior. `--version` still bypassed
the debugger and matched the original QEMU stdout/exit. A fresh COW/output
was used for the root-authorized continuation of the same BP14 observation.
Its runtime is `/tmp/nextcore-apls-normal-recovery-translation-b-20260907`.
`bp14b-static-preflight.json` records the helpers actually used, and their
unchanged originals are preserved in private `bp14-attempt-2`.

## Bounds, integrity and cleanup

Attempt 2 took 44.469 seconds overall. The wrapper ran for 36.354 seconds;
the normal runner's termination signal was forwarded to its adopted QEMU
child, which exited and was reaped. The worker, wrapper, GDB and QEMU were
collected. The 60-second child bound and absolute 90-second owned-session
bound were not exhausted. Process exits were zero and mean only completion
of the research run, not boot success.

An independent post-interruption readback rehashed all 13 original inputs,
manifest and helper: all matched the reviewed originals. It found no related
worker, wrapper, QEMU or GDB process remaining. Old PID numbers were checked
against experiment identity, not treated as safe kill targets if reused.
Writes remained in the fresh COWs. Both attempts' executed-helper snapshot
hashes still match their respective preflight receipts.

Pre-execution cleanup testing covered a leader that exited before an owned
child in another process group; the child ignored TERM and was killed and
reaped within the bound. After the actual run, a separate minimal follow-up
added TERM/HUP handling during the outer owned-session wait. Synthetic TERM
and HUP tests both passed with no owned child remaining. This follow-up was
**not used for either guest attempt** and was not validated by another QEMU
run. `bp14-postrun-signal-check.json` separates executed and follow-up hashes;
only `bp14b_lifecycle.py` changed after attempt 2.

The 194,205,935-byte attempt-2 trace remains preserved. Its initial 64 MiB
head/tail summary is explicitly incomplete; BP14's translation conclusion
comes from the single callback and captured flatview, not inferred complete
trace counts. No additional guest run, public product change, commit or push
was performed while completing this result.

Evidence: `bp14-same-event-transaction.json`,
`normal-recovery-translation-b-observation.json`,
`bp14-independent-postrun-check.json`, `bp14b-argv-roundtrip.json`,
`bp14-cleanup-synthetic-test.json`, and `bp14-postrun-signal-check.json`.

Decision status: BP14 completed. Preserve unknown device identity and the
observed physical decode failure; any implementation requires a separately
supported public device contract.
