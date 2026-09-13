// Independently authored Arm stage-1 permission experiment; no NextCore code.
typedef unsigned long long u64;
typedef unsigned int u32;
#ifndef GRANULE
#define GRANULE 4096
#endif
#define TARGET 0x400000000000ULL
#define RESULT ((volatile u64 *)0x41000000ULL)
#define BIT(n) (1ULL << (n))
static u64 tables[10][GRANULE / 8] __attribute__((aligned(GRANULE)));
static u64 backing[GRANULE / 8] __attribute__((aligned(GRANULE)));
static unsigned used;
struct observation { u64 success, esr, far, elr, value; };
extern void execute_access(u64, u64, u64, struct observation *);
extern char privileged_read[], privileged_write[], privileged_fetch[];
extern char unprivileged_read[], unprivileged_write[], unprivileged_fetch[], access_done[];
extern const u32 oracle_ret;
static inline u64 read_tcr(void) { u64 v; __asm__ volatile("mrs %0,tcr_el1":"=r"(v)); return v; }
static inline u64 read_sctlr(void) { u64 v; __asm__ volatile("mrs %0,sctlr_el1":"=r"(v)); return v; }
static unsigned shift(unsigned level) { return GRANULE == 4096 ? 39-9*level : 47-11*level; }
static unsigned index(u64 va, unsigned level) { return (va >> shift(level)) & (GRANULE/8-1); }
static u64 *next_table(u64 *table, unsigned entry) {
    if (!(table[entry]&1)) table[entry]=(u64)tables[used++]|3;
    return (u64 *)(table[entry]&0x0000ffffffffffffULL & ~(u64)(GRANULE-1));
}
void oracle_main(void) {
    for(unsigned t=0;t<10;t++) for(unsigned i=0;i<GRANULE/8;i++) tables[t][i]=0;
    used=1;
    unsigned start_level=GRANULE==4096 ? 0 : 1;
    u64 *identity=start_level==0 ? next_table(tables[0],index(0x40000000,0)) : tables[0];
    unsigned identity_level=1;
    if(GRANULE==16384) { identity=next_table(identity,index(0x40000000,1)); identity_level=2; }
    identity[index(0x40000000,identity_level)]=0x40000000ULL|BIT(10)|1;
    u64 *parents[3]={0,0,0}; u64 *target=tables[0];
    for(unsigned l=start_level;l<3;l++) { parents[l]=&target[index(TARGET,l)]; target=next_table(target,index(TARGET,l)); }
    u64 *leaf=&target[index(TARGET,3)];
    backing[0]=oracle_ret;
    // Exact immutable-profile TCR fields, including the disabled TTBR1 half.
    u64 tcr=16|(16ULL<<16)|(2ULL<<30)|BIT(23)|(5ULL<<32);
    if(GRANULE==16384) tcr=17|(17ULL<<16)|(1ULL<<30)|(2ULL<<14)|BIT(23)|(5ULL<<32);
    u64 root=(u64)tables[0],mair=0x44,sctlr=0x30d00801;
    __asm__ volatile("dsb sy\nmsr mair_el1,%0\nmsr ttbr0_el1,%1\nmsr ttbr1_el1,xzr\nmsr tcr_el1,%2\nisb\ntlbi vmalle1\ndsb sy\nisb\nmsr sctlr_el1,%3\nisb"::"r"(mair),"r"(root),"r"(tcr),"r"(sctlr):"memory");
    u64 mmfr0,mmfr1,current;
    __asm__ volatile("mrs %0,id_aa64mmfr0_el1\nmrs %1,id_aa64mmfr1_el1\nmrs %2,currentel":"=r"(mmfr0),"=r"(mmfr1),"=r"(current));
    RESULT[0]=0x4849455241524348ULL; RESULT[1]=GRANULE;
    RESULT[2]=read_tcr(); RESULT[3]=read_sctlr(); RESULT[4]=mmfr0; RESULT[5]=mmfr1; RESULT[6]=current;
    RESULT[7]=0;
    RESULT[8]=(u64)privileged_read; RESULT[9]=(u64)privileged_write; RESULT[10]=(u64)privileged_fetch;
    RESULT[11]=(u64)unprivileged_read; RESULT[12]=(u64)unprivileged_write; RESULT[13]=(u64)unprivileged_fetch; RESULT[14]=(u64)access_done;
    u64 actual_root,actual_mair;
    __asm__ volatile("mrs %0,ttbr0_el1\nmrs %1,mair_el1":"=r"(actual_root),"=r"(actual_mair));
    RESULT[15]=actual_root;RESULT[16]=actual_mair;RESULT[17]=(u64)backing;
    for(unsigned l=0;l<3;l++) RESULT[18+l]=(u64)parents[l];
    RESULT[21]=(u64)leaf;
    u64 pfr0,ttbr1;
    __asm__ volatile("mrs %0,id_aa64pfr0_el1\nmrs %1,ttbr1_el1":"=r"(pfr0),"=r"(ttbr1));
    RESULT[22]=start_level;RESULT[23]=pfr0;RESULT[24]=ttbr1;
    unsigned row=0;
    // kind0 matrix; 1/2 table PXN/UXN; 3/4 leaf PXN/UXN;
    // 5 split ancestors; 6 deeper invalid; 7 AF0; 8 invalid output PA;
    // 9/10 identical AP restrictions moved to L0/L1 table descriptors.
    for(unsigned kind=0;kind<11;kind++) for(unsigned ap=0;ap<4;ap++) for(unsigned parent=0;parent<4;parent++) {
        if(kind && (ap!=1 || parent!=3)) continue;
        if(kind==9 && start_level!=0) continue;
        for(unsigned el=0;el<2;el++) for(unsigned access=0;access<3;access++) {
            // Break the target-only root entry before changing any descendants.
            // Identity code, exception vectors and result RAM use another root entry.
            u64 root_descriptor=*parents[start_level]&0x0000ffffffffffffULL;
            *parents[start_level]=0;
            __asm__ volatile("dsb sy\ntlbi vmalle1\ndsb sy\nisb":::"memory");
            for(unsigned l=start_level+1;l<3;l++) *parents[l]&=0x0000ffffffffffffULL;
            *parents[2]|=(u64)parent<<61;
            if(kind==1) *parents[2]|=BIT(59);
            if(kind==2) *parents[2]|=BIT(60);
            if(kind==5) {
                *parents[2]&=~(3ULL<<61);
                if(start_level==1) root_descriptor|=BIT(61); else *parents[1]|=BIT(61);
                *parents[2]|=BIT(62);
            }
            if(kind==9) { *parents[2]&=~(3ULL<<61); root_descriptor|=3ULL<<61; }
            if(kind==10) {
                *parents[2]&=~(3ULL<<61);
                if(start_level==1) root_descriptor|=3ULL<<61; else *parents[1]|=3ULL<<61;
            }
            *leaf=(u64)backing|3|BIT(10)|((u64)ap<<6);
            if(kind==3) *leaf|=BIT(53);
            if(kind==4) *leaf|=BIT(54);
            if(kind==6) *leaf=0;
            if(kind==7) *leaf&=~BIT(10);
            // Address-size priority is a separately declared 40-bit IPS case.
            // With ordinary 48-bit descriptors, bit50 is not an output PA bit.
            u64 case_tcr=kind==8 ? ((tcr&~(7ULL<<32))|(2ULL<<32)) : tcr;
            __asm__ volatile("msr tcr_el1,%0\nisb"::"r"(case_tcr):"memory");
            if(kind==8) *leaf|=BIT(44);
            backing[16]=0x1234;
            *parents[start_level]=root_descriptor;
            __asm__ volatile("dsb sy\ntlbi vmalle1\ndsb sy\nisb":::"memory");
            u64 descriptors_before[4]={start_level==0?*parents[0]:0,*parents[1],*parents[2],*leaf};
            struct observation o={1,0,0,0,0};
            execute_access(TARGET+(access==2?0:128),access,el,&o);
            volatile u64 *r=RESULT+32+row*24;
            r[0]=kind;r[1]=ap;r[2]=parent;r[3]=el;r[4]=access;
            r[5]=o.success;r[6]=o.esr;r[7]=o.far;r[8]=o.elr;r[9]=o.value;r[10]=backing[16];
            r[11]=*leaf;r[12]=*parents[1];r[13]=*parents[2];r[14]=read_tcr();r[15]=read_sctlr();
            r[16]=start_level==0?*parents[0]:0;
            for(unsigned l=0;l<4;l++) r[17+l]=descriptors_before[l];
            __asm__ volatile("mrs %0,ttbr0_el1\nmrs %1,mair_el1":"=r"(actual_root),"=r"(actual_mair));
            r[21]=actual_root;r[22]=actual_mair;r[23]=backing[0];
            RESULT[7]=++row;
        }
    }
    __asm__ volatile("dsb sy":::"memory");
}
