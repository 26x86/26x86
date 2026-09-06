/* SPDX-License-Identifier: BSD-4-Clause */
#include "uefi.h"
#include "handoff.h"
#include "preos_bridge.h"
#include "../devices/aic_v1.h"
static EFI_GUID memory_guid={0xf4560cf6,0x40ec,0x4b4a,{0xa1,0x92,0xbf,0x1d,0x57,0xd0,0xb1,0x89}};
static EFI_GUID loaded_guid={0x5b1b31a1,0x9562,0x11d2,{0x8e,0x3f,0x00,0xa0,0xc9,0x69,0x72,0x3b}};
static EFI_GUID fs_guid={0x964e5b22,0x6459,0x11d2,{0x8e,0x39,0x00,0xa0,0xc9,0x69,0x72,0x3b}};
static EFI_GUID cpu_guid={0x26baccb1,0x6f42,0x11d4,{0xbc,0xe7,0x00,0x80,0xc7,0x3c,0x88,0x81}};
typedef struct { EFI_MEMORY_ATTRIBUTE *memory;EFI_CPU_ARCH *cpu; } protection_context;
typedef struct { uint64_t count,bytes; } allocation_metrics;
typedef struct {
    uint64_t x1,x3,ram_offset,ram_qword,retired,guest_pc;
} preos_expectation;
static EFI_SYSTEM_TABLE *system_table;
static vf_aic_v1 aic;
void *memset(void *dst,int c,size_t n) { uint8_t *p=dst;while(n--)*p++=(uint8_t)c;return dst; }
void *memcpy(void *dst,const void *src,size_t n) { uint8_t *p=dst;const uint8_t *s=src;while(n--)*p++=*s++;return dst; }
static void print(const char *s) {
    CHAR16 buf[192];unsigned n=0;
    while(*s && n<191) {
#ifdef VF_QEMU_TEST
        __asm__ volatile("outb %0,$0xe9"::"a"((uint8_t)*s));
#endif
        buf[n++]=(CHAR16)*s++;
    }
    buf[n]=0;system_table->ConOut->OutputString(system_table->ConOut,buf);
}
static void print_hex(uint64_t value) {
    char text[19]="0x0000000000000000";
    for(unsigned i=0;i<16;i++)text[17-i]="0123456789abcdef"[(value>>(i*4))&15];
    print(text);
}
static void VF_PREOS_ABI preos_trace(const char *message,void *opaque) {
    (void)opaque;print(message);
}
static EFI_STATUS allocate_pages(EFI_BOOT_SERVICES *bs,uint64_t pages,uint64_t *address,
                                 allocation_metrics *metrics) {
    EFI_STATUS status=bs->AllocatePages(0,2,pages,address);
    if(!status) { metrics->count++;metrics->bytes+=pages*4096; }
    return status;
}
static void preos_result_init(VF_PREOS_RESULT *result) {
    memset(result,0,sizeof(*result));result->abi_version=VF_PREOS_ABI_VERSION;
    result->struct_size=sizeof(*result);
}
static int run_preos(vf_efi_execution *execution,const uint8_t *guest,uint64_t guest_size,
                     uint64_t budget,uint64_t initial_x2,const preos_expectation *expectation,
                     VF_PREOS_RESULT *result) {
    VF_PREOS_CONTEXT context={0};
    execution->guest_bytes=guest;execution->guest_size=guest_size;
    execution->initial_x2=initial_x2;
    memset(execution->guest_ram,0,(size_t)execution->guest_ram_size);
    context.abi_version=VF_PREOS_ABI_VERSION;context.struct_size=sizeof(context);
    context.machine_profile=VF_MACHINE_PROFILE_M1_DIAGNOSTIC;
    context.flags=expectation?VF_PREOS_EXPECT_GOLDEN_RESULT:0;
    context.execution_budget=budget;context.guest_bytes=guest;context.guest_size=guest_size;
    context.guest_ram=execution->guest_ram;context.guest_ram_size=execution->guest_ram_size;
    context.opaque_execution_handle=execution;context.trace=preos_trace;
    if(expectation) {
        context.expected_x1=expectation->x1;context.expected_x3=expectation->x3;
        context.expected_ram_offset=expectation->ram_offset;
        context.expected_ram_qword=expectation->ram_qword;
        context.expected_retired=expectation->retired;context.expected_guest_pc=expectation->guest_pc;
    }
    preos_result_init(result);print("VF: PREOS_CONTEXT_READY\r\n");
    return vf_preos_run(&context,result);
}
static EFI_STATUS efi_status_from_preos(int code) {
    if(code==VF_PREOS_E_ABI||code==VF_PREOS_E_CONTEXT||code==VF_PREOS_E_PROFILE||
       code==VF_PREOS_E_GUEST_INPUT)return EFI_INVALID_PARAMETER;
    if(code==VF_PREOS_E_BUDGET)return EFI_ABORTED;
    return EFI_UNSUPPORTED;
}
static void print_efi_error(EFI_STATUS status) {
    print("VF: EFI_RETURN_ERROR status=");print_hex(status);print("\r\n");
}
static int page_permissions(uint64_t address,int executable) {
    uint64_t cr0,cr3,cr4;uint32_t lo,hi;
    __asm__ volatile("mov %%cr0,%0":"=r"(cr0));__asm__ volatile("mov %%cr3,%0":"=r"(cr3));
    __asm__ volatile("mov %%cr4,%0":"=r"(cr4));
    __asm__ volatile("rdmsr":"=a"(lo),"=d"(hi):"c"(0xc0000080));
    (void)hi;
    if(!(cr0&(1u<<16))||!(lo&(1u<<11))||(cr4&(1u<<12)))return -1;
    uint64_t table=cr3&UINT64_C(0x000ffffffffff000);int writable=1,nx=0;
    for(int level=3;level>=0;level--) {
        uint64_t pte=((volatile const uint64_t*)(uintptr_t)table)[(address>>(12+level*9))&511];
        if(!(pte&1))return -1;
        writable=writable&&((pte&2)!=0);nx=nx||((pte>>63)!=0);
        if(level==0 || ((level==1||level==2)&&(pte&128)))return executable?(!writable&&!nx?0:-1):(writable&&nx?0:-1);
        if(level==3&&(pte&128))return -1;
        table=pte&UINT64_C(0x000ffffffffff000);
    }
    return -1;
}
static int protect(void *p,size_t n,int executable,void *opaque) {
    protection_context *context=opaque;EFI_MEMORY_ATTRIBUTE *m=context->memory;
    uint64_t attrs=0,base=(uint64_t)(uintptr_t)p;
    if(!m) {
        /* PI CPU architectural protocol sets complete attributes. Split each
         * transition through RO+NX, preserving WB, so no intermediate RWX. */
        if(!context->cpu || context->cpu->SetMemoryAttributes(context->cpu,base,n,8|EFI_MEMORY_RO|EFI_MEMORY_XP))return -1;
        if(context->cpu->SetMemoryAttributes(context->cpu,base,n,8|(executable?EFI_MEMORY_RO:EFI_MEMORY_XP)))return -1;
        for(size_t off=0;off<n;off+=4096)if(page_permissions(base+off,executable))return -1;
        return 0;
    }
    /* Always remove write before execute and remove execute before write. */
    if(executable) {
        if(m->Set(m,base,n,EFI_MEMORY_RO))return -1;
        if(m->Clear(m,base,n,EFI_MEMORY_XP))return -1;
    } else {
        if(m->Set(m,base,n,EFI_MEMORY_XP))return -1;
        if(m->Clear(m,base,n,EFI_MEMORY_RO))return -1;
    }
    if(m->Get(m,base,n,&attrs))return -1;
    return vf_memory_attributes_satisfy(attrs, executable) ? 0 : -1;
}
static EFI_STATUS read_guest(EFI_LOADED_IMAGE *image,uint8_t *data,uint64_t *size) {
    EFI_FS *fs=0;EFI_FILE *root=0,*file=0;
    EFI_STATUS s=system_table->BootServices->HandleProtocol(image->DeviceHandle,&fs_guid,(void**)&fs);
    if(s)return s;s=fs->OpenVolume(fs,&root);if(s)return s;
    s=root->Open(root,&file,(const CHAR16*)L"\\EFI\\26x86\\guest.a64",1,0);root->Close(root);
    if(s)return s;s=file->Read(file,size,data);file->Close(file);return s;
}
EFI_STATUS VF_ABI efi_main(EFI_HANDLE handle,EFI_SYSTEM_TABLE *table) {
    static const uint32_t golden_guest[]={
        0xd2800140,0xd2800001,0x8b000021,0xd1000400,
        0xb5ffffc0,0xf9000041,0xf9400043,0xd4400000,
    };
    static const preos_expectation golden_expectation={55,55,16,55,35,32};
    system_table=table;EFI_BOOT_SERVICES *bs=table->BootServices;EFI_LOADED_IMAGE *image=0;
    EFI_STATUS status=0;allocation_metrics allocations={0};VF_PREOS_RESULT preos_result;
    uint64_t code_addr=0,ram_addr=0,guest_addr=0;
    vf_cpu cpu={0};vf_code code={0};vf_efi_execution execution={0};
    print("VF: EFI_ENTRY\r\n");
    print("26x86 Apple Silicon Sandbox - native EFI JIT\r\n");
    if(!vf_host_supported()) {
        print("UNSUPPORTED CPU: SSE4.1 and SSE4.2 required; AVX is not required.\r\n");
        print_efi_error(EFI_UNSUPPORTED);
#ifdef VF_QEMU_TEST
        __asm__ volatile("outl %0,$0xf4"::"a"(0x12u));
#endif
        return EFI_UNSUPPORTED;
    }
    print("CPU SSE4.1/SSE4.2 baseline accepted (AVX not used).\r\n");
    uint32_t event=0;
    if(vf_aic_init(&aic,896,2)||vf_aic_set_line(&aic,7,1)||vf_aic_pending(&aic,0)||
       vf_aic_write(&aic,0,0x4180,4,1u<<7)||!vf_aic_pending(&aic,0)||
       vf_aic_read(&aic,0,0x2004,4,&event)||event!=0x10007||vf_aic_pending(&aic,0)) {
        print("AIC WIRED IRQ SELFTEST FAIL\r\n");print_efi_error(EFI_UNSUPPORTED);return EFI_UNSUPPORTED;
    }
    print("AIC WIRED IRQ SELFTEST PASS\r\n");
    status=bs->HandleProtocol(handle,&loaded_guid,(void**)&image);if(status) { print_efi_error(status);return status; }
    if(image->LoadOptionsSize) {
        const vf_handoff *h=image->LoadOptions;
        if(image->LoadOptionsSize!=sizeof(*h)||!h||h->magic!=VF_HANDOFF_MAGIC||h->version!=1||h->size!=64||h->flags||
           h->memory_bytes<(UINT64_C(4)<<30)||h->memory_bytes>(UINT64_C(1)<<40)||(h->memory_bytes&((1u<<20)-1))||h->cpu_count<1||h->cpu_count>64||
           (h->target_major!=26&&h->target_major!=27)||!h->iboot_path_ptr||!h->smbios_xml_ptr||!h->device_properties_xml_ptr) {
            print("Invalid OpenCore Sandbox handoff.\r\n");print_efi_error(EFI_INVALID_PARAMETER);return EFI_INVALID_PARAMETER;
        }
        print("AIC/iBoot handoff validated; Apple input remains unopened in diagnostic gate.\r\n");
    }
    protection_context memory={0};
    status=bs->LocateProtocol(&memory_guid,0,(void**)&memory.memory);
    if(status) {
        status=bs->LocateProtocol(&cpu_guid,0,(void**)&memory.cpu);
        if(status) { print("Firmware lacks memory protection protocols; cannot enforce JIT W^X.\r\n");print_efi_error(EFI_UNSUPPORTED);return EFI_UNSUPPORTED; }
        print("Using PI CPU Architectural Protocol with hardware page-permission verification.\r\n");
    }
    status=allocate_pages(bs,4,&code_addr,&allocations);if(status) { print_efi_error(status);return status; }
    status=allocate_pages(bs,16,&ram_addr,&allocations);if(status)goto done;
    /* Sixteen guest pages are bounded input; one probe page lets Read report a
     * file larger than 64 KiB without writing beyond the allocation. */
    status=allocate_pages(bs,17,&guest_addr,&allocations);if(status)goto done;
    code.bytes=(uint8_t*)(uintptr_t)code_addr;code.capacity=16384;
    execution.magic=VF_EFI_EXECUTION_MAGIC;execution.code=&code;execution.protect=protect;
    execution.protection_opaque=&memory;execution.guest_ram=(uint8_t*)(uintptr_t)ram_addr;
    execution.guest_ram_size=65536;execution.cpu=&cpu;
    execution.machine_profile=VF_MACHINE_PROFILE_M1_DIAGNOSTIC;
    print("VF: EFI_MEMORY_READY\r\n");
    uint64_t guest_size=65537;
    status=read_guest(image,(uint8_t*)(uintptr_t)guest_addr,&guest_size);
    if(status==EFI_NOT_FOUND) {
        int result=run_preos(&execution,(const uint8_t*)golden_guest,sizeof(golden_guest),100,16,
                             &golden_expectation,&preos_result);
        if(result!=VF_PREOS_OK||preos_result.code!=VF_PREOS_OK) { status=efi_status_from_preos(result);goto done; }
        print("JIT SELFTEST PASS: sum=55, retired=35, native x86 execution, W^X verified.\r\n");
        print("No guest.a64 supplied. Rust/JIT EFI diagnostic gate complete; iBoot/XNU/macOS boot is outside this EFI entry.\r\n");
        status=0;goto done;
    }
    if(status)goto done;
    if(!guest_size||guest_size>65536||(guest_size&3)) { print("Invalid guest.a64: require 4-byte aligned raw A64, 4..65536 bytes.\r\n");status=EFI_INVALID_PARAMETER;goto done; }
    int result=run_preos(&execution,(const uint8_t*)(uintptr_t)guest_addr,guest_size,100000,0,0,&preos_result);
    if(result==VF_PREOS_OK&&preos_result.code==VF_PREOS_OK)
        print("GUEST HALT: own-code A64 guest completed. This is not macOS.\r\n");
    else status=efi_status_from_preos(result);
done:
    /* Restore NX/writable before handing allocated memory back to firmware. */
    if(code_addr) { if(protect((void*)(uintptr_t)code_addr,16384,0,&memory))status=EFI_UNSUPPORTED;else bs->FreePages(code_addr,4); }
    if(ram_addr)bs->FreePages(ram_addr,16);if(guest_addr)bs->FreePages(guest_addr,17);
    print("VF: EFI_ALLOCATIONS count=");print_hex(allocations.count);print(" bytes=");print_hex(allocations.bytes);print("\r\n");
    if(status)print_efi_error(status);else print("VF: EFI_RETURN_OK\r\n");
#ifdef VF_QEMU_TEST
    __asm__ volatile("outl %0,$0xf4"::"a"(status?0x11u:0x10u));
#endif
    return status;
}
