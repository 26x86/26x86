# Bounded Original-Prefix Progress

## Current Status

The unchanged local macOS 27.0 / 26A5425a input reaches an explicitly selected
65,536-instruction budget with 11,702 completed data operations and no memory
provider error. The final request window contains successful stores at distinct
adjacent addresses. Its final store address is 17,872 bytes beyond the final
store observed at the 16,384-instruction checkpoint.

These observations show changing memory accesses in the measured windows. They
do not establish correct pointer transformations, the original entry ABI, full
kernel initialization or userspace. The owned framebuffer RGB hash still matches
an all-zero frame. Normal startup and physical desktop output remain unverified.

## Target State

Reach source-bound kernel initialization and sustained userspace with complete
platform services, persistent display and physical install/reboot evidence.
Use an observed execution requirement to choose the next implementation; a larger
instruction count is not an acceptance substitute.

## Observations and Controls

| Checkpoint | Retired instructions | Completed data operations | Provider status |
| --- | ---: | ---: | --- |
| Observed bounded prefix | 16,384 | 2,763 | No error |
| Explicit long prefix | 65,536 | 11,702 | No error |

The allocation-free observer forwards each request through the same memory
service exactly once and returns its unchanged reply. It retains only the last
64 request metadata records, without guest values or instruction words. The
16,384-instruction observed run has the same complete execution result and
configuration as its unobserved baseline. An authored EFI fixture independently
checks the 73-request total and exact retained final 64, alongside GOP readback.

The long tier requires a separate EFI build, exact `long-65536` selector,
65,536 budget and the named software profile. Existing default, tiered and deep
limits remain intact. An authored native arithmetic loop reaches the exact long
budget; the old EFI rejects it. This capability never changes normal readiness.

Two failed collection attempts are preserved. One terminated after a partial
UART error row; another stopped on transient DrvFs `ENODATA`. The host now waits
for an LF-terminated status row and retries only defined transient read errors
on the same process within the original deadline. Eleven host regressions cover
selection, video acknowledgement, fragmented rows, retry bounds and nontransient
failure. The successful original replay uses the same final EFI bytes.

[Final original-input metadata](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/original-prefix-r13-long-summary.json),
[bounded request evidence](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/memory-window-final-long-summary.json),
and [authored long-tier evidence](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/long-diagnostic/inventory.json)
preserve the distinction between execution, observation and physical boot.

## Next Execution Boundary

The current [provider loop](https://github.com/26x86/Nextcore-ISE/blob/002d2eff8b262e728224b9b039b9ffe168ed4586/runtime/jit.c#L782) generates native code and changes code-page permissions
after every successful instruction fetch. Its `compiled_blocks` counter measures
native entries, not a separate compilation statistic. Repeated PCs make a
run-local reuse investigation relevant, but any reuse must still perform fresh
instruction fetches, reply validation and data accesses. No cache speedup or
self-modifying-code correctness is claimed by the current evidence.

The [entry contract](NEXTCORE_ARM64E_ENTRY_CONTRACT.md) also distinguishes guest
self-fixups from unproven loader-side work. Do not rebase opaque pointers or
change startup registers solely to extend the trace.
