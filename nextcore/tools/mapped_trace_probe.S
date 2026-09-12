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
