/* SPDX-License-Identifier: BSD-4-Clause; repository LICENSE.txt applies.
 * Authenticated boot input preparation. No EBS, VMXON or guest execution yet. */
#include "platform.h"
#include "../../include/vf_bundle.h"
#include "../../include/vf_elf.h"
#include "trust_anchor.h"
#define EFI_SECURITY_VIOLATION (EFI_ERROR_BIT|26)
#define EFI_OUT_OF_RESOURCES (EFI_ERROR_BIT|9)
#define BOOT_INPUT_BUDGET (UINT64_C(256)*1024*1024)
static EFI_SYSTEM_TABLE *st;
static EFI_GUID loaded_guid={0x5b1b31a1,0x9562,0x11d2,{0x8e,0x3f,0x00,0xa0,0xc9,0x69,0x72,0x3b}};
static EFI_GUID fs_guid={0x964e5b22,0x6459,0x11d2,{0x8e,0x39,0x00,0xa0,0xc9,0x69,0x72,0x3b}};
static uint8_t manifest[VF_BUNDLE_MAX_MANIFEST_BYTES+1],signature[65];
static struct vf_bundle_manifest authenticated,verified;
static struct vf_bundle_blob blobs[VF_BUNDLE_MAX_ENTRIES];
static uint64_t allocations[VF_BUNDLE_MAX_ENTRIES*2],page_counts[VF_BUNDLE_MAX_ENTRIES*2];
static unsigned allocation_count;
static uint64_t allocated_bytes;
static struct vf_efi_probe probe;
static EFI_GUID memory_guid={0xf4560cf6,0x40ec,0x4b4a,{0xa1,0x92,0xbf,0x1d,0x57,0xd0,0xb1,0x89}};
static EFI_GUID cpu_guid={0x26baccb1,0x6f42,0x11d4,{0xbc,0xe7,0x00,0x80,0xc7,0x3c,0x88,0x81}};
static EFI_MEMORY_ATTRIBUTE *memory_attributes;
static EFI_CPU_ARCH *cpu_attributes;
static void print(const char *text) {
    CHAR16 buffer[192];unsigned n=0;
    while(*text&&n<191) {
#ifdef VF_QEMU_TEST
        __asm__ volatile("outb %0,$0xe9"::"a"((uint8_t)*text));
#endif
        buffer[n++]=(CHAR16)*text++;
    }
    buffer[n]=0;if(st->ConOut)st->ConOut->OutputString(st->ConOut,buffer);
}
static void number(uint64_t n) {char s[19]="0x0000000000000000";for(unsigned i=0;i<16;i++)s[17-i]="0123456789abcdef"[(n>>(4*i))&15];print(s);}
static EFI_STATUS read_file(EFI_FILE *root,const CHAR16 *path,void *out,uint64_t *bytes) {
    EFI_FILE *file=0;EFI_STATUS s=root->Open(root,&file,path,1,0);if(s)return s;
    s=file->Read(file,bytes,out);EFI_STATUS close=file->Close(file);return s?s:close;
}
static int writable_nx_page(uint64_t address) {
    uint64_t cr0,cr3,cr4;uint32_t lo,hi;
    __asm__ volatile("mov %%cr0,%0":"=r"(cr0));__asm__ volatile("mov %%cr3,%0":"=r"(cr3));
    __asm__ volatile("mov %%cr4,%0":"=r"(cr4));__asm__ volatile("rdmsr":"=a"(lo),"=d"(hi):"c"(0xc0000080));
    (void)hi;if(!(cr0&(1u<<16))||!(lo&(1u<<11))||(cr4&(1u<<12)))return 0;
    uint64_t base=cr3&UINT64_C(0x000ffffffffff000);int writable=1,nx=0;
    for(int level=3;level>=0;level--) {
        uint64_t pte=((const volatile uint64_t*)(uintptr_t)base)[(address>>(12+level*9))&511];
        if(!(pte&1))return 0;writable=writable&&((pte&2)!=0);nx=nx||((pte>>63)!=0);
        if(level==0||((level==1||level==2)&&(pte&128)))return writable&&nx;
        if(level==3&&(pte&128))return 0;base=pte&UINT64_C(0x000ffffffffff000);
    }
    return 0;
}
static EFI_STATUS make_staging_nx(uint64_t address,uint64_t bytes) {
    EFI_STATUS s;
    if(memory_attributes) {
        s=memory_attributes->Set(memory_attributes,address,bytes,EFI_MEMORY_XP);if(s)return s;
        s=memory_attributes->Clear(memory_attributes,address,bytes,EFI_MEMORY_RO);if(s)return s;
    } else if(cpu_attributes) {
        s=cpu_attributes->SetMemoryAttributes(cpu_attributes,address,bytes,8|EFI_MEMORY_XP);if(s)return s;
    } else return EFI_UNSUPPORTED;
    for(uint64_t off=0;off<bytes;off+=4096)if(!writable_nx_page(address+off))return EFI_UNSUPPORTED;
    return 0;
}
static EFI_STATUS allocate(uint64_t bytes,uint64_t *address) {
    if(!bytes||bytes>BOOT_INPUT_BUDGET||allocation_count>=VF_BUNDLE_MAX_ENTRIES*2)return EFI_OUT_OF_RESOURCES;
    uint64_t pages=(bytes+4095)/4096,rounded=pages*4096;*address=0;
    /* The limit covers actual page ownership, including final-page slack. */
    if(rounded>BOOT_INPUT_BUDGET-allocated_bytes)return EFI_OUT_OF_RESOURCES;
    EFI_STATUS s=st->BootServices->AllocatePages(0,2,pages,address);
    if(!s) {allocations[allocation_count]=*address;page_counts[allocation_count++]=pages;allocated_bytes+=rounded;s=make_staging_nx(*address,rounded);}
    return s;
}
static void role_path(const struct vf_bundle_entry *entry,CHAR16 *path) {
    const CHAR16 *prefix=(const CHAR16*)L"\\EFI\\26x86\\VSK\\";unsigned p=0;
    while(*prefix)path[p++]=*prefix++;
    const CHAR16 *name=entry->role==VF_BUNDLE_ROLE_CONFIG?(const CHAR16*)L"config.plist":
                       entry->role==VF_BUNDLE_ROLE_CORE?(const CHAR16*)L"core.elf":(const CHAR16*)L"cell-";
    while(*name)path[p++]=*name++;
    if(entry->role==VF_BUNDLE_ROLE_SERVICE) {
        if(entry->instance>=10)path[p++]=(CHAR16)('0'+entry->instance/10);
        path[p++]=(CHAR16)('0'+entry->instance%10);
        name=(const CHAR16*)L".elf";while(*name)path[p++]=*name++;
    }
    path[p]=0;
}
static EFI_STATUS inputs(EFI_LOADED_IMAGE *image) {
    struct vf_bundle_policy policy={.trusted_public_key=VF_TRUST_KEY_BYTES,
        .minimum_release_epoch=VF_MIN_RELEASE_EPOCH,.expected_target_major=VF_TARGET_MAJOR};
    unsigned key_set=0;for(unsigned i=0;i<32;i++)key_set|=policy.trusted_public_key[i];
    if(!key_set) {print("VSK E_TRUST_ANCHOR_UNPROVISIONED\r\n");return EFI_SECURITY_VIOLATION;}
    EFI_FS *fs=0;EFI_FILE *root=0;EFI_STATUS status=st->BootServices->HandleProtocol(image->DeviceHandle,&fs_guid,(void**)&fs);
    if(status)return status;status=fs->OpenVolume(fs,&root);if(status)return status;
    uint64_t mbytes=sizeof(manifest),sbytes=sizeof(signature);
    status=read_file(root,(const CHAR16*)L"\\EFI\\26x86\\VSK\\manifest.vfb",manifest,&mbytes);if(status)goto done;
    status=read_file(root,(const CHAR16*)L"\\EFI\\26x86\\VSK\\manifest.sig",signature,&sbytes);if(status)goto done;
    int result=vf_bundle_authenticate_manifest(manifest,(uint32_t)mbytes,signature,(uint32_t)sbytes,&policy,&authenticated);
    if(result) {print("VSK E_BUNDLE_AUTH ");number((uint32_t)result);print("\r\n");status=EFI_SECURITY_VIOLATION;goto done;}
    print("VSK MANIFEST_SIGNATURE_VERIFIED\r\n");
    uint64_t used=0;
    for(unsigned i=0;i<authenticated.entry_count;i++) {
        const struct vf_bundle_entry *e=&authenticated.entries[i];
        if(e->bytes>=BOOT_INPUT_BUDGET-used) {status=EFI_OUT_OF_RESOURCES;goto done;}
        used+=e->bytes+1;uint64_t address=0;
        status=allocate(e->bytes+1,&address);if(status)goto done;
        CHAR16 path[64];role_path(e,path);uint64_t bytes=e->bytes+1;
        status=read_file(root,path,(void*)(uintptr_t)address,&bytes);if(status)goto done;
        if(bytes!=e->bytes) {status=EFI_SECURITY_VIOLATION;goto done;}
        blobs[i].role=e->role;blobs[i].instance=e->instance;blobs[i].data=(const uint8_t*)(uintptr_t)address;blobs[i].bytes=bytes;
    }
    result=vf_bundle_verify(manifest,(uint32_t)mbytes,signature,(uint32_t)sbytes,&policy,blobs,authenticated.entry_count,&verified);
    if(result) {print("VSK E_BLOB_INTEGRITY ");number((uint32_t)result);print("\r\n");status=EFI_SECURITY_VIOLATION;goto done;}
    print("VSK ALL_BLOB_HASHES_VERIFIED\r\n");
    for(unsigned i=0;i<verified.entry_count;i++)if(blobs[i].role!=VF_BUNDLE_ROLE_CONFIG) {
        struct vf_elf_plan plan;result=vf_elf_make_plan(blobs[i].data,(size_t)blobs[i].bytes,VF_ELF_MAX_IMAGE_BYTES,&plan);
        if(result) {print("VSK E_ELF_PLAN\r\n");status=EFI_UNSUPPORTED;goto done;}
        if(plan.image_bytes>BOOT_INPUT_BUDGET-used) {status=EFI_OUT_OF_RESOURCES;goto done;}
        used+=plan.image_bytes;uint64_t address=0;
        status=allocate(plan.image_bytes,&address);if(status)goto done;
        result=vf_elf_copy(blobs[i].data,(size_t)blobs[i].bytes,&plan,(void*)(uintptr_t)address,(size_t)plan.image_bytes);
        if(result) {status=EFI_UNSUPPORTED;goto done;}
    }
    print("VSK CORE_AND_SERVICE_ELF_COPIED_RW_NX\r\n");
    /* Bytes are never executed from this staging buffer. ET_EXEC mappings,
     * W^X sealing, signed-config interpretation and cell ownership are next. */
    status=0;
done:
    {EFI_STATUS close=root->Close(root);if(!status)status=close;}return status;
}
EFI_STATUS VF_ABI efi_main(EFI_HANDLE handle,EFI_SYSTEM_TABLE *table) {
    st=table;allocation_count=0;allocated_bytes=0;
    print("26x86 VSK authenticated EFI bootstrap\r\n");
#ifdef VF_QEMU_TEST
    print("VSK TEST INSTRUMENTATION - NOT A PRODUCT RELEASE\r\n");
#endif
    EFI_LOADED_IMAGE *image=0;EFI_STATUS status=st->BootServices->HandleProtocol(handle,&loaded_guid,(void**)&image);
    if(!status) {
        st->BootServices->LocateProtocol(&memory_guid,0,(void**)&memory_attributes);
        if(!memory_attributes)st->BootServices->LocateProtocol(&cpu_guid,0,(void**)&cpu_attributes);
    }
    if(!status)status=inputs(image);
    if(!status) {
        EFI_STATUS measurement=vf_efi_measure(st,&probe);
        print("VSK EFI_MEMORY_MAP_DESCRIPTORS ");number(probe.map_descriptors);print("\r\n");
        print("VSK BSP_CPUID1_ECX ");number(probe.leaf1_ecx);print("\r\n");
        print("VSK ACPI_STATUS ");number((uint32_t)probe.acpi_status);print("\r\n");
        print("VSK DMAR_UNITS ");number(probe.dmar.unit_count);print("\r\n");
        print("VSK DMAR_IR_ADVERTISED ");number(probe.dmar.interrupt_remap_reported);print("\r\n");
        if(measurement) {print("VSK E_FIRMWARE_SNAPSHOT\r\n");status=measurement;}
        else {
            print("VSK FIRMWARE_SNAPSHOT_READ\r\n");
            print("VSK E_PLATFORM_PROFILE_UNREGISTERED: AppleIntelOnly, no EBS or guest execution\r\n");
            status=EFI_UNSUPPORTED;
        }
    }
    EFI_STATUS release_status=0;
    while(allocation_count) {
        unsigned i=--allocation_count;EFI_STATUS freed=st->BootServices->FreePages(allocations[i],page_counts[i]);
        if(freed) {if(!release_status)release_status=freed;}
        else allocated_bytes-=page_counts[i]*4096;
    }
    if(release_status) {
        print("VSK E_INPUT_ALLOCATION_RELEASE ");number(release_status);print("\r\n");
        if(!status)status=release_status;
    } else print("VSK INPUT_ALLOCATIONS_RELEASED\r\n");
#ifdef VF_QEMU_TEST
    __asm__ volatile("outl %0,$0xf4"::"a"(status==EFI_UNSUPPORTED?0x10u:0x11u));
#endif
    return status;
}
