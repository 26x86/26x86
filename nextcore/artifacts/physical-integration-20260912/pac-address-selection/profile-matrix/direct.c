#include "jit.h"
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
static int protect(void*p,size_t n,int x,void*o){(void)o;return mprotect(p,n,PROT_READ|(x?PROT_EXEC:PROT_WRITE));}
int main(){vf_code code={mmap(0,4096,3,0x22,-1,0),4096,0};for(int id=0;id<2;id++)for(int sentinel=0;sentinel<2;sentinel++){vf_cpu c;vf_cpu_reset(&c,1);if(sentinel)c.id_aa64isar1=0x123456789abcdef0ULL;c.x[0]=0xfeed;c.sp=0x800;c.pstate=0xf00003c5;unsigned w=id?0xd5380700:0xd5380620;uint64_t value=0;int api=vf_cpu_read_sysreg(&c,id?0x4038:0x4031,&value);unsigned char ram[8]={0};int status=vf_run(&c,(void*)&w,4,ram,8,&code,1,protect,0);printf("id=%s sentinel=%d api_status=%d api_value=%llx native_status=%d x0=%llx pc=%llu retired=%llu sp=%llx pstate=%llx\n",id?"MMFR0":"ISAR1",sentinel,api,(unsigned long long)value,status,(unsigned long long)c.x[0],(unsigned long long)c.pc,(unsigned long long)c.retired,(unsigned long long)c.sp,(unsigned long long)c.pstate);}return munmap(code.bytes,4096);}
