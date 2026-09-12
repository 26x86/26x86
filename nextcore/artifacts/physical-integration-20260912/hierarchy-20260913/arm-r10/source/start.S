.section .text.boot
.global _start
_start:
    ldr x0, =stack_top
    mov sp, x0
    ldr x0, =vectors
    msr vbar_el1, x0
    isb
    bl oracle_main
    mov x0, #0x6a1
1:  b 1b

.text
.global oracle_ret
oracle_ret:
    ret
.global execute_access
// x0: target, x1: read/write/fetch, x2: EL, x3: record.
execute_access:
    stp x19, x20, [sp, #-32]!
    str x30, [sp, #16]
    adr x19, access_done
    mov x20, x3
    mov x4, #0
    mov x5, #0x6789
    cmp x2, #0
    b.ne privileged_access
    adr x9, unprivileged_access
    msr elr_el1, x9
    mov x9, #0x3c0
    msr spsr_el1, x9
    eret
privileged_access:
    cmp x1, #0
    b.eq privileged_read
    cmp x1, #1
    b.eq privileged_write
.global privileged_fetch
privileged_fetch:
    blr x0
    b access_done
.global privileged_read
privileged_read:
    ldr x4, [x0]
    b access_done
.global privileged_write
privileged_write:
    str x5, [x0]
    b access_done
unprivileged_access:
    cmp x1, #0
    b.eq unprivileged_read
    cmp x1, #1
    b.eq unprivileged_write
.global unprivileged_fetch
unprivileged_fetch:
    blr x0
    svc #0
.global unprivileged_read
unprivileged_read:
    ldr x4, [x0]
    svc #0
.global unprivileged_write
unprivileged_write:
    str x5, [x0]
    svc #0
.global access_done
access_done:
    str x4, [x20, #32]
    ldr x30, [sp, #16]
    ldp x19, x20, [sp], #32
    ret

.balign 2048
vectors:
.rept 16
    b exception_handler
    .balign 128
.endr
exception_handler:
    mrs x9, esr_el1
    str x9, [x20, #8]
    mrs x10, far_el1
    str x10, [x20, #16]
    mrs x10, elr_el1
    str x10, [x20, #24]
    lsr x9, x9, #26
    cmp x9, #0x15
    b.eq 2f
    str xzr, [x20]
2:  msr elr_el1, x19
    mov x9, #0x3c5
    msr spsr_el1, x9
    eret

.section .bss
.balign 16
stack_bottom: .skip 16384
stack_top:
