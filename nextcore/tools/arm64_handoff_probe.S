// Independently authored AArch64 payload, containing no vendor instructions.
// Fixed QEMU virt platform and fixture geometry; failures exit independently.
.text
.global _start
_start:
    mov x20, x0
    adr x0, entry_message
    bl puts
    mrs x3, CurrentEL
    cmp x3, #4
    b.ne fail_cpu
    mrs x3, sctlr_el1
    ldr x4, =0x1005
    tst x3, x4
    b.ne fail_cpu
    mrs x3, daif
    and x3, x3, #0x3c0
    cmp x3, #0x3c0
    b.ne fail_cpu
    mov x3, sp
    tst x3, #15
    b.ne fail_cpu
    ldr x4, =0x42024000
    cmp x3, x4
    b.ne fail_cpu
    adr x0, cpu_message
    bl puts
    ldr x3, =0x4200c000
    cmp x20, x3
    b.ne fail_args
    ldr w3, [x20]
    ldr w4, =0x00020002
    cmp w3, w4
    b.ne fail_args
    ldr x3, [x20, #8]
    ldr x4, =0xfffffe0000000000
    cmp x3, x4
    b.ne fail_args
    ldr x3, [x20, #16]
    mov x4, #0x40000000
    cmp x3, x4
    b.ne fail_args
    ldr x3, [x20, #24]
    mov x4, #0x20000000
    cmp x3, x4
    b.ne fail_args
    ldr x3, [x20, #32]
    ldr x4, =0x42024000
    cmp x3, x4
    b.ne fail_args
    ldr w3, [x20, #108]
    mov w4, #0x762d
    cmp w3, w4
    b.ne fail_args
    ldr x3, [x20, #1136]
    cbnz x3, fail_args
    ldr x3, [x20, #1144]
    mov x4, #0x20000000
    cmp x3, x4
    b.ne fail_args
    adr x0, args_message
    bl puts
    // The wire DT pointer is a KVA. Translate with actual boot argument bases.
    ldr x21, [x20, #96]
    ldr x3, [x20, #8]
    sub x21, x21, x3
    ldr x3, [x20, #16]
    add x21, x21, x3
    ldr x4, =0x42010000
    cmp x21, x4
    b.ne fail_dt
    ldr w3, [x20, #104]
    cmp w3, #228
    b.ne fail_dt
    ldr w3, [x21]
    cmp w3, #1
    b.ne fail_dt
    ldr w3, [x21, #4]
    cmp w3, #1
    b.ne fail_dt
    ldr w3, [x21, #48]
    cmp w3, #4
    b.ne fail_dt
    ldr w3, [x21, #52]
    cbnz w3, fail_dt
    ldr x3, [x21, #92]
    ldr x4, =0x00006e65736f6863
    cmp x3, x4
    b.ne fail_dt
    ldr w3, [x21, #132]
    cmp w3, #8
    b.ne fail_dt
    ldr x3, [x21, #136]
    mov x4, #0x40000000
    cmp x3, x4
    b.ne fail_dt
    ldr w3, [x21, #176]
    cmp w3, #8
    b.ne fail_dt
    ldr x3, [x21, #180]
    mov x4, #0x20000000
    cmp x3, x4
    b.ne fail_dt
    ldr w3, [x21, #224]
    mov w4, #0x762d
    cmp w3, w4
    b.ne fail_dt
    adr x0, dt_message
    bl puts
    ldr x3, =0x42008000
    mov x4, #8192
    mov w5, #3
1:
    ldrb w6, [x3], #1
    and w7, w5, #255
    cmp w6, w7
    b.ne fail_data
    add w5, w5, #17
    subs x4, x4, #1
    b.ne 1b
    adr x0, data_message
    bl puts
    ldr x3, =0x4200a000
    mov x4, #8192
2:
    ldrb w5, [x3], #1
    cbnz w5, fail_bss
    subs x4, x4, #1
    b.ne 2b
    adr x0, bss_message
    bl puts
    adr x0, success_message
    bl puts
    adr x1, success_exit
    b exit
fail_cpu:
    adr x0, fail_cpu_message
    b fail
fail_args:
    adr x0, fail_args_message
    b fail
fail_dt:
    adr x0, fail_dt_message
    b fail
fail_data:
    adr x0, fail_data_message
    b fail
fail_bss:
    adr x0, fail_bss_message
fail:
    bl puts
    adr x1, failure_exit
exit:
    mov x0, #0x20
    hlt #0xf000
3:
    wfi
    b 3b
puts:
    mov x1, #0x09000000
4:
    ldrb w2, [x0], #1
    cbz w2, 6f
5:
    ldr w8, [x1, #0x18]
    tbnz w8, #5, 5b
    str w2, [x1]
    b 4b
6:
    ret
.balign 8
success_exit: .quad 0x20026, 0
failure_exit: .quad 0x20026, 1
entry_message: .asciz "NXARMPROBE: ENTRY\r\n"
cpu_message: .asciz "NXARMPROBE: CPU_STATE_OK\r\n"
args_message: .asciz "NXARMPROBE: BOOT_ARGS_OK\r\n"
dt_message: .asciz "NXARMPROBE: DEVICE_TREE_OK\r\n"
data_message: .asciz "NXARMPROBE: DATA_OK\r\n"
bss_message: .asciz "NXARMPROBE: BSS_OK\r\n"
success_message: .asciz "NXARMPROBE: HANDOFF_OK\r\n"
fail_cpu_message: .asciz "NXARMPROBE: FAIL_CPU\r\n"
fail_args_message: .asciz "NXARMPROBE: FAIL_ARGS\r\n"
fail_dt_message: .asciz "NXARMPROBE: FAIL_DT\r\n"
fail_data_message: .asciz "NXARMPROBE: FAIL_DATA\r\n"
fail_bss_message: .asciz "NXARMPROBE: FAIL_BSS\r\n"
identity: .asciz "NEXTCORE_AUTHORED_ARM64_HANDOFF_V1"
.balign 8
