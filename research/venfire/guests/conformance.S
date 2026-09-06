/* SPDX-License-Identifier: MIT
 * Self-authored bare-metal AArch64 tests. No Apple code or firmware.
 * GNU as: --defsym VMAPPLE=0 (virt) or 1 (research vmapple).
 */
.arch armv8.3-a
.if VMAPPLE
.equ UART, 0x20010000
.equ SCRATCH, 0x71000000
.equ GICD, 0x10000000
.equ GICR, 0x10010000
.else
.equ UART, 0x09000000
.equ SCRATCH, 0x41000000
.equ GICD, 0x08000000
.equ GICR, 0x080a0000
.endif
.equ TABLE, SCRATCH + 0x10000
.equ STACK, SCRATCH + 0x20000
.equ CODEBUF, SCRATCH + 0x30000

.section .boot, "ax"
.global _boot
_boot:
    ldr x0, =__payload_load
    ldr x1, =__payload_start
    ldr x2, =__payload_size
1:  ldrb w3, [x0], #1
    strb w3, [x1], #1
    subs x2, x2, #1
    b.ne 1b
    dsb sy
    ic iallu
    dsb sy
    isb
    ldr x0, =_start
    br x0
.ltorg

.section .text, "ax"
.global _start
_start:
    msr daifset, #15
    msr spsel, #1
    ldr x0, =STACK
    mov sp, x0
    adr x0, vectors
    msr vbar_el1, x0
    isb
    adr x0, begin
    bl puts
    adr x19, case_el1
    mrs x0, CurrentEL
    cmp x0, #4
    b.ne failed
    bl passed

    adr x19, case_integer
    ldr x0, =SCRATCH
    mov x1, #0x1234
    mov x2, #7
    madd x3, x1, x2, x2
    str x3, [x0]
    ldr x4, [x0]
    mov x5, #0x7f73
    cmp x4, x5
    b.ne failed
    mov x1, #-1
    adds x2, x1, #1
    b.ne failed
    b.cc failed
    mov w1, #-1
    lsr x2, x1, #32
    cbnz x2, failed
    bl passed

    /* The table is 16 KiB aligned and cleared for either granule size. */
    ldr x0, =TABLE
    mov x1, #0x4000
1:  str xzr, [x0], #8
    subs x1, x1, #8
    b.ne 1b
    ldr x0, =TABLE
    mov x1, #0x401          /* 0..1GiB: device, AF, block */
    str x1, [x0]
    ldr x1, =0x40000705     /* 1..2GiB: normal WB, inner shareable, RW */
    str x1, [x0, #8]
    ldr x1, =0x40000785     /* 2..3GiB: alias of RAM, EL1 read-only */
    str x1, [x0, #16]
    msr ttbr0_el1, x0
    mov x0, #0xff00         /* MAIR attr0=device nGnRnE, attr1=normal WB */
    msr mair_el1, x0
    ldr x0, =0x0000000200803519  /* 4KiB, 39 VA bits, 40 PA bits, EPD1 */
    msr tcr_el1, x0
    dsb sy
    tlbi vmalle1
    dsb sy
    isb
    mrs x0, sctlr_el1
    orr x0, x0, #1
    orr x0, x0, #4
    orr x0, x0, #0x1000
    orr x0, x0, #0x80000000  /* EnIA: real PACIA/AUTIA, never HINT forms */
    msr sctlr_el1, x0
    isb

    adr x19, case_pac
    mrs x0, id_aa64isar1_el1
    ubfx x1, x0, #4, #4    /* APA: architected QARMA5, not impdef API */
    cbz x1, pac_unsupported
    ldr x0, =0x0123456789abcdef
    msr apiakeylo_el1, x0
    ldr x0, =0xfedcba9876543210
    msr apiakeyhi_el1, x0
    isb
    ldr x9, =SCRATCH
    mov x10, x9
    mov x11, #0x1234
    pacia x10, x11
    cmp x10, x9
    b.eq failed           /* A no-op sign is not acceptable. */
    mov x12, x10
    autia x12, x11
    cmp x12, x9
    b.ne failed
    bl passed

    adr x19, case_pac_bad
    /* PAuth may poison the pointer, or FEAT_FPAC may fault immediately. */
    mov x21, #16
    mov x14, #0x4000
pac_bad_loop:
    mov x12, x10
    mov x23, #0x1c
    mov x24, #-1
    mov x22, #0
    adr x26, pac_bad_rejected
    mov x27, #0
    autia x12, x14
    cmp x12, x9
    b.eq failed
    /* Poison is only counted as rejected after its use faults. */
    mov x23, #0x25
    mov x25, x12
    mov x22, #1
    ldr x0, [x12]
    b failed
pac_bad_rejected:
    cmp x27, #1
    b.ne failed
    add x14, x14, #1
    subs x21, x21, #1
    b.ne pac_bad_loop
    mov x23, #-1
    bl passed
    b pac_done
pac_unsupported:
    bl unsupported
    adr x19, case_pac_bad
    bl unsupported
pac_done:
    adr x19, case_svc
    mov x23, #0x15
    mov x24, #-1
    mov x22, #0
    adr x26, svc_return
    mov x27, #0
    svc #0x52
svc_return:
    cmp x27, #1
    b.ne failed
    mrs x0, esr_el1
    and x0, x0, #0xffff
    cmp x0, #0x52
    b.ne failed
    mov x23, #-1
    bl passed

    adr x19, case_mmu4_ro
    mov x24, #0x0d         /* Permission fault, level 1 */
    bl test_readonly
    bl passed
    adr x19, case_mmu4_unmapped
    mov x24, #0x05         /* Translation fault, level 1 */
    bl test_unmapped
    bl passed

    /* Switch to real 16KiB translation granules, 32MiB L2 blocks. */
    mrs x0, id_aa64mmfr0_el1
    ubfx x0, x0, #20, #4
    cmp x0, #0
    b.eq mmu16_unsupported
    mrs x0, sctlr_el1
    bic x0, x0, #1
    bic x0, x0, #4
    bic x0, x0, #0x1000
    dsb sy
    msr sctlr_el1, x0
    isb
    ldr x0, =TABLE
    mov x1, #0x4000
1:  str xzr, [x0], #8
    subs x1, x1, #8
    b.ne 1b
    ldr x0, =TABLE
    mov x1, #0x401
    mov x2, #32
    mov x3, #0x2000000
1:  str x1, [x0], #8
    add x1, x1, x3
    subs x2, x2, #1
    b.ne 1b
    ldr x1, =0x40000705
    mov x2, #32
1:  str x1, [x0], #8
    add x1, x1, x3
    subs x2, x2, #1
    b.ne 1b
    ldr x1, =0x40000785
    mov x2, #32
1:  str x1, [x0], #8
    add x1, x1, x3
    subs x2, x2, #1
    b.ne 1b
    ldr x0, =0x000000020080b51c  /* 16KiB, 36 VA bits, 40 PA bits */
    msr tcr_el1, x0
    dsb sy
    tlbi vmalle1
    dsb sy
    isb
    mrs x0, sctlr_el1
    orr x0, x0, #1
    orr x0, x0, #4
    orr x0, x0, #0x1000
    msr sctlr_el1, x0
    isb
    adr x19, case_mmu16_ro
    mov x24, #0x0e         /* Permission fault, level 2 */
    bl test_readonly
    bl passed
    adr x19, case_mmu16_unmapped
    mov x24, #0x06         /* Translation fault, level 2 */
    bl test_unmapped
    bl passed
    b mmu_done
mmu16_unsupported:
    adr x19, case_mmu16_ro
    bl unsupported
    adr x19, case_mmu16_unmapped
    bl unsupported
mmu_done:
    adr x19, case_timer
    mrs x0, cntfrq_el0
    cbz x0, failed
    mrs x1, cntpct_el0
    mov x2, #1000
    msr cntp_tval_el0, x2
    mov x2, #3            /* Enable and mask IRQ; poll real ISTATUS. */
    msr cntp_ctl_el0, x2
    isb
    mov x3, #0x1000000
1:  mrs x2, cntp_ctl_el0
    tbnz x2, #2, timer_expired
    subs x3, x3, #1
    b.ne 1b
    b failed
timer_expired:
    mrs x2, cntpct_el0
    cmp x2, x1
    b.ls failed
    msr cntp_ctl_el0, xzr
    bl passed

    adr x19, case_irq
    /* GICv3: Group-1 virtual timer PPI27 is wired on both target boards. */
    ldr x0, =GICD
    mov w1, #0x12        /* ARE_NS and EnableGrp1NS (single NS state). */
    str w1, [x0]
    ldr x0, =GICR
    ldr w1, [x0, #0x14]
    bic w1, w1, #2      /* Wake redistributor. */
    str w1, [x0, #0x14]
    mov x3, #0x100000
1:  ldr w1, [x0, #0x14]
    tbz w1, #2, 2f
    subs x3, x3, #1
    b.ne 1b
    b failed
2:  ldr x0, =(GICR + 0x10000)
    mov w1, #-1
    str w1, [x0, #0x80] /* All SGI/PPI Group 1. */
    str wzr, [x0, #0xd00]
    mov w1, #0x80
    strb w1, [x0, #0x41b] /* PPI27 priority. */
    mov w1, #0x08000000
    str w1, [x0, #0x100] /* Enable PPI27. */
    mov x1, #1
    msr icc_sre_el1, x1
    isb
    mov x1, #0xff
    msr icc_pmr_el1, x1
    msr icc_ctlr_el1, xzr /* EOImode=0: EOIR also deactivates. */
    mov x1, #1
    msr icc_igrpen1_el1, x1
    isb
    mov x1, #1000
    msr cntv_tval_el0, x1
    mov x1, #1
    msr cntv_ctl_el0, x1
    mov x21, #1           /* Handler must be expected and INTID must be27. */
    mov x27, #0
    isb
    msr daifclr, #2
    mov x3, #0x1000000
1:  cbnz x27, irq_received
    subs x3, x3, #1
    b.ne 1b
    msr daifset, #2
    b failed
irq_received:
    msr daifset, #2
    mov x21, #0
    msr icc_igrpen1_el1, xzr
    ldr x0, =(GICR + 0x10000)
    mov w1, #0x08000000
    str w1, [x0, #0x180] /* Disable PPI27 after the test. */
    dsb sy
    ldr w1, [x0, #0x300] /* EOIR must have cleared its active state. */
    tbnz w1, #27, failed
    bl passed

    adr x19, case_smc
    ldr x15, =CODEBUF
    ldr w0, =0x52800540   /* mov w0, #42 */
    str w0, [x15]
    ldr w0, =0xd65f03c0   /* ret */
    str w0, [x15, #4]
    bl sync_code
    blr x15
    cmp w0, #42
    b.ne failed
    ldr w0, =0x52800a80   /* mov w0, #84 */
    str w0, [x15]
    bl sync_code
    blr x15
    cmp w0, #84
    b.ne failed
    bl passed
    adr x0, done
    bl puts
    mov x1, #0
    b exit_guest

test_readonly:
    ldr x0, =SCRATCH
    mov x1, #0x5a5a
    str x1, [x0]
    mov x2, #0x40000000
    add x25, x0, x2
    ldr x2, [x25]
    cmp x1, x2
    b.ne failed
    mov x23, #0x25
    mov x22, #1
    adr x26, readonly_return
    mov x27, #0
    str xzr, [x25]
readonly_return:
    cmp x27, #1
    b.ne failed
    mrs x2, esr_el1
    tbz x2, #6, failed     /* WnR must identify a write. */
    ldr x0, =SCRATCH
    ldr x2, [x0]
    mov x3, #0x5a5a
    cmp x2, x3
    b.ne failed
    mov x23, #-1
    ret

test_unmapped:
    mov x25, #0xc0000000
    mov x23, #0x25
    mov x22, #1
    adr x26, unmapped_return
    mov x27, #0
    ldr x0, [x25]
unmapped_return:
    cmp x27, #1
    b.ne failed
    mrs x2, esr_el1
    tbnz x2, #6, failed    /* WnR must identify a read. */
    mov x23, #-1
    ret

sync_code:
    dc cvau, x15
    dsb ish
    ic ivau, x15
    dsb ish
    isb
    ret

/* Register-only handler, x0..x3 clobbered. Test callers account for this. */
sync_handler:
    mrs x0, esr_el1
    lsr x1, x0, #26
    cmp x1, x23
    b.ne unexpected
    cmn x24, #1
    b.eq 1f
    and x1, x0, #0x3f
    cmp x1, x24
    b.ne unexpected
1:  cbz x22, 2f
    mrs x1, far_el1
    cmp x1, x25
    b.ne unexpected
2:  msr elr_el1, x26
    mov x27, #1
    eret
irq_handler:
    stp x0, x1, [sp, #-16]!
    cbz x21, unexpected
    mrs x0, icc_iar1_el1
    cmp x0, #27
    b.ne unexpected
    msr cntv_ctl_el0, xzr
    isb
    msr icc_eoir1_el1, x0
    dsb sy
    mov x27, #1
    ldp x0, x1, [sp], #16
    eret
unexpected:
    adr x19, case_unexpected
    b failed

passed:
    mov x18, x30
    adr x0, pass_prefix
    bl puts
    mov x0, x19
    bl puts
    adr x0, newline
    bl puts
    br x18
unsupported:
    mov x18, x30
    adr x0, unsupported_prefix
    bl puts
    mov x0, x19
    bl puts
    adr x0, newline
    bl puts
    br x18
failed:
    adr x0, fail_prefix
    bl puts
    mov x0, x19
    bl puts
    adr x0, newline
    bl puts
    mov x1, #1
exit_guest:
    sub sp, sp, #16
    ldr x0, =0x20026     /* SYS_EXIT_EXTENDED / ADP_Stopped_ApplicationExit */
    stp x0, x1, [sp]
    mov x1, sp
    mov x0, #0x20
    hlt #0xf000
1:  wfe
    b 1b
puts:
    ldr x16, =UART
1:  ldrb w17, [x0], #1
    cbz w17, 3f
2:  ldr w4, [x16, #0x18]
    tbnz w4, #5, 2b
    str w17, [x16]
    b 1b
3:  ret
.ltorg
.balign 2048
vectors:
.rept 4
    b sync_handler
    .balign 128
    b irq_handler
    .balign 128
    b sync_handler
    .balign 128
    b sync_handler
    .balign 128
.endr
begin: .asciz "VENFIRE|BEGIN|1\n"
done: .asciz "VENFIRE|DONE|1\n"
pass_prefix: .asciz "VENFIRE|PASS|"
fail_prefix: .asciz "VENFIRE|FAIL|"
unsupported_prefix: .asciz "VENFIRE|UNSUPPORTED|"
newline: .asciz "\n"
case_el1: .asciz "el1_entry"
case_integer: .asciz "integer_memory"
case_pac: .asciz "pauth_roundtrip"
case_pac_bad: .asciz "pauth_wrong_context"
case_svc: .asciz "exception_svc"
case_mmu4_ro: .asciz "mmu_4k_permissions"
case_mmu4_unmapped: .asciz "mmu_4k_translation"
case_mmu16_ro: .asciz "mmu_16k_permissions"
case_mmu16_unmapped: .asciz "mmu_16k_translation"
case_timer: .asciz "timer_deadline"
case_irq: .asciz "gicv3_timer_irq"
case_smc: .asciz "self_modify"
case_unexpected: .asciz "unexpected_exception"
