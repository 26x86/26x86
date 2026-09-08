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
.global enter_access
enter_access:
    stp x29, x30, [sp, #-16]!
    adr x9, el1_entry
    msr elr_el2, x9
    mov x9, #0x3c5
    msr spsr_el2, x9
    eret
el1_entry:
    cbnz x2, dispatch
    adr x9, dispatch
    msr elr_el1, x9
    mov x9, #0x3c0
    msr spsr_el1, x9
    eret
dispatch:
    cmp x1, #1
    b.eq store64
    cmp x1, #2
    b.eq fetch
    cmp x1, #3
    b.eq pair_load32
    cmp x1, #4
    b.eq pair_store32
    cmp x1, #5
    b.eq pair_load64
    cmp x1, #6
    b.eq pair_store64
.global load64
load64:
    ldr x2, [x0]
    b no_fault
.global store64
store64:
    str xzr, [x0]
    b no_fault
.global pair_load32
pair_load32:
    ldp w2, w4, [x0]
    b no_fault
.global pair_store32
pair_store32:
    stp wzr, wzr, [x0]
    b no_fault
.global pair_load64
pair_load64:
    ldp x2, x4, [x0]
    b no_fault
.global pair_store64
pair_store64:
    stp xzr, xzr, [x0]
    b no_fault
fetch:
    blr x0
no_fault:
    svc #0
    b .
el1_sync:
    mrs x5, spsr_el1
    mrs x6, CurrentEL
    mrs x0, esr_el1
    lsr x9, x0, #26
    cmp x9, #0x15
    b.eq no_exception
    mrs x1, far_el1
    mrs x2, elr_el1
    mov x3, #1
    hvc #0
    b .
no_exception:
    mov x0, #0
    mov x1, #0
    mov x2, #0
    mov x3, #0
    hvc #0
    b .
el2_sync:
    mrs x9, esr_el2
    lsr x9, x9, #26
    cmp x9, #0x16
    b.ne fatal
    adrp x9, abort_result
    add x9, x9, :lo12:abort_result
    stp x0, x1, [x9]
    stp x2, x3, [x9, #16]
    stp x5, x6, [x9, #32]
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
