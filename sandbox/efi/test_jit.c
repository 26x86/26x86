/* SPDX-License-Identifier: BSD-4-Clause */
#include "jit.h"
#ifdef _WIN32
typedef unsigned long DWORD;
#define MEM_COMMIT 0x1000
#define MEM_RESERVE 0x2000
#define MEM_RELEASE 0x8000
#define PAGE_READWRITE 0x04
#define PAGE_EXECUTE_READ 0x20
void *__stdcall VirtualAlloc(void *addr, size_t size, DWORD type, DWORD protect);
int __stdcall VirtualProtect(void *addr, size_t size, DWORD protect, DWORD *old);
int __stdcall VirtualFree(void *addr, size_t size, DWORD type);
static void *win_alloc(size_t n) { return VirtualAlloc(0,n,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE); }
static int win_perms(void *p,size_t n,int x,void *u) {
    (void)u;DWORD old;DWORD prot=x?PAGE_EXECUTE_READ:PAGE_READWRITE;
    return VirtualProtect(p,n,prot,&old)?0:-1;
}
static int win_free(void *p,size_t n) { (void)n;return VirtualFree(p,0,MEM_RELEASE)?0:-1; }
#define mmap(a,len,prot,flags,fd,off) win_alloc(len)
#define mprotect(p,n,prot) win_perms(p,n,(prot)&4,0)
#define munmap(p,n) win_free(p,n)
#define PROT_READ 1
#define PROT_WRITE 2
#define PROT_EXEC 4
#define MAP_PRIVATE 0
#define MAP_ANONYMOUS 0
#define MAP_FAILED ((void*)-1)
#else
#include <sys/mman.h>
#endif
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
static int perms(void *p,size_t n,int x,void *unused) { (void)unused;return mprotect(p,n,PROT_READ|(x?PROT_EXEC:PROT_WRITE)); }
static unsigned tests;
#define CHECK(x) do { ++tests;if(!(x)){fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x);exit(1);} } while(0)
static int run(vf_cpu *s,const uint32_t *g,size_t n,uint8_t *ram,vf_code *c,unsigned fuel) { return vf_run(s,(const uint8_t*)g,n*4,ram,256,c,fuel,perms,0); }
int main(void) {
    vf_code c={mmap(0,16384,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0),16384,0};
    CHECK(c.bytes!=MAP_FAILED);
    uint8_t ram[256]={0};vf_cpu s={0};
    /* sum 10..1; STR and LDR; branch back over two arithmetic instructions. */
    const uint32_t sum[]={0xd2800140,0xd2800001,0x8b000021,0xd1000400,0xb5ffffc0,0xf9000041,0xf9400043,0xd4400000};
    s.x[2]=16;CHECK(run(&s,sum,8,ram,&c,100)==VF_HALT);CHECK(s.x[1]==55);CHECK(s.x[3]==55);CHECK(ram[16]==55);CHECK(s.retired==35);
    /* W arithmetic zeroes the upper 32 bits; SP and ZR have distinct behavior. */
    const uint32_t narrow[]={0x11000400,0x910023ff,0xd280ffff,0xd4400000};
    memset(&s,0,sizeof(s));s.x[0]=UINT64_MAX;s.sp=16;
    CHECK(run(&s,narrow,4,ram,&c,100)==VF_HALT);CHECK(s.x[0]==0);CHECK(s.sp==24);
    const uint32_t move[]={0xd2824680,0xf2aacf00,0x728ffff0,0xd4400000};
    memset(&s,0,sizeof(s));s.x[16]=UINT64_MAX;
    CHECK(run(&s,move,4,ram,&c,100)==VF_HALT);CHECK(s.x[0]==UINT64_C(0x56781234));CHECK(s.x[16]==0xffff7fff);
    const uint32_t store[]={0xf9000020,0xd4400000};memset(&s,0,sizeof(s));s.x[1]=256;s.x[0]=123;
    CHECK(run(&s,store,2,ram,&c,10)==VF_DATA_ABORT);CHECK(s.pc==0);CHECK(s.retired==0);CHECK(ram[255]==0);
    CHECK(s.exception_pending==VF_EXCEPTION_DATA_ABORT);CHECK(s.exception_target_el==VF_EL1);
    CHECK(s.exception_from_lower_el==1);CHECK(s.far==256);CHECK(s.elr_el[VF_EL1]==0);
    CHECK((s.esr>>26)==VF_ESR_EC_DABT_LOWER);CHECK((s.esr&0x3f)==VF_ESR_FSC_TRANSLATION_L3);
    vf_cpu_clear_exception(&s);s.x[1]=UINT64_MAX-7;CHECK(run(&s,store,2,ram,&c,10)==VF_DATA_ABORT);
    const uint32_t wrap[]={0xf9000420};vf_cpu_clear_exception(&s);s.x[1]=UINT64_MAX-7;
    CHECK(run(&s,wrap,1,ram,&c,10)==VF_DATA_ABORT);CHECK(s.exception_pending==VF_EXCEPTION_DATA_ABORT);
    const uint32_t unaligned[]={0xf9000020};vf_cpu_reset(&s,VF_EL0);s.x[1]=1;
    CHECK(run(&s,unaligned,1,ram,&c,10)==VF_ALIGNMENT_FAULT);CHECK(s.far==1);
    CHECK(s.exception_pending==VF_EXCEPTION_ALIGNMENT_FAULT);CHECK((s.esr&0x3f)==VF_ESR_FSC_ALIGNMENT);
    const uint32_t unknown[]={0xd28000a0,0xffffffff};vf_cpu_reset(&s,VF_EL0);
    CHECK(run(&s,unknown,2,ram,&c,10)==VF_UNDEFINED_INSTRUCTION);CHECK(s.pc==4);CHECK(s.retired==1);
    CHECK(s.instruction==0xffffffff);CHECK(s.x[0]==5);CHECK(s.exception_pending==VF_EXCEPTION_UNDEFINED_INSTRUCTION);
    CHECK((s.esr>>26)==VF_ESR_EC_UNKNOWN);
    const uint32_t loop[]={0x14000000};memset(&s,0,sizeof(s));CHECK(run(&s,loop,1,ram,&c,7)==VF_BUDGET);CHECK(s.retired==7);
    vf_cpu_reset(&s,VF_EL0);s.pc=2;CHECK(run(&s,loop,1,ram,&c,7)==VF_INSTRUCTION_ABORT);
    CHECK(s.exception_pending==VF_EXCEPTION_INSTRUCTION_ABORT);CHECK(s.far==2);CHECK(s.elr_el[VF_EL1]==2);
    CHECK((s.esr>>26)==VF_ESR_EC_PC_ALIGNMENT);
    vf_cpu_reset(&s,VF_EL0);s.pc=4;CHECK(run(&s,loop,1,ram,&c,7)==VF_INSTRUCTION_ABORT);
    const uint32_t mrs_cntfrq[]={0xd53be000};vf_cpu_reset(&s,VF_EL0);
    CHECK(run(&s,mrs_cntfrq,1,ram,&c,10)==VF_SYSTEM_REGISTER_TRAP);
    CHECK(s.exception_pending==VF_EXCEPTION_SYSTEM_REGISTER_TRAP);CHECK(s.instruction==mrs_cntfrq[0]);
    CHECK((s.esr>>26)==VF_ESR_EC_SYSREG);

    /* The C-owned architectural state now has the same explicit register
     * bank boundary as the Rust reference core.  Reads/writes are tested
     * independently from the diagnostic JIT, which still rejects system
     * instructions until a C interpreter/IR path can commit them safely. */
    uint64_t sysreg_value=0;vf_cpu_reset(&s,VF_EL1);
    CHECK(vf_cpu_read_sysreg(&s,VF_SYSREG_KEY_CURRENT_EL,&sysreg_value)==VF_SYSREG_OK && sysreg_value==4);
    CHECK(vf_cpu_read_sysreg(&s,VF_SYSREG_KEY_ID_AA64MMFR0_EL1,&sysreg_value)==VF_SYSREG_OK && sysreg_value==UINT64_C(0x00101122));
    CHECK(vf_cpu_write_sysreg(&s,VF_SYSREG_KEY_TTBR0_EL1,0x4000)==VF_SYSREG_OK);
    CHECK(vf_cpu_read_sysreg(&s,VF_SYSREG_KEY_TTBR0_EL1,&sysreg_value)==VF_SYSREG_OK && sysreg_value==0x4000);
    CHECK(vf_cpu_write_sysreg(&s,VF_SYSREG_KEY_TTBR0_EL1,0x4001)==VF_SYSREG_INVALID_VALUE);
    CHECK(vf_cpu_set_current_el(&s,VF_EL0)==0);
    CHECK(vf_cpu_read_sysreg(&s,VF_SYSREG_KEY_SCTLR_EL1,&sysreg_value)==VF_SYSREG_PRIVILEGE);
    CHECK(vf_cpu_write_sysreg(&s,VF_SYSREG_KEY_CNTP_CVAL_EL0,3)==VF_SYSREG_OK);
    CHECK(vf_cpu_write_sysreg(&s,VF_SYSREG_KEY_CNTP_CTL_EL0,VF_TIMER_CTL_ENABLE)==VF_SYSREG_OK);
    vf_cpu_advance_counter(&s,3);
    CHECK(vf_cpu_timer_pending(&s));
    CHECK(vf_cpu_read_sysreg(&s,VF_SYSREG_KEY_CNTP_TVAL_EL0,&sysreg_value)==VF_SYSREG_OK && sysreg_value==0);
    CHECK(vf_cpu_write_sysreg(&s,VF_SYSREG_KEY_CNTP_CTL_EL0,0)==VF_SYSREG_OK && !vf_cpu_timer_pending(&s));

    const uint32_t unknown_sysreg[]={0xd53fffc0};vf_cpu_reset(&s,VF_EL0);
    CHECK(run(&s,unknown_sysreg,1,ram,&c,10)==VF_SYSTEM_REGISTER_TRAP);
    CHECK(s.exception_pending==VF_EXCEPTION_SYSTEM_REGISTER_TRAP);
    const uint32_t el1_sysreg[]={0xd5381000};vf_cpu_reset(&s,VF_EL0);
    CHECK(run(&s,el1_sysreg,1,ram,&c,10)==VF_PRIVILEGE_FAULT);
    CHECK(s.exception_pending==VF_EXCEPTION_PRIVILEGED_INSTRUCTION);
    const uint32_t eret[]={0xd69f03e0};vf_cpu_reset(&s,VF_EL0);
    CHECK(run(&s,eret,1,ram,&c,10)==VF_PRIVILEGE_FAULT);
    CHECK(s.exception_pending==VF_EXCEPTION_PRIVILEGED_INSTRUCTION);
    vf_cpu_reset(&s,VF_EL0);s.vbar_el[VF_EL1]=0x87ff;
    CHECK(vf_cpu_state_valid(&s));s.sp=0x1111;CHECK(vf_cpu_set_current_el(&s,VF_EL1)==0);
    CHECK(s.current_el==VF_EL1 && s.sp==0);s.sp=0x2222;
    CHECK(vf_cpu_set_current_el(&s,VF_EL0)==0);CHECK(s.sp==0x1111);
    CHECK(vf_cpu_set_current_el(&s,VF_EL1)==0);CHECK(s.sp==0x2222);
    CHECK(vf_cpu_set_current_el(&s,VF_EL0)==0);CHECK(s.sp==0x1111);
    CHECK(vf_cpu_raise_exception(&s,VF_EXCEPTION_DATA_ABORT,0x100,0x200,0,0)==0);
    CHECK(vf_cpu_take_exception(&s)==0);CHECK(s.current_el==VF_EL1);CHECK(s.pc==0x8400);
    CHECK(s.elr==0x100 && s.far==0x200 && s.exception_pending==VF_EXCEPTION_NONE);
    CHECK(s.exception_vector==0x8400 && (s.pstate&VF_PSTATE_DAIF_MASK)==VF_PSTATE_DAIF_MASK);
    CHECK(perms(c.bytes,c.capacity,0,0)==0);vf_code tiny={c.bytes,4,0};CHECK(vf_translate(&tiny,(const uint8_t*)sum,sizeof(sum),0,32)==VF_CODE_FULL);
    munmap(c.bytes,c.capacity);printf("{\"passed\":true,\"assertions\":%u,\"native_jit_executed\":true,\"wx_enforced\":true}\n",tests);return 0;
}
