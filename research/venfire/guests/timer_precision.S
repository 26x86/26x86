/* SPDX-License-Identifier: MIT
 * Self-authored debugger-driven timer fixture. No Apple input or firmware.
 * Runs at EL2 on QEMU virt with secure=off, virtualization=on, GICv3.
 */
.arch armv8.7-a
.section .text
.global _start, ready, nop_step, read_phys, read_virt, set_voff
.global set_p_cval, set_v_cval, set_p_ctl, set_v_ctl, read_irq, eoi_irq
.global wait_wfit, wait_wfet
.global clear_event
.global timer_run_p, timer_run_v, timer_pad_end_p, timer_pad_end_v
_start:
    msr daifset, #15
    mov x0, #3
    msr cnthctl_el2, x0
    msr cntvoff_el2, xzr
    msr cntp_ctl_el0, xzr
    msr cntv_ctl_el0, xzr
    /* Group 1, PPI27 and PPI30, one redistributor. */
    ldr x1, =0x08000000
    mov w0, #0x12
    str w0, [x1]
    ldr x1, =0x080a0014
    str wzr, [x1]
    ldr x1, =0x080b0080
    mov w0, #-1
    str w0, [x1]
    ldr x1, =0x080b0418
    mov w0, #0x80808080
    str w0, [x1]
    str w0, [x1, #4]
    ldr x1, =0x080b0100
    mov w0, #0x48000000
    str w0, [x1]
    mov x0, #0xf
    msr icc_sre_el2, x0
    isb
    mov x0, #1
    msr icc_sre_el1, x0
    mov x0, #0xff
    msr icc_pmr_el1, x0
    mov x0, #1
    msr icc_igrpen1_el1, x0
    isb
ready:
    b ready
nop_step:
    nop
    b ready
read_phys:
    mrs x0, cntpct_el0
    b ready
read_virt:
    mrs x0, cntvct_el0
    b ready
set_voff:
    msr cntvoff_el2, x0
    b ready
set_p_cval:
    msr cntp_cval_el0, x0
    b ready
set_v_cval:
    msr cntv_cval_el0, x0
    b ready
set_p_ctl:
    msr cntp_ctl_el0, x0
    b ready
set_v_ctl:
    msr cntv_ctl_el0, x0
    b ready
read_irq:
    mrs x0, icc_iar1_el1
    b ready
eoi_irq:
    msr icc_eoir1_el1, x0
    b ready
wait_wfit:
    wfit x0
    b ready
wait_wfet:
    wfet x0
    b ready
clear_event:
    sevl
    wfe
    b ready
.macro timer_run kind
timer_run_\kind:
    msr cnt\kind\()_ctl_el0, x0
    br x1
    .rept 2048
    nop
    .endr
timer_pad_end_\kind:
    mrs x2, cnt\kind\()_ctl_el0
    mrs x3, cnt\kind\()_ctl_el0
    mrs x4, icc_iar1_el1
    mrs x5, cntpct_el0
    msr cnt\kind\()_ctl_el0, xzr
    msr icc_eoir1_el1, x4
    b ready
.endm
timer_run p
timer_run v
.ltorg
