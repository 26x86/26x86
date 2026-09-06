/* SPDX-License-Identifier: BSD-4-Clause */
#include "jit.h"
#include <sys/mman.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
static int perms(void *p,size_t n,int x,void *unused) { (void)unused;return mprotect(p,n,PROT_READ|(x?PROT_EXEC:PROT_WRITE)); }
static unsigned tests;
#define CHECK(x) do { ++tests;if(!(x)){fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x);exit(1);} } while(0)
static int run(vf_cpu *s,const uint32_t *g,size_t n,uint8_t *ram,vf_code *c,unsigned fuel) { return vf_run(s,(const uint8_t*)g,n*4,ram,256,c,fuel,perms,0); }
int main(void) {
    vf_code c={mmap(0,16384,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0),16384,0};
    CHECK(c.bytes!=MAP_FAILED);uint8_t ram[256]={0};vf_cpu s={0};
    /* sum 10..1; STR and LDR; branch back over two arithmetic instructions. */
    const uint32_t sum[]={0xd2800140,0xd2800001,0x8b000021,0xd1000400,0xb5ffffc0,0xf9000041,0xf9400043,0xd4400000};
    s.x[2]=16;CHECK(run(&s,sum,8,ram,&c,100)==VF_HALT);CHECK(s.x[1]==55);CHECK(s.x[3]==55);CHECK(ram[16]==55);CHECK(s.retired==35);
    /* W arithmetic zeroes the upper 32 bits; SP and ZR have distinct behavior. */
    const uint32_t narrow[]={0x11000400,0x910023ff,0xd280ffff,0xd4400000};
    memset(&s,0,sizeof(s));s.x[0]=UINT64_MAX;s.x[31]=16;
    CHECK(run(&s,narrow,4,ram,&c,100)==VF_HALT);CHECK(s.x[0]==0);CHECK(s.x[31]==24);
    const uint32_t move[]={0xd2824680,0xf2aacf00,0x728ffff0,0xd4400000};
    memset(&s,0,sizeof(s));s.x[16]=UINT64_MAX;
    CHECK(run(&s,move,4,ram,&c,100)==VF_HALT);CHECK(s.x[0]==UINT64_C(0x56781234));CHECK(s.x[16]==0xffff7fff);
    const uint32_t store[]={0xf9000020,0xd4400000};memset(&s,0,sizeof(s));s.x[1]=249;s.x[0]=123;
    CHECK(run(&s,store,2,ram,&c,10)==VF_DATA_FAULT);CHECK(s.pc==0);CHECK(s.retired==0);CHECK(ram[255]==0);
    s.x[1]=UINT64_MAX;CHECK(run(&s,store,2,ram,&c,10)==VF_DATA_FAULT);
    const uint32_t wrap[]={0xf9000420};s.x[1]=UINT64_MAX-3;CHECK(run(&s,wrap,1,ram,&c,10)==VF_DATA_FAULT);
    const uint32_t unknown[]={0xd28000a0,0xffffffff};memset(&s,0,sizeof(s));
    CHECK(run(&s,unknown,2,ram,&c,10)==VF_BAD_INSTRUCTION);CHECK(s.pc==4);CHECK(s.retired==1);CHECK(s.instruction==0xffffffff);CHECK(s.x[0]==5);
    const uint32_t loop[]={0x14000000};memset(&s,0,sizeof(s));CHECK(run(&s,loop,1,ram,&c,7)==VF_BUDGET);CHECK(s.retired==7);
    memset(&s,0,sizeof(s));s.pc=2;CHECK(run(&s,loop,1,ram,&c,7)==VF_FETCH_FAULT);
    memset(&s,0,sizeof(s));s.pc=4;CHECK(run(&s,loop,1,ram,&c,7)==VF_FETCH_FAULT);
    CHECK(perms(c.bytes,c.capacity,0,0)==0);vf_code tiny={c.bytes,4,0};CHECK(vf_translate(&tiny,(const uint8_t*)sum,sizeof(sum),0,32)==VF_CODE_FULL);
    munmap(c.bytes,c.capacity);printf("{\"passed\":true,\"assertions\":%u,\"native_jit_executed\":true,\"wx_enforced\":true}\n",tests);return 0;
}
