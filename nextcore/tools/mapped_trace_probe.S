// Independently authored mapped diagnostic. No original image bytes or ABI claim.
// x1 initially addresses Core's encoded physical boot args (revision2/version2).
.arch armv8.3-a
.text
.global _start, mapped_loop, mapped_data, mapped_failure
_start:
    ldr w0, [x1]
    mov w7, #2
    movk w7, #2, lsl #16
    cmp w0, w7
    b.ne mapped_failure
    adr x4, mapped_data
    mov x6, x4
    movk x6, #0xabfe, lsl #48
    xpaci x6
    cmp x6, x4
    b.ne mapped_failure
    mov x7, #0x7654
    pacda x6, x7
    cmp x6, x4
    b.ne mapped_failure
    mov x1, x6
    mov x3, x6
    mov x5, #0x7788
    movk x5, #0x5566, lsl #16
    movk x5, #0x3344, lsl #32
    movk x5, #0x1122, lsl #48
    // Roundtrip SP_EL1 -> SP_EL0 -> SP_EL1, including repeated selections.
    msr spsel, #0
    msr spsel, #0
    msr spsel, #1
    msr spsel, #1
    sub sp, sp, #16
    str x5, [sp]
    ldr x2, [sp]
    add sp, sp, #16
    cmp x2, x5
    b.ne mapped_failure
    // Signed byte displacement is unscaled and does not update the base.
    sub sp, sp, #16
    add x9, sp, #8
    stur x5, [x9, #-8]
    ldur x2, [x9, #-8]
    cmp x2, x5
    b.ne mapped_failure
    add x10, sp, #8
    cmp x9, x10
    b.ne mapped_failure
    add sp, sp, #16
    // General logical registers, shifted operand, W zero-extension and flags.
    mov x9, #0xf0
    mov x10, #0x0f
    orr x11, x9, x10
    mov x12, #0xff
    cmp x11, x12
    b.ne mapped_failure
    eor w14, w11, w10, lsl #4
    cmp w14, w10
    b.ne mapped_failure
    orn w13, wzr, w10
    add x14, x13, #16
    movz x15, #1, lsl #32
    cmp x14, x15
    b.ne mapped_failure
    ands xzr, x11, x10
    b.eq mapped_failure
    b.mi mapped_failure
    b.cs mapped_failure
    b.vs mapped_failure
    // Scalar writeback commits after the transfer, with byte-sized offsets.
    mov x12, sp
    str x5, [sp, #-16]!
    ldr x2, [sp], #16
    cmp x2, x5
    b.ne mapped_failure
    mov x13, sp
    cmp x13, x12
    b.ne mapped_failure
    mov x9, x4
    str x5, [x9], #8
    add x10, x4, #8
    cmp x9, x10
    b.ne mapped_failure
    ldr x2, [x9, #-8]!
    cmp x2, x5
    b.ne mapped_failure
    cmp x9, x4
    b.ne mapped_failure
    // Variable shifts mask the count, preserve NZCV and zero-extend W results.
    mov x9, #-1
    mov x10, #64
    cmp x5, x5
    lslv w11, w9, w10
    b.ne mapped_failure
    b.cc mapped_failure
    movz x12, #1, lsl #32
    add x13, x11, #1
    cmp x13, x12
    b.ne mapped_failure
    mov x9, #1
    mov x10, #65
    lslv x9, x9, x10
    cmp x9, #2
    b.ne mapped_failure
    lsrv x11, x9, x10
    cmp x11, #1
    b.ne mapped_failure
    mov x10, #63
    rorv x11, x11, x10
    cmp x11, #2
    b.ne mapped_failure
    mov w9, #0x80000000
    mov w10, #31
    asrv w11, w9, w10
    add x13, x11, #1
    cmp x13, x12
    b.ne mapped_failure
    add x8, x4, #4
mapped_loop:
    str x5, [x8]
    ldr x2, [x8]
    cmp x2, x5
    b.ne mapped_failure
    b mapped_loop
mapped_failure:
    mov x0, #0xbad
    b mapped_failure
.balign 8
mapped_data:
    .quad 0, 0
