/* Authored test-only observer: canonical runtime performs every guest step. */
#include "memory_dynamic.h"
int run_captured(const vf_memory_controls_v2 *controls,uint64_t ram_base,uint64_t entry,
    uint64_t stack,uint64_t pstate,uint64_t data_va,uint64_t store,
    uint8_t *code,size_t code_bytes,vf_protect protect,
    vf_memory_callback_v2 memory,vf_dynamic_callback control,void *owner,
    vf_memory_run_result_dynamic *result,uint64_t observed[48]) {
    vf_cpu cpu;vf_cpu_reset(&cpu,VF_EL1);
    cpu.pc=entry;cpu.sp=stack;cpu.sp_el[VF_EL0]=stack;cpu.sp_el[VF_EL1]=stack;
    cpu.pstate=pstate;cpu.guest_ram_base=ram_base;
    cpu.x[0]=controls->sctlr|1;cpu.x[1]=data_va;cpu.x[2]=store;cpu.x[3]=store;
    cpu.sctlr=controls->sctlr;cpu.ttbr0=controls->ttbr0;cpu.ttbr1=controls->ttbr1;
    cpu.tcr=controls->tcr;cpu.mair=controls->mair;cpu.hcr_el2=controls->hcr;cpu.scr_el3=controls->scr;
    *result=(vf_memory_run_result_dynamic){0};
    result->memory.base.abi_version=3;result->memory.base.struct_size=512;
    result->memory.last_reply=(vf_memory_reply_v2){.abi_version=3,.struct_size=128,.level=UINT32_MAX};
    vf_code buffer={code,code_bytes,0};
    int status=vf_run_memory_provider_dynamic(&cpu,&buffer,32,protect,0,controls,memory,control,owner,result);
    vf_boot_snapshot(&cpu,status,&result->memory.base.execution);
    result->memory.base.guest_far=cpu.far_el[VF_EL1];
    for(unsigned i=0;i<31;i++)observed[i]=cpu.x[i];
    observed[31]=cpu.sp;observed[32]=cpu.pc;observed[33]=cpu.retired;observed[34]=cpu.current_el;
    observed[35]=cpu.pstate;observed[36]=cpu.esr_el[VF_EL1];observed[37]=cpu.far_el[VF_EL1];
    observed[38]=cpu.elr_el[VF_EL1];observed[39]=cpu.spsr_el[VF_EL1];
    observed[40]=cpu.sctlr;observed[41]=cpu.ttbr0;observed[42]=cpu.ttbr1;observed[43]=cpu.tcr;
    observed[44]=cpu.mair;observed[45]=cpu.compiled_blocks;observed[46]=cpu.exception_pending;observed[47]=status;
    return status;
}
