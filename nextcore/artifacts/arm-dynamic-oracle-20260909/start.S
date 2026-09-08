.section .text.start,"ax"
.global _start
_start:
    mrs x0, CurrentEL
    cmp x0, #8
    b.ne fatal
    ldr x0, =el2_stack_top
    mov sp, x0
    mov x0, #(1 << 31)
    msr hcr_el2, x0
    msr sctlr_el2, xzr
    adr x0, el2_vectors
    msr vbar_el2, x0
    adr x0, el1_vectors
    msr vbar_el1, x0
    ldr x0, =el1_stack_top
    msr sp_el1, x0
    isb
    bl oracle_main
fatal:
    mov x0, #0x20
    adr x1, failed_exit
    hlt #0xf000
    b .
.balign 8
failed_exit: .quad 0x20026, 1
.global enter_transition
enter_transition:
    stp x29, x30, [sp, #-16]!
    msr elr_el2, x0
    mov x9, #0x3c5
    msr spsr_el2, x9
    mov x0, x1
    mov x1, x2
    mov x2, x3
    mov x10, #0
    mov x11, #0
    mov x12, #0
    mov x13, #0
    mov x14, #0
    eret
el1_sync:
    mrs x4, esr_el1
    mrs x5, far_el1
    mrs x6, elr_el1
    mrs x7, spsr_el1
    mov x15, #1
    hvc #0x35
    b .
el2_sync:
    mrs x9, esr_el2
    lsr x16, x9, #26
    cmp x16, #0x16
    b.ne fatal
    and x9, x9, #0xffff
    cmp x9, #0x35
    b.eq capture
    cmp x9, #0x34
    b.ne fatal
    mov x4, #0
    mov x5, #0
    mov x6, #0
    mrs x7, spsr_el2
    mov x15, #0
capture:
    adrp x9, abort_result
    add x9, x9, :lo12:abort_result
    stp x4, x5, [x9]
    stp x6, x15, [x9, #16]
    stp x7, x10, [x9, #32]
    stp x11, x12, [x9, #48]
    stp x13, x14, [x9, #64]
    mrs x16, sctlr_el1
    mrs x17, elr_el2
    stp x16, x17, [x9, #80]
    mrs x16, CurrentEL
    str x16, [x9, #96]
    ldp x29, x30, [sp], #16
    ret
.balign 2048
el1_vectors:
.rept 16
    b el1_sync
    .balign 128
.endr
.balign 2048
el2_vectors:
.rept 16
    b el2_sync
    .balign 128
.endr
.section .bss
.balign 16
el2_stack: .skip 32768
el2_stack_top:
el1_stack: .skip 32768
el1_stack_top:
