/* Original UEFI/ACPI snapshot adapter; firmware pointers checked against the
 * current memory map before table reads. No firmware/MMIO mutation. */
#include "platform.h"
#include "../../include/vf_boot.h"
#define LIMIT 1048576u
static _Alignas(8) uint8_t memory_map[LIMIT], root_table[LIMIT], dmar_table[LIMIT];
static uint64_t map_bytes, map_stride;
typedef struct { EFI_GUID guid; void *table; } config_entry;
static const EFI_GUID acpi2={0x8868e871,0xe4f1,0x11d3,{0xbc,0x22,0x00,0x80,0xc7,0x3c,0x88,0x81}};
static const EFI_GUID acpi1={0xeb9d2d30,0x2d88,0x11d3,{0x9a,0x16,0x00,0x90,0x27,0x3f,0xc1,0x4d}};
static uint32_t rd32(const uint8_t *p) { return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24; }
static uint64_t rd64(const uint8_t *p) { return rd32(p)|(uint64_t)rd32(p+4)<<32; }
static void copy(void *o,const void *i,size_t n) { volatile uint8_t *d=o;const volatile uint8_t *s=i;while(n--)*d++=*s++; }
static void zero(void *o,size_t n) { volatile uint8_t *d=o;while(n--)*d++=0; }
static int equal(const void *a,const void *b,size_t n) {const uint8_t *x=a,*y=b;while(n--)if(*x++!=*y++)return 0;return 1;}
static int checksum(const uint8_t *b,size_t n) {uint8_t s=0;while(n--)s=(uint8_t)(s+*b++);return s==0;}
static int mapped(uint64_t address,uint64_t bytes) {
    if(!address||!bytes||bytes>UINT64_MAX-address)return 0;
    uint64_t end=address+bytes;
    while(address<end) {
        int found=0;
        for(uint64_t off=0;off<map_bytes;off+=map_stride) {
            const uint8_t *d=memory_map+off;uint32_t type=rd32(d);
            uint64_t base=rd64(d+8),length=rd64(d+24)*4096;
            if(address>=base && address-base<length) {
                /* Memory map already passed overflow/overlap validation. */
                if(!((type>=1&&type<=6)||type==9||type==10))return 0;
                uint64_t limit=base+length;address=limit<end?limit:end;found=1;break;
            }
        }
        if(!found)return 0;
    }
    return 1;
}
static int read_physical(uint64_t address,void *out,uint64_t bytes) {
    if(!mapped(address,bytes))return 0;
    copy(out,(const void *)(uintptr_t)address,(size_t)bytes);return 1;
}
static int table_read(uint64_t address,uint8_t *out,uint32_t *length) {
    uint8_t header[36];
    if(!read_physical(address,header,sizeof(header)))return -1;
    *length=rd32(header+4);
    if(*length<36||*length>LIMIT||!read_physical(address,out,*length)||
       !equal(header,out,sizeof(header))||!checksum(out,*length))return -2;
    return 0;
}
static void cpuid(uint32_t leaf,uint32_t sub,uint32_t *a,uint32_t *b,uint32_t *c,uint32_t *d) {
    __asm__ volatile("cpuid":"=a"(*a),"=b"(*b),"=c"(*c),"=d"(*d):"a"(leaf),"c"(sub));
}
static uint64_t msr(uint32_t id) {uint32_t lo,hi;__asm__ volatile("rdmsr":"=a"(lo),"=d"(hi):"c"(id));return lo|(uint64_t)hi<<32;}
static void cpu(struct vf_efi_probe *p) {
    uint32_t a,b,c,d,max;
    cpuid(0,0,&max,&b,&c,&d);
    p->intel_vendor=b==0x756e6547&&d==0x49656e69&&c==0x6c65746e;
    if(max<1)return;
    cpuid(1,0,&a,&b,&p->leaf1_ecx,&p->leaf1_edx);
    p->hypervisor_reported=(p->leaf1_ecx>>31)&1;
    cpuid(0x80000000u,0,&a,&b,&c,&d);
    if(a>=0x80000001u)cpuid(0x80000001u,0,&a,&b,&c,&p->extended_edx);
    /* A detected outer hypervisor is outside product admission. Do not probe
     * MSRs it may intercept without an exception recovery substrate. */
    if(!p->intel_vendor||p->hypervisor_reported||!(p->leaf1_ecx&(1u<<5)))return;
    p->feature_control=msr(0x3a);p->vmx_basic=msr(0x480);p->vmx_msr_sampled=1;
    uint64_t primary=msr((p->vmx_basic&(UINT64_C(1)<<55))?0x48e:0x482);
    if(primary&(UINT64_C(1)<<63)) {
        uint64_t secondary=msr(0x48b);
        if(secondary&(UINT64_C(1)<<33))p->ept_vpid_cap=msr(0x48c);
    }
}
static int acpi(EFI_SYSTEM_TABLE *st,struct vf_efi_probe *p) {
    if(st->NumberOfTableEntries>4096||!st->NumberOfTableEntries)return -1;
    uint64_t bytes=st->NumberOfTableEntries*sizeof(config_entry);
    if(!mapped((uint64_t)(uintptr_t)st->ConfigurationTable,bytes))return -2;
    const config_entry *entries=st->ConfigurationTable;
    uint64_t v1=0,v2=0;
    for(uint64_t i=0;i<st->NumberOfTableEntries;i++) {
        if(equal(&entries[i].guid,&acpi2,sizeof(acpi2))) {if(v2)return -3;v2=(uint64_t)(uintptr_t)entries[i].table;}
        if(equal(&entries[i].guid,&acpi1,sizeof(acpi1))) {if(v1)return -3;v1=(uint64_t)(uintptr_t)entries[i].table;}
    }
    uint64_t pointer=v2?v2:v1;uint8_t rsdp[4096],rsdp_header[36];
    if(!read_physical(pointer,rsdp,20)||!equal(rsdp,"RSD PTR ",8)||!checksum(rsdp,20))return -4;
    copy(rsdp_header,rsdp,20);
    p->rsdp_revision=rsdp[15];unsigned stride=4;uint64_t root=rd32(rsdp+16);
    if(p->rsdp_revision==2) {
        if(!read_physical(pointer,rsdp,36)||!equal(rsdp_header,rsdp,20))return -5;
        uint32_t length=rd32(rsdp+20);
        copy(rsdp_header,rsdp,36);
        if(length<36||length>sizeof(rsdp)||!read_physical(pointer,rsdp,length)||
           !equal(rsdp_header,rsdp,36)||!checksum(rsdp,length))return -5;
        if(rd64(rsdp+24)) {root=rd64(rsdp+24);stride=8;}
    } else if(p->rsdp_revision!=0)return -6;
    uint32_t length=0;
    if(table_read(root,root_table,&length)||!equal(root_table,stride==8?"XSDT":"RSDT",4)||
       (length-36)%stride||(length-36)/stride>4096)return -7;
    for(unsigned off=36;off<length;off+=stride) {
        uint64_t address=stride==8?rd64(root_table+off):rd32(root_table+off);uint8_t header[36];
        if(!read_physical(address,header,sizeof(header)))return -8;
        if(!equal(header,"DMAR",4))continue;
        if(p->dmar_bytes)return -9;
        if(table_read(address,dmar_table,&p->dmar_bytes))return -10;
        p->dmar_status=vf_dmar_parse(dmar_table,p->dmar_bytes,NULL,0,&p->dmar);
        if(p->dmar_status)return -11;
    }
    return 0;
}
EFI_STATUS vf_efi_measure(EFI_SYSTEM_TABLE *st,struct vf_efi_probe *p) {
    if(!st||!st->BootServices||!p)return EFI_INVALID_PARAMETER;
    zero(p,sizeof(*p));p->acpi_status=-1;p->dmar_status=-1;cpu(p);
    map_bytes=sizeof(memory_map);map_stride=0;
    struct vf_efi_map_snapshot snapshot;
    vf_status captured=vf_efi_capture_memory_map(
        (vf_efi_get_memory_map_fn)st->BootServices->GetMemoryMap,
        memory_map,sizeof(memory_map),&snapshot);
    if(captured!=VF_OK) {
        p->memory_map_status=(int32_t)captured;
        return captured==VF_ERANGE?EFI_BUFFER_TOO_SMALL:EFI_UNSUPPORTED;
    }
    map_bytes=snapshot.bytes;map_stride=snapshot.descriptor_bytes;
    p->memory_map_status=VF_BOOT_OK;
    p->memory_map_key=snapshot.map_key;
    p->map_descriptors=(uint32_t)(snapshot.bytes/snapshot.descriptor_bytes);
    p->acpi_status=acpi(st,p);
    return p->acpi_status?EFI_UNSUPPORTED:0;
}
