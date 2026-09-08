// Independent ARM payload: reads real boot_args and writes results/pixels.
.text
.global _start
_start:
    ldr x1, [x0]
    ldr x3, [x0, #96]
    movz x2, #0
    movk x2, #0x4001, lsl #16
    str x1, [x2]
    str x3, [x2, #8]
    ldr x4, [x0, #16]
    str x4, [x2, #16]
    ldr x4, [x0, #1144]
    str x4, [x2, #24]
#ifdef NEXTCORE_PAC
    movz x9, #0x8000, lsl #16
    msr sctlr_el1, x9
    movz x9, #16
    msr tcr_el1, x9
    movz x9, #0x1357
    movk x9, #0x2468, lsl #16
    movk x9, #0x369c, lsl #32
    movk x9, #0x48ad, lsl #48
    msr apiakeylo_el1, x9
    movz x9, #0xeca8
    movk x9, #0xdb97, lsl #16
    movk x9, #0xc963, lsl #32
    movk x9, #0xb752, lsl #48
    msr apiakeyhi_el1, x9
    movz x8, #0x130
    movz x9, #0x9876
    pacia x8, x9
    str x8, [x2, #32]
    autia x8, x9
    str x8, [x2, #40]
#endif
    movz x6, #0
    movk x6, #0x4003, lsl #16
    movz x7, #0x2233
    movk x7, #0x0011, lsl #16
    movk x7, #0x2233, lsl #32
    movk x7, #0x0011, lsl #48
    str x7, [x6]
    str x7, [x6, #8]
    str x7, [x6, #16]
    str x7, [x6, #24]
    str x7, [x6, #32]
    str x7, [x6, #40]
    str x7, [x6, #48]
    str x7, [x6, #56]
    hlt #0
#ifdef NEXTCORE_PAC
identity: .asciz "NEXTCORE_AUTHORED_ARM64E_JIT_PAC_V1"
#else
identity: .asciz "NEXTCORE_AUTHORED_ARM64_JIT_V1"
#endif
.balign 4
