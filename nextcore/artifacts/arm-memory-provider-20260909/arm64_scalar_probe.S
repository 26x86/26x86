// Independently authored unsigned-offset integer scalar EFI fixture.
.text
.global probe_start
probe_start:
    mov x3, #0x53
    add x9, sp, #0
#if defined(PROBE_BYTE) || defined(PROBE_HALF) || defined(PROBE_WORD) || defined(PROBE_QUAD)
    sub sp, sp, #32
#if defined(PROBE_BYTE)
    mov x4, #0xff81
    strb w4, [sp, #3]
    movz x0, #0xffff, lsl #48
    ldrb w0, [sp, #3]
#if defined(PROBE_BAD_SIGN)
    ldrb w1, [sp, #3]
#else
    ldrsb x1, [sp, #3]
#endif
    ldrsb w2, [sp, #3]
    strb wzr, [sp, #4]
    ldrb w5, [sp, #4]
    cmp w5, #0
    b.ne probe_bad
#elif defined(PROBE_HALF)
    mov x4, #0x8001
    strh w4, [sp, #6]
    movz x0, #0xffff, lsl #48
    ldrh w0, [sp, #6]
    ldrsh x1, [sp, #6]
    ldrsh w2, [sp, #6]
    add x5, sp, #6
    ldrh w5, [x5]
    cmp w5, w0
    b.ne probe_bad
#elif defined(PROBE_WORD)
    mov w4, #5
    movk w4, #0x8000, lsl #16
    str w4, [sp, #12]
    movz x0, #0xffff, lsl #48
    ldr w0, [sp, #12]
    ldrsw x1, [sp, #12]
    add x2, x9, #0
#elif defined(PROBE_QUAD)
    mov x4, #5
    movk x4, #0x8000, lsl #16
    movk x4, #0x5678, lsl #32
    movk x4, #0x1234, lsl #48
    str x4, [sp, #8]
    ldr x0, [sp, #8]
    str xzr, [sp, #16]
    ldr x2, [sp, #16]
    ldr xzr, [sp, #8]
    add x1, x9, #0
#endif
    add sp, sp, #32
    add x10, sp, #0
    cmp x10, x9
    b.ne probe_bad
.global probe_success
probe_success:
    hlt #0
probe_bad:
    mov x3, #0xbad
    hlt #0
#else
    mov x0, #0x7777
    movk x0, #0xaaaa, lsl #48
    mov x1, #0x8888
    movk x1, #0xbbbb, lsl #48
    add x2, sp, #0
#if defined(PROBE_DATA_LOAD) || defined(PROBE_DATA_STORE)
    msr sctlr_el1, xzr
    add x2, sp, #1
#elif defined(PROBE_SP_LOAD) || defined(PROBE_SP_STORE)
    mov x4, #8
    msr sctlr_el1, x4
    add sp, sp, #8
#endif
.global probe_fault
probe_fault:
#if defined(PROBE_DATA_LOAD)
    ldr w0, [x2]
#elif defined(PROBE_DATA_STORE)
    strh w0, [x2]
#elif defined(PROBE_SP_LOAD)
    ldrb w0, [sp]
#elif defined(PROBE_SP_STORE)
    str x0, [sp]
#elif defined(PROBE_SIMD)
    str d0, [x2]
#elif defined(PROBE_RESERVED)
    .inst 0xf9c00040
#elif defined(PROBE_PRFM)
    prfm pldl1keep, [x2]
#else
#error A probe definition is required
#endif
    hlt #0
#endif
