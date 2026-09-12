/* Authored regression comparison against the unchanged a8a06d native profile. */
#include "jit.h"
#include <sys/mman.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
#define CHECK(x) do { checks++; if (!(x)) { fprintf(stderr,"line%d: %s\n",__LINE__,#x); exit(1); } } while (0)
static int protect_code(void *p,size_t n,int execute,void *unused) {
    (void)unused; return mprotect(p,n,PROT_READ|(execute?PROT_EXEC:PROT_WRITE));
}
static void one(vf_code *code,uint32_t word,uint64_t source,uint64_t target,unsigned expected_status,uint64_t expected_pc,unsigned retired,unsigned link) {
    vf_cpu cpu; vf_cpu_reset(&cpu,VF_EL1); cpu.x[0]=source; cpu.x[30]=target;
    cpu.sp=0x9870; cpu.pstate=0xb00003c5;
    uint64_t expected[32]; memcpy(expected,cpu.x,sizeof(expected)); if(link)expected[30]=4;
    uint8_t ram[8]; memset(ram,0xa5,sizeof(ram));
    CHECK(vf_run(&cpu,(const uint8_t*)&word,4,ram,sizeof(ram),code,1,protect_code,0)==(int)expected_status);
    CHECK(cpu.pc==expected_pc && cpu.retired==retired);
    CHECK(!memcmp(cpu.x,expected,sizeof(expected)) && cpu.sp==0x9870 && cpu.pstate==0xb00003c5);
    CHECK(cpu.compiled_blocks==1);
    if(!retired)CHECK(cpu.instruction==word && cpu.esr_el[VF_EL1]==(1u<<25));
    for(unsigned i=0;i<sizeof(ram);i++)CHECK(ram[i]==0xa5);
}
int main(void) {
    vf_code code={mmap(0,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0),4096,0};
    CHECK(code.bytes!=MAP_FAILED);
    for(unsigned wide=0;wide<2;wide++)for(unsigned nonzero=0;nonzero<2;nonzero++)for(unsigned zr=0;zr<2;zr++) {
        uint32_t word=0x34000040|(wide<<31)|(nonzero<<24)|(zr?31:0);
        unsigned take=(zr?0:wide)==nonzero;
        one(&code,word,UINT64_C(1)<<32,0x1234,VF_BUDGET,take?8:4,1,0);
    }
    const uint32_t ops[]={0xd61f0000,0xd63f0000,0xd65f0000};
    for(unsigned op=0;op<3;op++)for(unsigned lr=0;lr<2;lr++) {
        one(&code,ops[op]|((lr?30:0)<<5),32,64,VF_BUDGET,lr?64:32,1,op==1);
    }
    for(unsigned op=0;op<3;op++)one(&code,ops[op]|(31<<5),32,0x1234,VF_UNDEFINED_INSTRUCTION,0,0,0);
    const uint32_t invalid[]={0xd61f0001,0xd63f0010,0xd65f001f,0xd67f0000,0xd6bf0000,0xd71f0000};
    for(unsigned i=0;i<sizeof(invalid)/sizeof(*invalid);i++)one(&code,invalid[i],32,0x1234,VF_UNDEFINED_INSTRUCTION,0,0,0);
    CHECK(munmap(code.bytes,4096)==0);
    printf("{\"passed\":true,\"native_generated_x86\":true,\"checks\":%u,\"rn31_is_profile_restriction\":true}\n",checks);
}
