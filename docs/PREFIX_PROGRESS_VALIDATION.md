# Bounded Original-Prefix Progress

## Current Status

The r29 mapped diagnostic retires 42,256,374 instructions, issues 42,256,375
fetch requests and completes 6,012,373 data operations in 151.399 seconds.
It stops with SYSTEM_REGISTER_TRAP (status 13) at MRS ID_AA64MMFR1_EL1,
a memory-model feature-identification register read. The provider reports no
error. Original input, EFI, host tools and ESP copies are preserved; QEMU exits
with code zero and is reaped. The owned 1280 by 800 framebuffer remains zero
and matches GOP. An independent calculation over its 3,072,000 zero RGB bytes
matches the recorded hash dff2e40b0a1ba325. No macOS screen has been established.

The original r29 receipt remains attributed to runtime `f2256f173ffae32924f1519ece7b1f0e4b251d6a`
and its recorded module revisions. The website package instead pins
`558865245830c4940d172b1e61f7e236ed769f86`, whose module updates correct obsolete
test-only ASID rejection and legacy MMFR0 reset-value expectations. Final NXARMJIT and NXASID rebuilds match
the previously tested binary bytes; this does not reattribute or rerun r29.


This completed run passes MMFR0 and adds five retired instructions with no new
data operations relative to r28. The elapsed time is a single-run observation,
not a benchmark. MMFR1 feature-policy qualification is the next boundary.
The software-defined Normal-NC profile, high virtual alias, canonical PAC callback
and immutable stack selection remain explicit diagnostic conditions. They do not
establish the target reset entry ABI, SPTM services, complete platform DeviceTree,
kernel initialization, userspace or physical boot.

The watchdog success marker appears twice because reporting writes to both
ConOut and Serial. The summary records the observation count and success presence
with no failure marker; it does not infer API call count from duplicate output.
The source contains one watchdog-disable call at this entry point. The authored
timer control below establishes the helper behavior. r22 completes beyond the
prior r21 termination time, but that does not by itself prove r21's cause.

[Latest r29 original-input receipt](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/original-prefix-r29-mmfr0-summary.json)
records this boundary without publishing original instruction words or addresses.
Historical r28 completed 42,256,369 instructions and 6,012,373 data operations
before the MMFR0 read. Historical r27 completed 42,256,360 instructions and 6,012,373 data operations
before the ISAR2 read. Historical r26 completed 42,255,998 instructions and 6,012,275 data operations
before the ISAR0 read. Historical r25 completed 42,255,990 instructions and 6,012,273 data operations
before the ZFR0 read. Historical r24 completed 42,255,878 instructions and 6,012,259 data operations
before LSLV. Historical r23 completed 42,255,830 instructions and 6,012,249 data operations
before post-indexed LDR. Historical r22 completed 42,252,452 instructions and 6,010,805 data operations
before register ORR. Historical r20 completed 42,252,448 instructions and 6,010,803 data operations
before an unscaled-load boundary. r21 supplied no terminal execution record.

## Authored MMFR0 and immutable ASID8 validation

The explicit MMFR0 policy is `0x0f100005`, describing this bounded EL1 memory
model: 48-bit maximum physical addresses, eight-bit ASIDs, little-endian execution
and 4 KiB/16 KiB stage-1 pages. It does not advertise 64 KiB pages, EL2/stage-2
or a secure-memory service. C API, native and reference reads use the same
constant and live EL1/HCR/SCR gate; mutation of retained storage does not create
a second feature identity.

MMFR0 tests pass 964 native assertions, 31 provider tests in each of three cache
modes and 34 reference tests. All 32 destination-register observations on actual
QEMU Cortex-A72 verify encoding/access/XZR/NZCV only: its `0x1124` differs from
this software policy. EL0 writes retain the existing known-register privilege
fault, while exact unsupported read conditions retain their bounded trap policy.
ISAR2 and ISAR0 regressions pass. These observations do not identify a physical
CPU or establish complete architecture conformance.

Both immutable profiles 1/3 admit lower-eight-bit TTBR tags with A1 selecting
the active tag for both VA regions. High tag bits and AS=1 remain rejected;
dynamic profile 2 retains ASID=0/A1=0. Independent ASID tests pass 35 provider
tests in each of three cache modes and 102 reference tests, including both
profiles, granules, lower/upper addresses, conflicting TTBR tags, cold/warm
access, context isolation and transactional rejection. Three compiled mutants
that force tag zero, ignore A1 or choose by VA region are rejected. The same
final fixture rejects the preceding fixed source. The raw generic reference
configuration API remains outside this new immutable admission claim.

A separate actual NXASID EFI probe passes 64 cases. Each performs a lower-to-upper
alias store/load, then reads MMFR0 and controls, completing nine instructions
and two data operations with full RAM/table comparisons. The preceding runtime
with the identical authored probe rejects the first tagged configuration before
guest execution. EFI readback does not itself prove internal TLB-tag selection;
the independent native getter and mutants supply that discrimination.

Ten mapped EFI checks and eight preceding-EFI controls pass; the old EFI traps
at MMFR0 after 128 retired instructions on the authored mapped input. Rebuilding
the pinned mapped and NXASID images reproduces their tested bytes. Independent
website packages have their own recorded hashes. The dynamic comparator freezes
128 runtime files and passes six captures, fourteen regressions and three
negative controls while preserving 217 prior evidence files. Normal startup,
physical display and macOS boot remain unverified. The completed r29 replay
passes MMFR0 and reaches the MMFR1 trap described above.

[Public MMFR0/ASID8 native and EFI evidence](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/mmfr0-asid8/summary.json)
contains the final 93-file evidence inventory and exact source identities.

[Published MMFR0/ASID8 contract](https://github.com/26x86/Nextcore-ISE/blob/feb09b5f1ef5eecce60120ba39e624bb020bd071/docs/MMFR0_ASID8_PROFILE.md)
records the model, unsupported controls and primary sources.

## Authored exact ISAR2 and PAC address-selection validation

The exact read-only ISAR2 MRS returns the explicit bounded scalar-profile value
zero at EL1 with live HCR/SCR zero. Native tests pass 918 assertions covering
all destinations, rejected accesses and controls changed after compilation.
Six representative timed-wait, branch-consistency, memory-copy/set and range
prefetch extension instructions remain rejected without retirement or memory
changes. The 32 actual Cortex-A72 observations report zero and match this
profile's read result; they do not establish QARMA3, floating-point or complete
architectural conformance. The reference harness passes 35 tests, and canonical
mapped provider tests pass 32 cases in each of three cache modes with equal
exposed results, requests and RAM.

Independent public Arm pseudocode review found a PAC signing address-size
selection defect shared by the previous Rust implementation and QEMU 8.2.2.
For this non-TBI baseline APA1 contract, signing selects the address size from
pointer bit 63, whereas authentication and stripping select from bit 55.
The correction changes signing only; the cipher and failure policy are preserved.

A separately built test-only APA1 QEMU model runs 48 authored inputs. During
PAC only, both address-size fields are set to the size selected by the original
pointer's bit 63; the original TCR is restored before AUT/XPAC. Guest readbacks
verify original, temporary and restored controls plus unchanged pointers,
modifiers and keys. All 288 results agree with the corrected Rust implementation;
288 real C-ABI callback cases preserve non-destination state. The frozen old
source fails the same expected values. Forty unsupported-control rows and three
invalid key indices are rejected. This is an explicitly adapted control oracle,
not an identical-state observation from stock QEMU or physical hardware.

Separate native regressions pass 125 PAC assertions and 20 M0 tests. Nine full
CPU/RAM/ordered-request-and-reply cases agree across cached, uncached and small-slot
modes. The immutable mapped profile disables address PAC, so its PACDA operation
is a no-op while XPAC remains active. These mapped regressions do not verify
active signing under that profile.

A separate actual OVMF M0/provider-v1 EFI fixture enables all four address-PAC
keys and retains the original asymmetric TCR for every operation. It checks
control and selected-key readbacks and passes all 48 inputs / 288 numeric
comparisons, with 432 data operations. The preceding EFI runs the identical
input and reaches the distinct signing assertion for zero-based row 4 after
40 data operations. Both runs complete their 65,536-instruction diagnostic
budget and are reaped; the checker distinguishes the success and failure loops
by exact registers and PC. This supplies enabled-signing evidence separately
from the disabled mapped profile. The fixture omits ISB after a preserved earlier
run trapped on that instruction; it tests synchronous M0 callback controls and
does not establish architectural barrier execution.

Normal startup and physical desktop remain unverified. The historical r28 original-input replay passed ISAR2 and reached MMFR0;
r29 now passes that read.

Ten authored mapped EFI checks pass, with eight preceding-EFI control checks
separately identifying the old ISAR2 trap. The register profile does not infer
support for extensions whose fields are zero.

[ISAR2 native and EFI receipts](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/isar2-scalar-profile/summary.json)
and [PAC oracle, M0 EFI and profile-matrix receipts](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/pac-address-selection/summary.json)
preserve the authored results and their provenance.

The updated dynamic comparator freezes 120 runtime files, passes six captured
replays, fourteen regressions and three negative controls, and preserves 187
prior evidence files. The pinned integration rebuild matches the tested EFI
bytes; website packages are independently built and have their own hashes.

[Published ISAR2 contract](https://github.com/26x86/Nextcore-ISE/blob/5cd1e44413958450875392d8a431dba15bb76f2e/docs/ISAR2_SCALAR_PROFILE.md)
and [PAC qualification contract](https://github.com/26x86/Nextcore-ISE/blob/5cd1e44413958450875392d8a431dba15bb76f2e/docs/MAPPED_PAUTH_V2.md)
record the supported feature scope and primary references.

## Authored exact ISAR0 scalar-profile validation

The exact read-only ISAR0 MRS uses an explicit scalar profile with all fifteen
extension fields absent and its reserved low nibble zero. This is not an
unknown-register fallback. Native tests pass 928 assertions, including every
destination, rejected accesses and live control changes. Sixteen representative
unsupported extension instructions are rejected with the expected exception
class and without retirement or data changes. The shared ZFR0 regression passes.

An actual QEMU cortex-a72 reports ISAR0=0x11120, whereas this software profile
returns zero. The 32 Arm observations verify encoding, access, XZR and NZCV
behavior; they do not verify equality of the hardware and software feature
values. The Rust reference harness passes 35 tests. Canonical mapped v2 provider
tests pass 32 cases in each of cached, uncached and small-slot modes with equal
exposed results, requests and RAM.

Ten authored EFI checks pass. With the same authored input, the preceding EFI
stops at the first ISAR0 read after 114 retired instructions; the new EFI
completes 65,536. This discriminates support in the fixture and is not an
original-kernel progress result. The dynamic comparator freezes 114 files and
passes six captured replays, fourteen regressions and three negative controls,
while preserving 172 historical evidence files. The integration receipt records a pinned runtime rebuild matching its tested
binary bytes; independently built website packages have their own hashes. Normal startup and physical boot remain
unverified. The historical r27 original replay passed ISAR0 and reached the ISAR2 trap;
r28 now passes that read.

[Public ISAR0 evidence](https://github.com/26x86/26x86/tree/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/isar0-scalar-profile)
records the scoped checks.

## Authored exact ZFR0 scalar-profile validation

The bounded scalar profile provides neither SVE nor SME. Its exact read-only
MRS ID_AA64ZFR0_EL1 returns zero only at EL1 with inactive HCR/SCR controls.
Unknown IDs are not blanket-zeroed; PFR0 and PFR1 remain unsupported. Zero in
ZFR0 alone is not a universal declaration that SVE is absent.

An authored QEMU 8.2.2 cortex-a72 fixture supplies 32 destination-register
results, including XZR, compared against native and Rust execution. The native
suite passes 912 assertions, including EL0/EL2/EL3, MSR and neighboring-ID
rejection, high-bit-only HCR/SCR values, direct C API output-sentinel checks and
live-control changes in both directions on the same generated block. The Rust
reference harness passes 34 tests. The canonical mapped v2 provider passes 31
tests in each of cached, uncached and small-slot modes; exposed results, ordered
requests and RAM agree across those modes. This adds no new v1-specific fixture.
Sources are preserved and the oracle process is reaped. Ten authored EFI
integration checks pass. The dynamic comparator freezes 110 files and passes
six captured replays, fourteen regressions and three negative controls while
preserving 157 historical evidence files.

[Public ZFR0 profile evidence](https://github.com/26x86/26x86/tree/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/zfr0-scalar-profile)
records these authored checks.

The separately retained max,sve=off,sme=off fixture returns nonzero ZFR0 despite
cleared PFR SVE/SME fields. That model observation and the cortex-a72 zero result
are both retained; disabling QEMU vector options is not a universal zero-value
oracle. The runtime value is an explicit restricted profile contract. These
checks do not establish the original reset ABI, SVE execution, kernel startup,
a macOS screen or physical boot. The completed r26 replay passes this exact ZFR0 read and reaches the ISAR0
feature-register trap described above.

## Authored variable-register shift validation

LSLV, LSRV, ASRV and RORV at W and X widths pass 16,464 direct native cases
with 53,246 assertions. Independently assembled instructions executed by QEMU
Arm supply 1,920 result and NZCV vectors compared against the native translator
and Rust reference. These cover every count residue, high count bits and seven
register-overlap or ZR patterns. The reference harness passes 34 tests. Ten authored EFI integration checks
pass. The dynamic comparator freezes 106 files and passes six captured replays,
fourteen regressions and three negative controls; 142 prior evidence files
remain unchanged.

[Public variable-shift evidence](https://github.com/26x86/26x86/tree/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/variable-register-shifts)
records the authored native and EFI checks.

The canonical provider harness passes 31 tests in each of cached, uncached and
small-slot modes. Its exposed execution results, ordered requests and RAM
snapshots agree between modes; this is not a full private CPU or reply-structure
comparison. Sources remain preserved and the oracle process is reaped. No
original image is used in these authored checks. The completed r25 replay passes LSLV and reaches the feature-register trap
described above. These
results do not establish kernel startup, a macOS screen or physical boot.

## Historical M=0 boundary

The r18 macOS 27.0 / 26A5425a input stopped after 1,542,930
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

[Historical r18 original-input receipt](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/original-prefix-r18-initialization-summary.json)
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
records these results separately from original-input execution.
That unaligned-transfer increment did not replay the original kernel in a new
memory environment. The subsequent authored mapped diagnostic below adds a
separate PAC callback entry point; the previous entry point remains unchanged.
The immutable profile still rejects arbitrary control changes. Normal startup
and physical macOS output remain unverified.

## Authored mapped diagnostic and PAC scope

A separately selected diagnostic now connects explicit Normal-NC mappings to
the canonical PAC callback and run-local native reuse. Profile 3 keeps address
PAC disabled; XPAC, PACGA and disabled PAC instructions are covered. This is an
authored execution capability, not evidence of original kernel initialization
or a correct reset entry ABI. **r18 remains the strongest original-input M=0 progress receipt.** The separate
r19 mapped attempt retires 13 instructions and stops with SYSTEM_REGISTER_TRAP
at SPSel, with zero completed data operations. Its owned framebuffer remains
zero and matches GOP readback at 1280 by 800. This new mapping regime did not
advance beyond r18; its retirement count is not a same-regime regression or
progress comparison. The subsequent r20 run includes verified immutable stack selection.
The [r19 mapped receipt](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/original-prefix-r19-mapped-summary.json)
records this boundary without original instruction words or addresses.

The initial independent native proof passes 31 tests in each of three separately compiled
modes: cached, uncached and 64-byte cache slots. Nine scenarios compare complete
CPU state, execution results, all RAM and ordered canonical Rust memory-service
requests/replies. Only the process-dependent callback pointer is normalized.
Real memory permissions enforce writable/executable transitions. Loop protection
calls fall from 528 to 6, and self-modifying code from 528 to 8, with equal
execution records. Coverage includes fresh-fetch failure, 65-PC eviction,
current-EL specialization, small-buffer bypass, slot-overflow fallback and both
writable and executable protection failures. The existing M=0 suite passes
20 tests; canonical PAC/native checks pass 125 assertions. Immutable-control
mutation attempts are rejected before callback state can be committed.

The independent Arm CPU capture retains 24 raw 47/48-bit vectors. Its QEMU CPU
advertises **APA5**, while the runtime implements **APA1**. Enabled sign/auth
comparison passes for **16 lower-range vectors** where the public semantics
coincide. XPAC and disabled-operation comparisons pass for **all 24 vectors**.
The **eight upper-range enabled vectors are not verified against an APA1 CPU**;
their APA5 results remain unmodified. This does not establish enabled address
PAC under mapped profile 3. The primary QEMU implementation defines the
[PAuth2 pointer-XOR distinction](https://github.com/qemu/qemu/blob/ae35f033b874c627d81d51070187fbf55f0bf1a7/target/arm/tcg/pauth_helper.c).

The authored EFI fixture passes ten aggregate checks across cached, uncached
and unobserved runs. Each retires 65,536 instructions and completes 26,207 data
operations. Cached execution uses 28 writable and 27 executable transitions,
including final writable restore, versus 65,537 and 65,536 without reuse.
Observed and unobserved execution records agree. These fixtures do not establish
original kernel initialization, complete chained-fixup traversal, userspace,
installation or a physical desktop. Normal startup remains NOT_READY.

[Mapped diagnostic summary](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/mapped-normal-profile/summary.json),
[final authored EFI receipt](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/mapped-normal-profile/efi/receipt.json), and
[independent native receipt](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/mapped-normal-profile/native/receipt.json)
record these results separately from the original r18 boundary.

## Immutable stack selection

The follow-on native suite passes **32 tests in each of three modes**, preserving
the full-state cache comparisons and existing M=0 rejection gates. Immediate EL1
stack-bank selection preserves the live SP on same-bank writes and validates
subsequent stack accesses. Authored EFI cached/uncached checks pass and the old
runtime rejects the new operation. [Stack-selection evidence](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/immutable-stack-selection/summary.json)
separates those authored checks from the r20 original-input result.

## Authored scalar unscaled memory support

Thirteen scalar integer unscaled transfer forms now support signed byte
displacements without base-register writeback. The authored native proof passes
546 cases and 2,022 assertions, including exact fault classification. Thirty-nine
independent actual Arm cases match both the native C execution and Rust reference.
The canonical service suite passes 33 tests in each of three modes; the authored
EFI consumer passes ten aggregate checks. [Unscaled scalar memory evidence](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/unscaled-scalar-memory/summary.json)
records this instruction-family scope. These authored results do not establish
original-input progress by themselves; the completed r24 receipt above records
the separate original replay.

## Firmware watchdog ownership and incomplete r21 run

The r21 attempt ended after 334.283 seconds with QEMU exit 0 and no host-requested
termination. It has no terminal execution record and therefore no verified
retired-instruction count. Its input and EFI hashes were preserved. r20 remained
the strongest completed original diagnostic at that point; no progress is inferred
from r21 elapsed time or clean process exit. Subsequent completed runs are distinguished above.

A separate authored OVMF test arms an actual two-second firmware watchdog and
stalls for three seconds. The control naturally exits before completion; the
shared production disable helper permits the completion marker. Fifteen host
checks pass, including ordered markers, reaped processes, source preservation
and an injected DEVICE_ERROR forwarded unchanged. The injected failure tests the
helper boundary, not a real firmware-error response. Baseline BOOTX64 and NXARMJIT
now request disable after service initialization and report success or the exact
failure while preserving otherwise usable operation. Host timeouts and guest
instruction budgets remain unchanged.

[Watchdog integrity evidence](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/firmware-watchdog/summary.json)
records the timer control independently. It does not establish that watchdog
expiry caused r21 or that any physical machine boots macOS. The subsequent original replays are reported separately above.

## Authored logical shifted-register support

AND, BIC, ORR, ORN, EOR, EON, ANDS and BICS now support both integer widths and
LSL, LSR, ASR and ROR operands. The native bit-origin oracle passes 64,512 cases
and 197,122 assertions. The independent Arm capture supplies 768 result/flag
vectors for comparison against native execution and the Rust reference. The
canonical regression suite passes 31 tests in each of three native modes, and
the authored mapped EFI consumer passes ten checks.

The new provider-specific comparison covers exposed execution results and ordered
memory requests, with RAM asserted unchanged; it is not a complete private-CPU
or reply snapshot comparison. ZR positions, source/destination overlap, W result
zero-extension, preserved PSTATE, flag-setting forms and undefined W shift amounts
are covered. [Logical shifted-register evidence](https://github.com/26x86/26x86/blob/codex/physical-golden-gate-20260912/nextcore/artifacts/physical-integration-20260912/logical-shifted-register/summary.json)
records the authored result separately from original kernel execution. The
completed r24 original receipt above establishes the new observed boundary;
instruction support alone is not evidence of boot progress.

## Authored scalar indexed memory support

Scalar pre-indexed and post-indexed transfers now have independent authored
coverage: 910 native cases and 3,432 assertions, 78 actual Arm comparisons against
both native C and Rust execution, 35 canonical provider tests in each of three
modes, and ten authored EFI consumer checks. The immutable dynamic-comparison
freeze contains 102 files and preserves six captured Arm replays, fourteen
regressions and three negative controls. These are instruction and integration
checks, not original-input progress or physical boot evidence. The completed r24 receipt above records the separate original replay.

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
600-second timeout remains a hard limit. Historical r18 stopped at the alignment
fault; r20 stopped at an unscaled load, r22 at register ORR, and r23 at
post-indexed LDR.
These runs do not reach the requested maximum, which is not their retirement count.
