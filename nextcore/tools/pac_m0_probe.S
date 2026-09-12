// Authored enabled-PAC EFI fixture. The checker generates the vector table
// exclusively from the separately qualified APA1 adapted-control oracle.
// Here every PAC executes under the ORIGINAL asymmetric TCR, without adaptation.
.arch armv8.3-a
.text
.global _start
_start:
    movz x13, #0x1357
    movk x13, #0x2468, lsl #16
    movk x13, #0x369c, lsl #32
    movk x13, #0x48ad, lsl #48
    movz x14, #0xeca8
    movk x14, #0xdb97, lsl #16
    movk x14, #0xc963, lsl #32
    movk x14, #0xb752, lsl #48
    msr APIAKeyLo_EL1, x13
    msr APIAKeyHi_EL1, x14
    msr APIBKeyLo_EL1, x13
    msr APIBKeyHi_EL1, x14
    msr APDAKeyLo_EL1, x13
    msr APDAKeyHi_EL1, x14
    msr APDBKeyLo_EL1, x13
    msr APDBKeyHi_EL1, x14
    // M remains zero; enable IA, IB, DA and DB. All transfers are aligned.
    movz x12, #0x2800
    movk x12, #0xf8d0, lsl #16
    msr SCTLR_EL1, x12
    // M0 PAC callbacks commit control writes synchronously; this fixture does
    // not claim architectural barrier execution or enable address translation.
    adr x20, pac_vectors
    mov x21, #48
    mov x22, #0
    mov x23, #0
    mov x2, #0x9876
pac_next:
    ldr x10, [x20]
    ldr x1, [x20, #8]
    ldr x6, [x20, #16]
    msr TCR_EL1, x10
    mov x24, #6
    mrs x11, TCR_EL1
    cmp x11, x10
    b.ne pac_fail
    mov x24, #7
    mrs x11, SCTLR_EL1
    cmp x11, x12
    b.ne pac_fail
    cmp x6, #0
    b.eq pac_ia
    cmp x6, #1
    b.eq pac_ib
    cmp x6, #2
    b.eq pac_da
    b pac_db

.macro OPERATIONS label, lo, hi, pac, aut, xpac
\label:
    mov x24, #8
    mrs x11, \lo
    cmp x11, x13
    b.ne pac_fail
    mov x24, #9
    mrs x11, \hi
    cmp x11, x14
    b.ne pac_fail
    mov x3, x1
    \pac x3, x2
    mov x4, x3
    \aut x4, x2
    mov x5, x1
    \xpac x5
    mov x7, x3
    \xpac x7
    eor x8, x3, #0x0040000000000000
    \aut x8, x2
    mov x9, x1
    \aut x9, x2
    b pac_compare
.endm
OPERATIONS pac_ia, APIAKeyLo_EL1, APIAKeyHi_EL1, pacia, autia, xpaci
OPERATIONS pac_ib, APIBKeyLo_EL1, APIBKeyHi_EL1, pacib, autib, xpaci
OPERATIONS pac_da, APDAKeyLo_EL1, APDAKeyHi_EL1, pacda, autda, xpacd
OPERATIONS pac_db, APDBKeyLo_EL1, APDBKeyHi_EL1, pacdb, autdb, xpacd

.macro CHECK reg, offset, number
    mov x24, #\number
    mov x11, \reg
    ldr x10, [x20, #\offset]
    cmp x11, x10
    b.ne pac_fail
    add x23, x23, #1
.endm
pac_compare:
    CHECK x3, 24, 0
    CHECK x4, 32, 1
    CHECK x5, 40, 2
    CHECK x7, 48, 3
    CHECK x8, 56, 4
    CHECK x9, 64, 5
    add x20, x20, #72
    add x22, x22, #1
    subs x21, x21, #1
    b.ne pac_next
    movz x0, #0x4143
    movk x0, #0x50, lsl #16
    mov x1, x22
    mov x2, x23
    mov x3, #1
.global pac_success_loop
pac_success_loop:
    b pac_success_loop
pac_fail:
    mov x0, #0xbad
    mov x1, x22
    mov x2, x24
    mov x3, x11
.global pac_failure_loop
pac_failure_loop:
    b pac_failure_loop
.balign 8
pac_vectors:
.include "pac_m0_vectors.inc"
