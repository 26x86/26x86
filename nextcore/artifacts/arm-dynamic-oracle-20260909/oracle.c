typedef unsigned long long u64;
typedef unsigned u32;
static u64 tables[32][2048] __attribute__((aligned(16384)));
static unsigned char transition[32768] __attribute__((aligned(16384)));
static unsigned char target[16384] __attribute__((aligned(16384)));
static u64 data[2048] __attribute__((aligned(16384)));
static unsigned used, gran;
u64 abort_result[13];
extern void enter_transition(u64,u64,u64,u64);
extern unsigned char transition_words[],transition_end[],target_words[],target_end[],decoy_words[],decoy_end[],_image_end[];
static void print(const char *s) {
 register u64 x0 __asm__("x0")=4;register const char *x1 __asm__("x1")=s;
 __asm__ volatile("hlt #0xf000":"+r"(x0),"+r"(x1)::"memory");
}
static void hex(u64 value) {char s[18];for(unsigned i=0;i<16;i++)s[i]="0123456789abcdef"[(value>>(60-4*i))&15];s[16]=' ';s[17]=0;print(s);}
static void dec(unsigned value) {char s[12];unsigned p=11;s[p]=0;do{s[--p]='0'+value%10;value/=10;}while(value);print(s+p);}
static void field(const char *name,const char *key,u64 value) {print(name);print(".");print(key);print(" ");hex(value);print("\n");}
static void panic(void) {
 static u64 status[2]={0x20026,1};register u64 x0 __asm__("x0")=0x20;register u64 *x1 __asm__("x1")=status;
 __asm__ volatile("hlt #0xf000"::"r"(x0),"r"(x1):"memory");for(;;){}
}
static u64 *allocate(void) {if(used>=32)panic();return tables[used++];}
static u64 *leaf(u64 *root,u64 va) {
 unsigned bits=gran==4096?9:11,shift=gran==4096?12:14,start=gran==4096?0:1;
 u64 *table=root;
 for(unsigned level=start;level<3;level++){
  unsigned index=(unsigned)((va>>(shift+bits*(3-level)))&((1u<<bits)-1));
  if(!table[index])table[index]=(u64)allocate()|3;
  table=(u64*)(table[index]&~((u64)gran-1));
 }
 return &table[(va>>shift)&((1u<<bits)-1)];
}
static void copy(unsigned char *dst,const unsigned char *src,u64 len) {for(u64 i=0;i<len;i++)dst[i]=src[i];}
static void dump_tables(const char *name) {
 for(unsigned t=0;t<used;t++){
  print(name);print(".table");dec(t);print(".base ");hex((u64)tables[t]);print("\n");
  for(unsigned j=0;j<gran/8;j++)if(tables[t][j]){
   print(name);print(".table");dec(t);print(".entry");dec(j);print(" ");hex(tables[t][j]);print("\n");
  }
 }
}
void oracle_main(void) {
 u64 state;__asm__ volatile("mrs %0,hcr_el2":"=r"(state));print("HCR ");hex(state);print("\n");
 __asm__ volatile("mrs %0,CurrentEL":"=r"(state));print("CURRENT_EL ");hex(state);print("\n");
 const char *names[2][3]={{"g4096_success","g4096_fetch_unmapped","g4096_data_unmapped"},{"g16384_success","g16384_fetch_unmapped","g16384_data_unmapped"}};
 for(unsigned g=0;g<2;g++)for(unsigned kind=0;kind<3;kind++){
  gran=g?16384:4096;used=0;const char *name=names[g][kind];
  __asm__ volatile("msr sctlr_el1,xzr\n isb\n tlbi vmalle1\n dsb sy\n isb":::"memory");
  for(unsigned t=0;t<32;t++)for(unsigned j=0;j<2048;j++)tables[t][j]=0;
  for(unsigned j=0;j<32768;j++)transition[j]=0;
  for(unsigned j=0;j<16384;j++)target[j]=0;
  for(unsigned j=0;j<2048;j++)data[j]=0;
  for(unsigned j=0;j<13;j++)abort_result[j]=0;
  const u64 seed=0x1122334455667788ULL,stored=0x8877665544332211ULL,canary=0xa5a5a5a5a5a5a5a5ULL;
  data[0]=seed;data[1]=canary;
  copy(transition+gran-8,transition_words,(u64)(transition_end-transition_words));
  copy(transition+gran,decoy_words,(u64)(decoy_end-decoy_words));
  copy(target,target_words,(u64)(target_end-target_words));
#ifdef OMIT_ENABLE
  if(kind==0)*(u32*)(transition+gran-8)=0xd503201f; /* actual NOP, unchanged expected result */
#endif
  u64 entry=(u64)transition+gran-8,code_va=(u64)transition+gran,data_va=0x60000000ULL;
  u64 *root=allocate(),*upper=allocate();
  u64 end=((u64)_image_end+gran-1)&~((u64)gran-1);
  for(u64 va=0x40000000ULL;va<end;va+=gran)*leaf(root,va)=va|0x403;
  *leaf(root,code_va)=kind==1?0:(u64)target|0x403;
#ifdef OMIT_CODE_MAPPING
  if(kind==0)*leaf(root,code_va)=0; /* actual leaf omission */
#endif
  *leaf(root,data_va)=kind==2?0:(u64)data|0x403;
  u64 tsz=g?17:16;
  u64 tcr=tsz|(tsz<<16)|(g?((2ULL<<14)|(1ULL<<30)):(2ULL<<30)),off=0x30d00802,on=0x30d00803,mair=0x44;
  __asm__ volatile("dsb sy\n msr ttbr0_el1,%0\n msr ttbr1_el1,%1\n msr tcr_el1,%2\n msr mair_el1,%3\n isb\n msr sctlr_el1,%4\n isb\n ic iallu\n dsb sy\n isb"::"r"((u64)root),"r"((u64)upper),"r"(tcr),"r"(mair),"r"(off):"memory");
  field(name,"granule",gran);field(name,"kind",kind);field(name,"entry",entry);field(name,"isb_pc",entry+4);
  field(name,"code_va",code_va);field(name,"code_pa",(u64)target);field(name,"data_va",data_va);field(name,"data_pa",(u64)data);
  field(name,"guard_descriptor",*leaf(root,entry));field(name,"code_descriptor",*leaf(root,code_va));field(name,"data_descriptor",*leaf(root,data_va));
  field(name,"msr_word",*(u32*)(transition+gran-8));field(name,"isb_word",*(u32*)(transition+gran-4));
  field(name,"seed",data[0]);field(name,"data_before",data[1]);field(name,"store_operand",stored);
  __asm__ volatile("mrs %0,ttbr0_el1":"=r"(state));field(name,"ttbr0",state);
  __asm__ volatile("mrs %0,ttbr1_el1":"=r"(state));field(name,"ttbr1",state);
  __asm__ volatile("mrs %0,tcr_el1":"=r"(state));field(name,"tcr",state);
  __asm__ volatile("mrs %0,sctlr_el1":"=r"(state));field(name,"sctlr_before",state);
  __asm__ volatile("mrs %0,mair_el1":"=r"(state));field(name,"mair",state);
  field(name,"tables_used",used);dump_tables(name);
  enter_transition(entry,on,data_va,stored);
  print(name);print(" ");for(unsigned i=0;i<13;i++)hex(abort_result[i]);print("\n");
  field(name,"data_after0",data[0]);field(name,"data_after1",data[1]);
 }
 static u64 status[2]={0x20026,0};register u64 x0 __asm__("x0")=0x20;register u64 *x1 __asm__("x1")=status;
 __asm__ volatile("hlt #0xf000"::"r"(x0),"r"(x1):"memory");for(;;){}
}
