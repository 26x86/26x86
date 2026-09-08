# A64 conditional comparison: native and reference contract

## Scope and primary definitions

The native and reference decoders now support the standard CCMP/CCMN family:
register and immediate forms, in both 32-bit and 64-bit widths, as generated
x86 arithmetic with a reference interpreter implementation. This is a generic
ISA extension. No original operating-system instruction or operand is used in
the implementation or tests.

The operation and encoding definitions are Arm's A64 ISA pages for CCMP and
CCMN, register and immediate:
[Arm A64 ISA, 2025-06](https://documentation-service.arm.com/static/685eb35c3cb5b729562ba389).
The exact condition predicate is `ConditionHolds` in the shared pseudocode,
printed page3383:
[Arm A64 ISA and shared functions](https://documentation-service.arm.com/static/6023d61995978b529036da45).
These public definitions specify subtraction for CCMP, addition for CCMN,
32/64-bit source views, an unsigned five-bit immediate, a four-bit fallback
NZCV, and flags-only results. Conditions14 and15 are both always true; NV is
not a never-execute condition in this A64 predicate. Register31 reads zero,
including both register operands; SP is not a source in this instruction.

## Decoder and commit contract

The family has fixed bits selected by `(word & 0x3fe00410)==0x3a400000`.
Bit31 chooses width; bit30 chooses subtraction; bit11 selects immediate rather
than register. Bits20:16 hold the register or unsigned immediate, bits15:12
the condition, bits9:5 the first register and bits3:0 fallback NZCV. Bit29(S)
must be1, bits10(o2) and4(o3) must be0; the mask enforces those fixed fields.
Other surrounding instruction families must retain their existing decoding.

Evaluate the condition using the incoming PSTATE NZCV. If true, compute flags
from width-limited A+B (CCMN) or A-B (CCMP). N is the result sign, Z is zero,
C is unsigned carry for addition and absence of borrow for subtraction, and
V is signed overflow. The incoming C flag is never an arithmetic carry input.
If false, replace all four NZCV bits with the encoded fallback. Other PSTATE
bits, all source/general registers and SP remain unchanged. A successful
instruction advances PC by4 and retires once. There is no memory access,
callback, architectural exception or destination register for this family.

The native implementation reuses existing condition tests and x86 flag packing
where practical. It must leave comparison and replacement in the generated
block, rather than introducing a Rust arithmetic callback. The M=0 provider
path uses the same translator. Existing MMU gates, record layouts, W^X,
interrupt boundaries and retirement rules remain unchanged. Unsupported
fixed-bit encodings remain undefined and cannot partially alter NZCV.

## Validation contract

An authored assembly oracle uses LLVM's assembler mnemonics and executes on an
independent AArch64 CPU model. Its expected results are computed separately in
Python with bounded integer arithmetic. It covers every condition against all
16 incoming NZCV values, both arithmetic operations/operand forms/widths,
carry/overflow/zero boundaries, every immediate0..31 and fallback0..15,
zero-register sources and upper-half contamination of W sources. Source
registers and SP are checked after execution. The assembler must reject SP
syntax. Negative controls deliberately misinterpret NV and corrupt expected
NZCV; each must fail, with canonical source hashes preserved.

Native and Rust reference tests cover those semantics plus invalid encodings,
complete PSTATE/register preservation, actual generated-block counts and
provider integration. Runtime source lives only in a new worktree based on
the parent's immutable BP30+MMU commit. No memory-provider, MMU or external ABI
changes belong to this extension.

## Reproduction and results

```sh
python3 tools/probe_conditional_compare.py --work-dir /path/to/arm-oracle --output /path/to/arm-oracle.json
python3 tools/probe_efi_native_pauth.py --output /path/to/native.json
python3 tools/probe_efi_memory_provider.py --work-dir /path/to/provider --output /path/to/provider.json
```

The independent Arm oracle passes3,668 cases. The same generated fixture
fails when its expected semantics incorrectly make NV false, and fails when
an expected NZCV bit is corrupted. LLVM rejects the four deliberate SP,
out-of-range immediate and out-of-range fallback syntax cases. This oracle
uses no runtime decoder or original operating-system bytes.

The native C matrix passes34,264 cases with137,070 assertions. It includes
all condition/incoming/fallback flag combinations across eight variants,
every immediate, arithmetic boundaries and zero-register operands. The
corresponding Rust matrix and invalid-encoding tests pass, and the complete
canonical Rust reference suite passes93 tests. Native tests verify upper
PSTATE bits and every source register remain unchanged. A multi-instruction
native block chains true/false/NV comparisons into a conditional branch and
checks the committed PC, flags, retirement and block count.

The M=0 provider proof passes12 tests including an actual generated CCMP/CCMN
chain between Rust instruction-fetch callbacks; it issues no data callbacks
for these instructions. The service's five tests and its provider-bypass
negative control also pass unchanged. All11 legacy/native proof programs
pass, including the complete existing B.cond predicate regression after its
emitter was factored into the shared condition helper.

A separate external copy of the native emitter deliberately made condition15
false. `test_conditional_jit.c` rejected it through the exact PSTATE assertion.
The canonical source hash remained unchanged. Actual EFI integration and the
next private operating-system diagnostic are subsequent checks, not implied
by these host-native results. No data-independent-timing guarantee is added.
