/* SPDX-License-Identifier: BSD-4-Clause; test-only complete private CPU observer. */
#include "memory_boot_v2.h"
#include <string.h>
#include <stdio.h>
size_t test_mapped_cpu_size(void) {return sizeof(vf_cpu);}
typedef struct {vf_memory_callback_v2 callback;void *owner;vf_cpu *cpu;unsigned fetches,change_el;} observer;
static int32_t observed(void *opaque,const vf_memory_request_v2 *q,vf_memory_reply_v2 *r) {
    observer *o=opaque;int32_t status=o->callback(o->owner,q,r);
    if(q->operation==VF_MEMORY_FETCH && ++o->fetches==(o->change_el==3?1u:3u) && (o->change_el==1 || o->change_el==3) && !status)
        (void)vf_cpu_set_current_el(o->cpu,VF_EL0); /* Explicit test-only perturbation. */
    return status;
}
int test_mapped_snapshot(const vf_memory_controls_v2 *c,uint8_t *bytes,size_t capacity,
    uint64_t budget,vf_protect protect,void *protect_owner,vf_memory_callback_v2 callback,
    void *owner,const uint64_t initial[4],vf_pauth_step pauth,unsigned change_el,void *snapshot,
    vf_memory_run_result_v2 *result) {
    vf_cpu cpu;vf_cpu_reset(&cpu,VF_EL1);cpu.pc=0x10000;cpu.sp=0x10400;
    cpu.sp_el[0]=cpu.sp_el[1]=cpu.sp;cpu.pstate=0x3c5;cpu.guest_ram_base=0x40000000;
    cpu.sctlr=c->sctlr;cpu.ttbr0=c->ttbr0;cpu.ttbr1=c->ttbr1;cpu.tcr=c->tcr;
    if(change_el>=2){cpu.sp_el[0]=0x10800;cpu.sp_el[1]=0x10c00;cpu.pstate=0xa00003c5;}
    cpu.mair=c->mair;cpu.hcr_el2=c->hcr;cpu.scr_el3=c->scr;
    for(unsigned i=0;i<4;i++)cpu.x[i]=initial[i];cpu.pauth_step=pauth;if(change_el==100)cpu.id_aa64isar1=0x123456789abcdef0ULL;
    memset(result,0,sizeof(*result));result->base.abi_version=2;result->base.struct_size=sizeof(*result);
    vf_code code={bytes,capacity,0};
    observer o={callback,owner,&cpu,0,change_el};
    int status=(pauth?vf_run_memory_provider_pauth_v2:vf_run_memory_provider_v2)(&cpu,&code,budget,protect,protect_owner,c,observed,&o,result);
    vf_boot_snapshot(&cpu,status,&result->base.execution);result->base.guest_far=cpu.far_el[1];
    /* Function addresses differ with ASLR and are not architectural state. */
    uint64_t value=0;vf_cpu_read_sysreg(&cpu,0x4031,&value);printf("stored_isar1=%llx\n",(unsigned long long)value);cpu.pauth_step=0;memcpy(snapshot,&cpu,sizeof(cpu));return status;
}

/* Architectural checks read through the actual C type, never guessed offsets. */
int test_mapped_stack_state(const void *snapshot,const vf_memory_controls_v2 *c) {
    const vf_cpu *cpu=snapshot;
    return cpu->sp==0x10400 && cpu->sp_el[0]==0x10800 && cpu->sp_el[1]==0x10400 &&
        cpu->pstate==0xa00003c5 && cpu->current_el==VF_EL1 &&
        cpu->sctlr==c->sctlr && cpu->tcr==c->tcr && cpu->ttbr0==c->ttbr0 &&
        cpu->ttbr1==c->ttbr1 && cpu->mair==c->mair && cpu->hcr_el2==c->hcr && cpu->scr_el3==c->scr;
}
