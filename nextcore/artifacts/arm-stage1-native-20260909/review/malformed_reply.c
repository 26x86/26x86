#include <stdio.h>
#include "/home/sharh/work/bp32-ise-native-mmu/runtime/jit.c"
static int32_t cb(void *owner,const vf_memory_request_v2 *q,vf_memory_reply_v2 *r){(void)q;*r=*(vf_memory_reply_v2*)owner;return 0;}
int main(void){for(unsigned test=0;test<4;test++){
 vf_cpu cpu;vf_cpu_reset(&cpu,VF_EL1);cpu.pc=0x10000;cpu.sctlr=0x30d00803;
 vf_memory_controls_v2 controls={2,80,1,0,0x30d00803,0x1000,0x1000,16|(UINT64_C(16)<<16)|(UINT64_C(2)<<30),0x44,0,0,1};
 vf_memory_request_v2 q=memory_request_v2(&cpu,&controls,VF_MEMORY_LOAD,8,1,0x20000);q.controls=controls;
 vf_memory_reply_v2 reply={.abi_version=2,.struct_size=128,.result=1,.fault=VF_MEMORY_V2_TRANSLATION,.level=3,.context=VF_MEMORY_V2_WALK,.fsc=7,.metadata_flags=1,.address=q.address,.esr=0x96000007,.epoch=1,.descriptor_pa=0x4000};
 if(test==0){cpu.pc=0x10001;q.operation=VF_MEMORY_FETCH;q.width=4;q.pc=cpu.pc;q.address=cpu.pc;reply.address=cpu.pc;reply.esr=0x86000007;}
 if(test==1){q.address++;reply.address=q.address;}
 if(test==2){reply.fault=VF_MEMORY_V2_ADDRESS_SIZE;reply.level=0;reply.context=VF_MEMORY_V2_CACHED_LEAF;reply.fsc=0;reply.esr=0x96000000;}
 if(test==3){reply.context=VF_MEMORY_V2_LEAF;}
 vf_memory_reply_v2 out;vf_memory_run_result_v2 run={0};
 int status=memory_exchange_v2(&cpu,cb,&reply,&q,&out,&run);
 printf("case=%u status=%d provider=%u ESR=%llx retired=%llu context=%u level=%u\n",test,status,run.base.provider_status,(unsigned long long)cpu.esr_el[1],(unsigned long long)cpu.retired,run.last_reply.context,run.last_reply.level);
 if(status==VF_DATA_FAULT || run.base.provider_status)return 1;
}return 0;}
