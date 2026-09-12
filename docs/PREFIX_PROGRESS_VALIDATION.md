# Bounded Original-Prefix Progress

## Current Status

The unchanged local macOS 27.0 / 26A5425a input now stops after 1,542,930
retired instructions with a guest data-alignment fault, before the explicitly
selected initialization budget of 67,108,864. It completes 208,610 data
operations; the memory provider itself reports no error.

The faulting instruction is an ordinary 64-bit scalar load from an address that
is four-byte aligned but not eight-byte aligned. Static input metadata identifies
that location as chained-fixup node 51,889, immediately after the two nodes in
the final successful store window. This binds the next boundary to an actual
memory access rather than an exhausted instruction limit.

The selected M=0, HCR=0 memory profile requires Device-nGnRnE natural alignment.
Its fault must not be removed simply to extend execution. Establish the target's
entry memory regime and supply a supported, validated profile. Normal startup,
complete fixup traversal and userspace remain unverified. The owned framebuffer
still matches an all-zero frame.

[Latest original-input receipt](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/original-prefix-r18-initialization-summary.json)
and [fault membership](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/original-chain-fault-membership-summary.json)
retain the distinction between a completed diagnostic and a booted OS.

## Target State

Reach source-bound kernel initialization and sustained userspace with complete
platform services, persistent display and physical install/reboot evidence.
Use an observed execution requirement to choose the next implementation; a larger
instruction count is not an acceptance substitute.

## Explicit Normal-memory unaligned support

An independently selected immutable profile 3 now provides Normal-NC mappings
with SCTLR.A clear. Existing M=0 Device alignment and strict mapped profile 1
remain unchanged. The new path validates each transferred byte before any store
or register update, including adjacent virtual pages with nonadjacent backing.

The actual native C/Rust suite passes 23 stage-1 tests and 20 existing M=0 tests.
New coverage includes 48 successful scalar/pair transfers, 20 precise second-page
failures without partial mutation, PC/SP checks and fabricated-reply rejection.
Three separately compiled defective variants are rejected. Final committed EFI
sources pass 152 authored OVMF cases, including 44 new unaligned success/failure
cases across 4 KiB/16 KiB mappings and both virtual-address halves. The receipt
reader passes five tests and module inventories match actual committed Git bytes.

[Authored profile receipt](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/unaligned-normal-profile/summary.json)
records these results separately from the unchanged original-input boundary above.
This increment does not replay the original kernel in a new environment. That
requires explicit entry mappings and mapped pointer authentication; the current
immutable runner has no PAC callback and cannot supply later arbitrary control
changes. Normal startup and physical macOS output remain unverified.

## Observations and Controls

| Checkpoint | Retired instructions | Completed data operations | Provider status |
| --- | ---: | ---: | --- |
| Observed bounded prefix | 16,384 | 2,763 | No error |
| Explicit long prefix | 65,536 | 11,702 | No error |
| Initialization diagnostic | 1,542,930 | 208,610 | No provider error; guest alignment fault |

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

## Run-local Native Reuse

The v1 memory provider now reuses native entries within one run, keyed by PC,
freshly fetched instruction word and current EL. Every iteration still fetches
through the memory service. Small buffers bypass the cache; slot overflow
invalidates all entries and retries with the original full buffer.

Thirteen independent native cases compare complete CPU/result bytes, entire RAM
and ordered requests/replies against a separately compiled uncached variant.
Self-modifying code, PC/EL keys, eviction, malformed fetches, data faults, small
buffers and protection failures pass. Five compiled semantic mutants are
rejected. The unchanged dynamic backend also reproduces six captured Arm cases
and fourteen comparator regressions against an immutable 83-file source freeze.

Final EFI variants pass the authored framebuffer and 65,536-step BFM consumers.
The latter requires 13 executable transitions with reuse versus 65,536 without
reuse, with one final writable restore and no protection failures. The framebuffer
consumer retains exact full GOP RGB readback. The native-entry counter still
counts executions, not translations.

The final original-input comparison preserves the complete reported execution
record and last 64 request metadata entries. Both variants retire 65,536
instructions and complete 11,702 data operations. Executable transitions fall
from 65,536 to 283, with 284 writable transitions including restore and no
protection failures. The single serial runs took 57.754 seconds uncached and
23.868 seconds cached, including staging, UART and GOP; this is not a benchmark
or a guaranteed speedup. Complete original guest RAM was not compared.

[Authored cache evidence](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/provider-cache/inventory.json)
and the [original-prefix comparison](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/original-prefix-cache-comparison.json)
separate test coverage from physical acceptance.

## Next Execution Boundary

Normal startup remains NOT_READY. Source-bound kernel initialization, complete
platform services, persistent presentation, installation and physical reboot
remain required. The framebuffer remains all zero in the original prefix.
The [entry contract](NEXTCORE_ARM64E_ENTRY_CONTRACT.md) distinguishes guest
self-fixups from unproven loader-side work. Do not rebase opaque pointers or
change startup registers solely to extend the trace.

## Explicit initialization bound

The new Core API, separate EFI build and host selector require the exact
initialization tier, budget and named profile. Twenty-four Core tests, fourteen
host tests and no_std UEFI compilation pass. An authored BFM loop executes the
full 67,108,864 steps in the final EFI and preserves expected state and inputs;
the old build rejects the new selector before guest entry. The unchanged
600-second timeout remains a hard limit. The original input stops earlier at the
reported alignment fault; the requested maximum is not its retirement count.
