# A64 startup execution coverage audit

## Current Status and Scope

Read-only dispatch audit of published ISE
`a8a06dad15449b15ffb2383934f6a4239a54327f`. This is a source inventory,
not a complete architecture conformance test or an operating-system boot claim.
Priority reflects implementation reuse, not frequency in any private input.

## Remaining basic families

| Family | Published snapshot status | Main integration boundary |
| --- | --- | --- |
| Logical shifted-register | Only native MOV/ORR-ZR-LSL0 alias; general AND/ORR/EOR/ANDS and inverted operands absent | Native dispatch, reference execution, width/NZCV handling |
| Scalar signed imm9 memory | Unscaled and scalar pre/post-index absent; pair pre/post-index does not provide this | Private memory shape, native/provider address and writeback commit, reference memory |
| SBFM/BFM/EXTR | Snapshot lacked all three; BFM is now integrated at 002d2ef, SBFM/EXTR remain absent | Bitmask decode and native/reference result generation |
| Variable shifts and rotate | LSLV/LSRV/ASRV/RORV absent | Native/reference dispatch |
| Carry arithmetic | ADC/ADCS/SBC/SBCS absent | Carry input and width-specific NZCV |
| Literal loads | Integer LDR/LDRSW literal absent; ADR/ADRP only form addresses | PC-relative address plus precise memory access |
| Divide and bit operations | SDIV/UDIV, CLZ/CLS/RBIT/REV absent | Native/reference dispatch |
| Exclusive and ordered memory | Reference has limited single-core exclusive/barrier behavior; native/provider transaction path absent | Reservation, access ordering and provider semantics; separate scope required |

MADD/MSUB and BFM are now integrated and independently tested. Long and high-half multiplication
are distinct encodings and must not be inferred from ordinary multiply support.

## Existing support to preserve

Both paths have logical immediate, CCMP/CCMN register and immediate, conditional
selection, ADD/SUB immediate/shifted/extended, UBFM and test-bit branches.
Integer pair W/X offset/pre/post and scalar unsigned/register-offset memory
exist; non-temporal pair, LDPSW and SIMD are separate cases.

## Reference parity limitations

The snapshot's reference path lacks native MOVN, ADR/ADRP, MOV-register alias,
B.cond and BL-immediate behavior. Independent architectural expected values,
not unverified reference equivalence, must determine new instruction tests.

Two concrete reference concerns were reproduced in an isolated snapshot and
repaired in the following integration: W CBZ/CBNZ observed upper register bits,
and register-branch decoding was broader than native BR/BLR/RET validation.
Five new regressions and the combined 113-test preOS suite pass. The reference
now matches the native profile's Rn31 rejection; this is a profile restriction,
not an architectural prohibition. Architectural Rn31 reads XZR, never SP.
The independent native/reference comparison receipt records this repair's
separate source scope; it does not close the other parity gaps listed above.

## Target State

Even after these basic instruction gaps are closed, validated target entry/services,
complete platform data, sustained kernel initialization, userspace and actual
physical display/input remain separate acceptance boundaries.

The latest BFM EFI consumer passes its exact 64-instruction contract. The local
original prefix reaches the 16384 diagnostic budget with 2763 completed data
operations. This does not prove normal startup or forward OS progress. The j274
manifest has no SPTM/TXM roles; the trace profile does not validate target ABI.
