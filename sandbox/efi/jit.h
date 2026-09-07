/* SPDX-License-Identifier: BSD-4-Clause; see ../../LICENSE.txt and repository LICENSE.txt. */
#ifndef VENFIRE_JIT_H
#define VENFIRE_JIT_H
#include <stdint.h>
#include <stddef.h>
#define VF_ABI __attribute__((ms_abi))
enum vf_status { VF_NEXT, VF_HALT, VF_BAD_INSTRUCTION, VF_FETCH_FAULT, VF_DATA_FAULT,
                 VF_BUDGET, VF_CODE_FULL, VF_PROTECTION,
                 VF_UNDEFINED_INSTRUCTION, VF_PRIVILEGE_FAULT,
                 VF_TRANSLATION_FAULT, VF_PERMISSION_FAULT, VF_ALIGNMENT_FAULT,
                 VF_SYSTEM_REGISTER_TRAP, VF_TIMER_INTERRUPT, VF_EXTERNAL_INTERRUPT,
                 VF_INSTRUCTION_ABORT, VF_DATA_ABORT };

/* These are guest architectural exceptions.  They are deliberately separate
 * from vf_status: a terminal JIT result is an execution-layer status, while a
 * pending exception is state that a future exception dispatcher may consume. */
enum vf_exception_kind {
    VF_EXCEPTION_NONE = 0,
    VF_EXCEPTION_UNDEFINED_INSTRUCTION = 1,
    VF_EXCEPTION_PRIVILEGED_INSTRUCTION = 2,
    VF_EXCEPTION_INSTRUCTION_ABORT = 3,
    VF_EXCEPTION_DATA_ABORT = 4,
    VF_EXCEPTION_TRANSLATION_FAULT = 5,
    VF_EXCEPTION_PERMISSION_FAULT = 6,
    VF_EXCEPTION_ALIGNMENT_FAULT = 7,
    VF_EXCEPTION_SYSTEM_REGISTER_TRAP = 8,
    VF_EXCEPTION_TIMER_INTERRUPT = 9,
    VF_EXCEPTION_EXTERNAL_INTERRUPT = 10,
};

enum vf_exception_level { VF_EL0 = 0, VF_EL1 = 1, VF_EL2 = 2, VF_EL3 = 3 };

/* ESR_ELx encodings used by the Phase-1 exception recorder.  They are not a
 * system-register implementation; the next system-register phase owns the
 * read/write bank and trap controls. */
#define VF_ESR_EC_UNKNOWN UINT32_C(0x00)
#define VF_ESR_EC_WFX_TRAP UINT32_C(0x01)
#define VF_ESR_EC_SYSREG UINT32_C(0x18)
#define VF_ESR_EC_IABT_LOWER UINT32_C(0x20)
#define VF_ESR_EC_IABT_SAME UINT32_C(0x21)
#define VF_ESR_EC_DABT_LOWER UINT32_C(0x24)
#define VF_ESR_EC_DABT_SAME UINT32_C(0x25)
#define VF_ESR_EC_PC_ALIGNMENT UINT32_C(0x22)
#define VF_ESR_FSC_TRANSLATION_L3 UINT32_C(0x07)
#define VF_ESR_FSC_PERMISSION_L3 UINT32_C(0x0d)
#define VF_ESR_FSC_ALIGNMENT UINT32_C(0x21)
#define VF_TIMER_CTL_ENABLE UINT64_C(0x1)
#define VF_TIMER_CTL_IMASK UINT64_C(0x2)
#define VF_TIMER_CTL_ISTATUS UINT64_C(0x4)
#define VF_PSTATE_MODE_MASK UINT64_C(0x0f)
#define VF_PSTATE_DAIF_MASK UINT64_C(0x3c0)

/* A system-register key is op0:op1:CRn:CRm, with Rt removed.  Keep the
 * values in one header so the C decoder, the explicit bank, and host tests
 * cannot silently disagree about timer or ID-register encodings. */
#define VF_SYSREG_KEY_CNTFRQ_EL0 UINT32_C(0x5f00)
#define VF_SYSREG_KEY_CNTPCT_EL0 UINT32_C(0x5f01)
#define VF_SYSREG_KEY_CNTVCT_EL0 UINT32_C(0x5f02)
#define VF_SYSREG_KEY_CNTP_TVAL_EL0 UINT32_C(0x5f10)
#define VF_SYSREG_KEY_CNTP_CTL_EL0 UINT32_C(0x5f11)
#define VF_SYSREG_KEY_CNTP_CVAL_EL0 UINT32_C(0x5f12)
#define VF_SYSREG_KEY_CNTV_CTL_EL0 UINT32_C(0x5f19)
#define VF_SYSREG_KEY_CNTV_CVAL_EL0 UINT32_C(0x5f1a)
#define VF_SYSREG_KEY_CURRENT_EL UINT32_C(0x4212)
#define VF_SYSREG_KEY_ID_AA64ISAR1_EL1 UINT32_C(0x4031)
#define VF_SYSREG_KEY_ID_AA64MMFR0_EL1 UINT32_C(0x4038)
#define VF_SYSREG_KEY_SCTLR_EL1 UINT32_C(0x4080)
#define VF_SYSREG_KEY_TTBR0_EL1 UINT32_C(0x4100)
#define VF_SYSREG_KEY_TTBR1_EL1 UINT32_C(0x4101)
#define VF_SYSREG_KEY_TCR_EL1 UINT32_C(0x4102)
#define VF_SYSREG_KEY_SPSR_EL1 UINT32_C(0x4200)
#define VF_SYSREG_KEY_ELR_EL1 UINT32_C(0x4201)
#define VF_SYSREG_KEY_ESR_EL1 UINT32_C(0x4290)
#define VF_SYSREG_KEY_FAR_EL1 UINT32_C(0x4300)
#define VF_SYSREG_KEY_MAIR_EL1 UINT32_C(0x4500)
#define VF_SYSREG_KEY_VBAR_EL1 UINT32_C(0x4600)
#define VF_SYSREG_KEY_HCR_EL2 UINT32_C(0x6088)
#define VF_SYSREG_KEY_CNTHCTL_EL2 UINT32_C(0x6708)
#define VF_SYSREG_KEY_SPSR_EL2 UINT32_C(0x6200)
#define VF_SYSREG_KEY_ELR_EL2 UINT32_C(0x6201)
#define VF_SYSREG_KEY_ESR_EL2 UINT32_C(0x6290)
#define VF_SYSREG_KEY_FAR_EL2 UINT32_C(0x6300)
#define VF_SYSREG_KEY_VBAR_EL2 UINT32_C(0x6600)
#define VF_SYSREG_KEY_SCR_EL3 UINT32_C(0x7088)
#define VF_SYSREG_KEY_SPSR_EL3 UINT32_C(0x7200)
#define VF_SYSREG_KEY_ELR_EL3 UINT32_C(0x7201)
#define VF_SYSREG_KEY_ESR_EL3 UINT32_C(0x7290)
#define VF_SYSREG_KEY_FAR_EL3 UINT32_C(0x7300)
#define VF_SYSREG_KEY_VBAR_EL3 UINT32_C(0x7600)

enum vf_sysreg_result {
    VF_SYSREG_OK = 0,
    VF_SYSREG_UNKNOWN = -1,
    VF_SYSREG_PRIVILEGE = -2,
    VF_SYSREG_READ_ONLY = -3,
    VF_SYSREG_INVALID_VALUE = -4,
};

/* Architectural state is explicit even while the first translator supports a
 * bounded base subset.  x[0..30] are GPRs; x[31] is reserved padding and is
 * kept only so old zero-initialized callers do not change the private layout
 * assumptions of the host test.  The translator always uses sp for SP/WSP. */
typedef struct {
    uint64_t x[32], sp, pc, pstate, sctlr, ttbr0, ttbr1, tcr, mair;
    uint64_t vbar, esr, far, elr;
    uint64_t sp_el[4], spsr_el[4], vbar_el[4], esr_el[4], far_el[4], elr_el[4];
    uint64_t exception_syndrome, exception_far, exception_pc, exception_vector;
    uint64_t cntfrq, cntpct, cntp_ctl, cntp_cval;
    uint64_t id_aa64mmfr0, id_aa64isar1;
    uint64_t cntvct, cntv_ctl, cntv_cval, cntp_tval;
    uint64_t hcr_el2, cnthctl_el2, scr_el3;
    uint64_t retired, tlb_tag, tlb_pa, tlb_generation;
    uint32_t current_el, exception_pending, exception_target_el,
             exception_from_lower_el, instruction, status;
} vf_cpu;
typedef struct { uint8_t *bytes; size_t capacity, used; } vf_code;
typedef int (VF_ABI *vf_entry)(vf_cpu *, uint8_t *, uint64_t);
typedef int (*vf_protect)(void *, size_t, int executable, void *);
int vf_translate(vf_code *, const uint8_t *, size_t, uint64_t pc, unsigned limit);
int vf_translate_cpu(vf_code *, vf_cpu *, const uint8_t *, size_t, uint64_t pc,
                     unsigned limit);
int vf_run(vf_cpu *, const uint8_t *, size_t, uint8_t *, size_t,
           vf_code *, uint64_t budget, vf_protect, void *);
int vf_host_supported(void);

void vf_cpu_reset(vf_cpu *, uint32_t initial_el);
int vf_cpu_set_current_el(vf_cpu *, uint32_t el);
int vf_cpu_state_valid(const vf_cpu *);
void vf_cpu_clear_exception(vf_cpu *);
int vf_cpu_raise_exception(vf_cpu *, enum vf_exception_kind, uint64_t pc,
                           uint64_t far, uint32_t syndrome, uint32_t instruction);
int vf_cpu_take_exception(vf_cpu *);
int vf_cpu_commit_status(vf_cpu *, int status);
int vf_cpu_read_sysreg(const vf_cpu *, uint32_t key, uint64_t *value);
int vf_cpu_write_sysreg(vf_cpu *, uint32_t key, uint64_t value);
void vf_cpu_advance_counter(vf_cpu *, uint64_t ticks);
int vf_cpu_timer_pending(const vf_cpu *);
void vf_cpu_invalidate_tlb(vf_cpu *);
#endif
