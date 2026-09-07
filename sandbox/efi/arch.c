/* SPDX-License-Identifier: BSD-4-Clause
 *
 * A small, explicit AArch64 architectural-state boundary.  This file does
 * not access EFI, host page tables, or the JIT code buffer.  It records a
 * synchronous exception and provides a separate take/dispatch operation for
 * the future exception-handler phase.
 */
#include "jit.h"

static void clear(void *memory, size_t bytes) {
    uint8_t *p = memory;
    while (bytes--) *p++ = 0;
}

static int sysreg_min_el(uint32_t key) {
    switch (key) {
    case VF_SYSREG_KEY_CNTFRQ_EL0:
    case VF_SYSREG_KEY_CNTPCT_EL0:
    case VF_SYSREG_KEY_CNTVCT_EL0:
    case VF_SYSREG_KEY_CNTP_TVAL_EL0:
    case VF_SYSREG_KEY_CNTP_CTL_EL0:
    case VF_SYSREG_KEY_CNTP_CVAL_EL0:
    case VF_SYSREG_KEY_CNTV_CTL_EL0:
    case VF_SYSREG_KEY_CNTV_CVAL_EL0:
    case VF_SYSREG_KEY_CURRENT_EL:
        return VF_EL0;
    case VF_SYSREG_KEY_ID_AA64ISAR1_EL1:
    case VF_SYSREG_KEY_ID_AA64MMFR0_EL1:
    case VF_SYSREG_KEY_SCTLR_EL1:
    case VF_SYSREG_KEY_TTBR0_EL1:
    case VF_SYSREG_KEY_TTBR1_EL1:
    case VF_SYSREG_KEY_TCR_EL1:
    case VF_SYSREG_KEY_SPSR_EL1:
    case VF_SYSREG_KEY_ELR_EL1:
    case VF_SYSREG_KEY_ESR_EL1:
    case VF_SYSREG_KEY_FAR_EL1:
    case VF_SYSREG_KEY_MAIR_EL1:
    case VF_SYSREG_KEY_VBAR_EL1:
        return VF_EL1;
    case VF_SYSREG_KEY_HCR_EL2:
    case VF_SYSREG_KEY_CNTHCTL_EL2:
    case VF_SYSREG_KEY_SPSR_EL2:
    case VF_SYSREG_KEY_ELR_EL2:
    case VF_SYSREG_KEY_ESR_EL2:
    case VF_SYSREG_KEY_FAR_EL2:
    case VF_SYSREG_KEY_VBAR_EL2:
        return VF_EL2;
    case VF_SYSREG_KEY_SCR_EL3:
    case VF_SYSREG_KEY_SPSR_EL3:
    case VF_SYSREG_KEY_ELR_EL3:
    case VF_SYSREG_KEY_ESR_EL3:
    case VF_SYSREG_KEY_FAR_EL3:
    case VF_SYSREG_KEY_VBAR_EL3:
        return VF_EL3;
    default:
        return -1;
    }
}

static void update_timer_status(vf_cpu *cpu) {
    if ((cpu->cntp_ctl & VF_TIMER_CTL_ENABLE) &&
        !(cpu->cntp_ctl & VF_TIMER_CTL_IMASK) && cpu->cntpct >= cpu->cntp_cval)
        cpu->cntp_ctl |= VF_TIMER_CTL_ISTATUS;
    else
        cpu->cntp_ctl &= ~VF_TIMER_CTL_ISTATUS;
    if ((cpu->cntv_ctl & VF_TIMER_CTL_ENABLE) &&
        !(cpu->cntv_ctl & VF_TIMER_CTL_IMASK) && cpu->cntvct >= cpu->cntv_cval)
        cpu->cntv_ctl |= VF_TIMER_CTL_ISTATUS;
    else
        cpu->cntv_ctl &= ~VF_TIMER_CTL_ISTATUS;
    cpu->cntp_tval = cpu->cntp_cval >= cpu->cntpct ? cpu->cntp_cval - cpu->cntpct : 0;
}

static int valid_exception_kind(enum vf_exception_kind kind) {
    return kind >= VF_EXCEPTION_UNDEFINED_INSTRUCTION &&
           kind <= VF_EXCEPTION_EXTERNAL_INTERRUPT;
}

static uint32_t mode_for_el(uint32_t el) {
    switch (el) {
    case VF_EL0: return 0u;  /* EL0t */
    case VF_EL1: return 5u;  /* EL1h */
    case VF_EL2: return 9u;  /* EL2h */
    case VF_EL3: return 13u; /* EL3h */
    default: return 0u;
    }
}

static unsigned active_sp_index(const vf_cpu *cpu) {
    if (cpu->current_el == VF_EL0 || !(cpu->pstate & 1)) return VF_EL0;
    return cpu->current_el;
}

static void save_active_sp(vf_cpu *cpu) {
    if (cpu->current_el <= VF_EL3) cpu->sp_el[active_sp_index(cpu)] = cpu->sp;
}

static uint32_t target_el(const vf_cpu *cpu) {
    /* Phase 1 has no HCR_EL2/SCR_EL3 routing.  A lower-EL synchronous fault
     * enters EL1; an exception raised at a higher EL remains at that EL. */
    return cpu->current_el == VF_EL0 ? VF_EL1 : cpu->current_el;
}

static uint32_t exception_syndrome(enum vf_exception_kind kind,
                                   uint32_t current_el, uint64_t pc,
                                   uint32_t instruction) {
    uint32_t ec;
    uint32_t fsc = 0;

    switch (kind) {
    case VF_EXCEPTION_SYSTEM_REGISTER_TRAP:
        ec = VF_ESR_EC_SYSREG;
        return (ec << 26) | (instruction & UINT32_C(0x01ffffff));
    case VF_EXCEPTION_INSTRUCTION_ABORT:
        if (pc & 3) return VF_ESR_EC_PC_ALIGNMENT << 26;
        ec = current_el == VF_EL0 ? VF_ESR_EC_IABT_LOWER : VF_ESR_EC_IABT_SAME;
        fsc = VF_ESR_FSC_TRANSLATION_L3;
        break;
    case VF_EXCEPTION_DATA_ABORT:
    case VF_EXCEPTION_TRANSLATION_FAULT:
        ec = current_el == VF_EL0 ? VF_ESR_EC_DABT_LOWER : VF_ESR_EC_DABT_SAME;
        fsc = VF_ESR_FSC_TRANSLATION_L3;
        break;
    case VF_EXCEPTION_PERMISSION_FAULT:
        ec = current_el == VF_EL0 ? VF_ESR_EC_DABT_LOWER : VF_ESR_EC_DABT_SAME;
        fsc = VF_ESR_FSC_PERMISSION_L3;
        break;
    case VF_EXCEPTION_ALIGNMENT_FAULT:
        ec = current_el == VF_EL0 ? VF_ESR_EC_DABT_LOWER : VF_ESR_EC_DABT_SAME;
        fsc = VF_ESR_FSC_ALIGNMENT;
        break;
    case VF_EXCEPTION_UNDEFINED_INSTRUCTION:
    case VF_EXCEPTION_PRIVILEGED_INSTRUCTION:
        /* The internal privilege class is retained even when the current
         * system-register bank cannot yet provide a more specific ISS. */
        return VF_ESR_EC_UNKNOWN << 26;
    case VF_EXCEPTION_TIMER_INTERRUPT:
    case VF_EXCEPTION_EXTERNAL_INTERRUPT:
        return 0;
    case VF_EXCEPTION_NONE:
        return 0;
    }
    return (ec << 26) | fsc;
}

void vf_cpu_reset(vf_cpu *cpu, uint32_t initial_el) {
    if (!cpu) return;
    clear(cpu, sizeof(*cpu));
    if (initial_el > VF_EL3) initial_el = VF_EL0;
    cpu->current_el = initial_el;
    cpu->pstate = mode_for_el(initial_el);
    cpu->cntfrq = UINT64_C(24000000);
    cpu->id_aa64mmfr0 = UINT64_C(0x00101122);
    cpu->id_aa64isar1 = 0;
    cpu->tcr = 16;
    cpu->status = VF_NEXT;
}

int vf_cpu_set_current_el(vf_cpu *cpu, uint32_t el) {
    if (!cpu || el > VF_EL3 || !vf_cpu_state_valid(cpu)) return -1;
    save_active_sp(cpu);
    cpu->current_el = el;
    cpu->pstate = (cpu->pstate & ~VF_PSTATE_MODE_MASK) | mode_for_el(el);
    cpu->sp = cpu->sp_el[el];
    return 0;
}

int vf_cpu_state_valid(const vf_cpu *cpu) {
    uint64_t mode;
    if (!cpu || cpu->current_el > VF_EL3 ||
        cpu->exception_pending > VF_EXCEPTION_EXTERNAL_INTERRUPT ||
        cpu->exception_target_el > VF_EL3 ||
        cpu->exception_from_lower_el > 1) return 0;
    mode = cpu->pstate & VF_PSTATE_MODE_MASK;
    switch (cpu->current_el) {
    case VF_EL0: return mode == 0;
    case VF_EL1: return mode == 4 || mode == 5;
    case VF_EL2: return mode == 8 || mode == 9;
    case VF_EL3: return mode == 12 || mode == 13;
    default: return 0;
    }
}

void vf_cpu_clear_exception(vf_cpu *cpu) {
    if (!cpu) return;
    cpu->exception_pending = VF_EXCEPTION_NONE;
    cpu->exception_target_el = VF_EL0;
    cpu->exception_from_lower_el = 0;
    cpu->exception_syndrome = 0;
    cpu->exception_far = 0;
    cpu->exception_pc = 0;
    /* exception_vector is an archived dispatch result.  Clearing the
     * pending record must not erase the evidence that vf_cpu_take_exception()
     * entered the vector; reset() clears the complete architectural state. */
}

int vf_cpu_raise_exception(vf_cpu *cpu, enum vf_exception_kind kind, uint64_t pc,
                           uint64_t far, uint32_t syndrome, uint32_t instruction) {
    uint32_t target;

    if (!cpu || !vf_cpu_state_valid(cpu) || !valid_exception_kind(kind) ||
        cpu->exception_pending != VF_EXCEPTION_NONE) return -1;
    target = target_el(cpu);
    if (syndrome == 0) {
        syndrome = exception_syndrome(kind, cpu->current_el, pc, instruction);
    }

    save_active_sp(cpu);
    cpu->exception_pending = kind;
    cpu->exception_target_el = target;
    cpu->exception_from_lower_el = cpu->current_el < target;
    cpu->exception_syndrome = syndrome;
    cpu->exception_far = far;
    cpu->exception_pc = pc;
    cpu->instruction = instruction;

    /* The aliases describe the selected target bank while the arrays retain
     * the complete EL-indexed architectural record. */
    cpu->spsr_el[target] = cpu->pstate;
    cpu->elr_el[target] = pc;
    cpu->esr_el[target] = syndrome;
    cpu->far_el[target] = far;
    cpu->vbar = cpu->vbar_el[target];
    cpu->esr = syndrome;
    cpu->far = far;
    cpu->elr = pc;
    return 0;
}

int vf_cpu_take_exception(vf_cpu *cpu) {
    uint32_t target;
    uint64_t base;
    uint64_t offset;
    uint64_t vector;

    if (!cpu || !vf_cpu_state_valid(cpu) ||
        cpu->exception_pending == VF_EXCEPTION_NONE ||
        cpu->exception_target_el > VF_EL3) return -1;
    target = cpu->exception_target_el;
    base = cpu->vbar_el[target] & ~UINT64_C(0x7ff);
    offset = cpu->exception_from_lower_el ? UINT64_C(0x400) :
             ((cpu->spsr_el[target] & 1) ? UINT64_C(0x200) : UINT64_C(0));
    if (base > UINT64_MAX - offset) return -1;
    vector = base + offset;

    cpu->current_el = target;
    cpu->pstate = (cpu->spsr_el[target] & ~VF_PSTATE_MODE_MASK) |
                  mode_for_el(target) | VF_PSTATE_DAIF_MASK;
    cpu->sp = cpu->sp_el[target];
    cpu->pc = vector;
    cpu->exception_vector = vector;
    cpu->vbar = base;
    cpu->esr = cpu->esr_el[target];
    cpu->far = cpu->far_el[target];
    cpu->elr = cpu->elr_el[target];
    vf_cpu_clear_exception(cpu);
    return 0;
}

int vf_cpu_commit_status(vf_cpu *cpu, int status) {
    enum vf_exception_kind kind = VF_EXCEPTION_NONE;
    uint64_t far;
    uint64_t pc;
    uint32_t instruction;

    if (!cpu) return -1;
    cpu->status = (uint32_t)status;
    pc = cpu->pc;
    far = cpu->far;
    instruction = cpu->instruction;
    switch (status) {
    case VF_BAD_INSTRUCTION:
    case VF_UNDEFINED_INSTRUCTION:
        kind = VF_EXCEPTION_UNDEFINED_INSTRUCTION;
        break;
    case VF_FETCH_FAULT:
    case VF_INSTRUCTION_ABORT:
        kind = VF_EXCEPTION_INSTRUCTION_ABORT;
        far = pc;
        instruction = 0;
        break;
    case VF_DATA_FAULT:
    case VF_DATA_ABORT:
        kind = VF_EXCEPTION_DATA_ABORT;
        break;
    case VF_TRANSLATION_FAULT:
        kind = VF_EXCEPTION_TRANSLATION_FAULT;
        break;
    case VF_PERMISSION_FAULT:
        kind = VF_EXCEPTION_PERMISSION_FAULT;
        break;
    case VF_ALIGNMENT_FAULT:
        kind = VF_EXCEPTION_ALIGNMENT_FAULT;
        break;
    case VF_PRIVILEGE_FAULT:
        kind = VF_EXCEPTION_PRIVILEGED_INSTRUCTION;
        break;
    case VF_SYSTEM_REGISTER_TRAP:
        kind = VF_EXCEPTION_SYSTEM_REGISTER_TRAP;
        break;
    case VF_TIMER_INTERRUPT:
        kind = VF_EXCEPTION_TIMER_INTERRUPT;
        break;
    case VF_EXTERNAL_INTERRUPT:
        kind = VF_EXCEPTION_EXTERNAL_INTERRUPT;
        break;
    default:
        return 0;
    }
    return vf_cpu_raise_exception(cpu, kind, pc, far, 0, instruction);
}

int vf_cpu_read_sysreg(const vf_cpu *cpu, uint32_t key, uint64_t *value) {
    int minimum;
    if (!cpu || !value || !vf_cpu_state_valid(cpu)) return VF_SYSREG_INVALID_VALUE;
    minimum = sysreg_min_el(key);
    if (minimum < 0) return VF_SYSREG_UNKNOWN;
    if ((int)cpu->current_el < minimum) return VF_SYSREG_PRIVILEGE;
    switch (key) {
    case VF_SYSREG_KEY_CNTFRQ_EL0: *value = cpu->cntfrq; break;
    case VF_SYSREG_KEY_CNTPCT_EL0: *value = cpu->cntpct; break;
    case VF_SYSREG_KEY_CNTVCT_EL0: *value = cpu->cntvct; break;
    case VF_SYSREG_KEY_CNTP_TVAL_EL0: *value = cpu->cntp_tval; break;
    case VF_SYSREG_KEY_CNTP_CTL_EL0: *value = cpu->cntp_ctl; break;
    case VF_SYSREG_KEY_CNTP_CVAL_EL0: *value = cpu->cntp_cval; break;
    case VF_SYSREG_KEY_CNTV_CTL_EL0: *value = cpu->cntv_ctl; break;
    case VF_SYSREG_KEY_CNTV_CVAL_EL0: *value = cpu->cntv_cval; break;
    case VF_SYSREG_KEY_CURRENT_EL: *value = (uint64_t)cpu->current_el << 2; break;
    case VF_SYSREG_KEY_ID_AA64MMFR0_EL1: *value = cpu->id_aa64mmfr0; break;
    case VF_SYSREG_KEY_ID_AA64ISAR1_EL1: *value = cpu->id_aa64isar1; break;
    case VF_SYSREG_KEY_SCTLR_EL1: *value = cpu->sctlr; break;
    case VF_SYSREG_KEY_TTBR0_EL1: *value = cpu->ttbr0; break;
    case VF_SYSREG_KEY_TTBR1_EL1: *value = cpu->ttbr1; break;
    case VF_SYSREG_KEY_TCR_EL1: *value = cpu->tcr; break;
    case VF_SYSREG_KEY_SPSR_EL1: *value = cpu->spsr_el[VF_EL1]; break;
    case VF_SYSREG_KEY_ELR_EL1: *value = cpu->elr_el[VF_EL1]; break;
    case VF_SYSREG_KEY_ESR_EL1: *value = cpu->esr_el[VF_EL1]; break;
    case VF_SYSREG_KEY_FAR_EL1: *value = cpu->far_el[VF_EL1]; break;
    case VF_SYSREG_KEY_MAIR_EL1: *value = cpu->mair; break;
    case VF_SYSREG_KEY_VBAR_EL1: *value = cpu->vbar_el[VF_EL1]; break;
    case VF_SYSREG_KEY_HCR_EL2: *value = cpu->hcr_el2; break;
    case VF_SYSREG_KEY_CNTHCTL_EL2: *value = cpu->cnthctl_el2; break;
    case VF_SYSREG_KEY_SPSR_EL2: *value = cpu->spsr_el[VF_EL2]; break;
    case VF_SYSREG_KEY_ELR_EL2: *value = cpu->elr_el[VF_EL2]; break;
    case VF_SYSREG_KEY_ESR_EL2: *value = cpu->esr_el[VF_EL2]; break;
    case VF_SYSREG_KEY_FAR_EL2: *value = cpu->far_el[VF_EL2]; break;
    case VF_SYSREG_KEY_VBAR_EL2: *value = cpu->vbar_el[VF_EL2]; break;
    case VF_SYSREG_KEY_SCR_EL3: *value = cpu->scr_el3; break;
    case VF_SYSREG_KEY_SPSR_EL3: *value = cpu->spsr_el[VF_EL3]; break;
    case VF_SYSREG_KEY_ELR_EL3: *value = cpu->elr_el[VF_EL3]; break;
    case VF_SYSREG_KEY_ESR_EL3: *value = cpu->esr_el[VF_EL3]; break;
    case VF_SYSREG_KEY_FAR_EL3: *value = cpu->far_el[VF_EL3]; break;
    case VF_SYSREG_KEY_VBAR_EL3: *value = cpu->vbar_el[VF_EL3]; break;
    default: return VF_SYSREG_UNKNOWN;
    }
    return VF_SYSREG_OK;
}

int vf_cpu_write_sysreg(vf_cpu *cpu, uint32_t key, uint64_t value) {
    int minimum;
    if (!cpu || !vf_cpu_state_valid(cpu)) return VF_SYSREG_INVALID_VALUE;
    minimum = sysreg_min_el(key);
    if (minimum < 0) return VF_SYSREG_UNKNOWN;
    if ((int)cpu->current_el < minimum) return VF_SYSREG_PRIVILEGE;
    switch (key) {
    case VF_SYSREG_KEY_CNTFRQ_EL0:
    case VF_SYSREG_KEY_CNTPCT_EL0:
    case VF_SYSREG_KEY_CNTVCT_EL0:
    case VF_SYSREG_KEY_CURRENT_EL:
    case VF_SYSREG_KEY_ID_AA64MMFR0_EL1:
    case VF_SYSREG_KEY_ID_AA64ISAR1_EL1:
        return VF_SYSREG_READ_ONLY;
    case VF_SYSREG_KEY_CNTP_TVAL_EL0:
        cpu->cntp_cval = cpu->cntpct + value;
        cpu->cntp_tval = value;
        break;
    case VF_SYSREG_KEY_CNTP_CTL_EL0:
        cpu->cntp_ctl = value & (VF_TIMER_CTL_ENABLE | VF_TIMER_CTL_IMASK);
        break;
    case VF_SYSREG_KEY_CNTP_CVAL_EL0: cpu->cntp_cval = value; break;
    case VF_SYSREG_KEY_CNTV_CTL_EL0:
        cpu->cntv_ctl = value & (VF_TIMER_CTL_ENABLE | VF_TIMER_CTL_IMASK);
        break;
    case VF_SYSREG_KEY_CNTV_CVAL_EL0: cpu->cntv_cval = value; break;
    case VF_SYSREG_KEY_SCTLR_EL1: cpu->sctlr = value; break;
    case VF_SYSREG_KEY_TTBR0_EL1:
        if (value & UINT64_C(0xfff)) return VF_SYSREG_INVALID_VALUE;
        cpu->ttbr0 = value; vf_cpu_invalidate_tlb(cpu); break;
    case VF_SYSREG_KEY_TTBR1_EL1:
        if (value & UINT64_C(0xfff)) return VF_SYSREG_INVALID_VALUE;
        cpu->ttbr1 = value; vf_cpu_invalidate_tlb(cpu); break;
    case VF_SYSREG_KEY_TCR_EL1: cpu->tcr = value; vf_cpu_invalidate_tlb(cpu); break;
    case VF_SYSREG_KEY_SPSR_EL1: cpu->spsr_el[VF_EL1] = value; break;
    case VF_SYSREG_KEY_ELR_EL1: cpu->elr_el[VF_EL1] = value; break;
    case VF_SYSREG_KEY_ESR_EL1: cpu->esr_el[VF_EL1] = value; break;
    case VF_SYSREG_KEY_FAR_EL1: cpu->far_el[VF_EL1] = value; break;
    case VF_SYSREG_KEY_MAIR_EL1: cpu->mair = value; break;
    case VF_SYSREG_KEY_VBAR_EL1: cpu->vbar_el[VF_EL1] = value & ~UINT64_C(0x7ff); break;
    case VF_SYSREG_KEY_HCR_EL2: cpu->hcr_el2 = value; break;
    case VF_SYSREG_KEY_CNTHCTL_EL2: cpu->cnthctl_el2 = value; break;
    case VF_SYSREG_KEY_SPSR_EL2: cpu->spsr_el[VF_EL2] = value; break;
    case VF_SYSREG_KEY_ELR_EL2: cpu->elr_el[VF_EL2] = value; break;
    case VF_SYSREG_KEY_ESR_EL2: cpu->esr_el[VF_EL2] = value; break;
    case VF_SYSREG_KEY_FAR_EL2: cpu->far_el[VF_EL2] = value; break;
    case VF_SYSREG_KEY_VBAR_EL2: cpu->vbar_el[VF_EL2] = value & ~UINT64_C(0x7ff); break;
    case VF_SYSREG_KEY_SCR_EL3: cpu->scr_el3 = value; break;
    case VF_SYSREG_KEY_SPSR_EL3: cpu->spsr_el[VF_EL3] = value; break;
    case VF_SYSREG_KEY_ELR_EL3: cpu->elr_el[VF_EL3] = value; break;
    case VF_SYSREG_KEY_ESR_EL3: cpu->esr_el[VF_EL3] = value; break;
    case VF_SYSREG_KEY_FAR_EL3: cpu->far_el[VF_EL3] = value; break;
    case VF_SYSREG_KEY_VBAR_EL3: cpu->vbar_el[VF_EL3] = value & ~UINT64_C(0x7ff); break;
    default: return VF_SYSREG_UNKNOWN;
    }
    update_timer_status(cpu);
    return VF_SYSREG_OK;
}

void vf_cpu_advance_counter(vf_cpu *cpu, uint64_t ticks) {
    if (!cpu) return;
    cpu->cntpct += ticks;
    cpu->cntvct += ticks;
    update_timer_status(cpu);
}

int vf_cpu_timer_pending(const vf_cpu *cpu) {
    return cpu && ((cpu->cntp_ctl & VF_TIMER_CTL_ISTATUS) ||
                   (cpu->cntv_ctl & VF_TIMER_CTL_ISTATUS));
}

void vf_cpu_invalidate_tlb(vf_cpu *cpu) {
    if (!cpu) return;
    cpu->tlb_tag = 0;
    cpu->tlb_pa = 0;
    cpu->tlb_generation++;
}
