/* SPDX-License-Identifier: BSD-4-Clause. UNIT fixtures contain our own x86 code.
 * Optional argv[1] is a separately clang/lld-built own-code ET_EXEC fixture.
 * It must return 42, read zero BSS, and be linked at an unused low user address.
 */
#define _GNU_SOURCE
#include "vf_elf.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
static unsigned checks;
#define CHECK(x) do {++checks;if(!(x)){fprintf(stderr,"test_elf:%d: %s\n",__LINE__,#x);exit(1);}}while(0)
static uint8_t fixture[0x4000],output[0x5000];
static void w16(unsigned o,uint16_t v) {fixture[o]=(uint8_t)v;fixture[o+1]=(uint8_t)(v>>8);}
static void w32(unsigned o,uint32_t v) {w16(o,(uint16_t)v);w16(o+2,(uint16_t)(v>>16));}
static void w64(unsigned o,uint64_t v) {w32(o,(uint32_t)v);w32(o+4,(uint32_t)(v>>32));}
static void make_fixture(void) {
    memset(fixture,0,sizeof(fixture));fixture[0]=0x7f;fixture[1]='E';fixture[2]='L';fixture[3]='F';
    fixture[4]=2;fixture[5]=1;fixture[6]=1;w16(16,2);w16(18,62);w32(20,1);
    w64(24,0x20000000);w64(32,64);w16(52,64);w16(54,56);w16(56,2);
    w32(64,1);w32(68,5);w64(72,0x1000);w64(80,0x20000000);w64(88,UINT64_MAX);
    w64(96,6);w64(104,16);w64(112,4096);
    w32(120,1);w32(124,6);w64(128,0x2000);w64(136,0x20002000);
    w64(152,4);w64(160,0x1200);w64(168,4096);
    /* mov eax,42; ret -- local synthetic code, never an Apple byte stream. */
    fixture[0x1000]=0xb8;fixture[0x1001]=42;fixture[0x1005]=0xc3;
    fixture[0x2000]=1;fixture[0x2001]=2;fixture[0x2002]=3;fixture[0x2003]=4;
}
static int plan(struct vf_elf_plan *p) {return vf_elf_make_plan(fixture,sizeof(fixture),65536,p);}
static int all_value(const void *p,size_t n,uint8_t value) {
    const uint8_t *b=p;while(n--)if(*b++!=value)return 0;return 1;
}
static void test_plan_copy(void) {
    struct vf_elf_plan p,changed;make_fixture();CHECK(plan(&p)==VF_ELF_OK);
    CHECK(p.segment_count==2&&p.image_base==0x20000000&&p.image_bytes==0x4000&&p.entry_offset==0);
    CHECK(p.segments[1].image_offset==0x2000&&p.segments[0].flags==5);
    memset(output,0x5a,sizeof(output));CHECK(vf_elf_copy(fixture,sizeof(fixture),&p,output,sizeof(output))==VF_ELF_OK);
    CHECK(!memcmp(output,fixture+0x1000,6));CHECK(all_value(output+6,0x2000-6,0));
    CHECK(!memcmp(output+0x2000,fixture+0x2000,4));CHECK(all_value(output+0x2004,0x4000-0x2004,0));
    CHECK(all_value(output+0x4000,0x1000,0x5a));
    changed=p;changed.entry_offset=8;memset(output,0x5a,sizeof(output));
    CHECK(vf_elf_copy(fixture,sizeof(fixture),&changed,output,sizeof(output))==VF_ELF_EPLAN);
    CHECK(all_value(output,sizeof(output),0x5a));
    CHECK(vf_elf_copy(fixture,sizeof(fixture),&p,output,0x3fff)==VF_ELF_ERANGE);
    CHECK(all_value(output,sizeof(output),0x5a));
    changed=p;changed.segments[0].file_offset=UINT64_MAX;
    CHECK(vf_elf_copy(fixture,sizeof(fixture),&changed,output,sizeof(output))==VF_ELF_EPLAN);
    CHECK(all_value(output,sizeof(output),0x5a));
    CHECK(vf_elf_copy(fixture,sizeof(fixture),&p,fixture,sizeof(fixture))==VF_ELF_EARG);
    CHECK(fixture[0]==0x7f&&fixture[0x1000]==0xb8);
    CHECK(vf_elf_make_plan(fixture,sizeof(fixture),65536,(struct vf_elf_plan *)(void *)fixture)==VF_ELF_EARG);
    CHECK(fixture[0]==0x7f&&fixture[0x1000]==0xb8);
    CHECK(vf_elf_copy(fixture,sizeof(fixture),&p,&p,sizeof(p))==VF_ELF_EARG);
    w32(68,7);CHECK(vf_elf_copy(fixture,sizeof(fixture),&p,output,sizeof(output))==VF_ELF_EWX);
    CHECK(all_value(output,sizeof(output),0x5a));
}
static void test_rejects(void) {
    struct vf_elf_plan p;
    for(unsigned size=0;size<64;size++) {make_fixture();CHECK(vf_elf_make_plan(fixture,size,65536,&p)!=VF_ELF_OK);}
    make_fixture();fixture[4]=1;CHECK(plan(&p)==VF_ELF_EUNSUPPORTED);
    make_fixture();fixture[5]=2;CHECK(plan(&p)==VF_ELF_EUNSUPPORTED);
    make_fixture();w16(16,3);CHECK(plan(&p)==VF_ELF_EUNSUPPORTED);
    make_fixture();w16(18,183);CHECK(plan(&p)==VF_ELF_EUNSUPPORTED);
    make_fixture();w64(32,UINT64_MAX-7);CHECK(plan(&p)==VF_ELF_ERANGE);
    make_fixture();w16(56,65);CHECK(plan(&p)==VF_ELF_ELIMIT);
    make_fixture();w64(96,17);CHECK(plan(&p)==VF_ELF_ERANGE);
    make_fixture();w64(72,UINT64_MAX);CHECK(plan(&p)==VF_ELF_ERANGE);
    make_fixture();w64(104,UINT64_MAX);CHECK(plan(&p)==VF_ELF_ERANGE);
    make_fixture();w64(80,UINT64_C(0x0000800000000000));CHECK(plan(&p)==VF_ELF_ERANGE);
    make_fixture();w64(80,UINT64_C(0x00007ffffffff000));w64(104,8192);CHECK(plan(&p)==VF_ELF_ERANGE);
    make_fixture();w64(80,UINT64_C(0xfffffffffffff000));CHECK(plan(&p)==VF_ELF_ERANGE);
    make_fixture();w64(112,3);CHECK(plan(&p)==VF_ELF_EFORMAT);
    make_fixture();w64(80,0x20000008);CHECK(plan(&p)==VF_ELF_EFORMAT);
    make_fixture();w32(68,7);CHECK(plan(&p)==VF_ELF_EWX);
    /* Disjoint byte ranges in one hardware page must still fail W^X ownership. */
    make_fixture();w64(128,0x2020);w64(136,0x20000020);w64(160,4);
    CHECK(plan(&p)==VF_ELF_EOVERLAP);
    make_fixture();w64(24,0x20000008);CHECK(plan(&p)==VF_ELF_EENTRY); /* executable BSS */
    make_fixture();w64(24,0x20002000);CHECK(plan(&p)==VF_ELF_EENTRY); /* data segment */
    make_fixture();CHECK(vf_elf_make_plan(fixture,sizeof(fixture),0x3fff,&p)==VF_ELF_ELIMIT);
    CHECK(all_value(&p,sizeof(p),0));
    make_fixture();CHECK(vf_elf_make_plan(fixture,sizeof(fixture),VF_ELF_MAX_IMAGE_BYTES+1,&p)==VF_ELF_ELIMIT);
    const unsigned unsupported[]={2,3,4,7,0x6474e552,0x6474e553};
    for(unsigned i=0;i<sizeof(unsupported)/sizeof(unsupported[0]);i++) {
        make_fixture();w32(120,unsupported[i]);CHECK(plan(&p)==VF_ELF_EUNSUPPORTED);
    }
    make_fixture();w32(120,0x6474e551);w64(152,0);w64(160,0);w32(124,7);
    CHECK(plan(&p)==VF_ELF_EUNSUPPORTED);
    make_fixture();w64(40,0x3000);w16(58,64);w16(60,1);w32(0x3004,4);
    CHECK(plan(&p)==VF_ELF_EUNSUPPORTED); /* SHT_RELA, including empty declarations */
    w32(0x3004,9);CHECK(plan(&p)==VF_ELF_EUNSUPPORTED);
    w32(0x3004,19);CHECK(plan(&p)==VF_ELF_EUNSUPPORTED);
    w32(0x3004,1);w64(0x3008,0x400);CHECK(plan(&p)==VF_ELF_EUNSUPPORTED); /* TLS section */
    make_fixture();w64(40,0x3000);w16(58,64);w16(60,1);w64(0x3018,0x3fff);w64(0x3020,2);
    CHECK(plan(&p)==VF_ELF_ERANGE);
    make_fixture();w64(40,64);w16(58,64);w16(60,1);CHECK(plan(&p)==VF_ELF_EOVERLAP);
    /* Bounded revalidated mutations under ASan/UBSan; invalid plans stay zero. */
    for(unsigned pos=0;pos<176;pos++) {
        make_fixture();fixture[pos]^=0xff;int rc=plan(&p);
        CHECK(rc>=VF_ELF_EPLAN&&rc<=VF_ELF_OK);
        if(rc)CHECK(all_value(&p,sizeof(p),0));
    }
}
#if defined(__clang__)
__attribute__((no_sanitize("function")))
#endif
static void execute_own_fixture(const char *path) {
    FILE *file=fopen(path,"rb");CHECK(file!=NULL);CHECK(!fseek(file,0,SEEK_END));
    long size=ftell(file);CHECK(size>0&&(uint64_t)size<=VF_ELF_MAX_IMAGE_BYTES);rewind(file);
    uint8_t *bytes=malloc((size_t)size);CHECK(bytes!=NULL);CHECK(fread(bytes,1,(size_t)size,file)==(size_t)size);fclose(file);
    struct vf_elf_plan p;CHECK(vf_elf_make_plan(bytes,(size_t)size,65536,&p)==VF_ELF_OK);
    CHECK(p.image_base==0x20000000); /* Test fixture address, never arbitrary host memory. */
    void *target=mmap((void *)(uintptr_t)p.image_base,(size_t)p.image_bytes,PROT_READ|PROT_WRITE,
                      MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    CHECK(target!=MAP_FAILED);CHECK((uintptr_t)target==p.image_base);
    memset(target,0x5a,(size_t)p.image_bytes);
    CHECK(vf_elf_copy(bytes,(size_t)size,&p,target,(size_t)p.image_bytes)==VF_ELF_OK);
    CHECK(!mprotect(target,(size_t)p.image_bytes,PROT_NONE));
    for(unsigned i=0;i<p.segment_count;i++) {
        const struct vf_elf_segment *s=&p.segments[i];
        uint64_t start=s->virtual_address&~UINT64_C(4095);
        uint64_t end=((s->virtual_address+s->memory_bytes-1)|UINT64_C(4095))+1;
        int prot=PROT_READ|((s->flags&VF_ELF_WRITE)?PROT_WRITE:0)|((s->flags&VF_ELF_EXECUTE)?PROT_EXEC:0);
        CHECK(!mprotect((void *)(uintptr_t)start,(size_t)(end-start),prot));
    }
    uint32_t a=0,b,c,d;__asm__ volatile("cpuid":"+a"(a),"=b"(b),"=c"(c),"=d"(d)::"memory");
    unsigned (*entry)(void)=(unsigned (*)(void))((uint8_t *)target+p.entry_offset);
    CHECK(entry()==42);CHECK(!munmap(target,(size_t)p.image_bytes));free(bytes);
}
int main(int argc,char **argv) {
    CHECK(argc==1||argc==2);test_plan_copy();test_rejects();
    if(argc==2)execute_own_fixture(argv[1]);
    printf("{\"test\":\"elf\",\"level\":\"UNIT\",\"passed\":true,\"checks\":%u,\"hardware_verified\":false,\"own_compiled_native_execution\":%s,\"boot_authorized\":false}\n",checks,argc==2?"true":"false");
    return 0;
}
