/* Independent native-host execution check of the authored ARM input program.
 * This isolates JIT execution from EFI/Core placement validation.
 */
#include "boot_jit.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

static int protect(void *pointer,size_t bytes,int executable,void *opaque) {
    (void)opaque;
    return mprotect(pointer,bytes,PROT_READ|(executable?PROT_EXEC:PROT_WRITE));
}
static void put64(uint8_t *ram,size_t offset,uint64_t value) {
    memcpy(ram+offset,&value,8);
}
int main(int argc,char **argv) {
    assert(argc==2);
    uint8_t *ram=calloc(1,64*1024*1024);assert(ram);
    FILE *file=fopen(argv[1],"rb");assert(file);
    assert(fread(ram+0x2000000,1,40960,file)==40960);assert(fgetc(file)==EOF);fclose(file);
    put64(ram,0x200c000,0x20002);
    put64(ram,0x200c000+16,0x40000000);
    put64(ram,0x200c000+96,UINT64_C(0xfffffe0002010000));
    put64(ram,0x200c000+1144,64*1024*1024);
    uint8_t *code=mmap(0,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    assert(code!=MAP_FAILED);
    vf_boot_result result;
    int status=vf_boot_run(ram,64*1024*1024,0x40000000,0x42004400,0x4200c000,0x42024000,code,4096,100000,protect,0,&result);
    assert(status==VF_HALT&&result.status==VF_HALT);
    assert(result.retired==25&&result.pc==0x42004464&&result.compiled_blocks>0);
    assert(result.x0==0x4200c000&&result.x1==0x20002&&result.x2==0x40010000&&result.x3==UINT64_C(0xfffffe0002010000));
    uint64_t expected[4]={0x20002,UINT64_C(0xfffffe0002010000),0x40000000,64*1024*1024};
    assert(!memcmp(ram+0x10000,expected,sizeof(expected)));
    for(unsigned pixel=0;pixel<16;pixel++)assert(!memcmp(ram+0x30000+pixel*4,"\x33\x22\x11\0",4));
    printf("{\"passed\":true,\"host\":\"x86_64\",\"guest\":\"arm64\",\"retired\":%llu,\"native_blocks\":%llu,\"boot_args_readback\":true,\"guest_framebuffer_pixels\":16,\"efi_executed\":false,\"xnu_executed\":false}\n",(unsigned long long)result.retired,(unsigned long long)result.compiled_blocks);
    assert(!munmap(code,4096));free(ram);return 0;
}
