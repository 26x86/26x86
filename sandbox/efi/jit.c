/* SPDX-License-Identifier: BSD-4-Clause
 * Original, specification-based A64 subset translator; no QEMU code incorporated.
 * Generated ABI: Microsoft x64; RCX=cpu, RDX=RAM, R8=RAM size. Only volatile
 * RAX/R9/R10/R11 and flags are modified; no stack or helper calls in JIT code.
 */
#include "jit.h"
static void b(vf_code *c, unsigned x) { if (c->used < c->capacity) c->bytes[c->used] = (uint8_t)x; ++c->used; }
static void u32(vf_code *c, uint32_t x) { for (int i=0;i<4;i++) b(c,x>>(8*i)); }
static void u64(vf_code *c, uint64_t x) { for (int i=0;i<8;i++) b(c,(unsigned)(x>>(8*i))); }
static void imm(vf_code *c,uint64_t x) { b(c,0x48);b(c,0xb8);u64(c,x); }
static void load(vf_code *c,unsigned reg,int sp,int wide) {
    if (reg==31 && !sp) { b(c,0x31);b(c,0xc0); return; }
    if(wide)b(c,0x48); b(c,0x8b);b(c,0x81);u32(c,reg*8);
}
static void save(vf_code *c,unsigned reg,int sp) {
    if(reg==31 && !sp)return; b(c,0x48);b(c,0x89);b(c,0x81);u32(c,reg*8);
}
static void field(vf_code *c,unsigned off,uint64_t x) { imm(c,x);b(c,0x48);b(c,0x89);b(c,0x81);u32(c,off); }
static void finish(vf_code *c,uint64_t pc,unsigned count,unsigned status) {
    field(c,offsetof(vf_cpu,pc),pc);
    b(c,0x48);b(c,0x81);b(c,0x81);u32(c,offsetof(vf_cpu,retired));u32(c,count);
    b(c,0xb8);u32(c,status);b(c,0xc3);
}
static size_t jcc(vf_code *c,unsigned cc) { b(c,0x0f);b(c,cc);size_t p=c->used;u32(c,0);return p; }
static void fix(vf_code *c,size_t p) {
    uint32_t rel=(uint32_t)(c->used-p-4);
    if(p+4<=c->capacity)for(int i=0;i<4;i++)c->bytes[p+i]=(uint8_t)(rel>>(8*i));
}
static uint32_t word(const uint8_t *p) { return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static int64_t sext(uint32_t x,unsigned bits) { return (int64_t)(int32_t)(x<<(32-bits))>>(32-bits); }
int vf_translate(vf_code *c,const uint8_t *guest,size_t size,uint64_t pc,unsigned limit) {
    c->used=0;
    for(unsigned n=0;n<limit;n++,pc+=4) {
        if((pc&3) || size<4 || pc>size-4) { finish(c,pc,n,VF_FETCH_FAULT);break; }
        uint32_t w=word(guest+pc); unsigned rd=w&31,rn=(w>>5)&31,wide=w>>31;
        if((w&0x7f800000)==0x52800000 || (w&0x7f800000)==0x72800000) {
            unsigned shift=((w>>21)&3)*16; uint64_t v=(uint64_t)((w>>5)&65535)<<shift;
            if(!wide && shift>=32)goto bad;
            if((w&0x7f800000)==0x72800000) {
                load(c,rd,0,wide); b(c,0x49);b(c,0xb9);u64(c,~(UINT64_C(65535)<<shift));
                b(c,0x4c);b(c,0x21);b(c,0xc8);b(c,0x49);b(c,0xb9);u64(c,v);
                b(c,0x4c);b(c,0x09);b(c,0xc8);
            } else imm(c,v);
            save(c,rd,0);
        } else if((w&0x3f800000)==0x11000000) {
            /* ADD/SUB immediate without flag update: R31 is SP, including WSP. */
            uint32_t v=((w>>10)&4095)<<(((w>>22)&1)?12:0);
            load(c,rn,1,wide);if(wide)b(c,0x48);b(c,0x05+((w>>30)&1)*0x28);u32(c,v);save(c,rd,1);
        } else if((w&0x3fe0fc00)==0x0b000000) {
            /* ADD/SUB register, LSL #0 only, R31 is ZR. */
            unsigned rm=(w>>16)&31;load(c,rm,0,wide);b(c,0x49);b(c,0x89);b(c,0xc1);
            load(c,rn,0,wide);b(c,wide?0x4c:0x44);b(c,((w>>30)&1)?0x29:0x01);b(c,0xc8);save(c,rd,0);
        } else if((w&0xffc00000)==0xf9000000 || (w&0xffc00000)==0xf9400000) {
            /* 64-bit LDR/STR unsigned immediate. Guest address is an offset into RAM. */
            load(c,rn,1,1);b(c,0x49);b(c,0x89);b(c,0xc1);
            b(c,0x49);b(c,0x81);b(c,0xc1);u32(c,((w>>10)&4095)*8);
            size_t carry=jcc(c,0x82); /* Address overflow is a data fault. */
            b(c,0x4d);b(c,0x89);b(c,0xc2);b(c,0x49);b(c,0x83);b(c,0xea);b(c,8);
            b(c,0x4d);b(c,0x39);b(c,0xd1);size_t bound=jcc(c,0x87);
            if(w&0x400000) { b(c,0x4a);b(c,0x8b);b(c,0x04);b(c,0x0a);save(c,rd,0); }
            else { load(c,rd,0,1);b(c,0x4a);b(c,0x89);b(c,0x04);b(c,0x0a); }
            b(c,0xe9);size_t next=c->used;u32(c,0);
            fix(c,carry);fix(c,bound);finish(c,pc,n,VF_DATA_FAULT);fix(c,next);
        } else if((w&0x7e000000)==0x34000000) {
            load(c,rd,0,wide);b(c,0x48);b(c,0x85);b(c,0xc0);
            size_t fall=jcc(c,(w&0x1000000)?0x84:0x85);
            finish(c,pc+(uint64_t)(sext((w>>5)&0x7ffff,19)*4),n+1,VF_NEXT);
            fix(c,fall);finish(c,pc+4,n+1,VF_NEXT);break;
        } else if((w&0xfc000000)==0x14000000) {
            finish(c,pc+(uint64_t)(sext(w&0x3ffffff,26)*4),n+1,VF_NEXT);break;
        } else if(w==0xd503201f) { /* NOP */
        } else if(w==0xd4400000) { /* HLT #0 is the synthetic monitor exit, not an EL exception. */
            finish(c,pc+4,n+1,VF_HALT);break;
        } else {
bad:       b(c,0xc7);b(c,0x81);u32(c,offsetof(vf_cpu,instruction));u32(c,w);
            finish(c,pc,n,VF_BAD_INSTRUCTION);break;
        }
        if(n+1==limit)finish(c,pc+4,n+1,VF_NEXT);
    }
    return c->used>c->capacity?VF_CODE_FULL:VF_NEXT;
}
int vf_host_supported(void) {
    uint32_t a=1,bv,c,d;
    __asm__ volatile("cpuid":"+a"(a),"=b"(bv),"=c"(c),"=d"(d));
    return (c & ((1u<<19)|(1u<<20)))==((1u<<19)|(1u<<20));
}
int vf_run(vf_cpu *cpu,const uint8_t *guest,size_t size,uint8_t *ram,size_t ram_size,
           vf_code *code,uint64_t budget,vf_protect protect,void *opaque) {
    if(!cpu||!guest||!ram||ram_size<8||!code||!code->bytes||!protect)return VF_DATA_FAULT;
    uint64_t start=cpu->retired;
    while(cpu->retired-start<budget) {
        uint64_t left=budget-(cpu->retired-start);unsigned count=left>32?32:(unsigned)left;
        if(protect(code->bytes,code->capacity,0,opaque))return cpu->status=VF_PROTECTION;
        int status=vf_translate(code,guest,size,cpu->pc,count);
        if(status)return cpu->status=status;
        if(protect(code->bytes,code->capacity,1,opaque))return cpu->status=VF_PROTECTION;
        /* CPUID serializes stores before execution on x86; no I-cache invalidate needed. */
        uint32_t a=0,bv,cv,d;__asm__ volatile("cpuid":"+a"(a),"=b"(bv),"=c"(cv),"=d"(d)::"memory");
        status=((vf_entry)(void *)code->bytes)(cpu,ram,ram_size);
        if(status!=VF_NEXT)return cpu->status=status;
    }
    return cpu->status=VF_BUDGET;
}
