// Independently authored architectural fixture; no original-image instructions.
.text
.global probe_start
probe_start:
    mov x3, #0x31
    add x2, sp, #0
#if defined(PROBE_DATA_STORE) || defined(PROBE_DATA_LOAD)
    mov x0, #0x7777
    movk x0, #0xaaaa, lsl #48
    mov x1, #0x8888
    movk x1, #0xbbbb, lsl #48
    mov x4, #0
    msr sctlr_el1, x4
    add x2, sp, #1
.global probe_fault
probe_fault:
#if defined(PROBE_DATA_LOAD)
    ldp w0, w1, [x2, #-8]!
#else
    stp x0, x1, [x2, #-16]!
#endif
    hlt #0
#elif defined(PROBE_INVALID_PAIR)
    add x0, sp, #0
    mov x1, #0x8888
.global probe_fault
probe_fault:
    // STP x0,x1,[x0,#16]! selects UNDEFINED for base/source overlap.
    .inst 0xa9810400
    hlt #0
#elif defined(PROBE_SP_STORE) || defined(PROBE_SP_LOAD)
    mov x0, #0x7777
    mov x1, #0x8888
    mov x4, #8
    msr sctlr_el1, x4
    add sp, sp, #8
.global probe_fault
probe_fault:
#if defined(PROBE_SP_LOAD)
    ldp x0, x1, [sp, #-8]!
#else
    stp x0, x1, [sp, #-8]!
#endif
    hlt #0
#else
    mov x4, #0x1111
    movk x4, #0x2222, lsl #16
    movk x4, #0x3333, lsl #32
    movk x4, #0x4444, lsl #48
    mov x5, #0x5555
    movk x5, #0x6666, lsl #16
    movk x5, #0x7777, lsl #32
    movk x5, #0x8888, lsl #48
    stp x4, x5, [sp, #-32]!
    ldp x0, x1, [sp]
    cmp x0, x4
    b.ne probe_bad
    cmp x1, x5
    b.ne probe_bad
    stp x4, x5, [sp, #16]
    ldp x0, x1, [sp, #16]!
    stp x4, x5, [sp], #-16
    cmp x0, x4
    b.ne probe_bad
    cmp x1, x5
    b.ne probe_bad
    stp w4, w5, [sp, #16]
    ldp w6, w7, [sp, #16]
    and x8, x4, #0xffffffff
    cmp x6, x8
    b.ne probe_bad
    and x8, x5, #0xffffffff
    cmp x7, x8
    b.ne probe_bad
    stp w6, w7, [sp, #-16]!
    stp w6, w7, [sp], #16
    ldp w8, w9, [sp, #-16]!
    cmp x8, x6
    b.ne probe_bad
    cmp x9, x7
    b.ne probe_bad
    ldp w8, w9, [sp], #16
    cmp x8, x6
    b.ne probe_bad
    cmp x9, x7
    b.ne probe_bad
    ldp x0, x1, [sp], #32
    add x10, sp, #0
    cmp x10, x2
    b.ne probe_bad
.global probe_success
probe_success:
    hlt #0
probe_bad:
    mov x3, #0xbad
    hlt #0
#endif
