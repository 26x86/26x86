/* SPDX-License-Identifier: BSD-4-Clause
 * Original, specification-based A64 subset translator; no QEMU code incorporated.
 * Generated ABI: Microsoft x64; RCX=cpu, RDX=RAM, R8=RAM size. Only volatile
 * RAX/R9/R10/R11 and flags are modified; no stack or helper calls in JIT code.
 */
#include "jit.h"
#include "memory_boot.h"
#include "memory_boot_v2.h"
/* Private dispatcher signal, never an exported terminal execution status. */
#define VF_MEMORY_DISPATCH UINT32_C(0x7ffffffe)
static void b(vf_code *c, unsigned x) { if (c->used < c->capacity) c->bytes[c->used] = (uint8_t)x; ++c->used; }
static void u32(vf_code *c, uint32_t x) { for (int i=0;i<4;i++) b(c,x>>(8*i)); }
static void u64(vf_code *c, uint64_t x) { for (int i=0;i<8;i++) b(c,(unsigned)(x>>(8*i))); }
static void imm(vf_code *c,uint64_t x) { b(c,0x48);b(c,0xb8);u64(c,x); }
static void load(vf_code *c,unsigned reg,int sp,int wide) {
    if (reg==31) {
        if (!sp) { b(c,0x31);b(c,0xc0); return; }
        if (wide) b(c,0x48); b(c,0x8b);b(c,0x81);u32(c,offsetof(vf_cpu,sp)); return;
    }
    if(wide)b(c,0x48); b(c,0x8b);b(c,0x81);u32(c,reg*8);
}
static void save(vf_code *c,unsigned reg,int sp) {
    if(reg==31) { if(sp) { b(c,0x48);b(c,0x89);b(c,0x81);u32(c,offsetof(vf_cpu,sp)); } return; }
    b(c,0x48);b(c,0x89);b(c,0x81);u32(c,reg*8);
}
static void field(vf_code *c,unsigned off,uint64_t x) { imm(c,x);b(c,0x48);b(c,0x89);b(c,0x81);u32(c,off); }
static void field32(vf_code *c,unsigned off,uint32_t x) {
    b(c,0xc7);b(c,0x81);u32(c,off);u32(c,x);
}
static void save_host_r11(vf_code *c,unsigned off) {
    b(c,0x4c);b(c,0x89);b(c,0x99);u32(c,off);
}
static void save_arithmetic_flags(vf_code *c,int subtract) {
    /* Capture every flag before shifts/ORs clobber host flags. AArch64 C
     * means no borrow for subtraction, the inverse of x86 CF. The result
     * has already been saved; AL can now hold the overflow predicate. */
    b(c,0x41);b(c,0x0f);b(c,0x98);b(c,0xc1); /* sets r9b */
    b(c,0x41);b(c,0x0f);b(c,0x94);b(c,0xc2); /* setz r10b */
    b(c,0x41);b(c,0x0f);b(c,subtract?0x93:0x92);b(c,0xc3);
    b(c,0x0f);b(c,0x90);b(c,0xc0); /* seto al */
    b(c,0x45);b(c,0x0f);b(c,0xb6);b(c,0xc9);
    b(c,0x45);b(c,0x0f);b(c,0xb6);b(c,0xd2);
    b(c,0x45);b(c,0x0f);b(c,0xb6);b(c,0xdb);
    b(c,0x0f);b(c,0xb6);b(c,0xc0);
    b(c,0x41);b(c,0xc1);b(c,0xe1);b(c,31);
    b(c,0x41);b(c,0xc1);b(c,0xe2);b(c,30);
    b(c,0x41);b(c,0xc1);b(c,0xe3);b(c,29);
    b(c,0xc1);b(c,0xe0);b(c,28);
    b(c,0x44);b(c,0x09);b(c,0xc8);
    b(c,0x44);b(c,0x09);b(c,0xd0);
    b(c,0x44);b(c,0x09);b(c,0xd8);
    b(c,0x49);b(c,0xb9);u64(c,~UINT64_C(0xf0000000));
    b(c,0x4c);b(c,0x21);b(c,0x89);u32(c,offsetof(vf_cpu,pstate));
    b(c,0x48);b(c,0x09);b(c,0x81);u32(c,offsetof(vf_cpu,pstate));
}
static void finish(vf_code *c,uint64_t pc,unsigned count,unsigned status) {
    field(c,offsetof(vf_cpu,pc),pc);
    b(c,0x48);b(c,0x81);b(c,0x81);u32(c,offsetof(vf_cpu,retired));u32(c,count);
    b(c,0xb8);u32(c,status);b(c,0xc3);
}
static size_t jcc(vf_code *c,unsigned cc) { b(c,0x0f);b(c,cc);size_t p=c->used;u32(c,0);return p; }
static void fix_to(vf_code *c,size_t p,size_t target) {
    uint32_t rel=(uint32_t)(target-p-4);
    if(p+4<=c->capacity)for(int i=0;i<4;i++)c->bytes[p+i]=(uint8_t)(rel>>(8*i));
}
static void fix(vf_code *c,size_t p) { fix_to(c,p,c->used); }
/* Branch to the caller's false path using committed guest NZCV. Zero means
 * AL/NV: both predicates always hold in A64 ConditionHolds. */
static size_t condition_false(vf_code *c,unsigned condition) {
    if(condition>=14)return 0;
    b(c,0x8b);b(c,0x81);u32(c,offsetof(vf_cpu,pstate));
    b(c,0xc1);b(c,0xe8);b(c,28);
    unsigned group=condition>>1,fall_cc=0x84;
    if(group<4) {
        const unsigned masks[4]={4,2,8,1};
        b(c,0x83);b(c,0xe0);b(c,masks[group]);
    } else if(group==4) {
        b(c,0x83);b(c,0xe0);b(c,6);
        b(c,0x83);b(c,0xf8);b(c,2);fall_cc=0x85;
    } else {
        b(c,0x41);b(c,0x89);b(c,0xc1);
        b(c,0x41);b(c,0xc1);b(c,0xe9);b(c,3);
        b(c,0x44);b(c,0x31);b(c,0xc8);
        b(c,0x83);b(c,0xe0);b(c,group==5?1:5);fall_cc=0x85;
    }
    if(condition&1)fall_cc^=1;
    return jcc(c,fall_cc);
}
static uint32_t word(const uint8_t *p) { return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static int64_t sext(uint32_t x,unsigned bits) { return (int64_t)(int32_t)(x<<(32-bits))>>(32-bits); }
static int logical_mask(uint32_t w,uint64_t *mask) {
    unsigned width=(w>>31)?64:32,n=(w>>22)&1,s=(w>>10)&63,r=(w>>16)&63;
    if(width==32 && n)return 0;
    unsigned tag=(n<<6)|(~s&63),len=0;
    while(tag>1) {tag>>=1;len++;}
    if(len<1)return 0;
    unsigned size=1u<<len,levels=size-1;
    if(size>width || (s&levels)==levels)return 0;
    s&=levels;r&=levels;
    uint64_t element=(UINT64_C(1)<<(s+1))-1;
    if(r)element=(element>>r)|(element<<(size-r));
    if(size<64)element&=(UINT64_C(1)<<size)-1;
    *mask=0;for(unsigned at=0;at<width;at+=size)*mask|=element<<at;
    return 1;
}
static uint32_t sysreg_key(uint32_t w) { return (w >> 5) & 0x7fff; }
static int is_system_encoding(uint32_t w) { return (w & 0xffc00000) == 0xd5000000; }
static int is_exception_return(uint32_t w) {
    return w == 0xd69f03e0 || w == 0xd69f0be0 || w == 0xd69f0fe0;
}

static int sysreg_el0_visible(uint32_t key) {
    switch (key) {
    case 0x5801: /* CTR_EL0 */
    case 0x5802: /* DCZID_EL0 */
    case 0x5a20: /* FPCR */
    case 0x5a21: /* FPSR */
    case VF_SYSREG_KEY_TPIDR_EL0:
    case VF_SYSREG_KEY_TPIDRRO_EL0:
    case VF_SYSREG_KEY_CNTFRQ_EL0:
    case VF_SYSREG_KEY_CNTPCT_EL0:
    case VF_SYSREG_KEY_CNTVCT_EL0:
    case VF_SYSREG_KEY_CNTP_TVAL_EL0:
    case VF_SYSREG_KEY_CNTP_CTL_EL0:
    case VF_SYSREG_KEY_CNTP_CVAL_EL0:
    case VF_SYSREG_KEY_CNTV_CTL_EL0:
    case VF_SYSREG_KEY_CNTV_CVAL_EL0:
    case VF_SYSREG_KEY_CURRENT_EL:
        return 1;
    default:
        return 0;
    }
}

static int sysreg_el1_only(uint32_t key) {
    switch (key) {
    case VF_SYSREG_KEY_ID_AA64MMFR0_EL1:
    case VF_SYSREG_KEY_ID_AA64ISAR1_EL1:
    case VF_SYSREG_KEY_SCTLR_EL1:
    case VF_SYSREG_KEY_TTBR0_EL1:
    case VF_SYSREG_KEY_TTBR1_EL1:
    case VF_SYSREG_KEY_TCR_EL1:
    case VF_SYSREG_KEY_MAIR_EL1:
    case VF_SYSREG_KEY_VBAR_EL1:
    case VF_SYSREG_KEY_ESR_EL1:
    case VF_SYSREG_KEY_FAR_EL1:
    case VF_SYSREG_KEY_ELR_EL1:
    case VF_SYSREG_KEY_SPSR_EL1:
        return 1;
    default:
        return 0;
    }
}

static int is_mrs_msr(uint32_t w) {
    return (w & 0xffe00000) == 0xd5200000 ||
           (w & 0xffe00000) == 0xd5000000;
}

static unsigned thread_offset(uint32_t key) {
    switch (key) {
    case VF_SYSREG_KEY_TPIDR_EL0: return offsetof(vf_cpu,tpidr_el0);
    case VF_SYSREG_KEY_TPIDRRO_EL0: return offsetof(vf_cpu,tpidrro_el0);
    case VF_SYSREG_KEY_TPIDR_EL1: return offsetof(vf_cpu,tpidr_el1);
    default: return 0;
    }
}

static int known_privileged(uint32_t w, uint32_t current_el) {
    /* ERET is legal only at an exception level that owns an exception bank;
     * EL1+ is still a system-register phase boundary until SPSR/ELR reads are
     * implemented.  DAIF writes are privileged at EL0. */
    if (is_exception_return(w))
        return current_el == VF_EL0;
    if (w == 0xd503207f || w == 0xd503205f ||
        (w & 0xffe0001f) == 0xd4000002 ||
        (w & 0xffe0001f) == 0xd4000003)
        return current_el == VF_EL0;
    if ((w & 0xfffff0ff) == 0xd50340df || (w & 0xfffff0ff) == 0xd50340ff ||
        (w & 0xfffffeff) == 0xd50040bf)
        return current_el == VF_EL0;
    if (is_mrs_msr(w) && current_el == VF_EL0 &&
        !sysreg_el0_visible(sysreg_key(w)) &&
        sysreg_el1_only(sysreg_key(w)))
        return 1;
    return 0;
}

static int system_boundary(uint32_t w, uint32_t current_el) {
    if (is_exception_return(w)) return VF_SYSTEM_REGISTER_TRAP;
    if (!is_system_encoding(w)) return 0;
    if (w == 0xd503201f) return 0; /* NOP */
    if (known_privileged(w, current_el)) return VF_PRIVILEGE_FAULT;
    return VF_SYSTEM_REGISTER_TRAP;
}

typedef struct {
    unsigned width,count,read,signed_load,result64,mode,rn,rt,rt2;
    int32_t displacement;
} memory_shape;
static int memory_family(uint32_t w) {
    return (w&0x3a000000)==0x28000000 || (w&0x3b000000)==0x39000000;
}
static int decode_memory(uint32_t w,memory_shape *d) {
    *d=(memory_shape){0};d->rn=(w>>5)&31;d->rt=w&31;
    if((w&0x3a000000)==0x28000000) {
        unsigned opc=w>>30;d->mode=(w>>23)&3;d->read=(w>>22)&1;d->rt2=(w>>10)&31;
        if((w&(1u<<26)) || (opc!=0 && opc!=2) || !d->mode ||
           (d->mode!=2 && d->rn!=31 && (d->rn==d->rt || d->rn==d->rt2)) ||
           (d->read && d->rt==d->rt2))return 0;
        d->width=opc==2?8:4;d->count=2;d->result64=opc==2;
        d->displacement=(int32_t)(sext((w>>15)&127,7)*d->width);return 1;
    }
    if((w&0x3b000000)==0x39000000) {
        unsigned size=w>>30,opc=(w>>22)&3;
        if((w&(1u<<26)) || (opc>=2 && (size==3 || (opc==3 && size==2))))return 0;
        d->width=1u<<size;d->count=1;d->read=opc!=0;d->signed_load=opc>=2;
        d->result64=opc==2 || size==3;d->mode=2;
        d->displacement=((w>>10)&4095)*d->width;return 1;
    }
    return 0;
}
static int translate_impl(vf_code *c,const vf_cpu *cpu,const uint8_t *guest,
                          size_t size,uint64_t pc,unsigned limit,int provider) {
    uint32_t current_el = cpu ? cpu->current_el : VF_EL0;
    uint64_t base = cpu ? cpu->guest_ram_base : 0;
    c->used=0;
    for(unsigned n=0;n<limit;n++,pc+=4) {
        if(!provider && ((pc&3) || size<4 || pc<base || pc-base>size-4 || pc>UINT64_MAX-4)) { finish(c,pc,n,VF_INSTRUCTION_ABORT);break; }
        uint32_t w=word(guest+(provider?0:pc-base)); unsigned rd=w&31,rn=(w>>5)&31,wide=w>>31;
        unsigned thread = is_mrs_msr(w) ? thread_offset(sysreg_key(w)) : 0;
        if(provider && memory_family(w)) {
            field32(c,offsetof(vf_cpu,instruction),w);
            finish(c,pc,n,VF_MEMORY_DISPATCH);break;
        } else if((w&0x3fe00410)==0x3a400000) {
            /* CCMP/CCMN, register or imm5. R31 is ZR, never SP. */
            size_t fallback=condition_false(c,(w>>12)&15);
            if(w&(1u<<11))imm(c,(w>>16)&31);else load(c,(w>>16)&31,0,wide);
            b(c,0x49);b(c,0x89);b(c,0xc1);
            load(c,rn,0,wide);b(c,wide?0x4c:0x44);b(c,((w>>30)&1)?0x29:0x01);b(c,0xc8);
            save_arithmetic_flags(c,(w>>30)&1);
            if(fallback) {
                b(c,0xe9);size_t done=c->used;u32(c,0);fix(c,fallback);
                imm(c,(uint64_t)(w&15)<<28);
                b(c,0x49);b(c,0xb9);u64(c,~UINT64_C(0xf0000000));
                b(c,0x4c);b(c,0x21);b(c,0x89);u32(c,offsetof(vf_cpu,pstate));
                b(c,0x48);b(c,0x09);b(c,0x81);u32(c,offsetof(vf_cpu,pstate));fix(c,done);
            }
        } else if((w&0x1f800000)==0x12000000) {
            uint64_t mask;unsigned op=(w>>29)&3;
            if(!logical_mask(w,&mask)) {
                field32(c,offsetof(vf_cpu,instruction),w);
                finish(c,pc,n,VF_UNDEFINED_INSTRUCTION);break;
            }
            load(c,rn,0,wide);b(c,0x49);b(c,0xb9);u64(c,mask);
            b(c,wide?0x4c:0x44);b(c,op==1?0x09:op==2?0x31:0x21);b(c,0xc8);
            save(c,rd,op!=3);
            if(op==3)save_arithmetic_flags(c,0); /* Logical host C/V are zero. */
        } else if(thread) {
            int read = (w & 0x00200000) != 0;
            if(current_el==VF_EL0 && (sysreg_key(w)==VF_SYSREG_KEY_TPIDR_EL1 ||
                (!read && sysreg_key(w)==VF_SYSREG_KEY_TPIDRRO_EL0))) {
                field32(c,offsetof(vf_cpu,instruction),w);
                finish(c,pc,n,VF_UNDEFINED_INSTRUCTION);break;
            }
            /* These software thread values have no hardware side effects.
             * Rt31 is XZR for both directions, never SP. No helper/callback
             * or native TLS register is involved. Guest NZCV stays intact. */
            if(read) {
                b(c,0x48);b(c,0x8b);b(c,0x81);u32(c,thread);save(c,rd,0);
            } else {
                load(c,rd,0,1);b(c,0x48);b(c,0x89);b(c,0x81);u32(c,thread);
            }
        } else if((w&0x7f800000)==0x52800000 || (w&0x7f800000)==0x72800000 || (w&0x7f800000)==0x12800000) {
            unsigned shift=((w>>21)&3)*16; uint64_t v=(uint64_t)((w>>5)&65535)<<shift;
            if(!wide && shift>=32) {
                field32(c,offsetof(vf_cpu,instruction),w);
                finish(c,pc,n,VF_UNDEFINED_INSTRUCTION);
                break;
            }
            if((w&0x7f800000)==0x72800000) {
                load(c,rd,0,wide); b(c,0x49);b(c,0xb9);u64(c,~(UINT64_C(65535)<<shift));
                b(c,0x4c);b(c,0x21);b(c,0xc8);b(c,0x49);b(c,0xb9);u64(c,v);
                b(c,0x4c);b(c,0x09);b(c,0xc8);
            } else {
                if((w&0x7f800000)==0x12800000)v=wide?~v:(uint32_t)~v;
                imm(c,v);
            }
            save(c,rd,0);
        } else if((w&0x1f000000)==0x10000000) {
            /* ADR/ADRP use the guest PC; host allocation addresses never
             * participate in PC-relative address materialization. */
            int64_t displacement=sext((((w>>5)&0x7ffff)<<2)|((w>>29)&3),21);
            uint64_t target=(w>>31)?(pc&~UINT64_C(0xfff))+(uint64_t)(displacement*4096)
                                   :pc+(uint64_t)displacement;
            imm(c,target);save(c,rd,0);
        } else if((w&0x7fe0ffe0)==0x2a0003e0) {
            /* MOV register alias: ORR Xd/XZR/Xm, LSL #0. */
            load(c,(w>>16)&31,0,wide);save(c,rd,0);
        } else if((w&0x1f800000)==0x11000000) {
            /* ADD/SUB(S) immediate. Rn31 is SP; Rd31 is ZR for the flag
             * forms (CMP/CMN aliases), otherwise SP, including WSP. */
            uint32_t v=((w>>10)&4095)<<(((w>>22)&1)?12:0);
            int subtract=(w>>30)&1,flags=(w>>29)&1;
            load(c,rn,1,wide);if(wide)b(c,0x48);b(c,0x05+subtract*0x28);u32(c,v);
            save(c,rd,!flags);
            if(flags)save_arithmetic_flags(c,subtract);
        } else if((w&0x1f200000)==0x0b000000) {
            /* ADD/SUB(S) shifted register. Both R31 sources are ZR. */
            unsigned rm=(w>>16)&31,shift=(w>>22)&3,amount=(w>>10)&63;
            if(shift==3 || (!wide && amount>=32)) {
                field32(c,offsetof(vf_cpu,instruction),w);
                finish(c,pc,n,VF_UNDEFINED_INSTRUCTION);break;
            }
            load(c,rm,0,wide);
            if(amount) {if(wide)b(c,0x48);b(c,0xc1);b(c,shift==0?0xe0:shift==1?0xe8:0xf8);b(c,amount);}
            b(c,0x49);b(c,0x89);b(c,0xc1);
            load(c,rn,0,wide);b(c,wide?0x4c:0x44);b(c,((w>>30)&1)?0x29:0x01);b(c,0xc8);save(c,rd,0);
            if((w>>29)&1)save_arithmetic_flags(c,(w>>30)&1);
        } else if((w&0x3a000000)==0x28000000) {
            memory_shape shape;int valid=decode_memory(w,&shape);
            unsigned mode=shape.mode,read=shape.read,rt2=shape.rt2;
            int writeback=mode!=2;
            field32(c,offsetof(vf_cpu,instruction),w);
            if(!valid) {
                finish(c,pc,n,VF_UNDEFINED_INSTRUCTION);break;
            }
            uint64_t sctlr=cpu?cpu->sctlr:0;
            if(current_el>VF_EL1 || (cpu && (cpu->hcr_el2 || cpu->scr_el3)) ||
               (sctlr&(UINT64_C(1)<<(current_el==VF_EL0?24:25)))) {
                finish(c,pc,n,VF_SYSTEM_REGISTER_TRAP);break;
            }
            unsigned bytes=shape.width;
            int32_t displacement=shape.displacement;
            size_t sp_align=0,align=0;
            if(rn==31 && (sctlr&(current_el==VF_EL0?16u:8u))) {
                load(c,31,1,1);b(c,0x49);b(c,0x89);b(c,0xc3); /* r11=SP */
                b(c,0xa8);b(c,15);sp_align=jcc(c,0x85);
            }
            load(c,rn,1,1);
            if(mode!=1) {b(c,0x48);b(c,0x05);u32(c,(uint32_t)displacement);}
            b(c,0x49);b(c,0x89);b(c,0xc3); /* r11=guest element address */
            b(c,0x49);b(c,0x89);b(c,0xc1); /* r9=address, then RAM offset */
            /* MMU-off with HCR=0 is Device-nGnRnE, even with SCTLR.A=0. */
            b(c,0xa8);b(c,bytes-1);align=jcc(c,0x85);
            imm(c,base);b(c,0x49);b(c,0x29);b(c,0xc1);
            size_t below=jcc(c,0x82);
            b(c,0x49);b(c,0x83);b(c,0xf8);b(c,bytes);
            size_t short_first=jcc(c,0x82);
            b(c,0x4d);b(c,0x89);b(c,0xc2); /* r10=RAM size */
            b(c,0x49);b(c,0x83);b(c,0xea);b(c,bytes);
            b(c,0x4d);b(c,0x39);b(c,0xd1);
            size_t first=jcc(c,0x87);
            b(c,0x49);b(c,0x83);b(c,0xc3);b(c,bytes); /* FAR of second element */
            size_t wrapped=jcc(c,0x82);
            b(c,0x49);b(c,0x83);b(c,0xf8);b(c,2*bytes);
            size_t short_second=jcc(c,0x82);
            b(c,0x49);b(c,0x83);b(c,0xea);b(c,bytes);
            b(c,0x4d);b(c,0x39);b(c,0xd1);
            size_t second=jcc(c,0x87);
            b(c,0x49);b(c,0x83);b(c,0xeb);b(c,bytes); /* retain original EA */
            /* No memory operation precedes both complete element checks. */
            for(unsigned element=0;element<2;element++) {
                unsigned reg=element?rt2:rd;
                if(!read)load(c,reg,0,bytes==8);
                b(c,bytes==8?0x4a:0x42);b(c,read?0x8b:0x89);
                b(c,element?0x44:0x04);b(c,0x0a);if(element)b(c,bytes);
                if(read)save(c,reg,0);
            }
            if(writeback) {
                b(c,0x4c);b(c,0x89);b(c,0xd8); /* rax=EA */
                if(mode==1){b(c,0x48);b(c,0x05);u32(c,(uint32_t)displacement);}
                save(c,rn,1);
            }
            b(c,0xe9);size_t next=c->used;u32(c,0);
            size_t sp_target=c->used;
            if(sp_align){save_host_r11(c,offsetof(vf_cpu,far));finish(c,pc,n,VF_SP_ALIGNMENT_FAULT);}
            size_t align_target=c->used;
            if(align){save_host_r11(c,offsetof(vf_cpu,far));finish(c,pc,n,VF_ALIGNMENT_FAULT);}
            size_t data_target=c->used;
            save_host_r11(c,offsetof(vf_cpu,far));finish(c,pc,n,VF_DATA_ABORT);
            if(sp_align)fix_to(c,sp_align,sp_target);
            if(align)fix_to(c,align,align_target);
            fix_to(c,below,data_target);fix_to(c,short_first,data_target);
            fix_to(c,first,data_target);fix_to(c,wrapped,data_target);
            fix_to(c,short_second,data_target);fix_to(c,second,data_target);
            fix(c,next);
        } else if((w&0x3b000000)==0x39000000) {
            memory_shape shape;int valid=decode_memory(w,&shape);
            unsigned bytes=shape.width;
            int read=shape.read,signed_load=shape.signed_load,result64=shape.result64;
            field32(c,offsetof(vf_cpu,instruction),w);
            /* V=1 belongs to SIMD/FP. size=3/opc=2 is PRFM; other
             * rejected size/opc combinations are reserved integer forms. */
            if(!valid) {
                finish(c,pc,n,VF_UNDEFINED_INSTRUCTION);break;
            }
            uint64_t sctlr=cpu?cpu->sctlr:0;
            if(current_el>VF_EL1 || (cpu && (cpu->hcr_el2 || cpu->scr_el3)) ||
               (sctlr&(UINT64_C(1)<<(current_el==VF_EL0?24:25)))) {
                finish(c,pc,n,VF_SYSTEM_REGISTER_TRAP);break;
            }
            size_t sp_align=0,align=0;
            load(c,rn,1,1);
            if(rn==31 && (sctlr&(current_el==VF_EL0?16u:8u))) {
                b(c,0x49);b(c,0x89);b(c,0xc3);
                b(c,0xa8);b(c,15);sp_align=jcc(c,0x85);
            }
            b(c,0x48);b(c,0x05);u32(c,(uint32_t)shape.displacement);
            b(c,0x49);b(c,0x89);b(c,0xc3); /* r11=guest EA, r9=checked offset */
            b(c,0x49);b(c,0x89);b(c,0xc1);
            /* Supported native regime is MMU-off Device-nGnRnE. */
            if(bytes>1){b(c,0xa8);b(c,bytes-1);align=jcc(c,0x85);}
            imm(c,base);b(c,0x49);b(c,0x29);b(c,0xc1);
            size_t below=jcc(c,0x82);
            b(c,0x49);b(c,0x83);b(c,0xf8);b(c,bytes);
            size_t short_ram=jcc(c,0x82);
            b(c,0x4d);b(c,0x89);b(c,0xc2);b(c,0x49);b(c,0x83);b(c,0xea);b(c,bytes);
            b(c,0x4d);b(c,0x39);b(c,0xd1);size_t bound=jcc(c,0x87);
            if(read) {
                b(c,result64?0x4a:0x42);
                if(bytes<4){b(c,0x0f);b(c,(signed_load?0xbe:0xb6)+(bytes==2));}
                else b(c,signed_load?0x63:0x8b);
                b(c,0x04);b(c,0x0a);save(c,rd,0);
            } else {
                load(c,rd,0,bytes==8);
                if(bytes==2)b(c,0x66);
                b(c,bytes==8?0x4a:0x42);b(c,bytes==1?0x88:0x89);b(c,0x04);b(c,0x0a);
            }
            b(c,0xe9);size_t next=c->used;u32(c,0);
            size_t sp_target=c->used;
            if(sp_align){save_host_r11(c,offsetof(vf_cpu,far));finish(c,pc,n,VF_SP_ALIGNMENT_FAULT);}
            size_t alignment_target=c->used;
            if(align){save_host_r11(c,offsetof(vf_cpu,far));finish(c,pc,n,VF_ALIGNMENT_FAULT);}
            size_t data_target=c->used;
            save_host_r11(c,offsetof(vf_cpu,far));
            finish(c,pc,n,VF_DATA_ABORT);
            if(sp_align)fix_to(c,sp_align,sp_target);
            if(align)fix_to(c,align,alignment_target);
            fix_to(c,below,data_target);
            fix_to(c,short_ram,data_target);
            fix_to(c,bound,data_target);
            fix(c,next);
        } else if((w&0xff000010)==0x54000000) {
            unsigned condition=w&15;
            uint64_t target=pc+(uint64_t)(sext((w>>5)&0x7ffff,19)*4);
            if(condition>=14) { finish(c,target,n+1,VF_NEXT);break; }
            size_t fall=condition_false(c,condition);
            finish(c,target,n+1,VF_NEXT);
            fix(c,fall);finish(c,pc+4,n+1,VF_NEXT);break;
        } else if((w&0x7e000000)==0x34000000) {
            load(c,rd,0,wide);b(c,0x48);b(c,0x85);b(c,0xc0);
            size_t fall=jcc(c,(w&0x1000000)?0x84:0x85);
            finish(c,pc+(uint64_t)(sext((w>>5)&0x7ffff,19)*4),n+1,VF_NEXT);
            fix(c,fall);finish(c,pc+4,n+1,VF_NEXT);break;
        } else if((w&0x7c000000)==0x14000000) {
            if(w>>31)field(c,offsetof(vf_cpu,x)+30*8,pc+4);
            finish(c,pc+(uint64_t)(sext(w&0x3ffffff,26)*4),n+1,VF_NEXT);break;
        } else if((w&0xfffffc1f)==0xd61f0000 || (w&0xfffffc1f)==0xd63f0000 ||
                  (w&0xfffffc1f)==0xd65f0000) {
            if(rn==31){field32(c,offsetof(vf_cpu,instruction),w);finish(c,pc,n,VF_UNDEFINED_INSTRUCTION);break;}
            load(c,rn,0,1);b(c,0x49);b(c,0x89);b(c,0xc1); /* retain target before writing LR */
            if((w&0xfffffc1f)==0xd63f0000)field(c,offsetof(vf_cpu,x)+30*8,pc+4);
            b(c,0x4c);b(c,0x89);b(c,0x89);u32(c,offsetof(vf_cpu,pc));
            b(c,0x48);b(c,0x81);b(c,0x81);u32(c,offsetof(vf_cpu,retired));u32(c,n+1);
            b(c,0xb8);u32(c,VF_NEXT);b(c,0xc3);break;
        } else if(w==0xd503201f) { /* NOP */
        } else if(w==0xd4400000) { /* HLT #0 is the synthetic monitor exit, not an EL exception. */
            finish(c,pc+4,n+1,VF_HALT);break;
        } else {
            int boundary=known_privileged(w,current_el) ? VF_PRIVILEGE_FAULT
                                                         : system_boundary(w,current_el);
            if(boundary) {
                field32(c,offsetof(vf_cpu,instruction),w);
                finish(c,pc,n,(unsigned)boundary);break;
            }
            b(c,0xc7);b(c,0x81);u32(c,offsetof(vf_cpu,instruction));u32(c,w);
            finish(c,pc,n,VF_UNDEFINED_INSTRUCTION);break;
        }
        if(n+1==limit)finish(c,pc+4,n+1,VF_NEXT);
    }
    return c->used>c->capacity?VF_CODE_FULL:VF_NEXT;
}
int vf_translate(vf_code *c,const uint8_t *guest,size_t size,uint64_t pc,unsigned limit) {
    return translate_impl(c,0,guest,size,pc,limit,0);
}
int vf_translate_cpu(vf_code *c,vf_cpu *cpu,const uint8_t *guest,size_t size,
                     uint64_t pc,unsigned limit) {
    if(!cpu || !vf_cpu_state_valid(cpu)) return VF_PRIVILEGE_FAULT;
    /* This native path addresses caller RAM physically. A table walker is
     * not connected here: never execute an enabled guest MMU as identity. */
    if(cpu->sctlr&1) {cpu->instruction=0;return VF_SYSTEM_REGISTER_TRAP;}
    return translate_impl(c,cpu,guest,size,pc,limit,0);
}
int vf_host_supported(void) {
    uint32_t a=1,bv,c,d;
    __asm__ volatile("cpuid":"+a"(a),"=b"(bv),"=c"(c),"=d"(d));
    return (c & ((1u<<19)|(1u<<20)))==((1u<<19)|(1u<<20));
}

static int pauth_slow_step(vf_cpu *cpu) {
    if(!cpu->pauth_step || cpu->current_el!=VF_EL1 || (cpu->sctlr&1))return 0;
    vf_pauth_context context={0};
    for(unsigned i=0;i<31;i++)context.x[i]=cpu->x[i];
    for(unsigned i=0;i<5;i++)for(unsigned j=0;j<2;j++)context.keys[i][j]=cpu->pauth_keys[i][j];
    context.sp=cpu->sp;context.pc=cpu->pc;context.sctlr=cpu->sctlr;
    context.tcr=cpu->tcr;context.current_el=cpu->current_el;
    if(cpu->pauth_step(&context,cpu->instruction))return 0;
    /* Commit the architectural step only after the software PAC provider
     * returns success. It receives no guest or host-memory pointer. */
    for(unsigned i=0;i<31;i++)cpu->x[i]=context.x[i];
    for(unsigned i=0;i<5;i++)for(unsigned j=0;j<2;j++)cpu->pauth_keys[i][j]=context.keys[i][j];
    cpu->sp=context.sp;cpu->pc=context.pc;cpu->sctlr=context.sctlr;cpu->tcr=context.tcr;
    cpu->retired++;vf_cpu_advance_counter(cpu,1);
    return 1;
}
static int platform_slow_step(vf_cpu *cpu) {
    uint32_t w=cpu->instruction;
    if(!is_mrs_msr(w) || sysreg_key(w)!=VF_PLATFORM_OVERRIDE_KEY)return 0;
    unsigned rt=w&31;
    if(w&0x00200000) {
        uint64_t value;
        if(vf_cpu_read_sysreg(cpu,VF_PLATFORM_OVERRIDE_KEY,&value))return 0;
        if(rt!=31)cpu->x[rt]=value;
    } else if(vf_cpu_write_sysreg(cpu,VF_PLATFORM_OVERRIDE_KEY,rt==31?0:cpu->x[rt]))return 0;
    cpu->pc+=4;cpu->retired++;vf_cpu_advance_counter(cpu,1);return 1;
}
static int pstate_slow_step(vf_cpu *cpu) {
    uint32_t w=cpu->instruction;
    if(cpu->current_el==VF_EL0 || (cpu->sctlr&1))return 0;
    if((w&0xfffff0ff)==0xd50340df || (w&0xfffff0ff)==0xd50340ff) {
        uint64_t mask=(uint64_t)((w>>8)&15)<<6;
        if((w&255)==0xdf)cpu->pstate|=mask;else cpu->pstate&=~mask;
    } else if((w&0xfffffeff)==0xd50040bf) {
        unsigned old=(cpu->pstate&1)?cpu->current_el:VF_EL0;
        cpu->sp_el[old]=cpu->sp;
        cpu->pstate=(cpu->pstate&~UINT64_C(1))|((w>>8)&1);
        cpu->sp=cpu->sp_el[(cpu->pstate&1)?cpu->current_el:VF_EL0];
    } else return 0;
    cpu->pc+=4;cpu->retired++;vf_cpu_advance_counter(cpu,1);return 1;
}
static int execute_native_block(vf_cpu *cpu,vf_code *code,uint8_t *ram,uint64_t size) {
    uint32_t a=0,bv,cv,d;__asm__ volatile("cpuid":"+a"(a),"=b"(bv),"=c"(cv),"=d"(d)::"memory");
    uint64_t before=cpu->retired;
    int status=((vf_entry)(void *)code->bytes)(cpu,ram,size);
    vf_cpu_advance_counter(cpu,cpu->retired-before);cpu->compiled_blocks++;
    return status;
}
int vf_run(vf_cpu *cpu,const uint8_t *guest,size_t size,uint8_t *ram,size_t ram_size,
           vf_code *code,uint64_t budget,vf_protect protect,void *opaque) {
    if(!cpu||!guest||!ram||ram_size<8||!code||!code->bytes||!protect||
       !vf_cpu_state_valid(cpu)) return cpu ? (cpu->status=VF_DATA_FAULT) : VF_DATA_FAULT;
    uint64_t start=cpu->retired;
    while(cpu->retired-start<budget) {
        if(cpu->sctlr&1) {cpu->instruction=0;return cpu->status=VF_SYSTEM_REGISTER_TRAP;}
        int asynchronous=vf_cpu_poll_interrupt(cpu);
        if(asynchronous!=VF_NEXT)return cpu->status=asynchronous;
        uint64_t left=budget-(cpu->retired-start);unsigned count=left>32?32:(unsigned)left;
        /* Poll every instruction while a level or timer may change eligibility.
         * The common no-input path retains its native multi-instruction block. */
        if(cpu->irq_level || cpu->fiq_level ||
           ((cpu->cntp_ctl|cpu->cntv_ctl)&VF_TIMER_CTL_ENABLE))count=1;
        if(protect(code->bytes,code->capacity,0,opaque))return cpu->status=VF_PROTECTION;
        int status=vf_translate_cpu(code,cpu,guest,size,cpu->pc,count);
        if(status) {
            if(status!=VF_CODE_FULL) (void)vf_cpu_commit_status(cpu,status);
            return cpu->status=status;
        }
        if(protect(code->bytes,code->capacity,1,opaque))return cpu->status=VF_PROTECTION;
        /* CPUID serializes stores before execution on x86; no I-cache invalidate needed. */
        status=execute_native_block(cpu,code,ram,ram_size);
        if((status==VF_UNDEFINED_INSTRUCTION || status==VF_SYSTEM_REGISTER_TRAP)
            && (platform_slow_step(cpu) || pstate_slow_step(cpu) || pauth_slow_step(cpu)))continue;
        if(status!=VF_NEXT) {
            if(vf_cpu_commit_status(cpu,status)) return cpu->status=status;
            return cpu->status=status;
        }
    }
    return cpu->status=VF_BUDGET;
}

static int provider_error(vf_memory_run_result_v1 *result,unsigned reason) {
    result->provider_status=reason;return VF_DATA_FAULT;
}
static int memory_exchange(vf_cpu *cpu,vf_memory_callback_v1 callback,void *owner,
                          const vf_memory_request_v1 *request,vf_memory_reply_v1 *reply,
                          vf_memory_run_result_v1 *result) {
    *reply=(vf_memory_reply_v1){0};result->last_address=request->address;
    if(request->operation==VF_MEMORY_FETCH)result->fetch_requests++;else result->data_requests++;
    if(callback(owner,request,reply))return provider_error(result,VF_PROVIDER_CALLBACK_FAILURE);
    if(reply->abi_version!=1 || reply->struct_size!=sizeof(*reply) || reply->epoch ||
       reply->reserved[0] || reply->reserved[1] || reply->reserved[2] || reply->result>VF_MEMORY_INVALID_REQUEST)
        return provider_error(result,VF_PROVIDER_INVALID_REPLY);
    uint64_t mask=request->width==8?UINT64_MAX:(UINT64_C(1)<<(request->width*8))-1;
    if(reply->result==VF_MEMORY_OK) {
        if(reply->fault || reply->address || reply->esr || (reply->value0&~mask) || (reply->value1&~mask) ||
           (request->count==1 && reply->value1) ||
           (request->operation==VF_MEMORY_STORE && (reply->value0 || reply->value1)))
            return provider_error(result,VF_PROVIDER_INVALID_REPLY);
        return VF_NEXT;
    }
    if(reply->value0 || reply->value1)return provider_error(result,VF_PROVIDER_INVALID_REPLY);
    if(reply->result==VF_MEMORY_INVALID_REQUEST) {
        if(reply->fault || reply->address || reply->esr)return provider_error(result,VF_PROVIDER_INVALID_REPLY);
        return provider_error(result,VF_PROVIDER_INVALID_REQUEST);
    }
    if(reply->result==VF_MEMORY_UNSUPPORTED) {
        if(reply->fault || reply->esr || (reply->address!=request->address &&
           !(request->count==2 && reply->address==request->address+request->width)))
            return provider_error(result,VF_PROVIDER_INVALID_REPLY);
        result->last_address=reply->address;return provider_error(result,VF_PROVIDER_UNSUPPORTED);
    }
    enum vf_exception_kind kind;int status;uint64_t expected;
    if(request->operation==VF_MEMORY_FETCH) {
        kind=VF_EXCEPTION_INSTRUCTION_ABORT;status=VF_INSTRUCTION_ABORT;expected=UINT64_C(0x8a000000);
        if(reply->fault!=VF_MEMORY_PC_ALIGNMENT || !(request->pc&3))
            return provider_error(result,VF_PROVIDER_INVALID_REPLY);
    } else {
        kind=VF_EXCEPTION_ALIGNMENT_FAULT;status=VF_ALIGNMENT_FAULT;
        expected=((UINT64_C(0x24)+request->current_el)<<26)|(UINT64_C(1)<<25)|0x21|
            (request->operation==VF_MEMORY_STORE?64:0);
        if(reply->fault!=VF_MEMORY_DATA_ALIGNMENT || !(request->address&(request->width-1)))
            return provider_error(result,VF_PROVIDER_INVALID_REPLY);
    }
    if(reply->address!=request->address || reply->esr!=expected)
        return provider_error(result,VF_PROVIDER_INVALID_REPLY);
    if(vf_cpu_raise_exception(cpu,kind,cpu->pc,reply->address,(uint32_t)expected,
                             request->operation==VF_MEMORY_FETCH?0:cpu->instruction))
        return provider_error(result,VF_PROVIDER_INVALID_REPLY);
    result->last_address=reply->address;return status;
}
static uint64_t memory_register(const vf_cpu *cpu,unsigned reg,int sp) {
    return reg==31?(sp?cpu->sp:0):cpu->x[reg];
}
static void memory_save(vf_cpu *cpu,unsigned reg,uint64_t value,int wide) {
    if(reg!=31)cpu->x[reg]=wide?value:(uint32_t)value;
}
static int memory_data_step(vf_cpu *cpu,vf_memory_callback_v1 callback,void *owner,
                            vf_memory_run_result_v1 *result) {
    memory_shape shape;
    if(!decode_memory(cpu->instruction,&shape)) {
        (void)vf_cpu_commit_status(cpu,VF_UNDEFINED_INSTRUCTION);return VF_UNDEFINED_INSTRUCTION;
    }
    uint64_t base=memory_register(cpu,shape.rn,1);
    if(shape.rn==31 && (cpu->sctlr&(cpu->current_el==VF_EL0?16u:8u)) && (base&15)) {
        cpu->far=base;(void)vf_cpu_commit_status(cpu,VF_SP_ALIGNMENT_FAULT);return VF_SP_ALIGNMENT_FAULT;
    }
    uint64_t updated=base+(int64_t)shape.displacement;
    uint64_t address=shape.mode==1?base:updated;
    uint64_t mask=shape.width==8?UINT64_MAX:(UINT64_C(1)<<(shape.width*8))-1;
    vf_memory_request_v1 request={1,sizeof(request),shape.read?VF_MEMORY_LOAD:VF_MEMORY_STORE,0,
        cpu->pc,address,0,0,cpu->sctlr,0,shape.width,shape.count,cpu->current_el,0};
    if(!shape.read) {
        request.value0=memory_register(cpu,shape.rt,0)&mask;
        if(shape.count==2)request.value1=memory_register(cpu,shape.rt2,0)&mask;
    }
    vf_memory_reply_v1 reply;
    int status=memory_exchange(cpu,callback,owner,&request,&reply,result);
    if(status!=VF_NEXT)return status;
    if(shape.read) {
        uint64_t value=shape.signed_load?(uint64_t)sext(reply.value0,shape.width*8):reply.value0;
        memory_save(cpu,shape.rt,value,shape.result64);
        if(shape.count==2)memory_save(cpu,shape.rt2,reply.value1,shape.result64);
    }
    if(shape.mode!=2) {
        if(shape.rn==31)cpu->sp=updated;else cpu->x[shape.rn]=updated;
    }
    cpu->pc+=4;cpu->retired++;vf_cpu_advance_counter(cpu,1);result->completed_data_operations++;
    return VF_NEXT;
}
int vf_run_memory_provider(vf_cpu *cpu,vf_code *code,uint64_t budget,
    vf_protect protect,void *protect_opaque,vf_memory_callback_v1 callback,void *owner,
    vf_memory_run_result_v1 *result) {
    if(!result)return VF_DATA_FAULT;
    if(!cpu || !code || !code->bytes || !protect || !callback || !owner || !budget ||
       !vf_cpu_state_valid(cpu) || cpu->exception_pending!=VF_EXCEPTION_NONE)
        return provider_error(result,VF_PROVIDER_INVALID_REQUEST);
    uint64_t start=cpu->retired;
    while(cpu->retired-start<budget) {
        if((cpu->sctlr&1) || cpu->current_el>VF_EL1 || cpu->hcr_el2 || cpu->scr_el3) {
            cpu->instruction=0;return cpu->status=VF_SYSTEM_REGISTER_TRAP;
        }
        int status=vf_cpu_poll_interrupt(cpu);
        if(status!=VF_NEXT)return cpu->status=status;
        vf_memory_request_v1 request={1,sizeof(request),VF_MEMORY_FETCH,0,cpu->pc,cpu->pc,
            0,0,cpu->sctlr,0,4,1,cpu->current_el,0};
        vf_memory_reply_v1 reply;
        status=memory_exchange(cpu,callback,owner,&request,&reply,result);
        if(status!=VF_NEXT)return cpu->status=status;
        uint32_t instruction=(uint32_t)reply.value0;
        if(protect(code->bytes,code->capacity,0,protect_opaque))return cpu->status=VF_PROTECTION;
        status=translate_impl(code,cpu,(const uint8_t *)&instruction,4,cpu->pc,1,1);
        if(status!=VF_NEXT)return cpu->status=status;
        if(protect(code->bytes,code->capacity,1,protect_opaque))return cpu->status=VF_PROTECTION;
        /* No guest RAM host pointer is supplied to the generated entry. */
        status=execute_native_block(cpu,code,0,0);
        if((uint32_t)status==VF_MEMORY_DISPATCH) {
            status=memory_data_step(cpu,callback,owner,result);
            if(status!=VF_NEXT)return cpu->status=status;
            continue;
        }
        if((status==VF_UNDEFINED_INSTRUCTION || status==VF_SYSTEM_REGISTER_TRAP) &&
           (platform_slow_step(cpu) || pstate_slow_step(cpu) || pauth_slow_step(cpu)))continue;
        if(status!=VF_NEXT) {(void)vf_cpu_commit_status(cpu,status);return cpu->status=status;}
    }
    return cpu->status=VF_BUDGET;
}

#include "memory_stage1.inc"
#include "/home/sharh/work/integration-validation-bp34-20260909/native-dynamic/cpu_bank_before_commit_ack/memory_dynamic.inc"

int vf_run_boot(vf_cpu *cpu,uint8_t *ram,size_t ram_size,uint64_t base,
                uint64_t entry,uint64_t args,uint64_t stack,vf_code *code,
                uint64_t budget,vf_protect protect,void *opaque) {
    return vf_run_boot_with_pauth(cpu,ram,ram_size,base,entry,args,stack,code,
                                  budget,protect,opaque,0);
}

int vf_run_boot_with_pauth(vf_cpu *cpu,uint8_t *ram,size_t ram_size,uint64_t base,
                uint64_t entry,uint64_t args,uint64_t stack,vf_code *code,
                uint64_t budget,vf_protect protect,void *opaque,vf_pauth_step pauth) {
    const uint64_t registers[4]={args,0,0,0};
    return vf_run_boot_with_registers(cpu,ram,ram_size,base,entry,args,stack,
                                      code,budget,protect,opaque,registers,pauth);
}

int vf_run_boot_with_registers(vf_cpu *cpu,uint8_t *ram,size_t ram_size,uint64_t base,
                uint64_t entry,uint64_t args,uint64_t stack,vf_code *code,
                uint64_t budget,vf_protect protect,void *opaque,
                const uint64_t registers[4],vf_pauth_step pauth) {
    return vf_run_boot_v2(cpu,ram,ram_size,base,entry,args,stack,code,budget,
                         protect,opaque,registers,pauth,0);
}

int vf_run_boot_v2(vf_cpu *cpu,uint8_t *ram,size_t ram_size,uint64_t base,
                uint64_t entry,uint64_t args,uint64_t stack,vf_code *code,
                uint64_t budget,vf_protect protect,void *opaque,
                const uint64_t registers[4],vf_pauth_step pauth,
                const vf_boot_options_v2 *options) {
    if(!ram)return VF_DATA_FAULT;
    int status=vf_cpu_prepare_boot(cpu,ram_size,base,entry,args,stack,registers,pauth,options,budget);
    if(status!=VF_NEXT)return status;
    return vf_run(cpu,ram,ram_size,ram,ram_size,code,budget,protect,opaque);
}
int vf_cpu_prepare_boot(vf_cpu *cpu,uint64_t ram_size,uint64_t base,
                uint64_t entry,uint64_t args,uint64_t stack,
                const uint64_t registers[4],vf_pauth_step pauth,
                const vf_boot_options_v2 *options,uint64_t budget) {
    if(!cpu || ram_size<8 || base>UINT64_MAX-ram_size ||
       (base&0x3fff) || (entry&3) || entry<base || entry-base>ram_size-4 ||
       (args&7) || args<base || args-base>=ram_size ||
       (stack&15) || stack<=base || stack-base>ram_size || !budget || !registers)
        return VF_DATA_FAULT;
    const vf_boot_options_v2 defaults={2,sizeof(vf_boot_options_v2),0,0,0,0x3c5,0,0,0,0};
    vf_boot_options_v2 config=options?*options:defaults;
    if(config.abi_version!=2 || config.struct_size!=sizeof(config) || config.flags ||
       config.reserved || config.irq_level>1 || config.fiq_level>1 ||
       ((config.initial_pstate&15)!=4 && (config.initial_pstate&15)!=5) ||
       (config.initial_pstate&~UINT64_C(0xf00003cf)) ||
       (config.vbar && ((config.vbar&0x7ff) || config.vbar<base ||
                       ram_size<0x800 || config.vbar-base>ram_size-0x800)))return VF_DATA_FAULT;
    uint64_t initial[4];for(unsigned i=0;i<4;i++)initial[i]=registers[i];
    vf_cpu_reset(cpu,VF_EL1);
    if(vf_cpu_configure_platform(cpu,config.platform_profile,config.initial_override))return VF_DATA_FAULT;
    cpu->pc=entry;
    for(unsigned i=0;i<4;i++)cpu->x[i]=initial[i];
    cpu->sp=stack;cpu->sp_el[VF_EL1]=stack;cpu->sp_el[VF_EL0]=stack;
    cpu->pstate=config.initial_pstate;cpu->vbar_el[VF_EL1]=config.vbar;
    vf_cpu_set_interrupt_lines(cpu,(unsigned)config.irq_level,(unsigned)config.fiq_level);
    cpu->guest_ram_base=base;
    cpu->pauth_step=pauth;
    return VF_NEXT;
}
