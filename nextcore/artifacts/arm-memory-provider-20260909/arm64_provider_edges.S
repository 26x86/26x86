// Authored memory-service boundary fixtures, no original-image bytes.
.text
.global probe_start
probe_start:
    mov x0, #0x55
    mov x1, #0x66
    mov x3, #0x70
#if defined(PROBE_PC_ALIGNMENT)
    movz x2, #0x4000, lsl #16
    add x2, x2, #2
.global probe_fault
probe_fault:
    br x2
#elif defined(PROBE_MISSING_FETCH)
    movz x2, #0x4400, lsl #16
.global probe_fault
probe_fault:
    br x2
#else
#if defined(PROBE_TRANSPORT)
    movz x2, #0x4300, lsl #16
#else
    movz x2, #0x4400, lsl #16
#endif
#if defined(PROBE_PAIR_LOAD) || defined(PROBE_PAIR_STORE)
    sub x2, x2, #8
#endif
.global probe_fault
probe_fault:
#if defined(PROBE_PAIR_LOAD)
    ldp x0, x1, [x2], #16
#elif defined(PROBE_PAIR_STORE)
    stp x0, x1, [x2], #16
#elif defined(PROBE_LOAD)
    ldr x0, [x2]
#else
    str x0, [x2]
#endif
    hlt #0
#endif
