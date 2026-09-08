typedef unsigned long long u64;
struct test_case {const char *name;unsigned granule,tsz,start,level,kind,access,el,misaligned,cross;};
#include "operation_cases.h"
static u64 tables[4][2048] __attribute__((aligned(16384)));
static u64 code[4][2048] __attribute__((aligned(16384)));
static u64 data[4][2048] __attribute__((aligned(16384)));
u64 abort_result[6];
extern void enter_access(u64,u64,u64);
extern char load64[],store64[],pair_load32[],pair_store32[],pair_load64[],pair_store64[];
static void print(const char *s) {
 register u64 x0 __asm__("x0")=4;register const char *x1 __asm__("x1")=s;
 __asm__ volatile("hlt #0xf000":"+r"(x0),"+r"(x1)::"memory");
}
static void hex(u64 value) {char s[18];for(unsigned i=0;i<16;i++)s[i]="0123456789abcdef"[(value>>(60-4*i))&15];s[16]=' ';s[17]=0;print(s);}
static void field(const char *name,const char *key,u64 value) {print(name);print(key);hex(value);print("\n");}
void oracle_main(void) {
 u64 state;__asm__ volatile("mrs %0,hcr_el2":"=r"(state));print("HCR ");hex(state);print("\n");
 __asm__ volatile("mrs %0,CurrentEL":"=r"(state));print("CURRENT_EL ");hex(state);print("\n");
 for(unsigned n=0;n<sizeof(cases)/sizeof(cases[0]);n++) {
  const struct test_case *c=&cases[n];
  __asm__ volatile("msr sctlr_el1,xzr\n isb\n tlbi vmalle1\n dsb sy\n isb":::"memory");
  for(unsigned i=0;i<4;i++)for(unsigned j=0;j<2048;j++){tables[i][j]=0;code[i][j]=0;data[i][j]=0;}
  for(unsigned level=c->start;level<3;level++)tables[level][0]=(u64)tables[level+1]|3;
  if(c->granule==4096){code[0][0]=(u64)code[1]|3;code[1][1]=0x400004c1ULL;}
  else{code[1][0]=(u64)code[2]|3;code[2][32]=0x400004c1ULL;}
  u64 descriptor=(c->level==3?(u64)data[0]:0x40000000ULL)|0x440|(c->level==3?3:1);
  if(c->access==2 && c->el==1)descriptor&=~0x40ULL;
  if(c->kind==1)descriptor=0;
  else if(c->kind==2)descriptor&=~0x400ULL;
  else if(c->kind==3){if(c->el==0)descriptor&=~0x40ULL;else descriptor|=0x80ULL;}
  else if(c->kind==4)descriptor|=1ULL<<(c->el==0?54:53);
  if(c->kind>=10){unsigned bits=c->kind-10;descriptor&=~(0xc0ULL|(1ULL<<53)|(1ULL<<54));descriptor|=(u64)(bits>>2)<<6;descriptor|=(u64)((bits>>1)&1)<<54;descriptor|=(u64)(bits&1)<<53;}
  if(c->cross){tables[3][0]=(u64)data[0]|0x443; if(c->kind==0)descriptor=(u64)data[2]|0x443; tables[3][1]=descriptor;}
  else tables[c->level][0]=descriptor;
  unsigned width=c->access==3||c->access==4?4:8;
  u64 va=~((1ULL<<(64-c->tsz))-1);
  va+=c->cross?c->granule-width:0x230;
  if(c->misaligned)va+=1;
  if(c->access==2){unsigned *p=(unsigned*)((char*)data[0]+0x230);*p=0xd65f03c0;}
  u64 root=(u64)tables[c->start],lower=(u64)code[c->start];
  u64 tcr=c->tsz|((u64)c->tsz<<16);
  tcr|=c->granule==16384?((2ULL<<14)|(1ULL<<30)):(2ULL<<30);
  u64 sctlr=0x30d00803,mair=0x44;
#ifdef NEGATIVE_CONTROL
  if(n==0)va&=~3ULL; /* actual changed target, no fabricated ESR */
#endif
  __asm__ volatile("dsb sy\n msr ttbr0_el1,%0\n msr ttbr1_el1,%1\n msr tcr_el1,%2\n"
                   "msr mair_el1,%3\n isb\n msr sctlr_el1,%4\n isb"
                   ::"r"(lower),"r"(root),"r"(tcr),"r"(mair),"r"(sctlr):"memory");
  __asm__ volatile("mrs %0,ttbr0_el1":"=r"(state));field(c->name,".ttbr0 ",state);
  __asm__ volatile("mrs %0,ttbr1_el1":"=r"(state));field(c->name,".ttbr1 ",state);
  __asm__ volatile("mrs %0,tcr_el1":"=r"(state));field(c->name,".tcr ",state);
  field(c->name,".va ",va);field(c->name,".access ",c->access);field(c->name,".target_el ",c->el);
  __asm__ volatile("mrs %0,sctlr_el1":"=r"(state));field(c->name,".sctlr ",state);
  __asm__ volatile("mrs %0,mair_el1":"=r"(state));field(c->name,".mair ",state);
  for(unsigned i=0;i<4;i++){char address[]=".table0 ",value[]=".value0 ";address[6]+=i;value[6]+=i;field(c->name,address,(u64)tables[i]);field(c->name,value,tables[i][0]);}
  field(c->name,".second_page ",tables[3][1]);
  enter_access(va,c->access,c->el);
  print(c->name);print(" ");for(unsigned i=0;i<6;i++)hex(abort_result[i]);
  hex(va);void *labels[]={load64,store64,0,pair_load32,pair_store32,pair_load64,pair_store64};
  hex(c->access==2?va:(u64)labels[c->access]);print("\n");
 }
 static u64 status[2]={0x20026,0};register u64 x0 __asm__("x0")=0x20;register u64 *x1 __asm__("x1")=status;
 __asm__ volatile("hlt #0xf000"::"r"(x0),"r"(x1):"memory");for(;;){}
}
