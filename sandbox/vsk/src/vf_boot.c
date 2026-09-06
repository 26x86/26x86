/* SPDX-License-Identifier: BSD-4-Clause. Original implementation of VF-SPEC-001.
 * No EFI/EBS/VMX/VT-d instructions or cryptographic verification implemented.
 */
#include "vf_boot.h"

static int stage_valid(uint32_t s) { return s<VF_BOOT_STAGE_COUNT; }
void vf_boot_init(struct vf_boot_state *s) {
    if(s) { s->stage=VF_BOOT_EFI_ENTRY;s->failed_stage=VF_BOOT_EFI_ENTRY;s->error=0;s->ebs_exited=0; }
}
int vf_boot_expected_next(uint32_t current,uint32_t next) {
    return stage_valid(current)&&stage_valid(next)&&next==current+1;
}
int vf_boot_fail(struct vf_boot_state *s,int error) {
    if(!s)return VF_BOOT_EARG;
    if(s->stage==VF_BOOT_FAILED)return VF_BOOT_EFAILED;
    s->failed_stage=s->stage;s->stage=VF_BOOT_FAILED;
    s->error=error<0?error:VF_BOOT_EARG;return s->error;
}
int vf_boot_advance(struct vf_boot_state *s,uint32_t next) {
    if(!s)return VF_BOOT_EARG;
    if(s->stage==VF_BOOT_FAILED)return VF_BOOT_EFAILED;
    if(!vf_boot_expected_next(s->stage,next))return vf_boot_fail(s,VF_BOOT_EORDER);
    /* There is intentionally no "verified=true", injectable success callback,
     * fixture receipt, or public authority-token constructor. Future trusted
     * implementations must replace these unavailable boundaries with real
     * signature/measurement/ownership/isolation work, not toggle capability bits.
     */
    switch(next) {
    case VF_BOOT_LOAD_CONFIG_AND_SIGNED_BUNDLE:s->stage=next;return VF_BOOT_OK;
    case VF_BOOT_VALIDATE_CONFIG_AND_PLATFORM_POLICY:return vf_boot_fail(s,VF_BOOT_ESIGNATURE_VERIFIER_UNAVAILABLE);
    case VF_BOOT_SNAPSHOT_FIRMWARE_TABLES:return vf_boot_fail(s,VF_BOOT_EPLATFORM_MEASUREMENT_UNAVAILABLE);
    case VF_BOOT_EXIT_BOOT_SERVICES:return vf_boot_fail(s,VF_BOOT_EFIRMWARE_SNAPSHOT_UNAVAILABLE);
    case VF_BOOT_ROOT_MEMORY_AND_CPU_INIT:
        return vf_boot_fail(s,s->ebs_exited?VF_BOOT_EROOT_INIT_UNAVAILABLE:VF_BOOT_EEBS_UNAVAILABLE);
    case VF_BOOT_QUIESCE_AND_QUARANTINE_DEVICES:return vf_boot_fail(s,VF_BOOT_EQUARANTINE_UNAVAILABLE);
    case VF_BOOT_ENABLE_VTD_AND_INTERRUPT_REMAP:return vf_boot_fail(s,VF_BOOT_EVTD_IR_UNAVAILABLE);
    case VF_BOOT_ENABLE_VMX_AND_CREATE_CELLS:return vf_boot_fail(s,VF_BOOT_EVMX_EPT_UNAVAILABLE);
    case VF_BOOT_START_APPROVED_DRIVERS:return vf_boot_fail(s,VF_BOOT_EDRIVER_VERIFICATION_UNAVAILABLE);
    case VF_BOOT_RESOLVE_AND_FREEZE_MACHINE:return vf_boot_fail(s,VF_BOOT_EMACHINE_FREEZE_UNAVAILABLE);
    case VF_BOOT_VALIDATE_EXACT_GUEST_PROFILE:return vf_boot_fail(s,VF_BOOT_EGUEST_PROFILE_VERIFIER_UNAVAILABLE);
    case VF_BOOT_RUN_ARM64_GUEST:return vf_boot_fail(s,VF_BOOT_EGUEST_RUNTIME_UNAVAILABLE);
    default:return vf_boot_fail(s,VF_BOOT_EORDER);
    }
}
int vf_boot_record_ebs_result(struct vf_boot_state *s,uint64_t status) {
    if(!s)return VF_BOOT_EARG;
    if(s->stage==VF_BOOT_FAILED)return VF_BOOT_EFAILED;
    if(s->stage!=VF_BOOT_EXIT_BOOT_SERVICES||s->ebs_exited)return vf_boot_fail(s,VF_BOOT_EFIRMWARE_LIFETIME);
    if(status)return vf_boot_fail(s,VF_BOOT_EEBS_UNAVAILABLE);
    s->ebs_exited=1;return VF_BOOT_OK;
}
int vf_boot_firmware_calls_allowed(const struct vf_boot_state *s) {
    return s&&stage_valid(s->stage)&&s->stage<=VF_BOOT_EXIT_BOOT_SERVICES&&!s->ebs_exited&&!s->error;
}
int vf_boot_authorized(const struct vf_boot_state *s) { (void)s;return 0; }

static uint32_t le32(const uint8_t *p) {
    return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;
}
static uint64_t le64(const uint8_t *p) { return (uint64_t)le32(p)|(uint64_t)le32(p+4)<<32; }
static int valid_range(struct vf_boot_range r) { return r.base&&r.bytes&&r.bytes<=UINT64_MAX-r.base; }
static int overlaps(struct vf_boot_range a,struct vf_boot_range b) {
    return a.base<b.base+b.bytes && b.base<a.base+a.bytes;
}
static int contains(struct vf_boot_range outer,struct vf_boot_range inner) {
    return inner.base>=outer.base && inner.base-outer.base<=outer.bytes && inner.bytes<=outer.bytes-(inner.base-outer.base);
}
static struct vf_boot_range descriptor_range(const uint8_t *d) {
    struct vf_boot_range r={le64(d+8),le64(d+24)*VF_BOOT_PAGE_BYTES};return r;
}
int vf_boot_validate_memory_map(const void *bytes,size_t length,uint32_t stride,uint32_t version) {
    if(!bytes)return VF_BOOT_EARG;
    if(version!=VF_BOOT_EFI_DESCRIPTOR_VERSION)return VF_BOOT_EVERSION;
    if(stride<40||stride>256||(stride&7)||!length||length%stride||length/stride>VF_BOOT_MAX_DESCRIPTORS)return VF_BOOT_EMAP;
    const uint8_t *map=bytes;
    for(size_t off=0;off<length;off+=stride) {
        const uint8_t *d=map+off;uint32_t type=le32(d);uint64_t base=le64(d+8),pages=le64(d+24);
        /* Preserve defined standard and OEM/OS-reserved descriptors; unknown
         * reserved types are never accepted as owned root RAM below. */
        if((type>15&&type<0x70000000)||!pages||pages>UINT64_MAX/VF_BOOT_PAGE_BYTES ||
           (base&4095)||(le64(d+16)&4095)||pages*VF_BOOT_PAGE_BYTES>UINT64_MAX-base)return VF_BOOT_EMAP;
        struct vf_boot_range r=descriptor_range(d);
        for(size_t prior=0;prior<off;prior+=stride)
            if(overlaps(r,descriptor_range(map+prior)))return VF_BOOT_EOVERLAP;
    }
    return VF_BOOT_OK;
}
static int type_allowed(const uint8_t *descriptor,uint32_t kind) {
    uint32_t type=le32(descriptor);
    if(kind==VF_BOOT_OWNED_FRAMEBUFFER)return type==0||type==11;
    /* The root may reserve only pages actually allocated as LoaderCode/Data;
     * conventional, boot-services, ACPI, runtime and unaccepted pages are not
     * allocator ownership evidence. EFI_MEMORY_RUNTIME excludes reclamation. */
    return kind==VF_BOOT_OWNED_RAM && (type==1||type==2) && !(le64(descriptor+32)&(UINT64_C(1)<<63));
}
static int covered(const uint8_t *map,size_t length,uint32_t stride,struct vf_boot_range r,uint32_t kind) {
    uint64_t pos=r.base,end=r.base+r.bytes;
    while(pos<end) {
        int found=0;
        for(size_t off=0;off<length;off+=stride) {
            struct vf_boot_range d=descriptor_range(map+off);
            if(pos>=d.base&&pos-d.base<d.bytes) {
                if(!type_allowed(map+off,kind))return VF_BOOT_EMEMORY_TYPE;
                uint64_t limit=d.base+d.bytes;pos=limit<end?limit:end;found=1;break;
            }
        }
        if(!found)return VF_BOOT_EMAP;
    }
    return VF_BOOT_OK;
}
static int owned_range(struct vf_boot_range range,uint32_t kind,const struct vf_boot_owned_extent *owned,size_t count) {
    for(size_t i=0;i<count;i++)if(owned[i].kind==kind&&contains(owned[i].range,range))return VF_BOOT_OK;
    return VF_BOOT_EUNOWNED;
}
static int any_nonzero(const uint8_t *bytes,size_t length) {
    uint8_t combined=0;for(size_t i=0;i<length;i++)combined|=bytes[i];return combined!=0;
}
int vf_boot_validate_handoff(const struct vf_boot_handoff *h,const void *map_bytes,size_t map_length,
                            const struct vf_boot_owned_extent *owned,size_t owned_count) {
    if(!h||!map_bytes||!owned||!owned_count||owned_count>VF_BOOT_MAX_OWNED_EXTENTS)return VF_BOOT_EARG;
    if(h->handoff_version!=VF_BOOT_HANDOFF_VERSION||h->struct_bytes!=sizeof(*h))return VF_BOOT_EVERSION;
    if(h->reserved0 || h->memory_map.bytes!=map_length)return VF_BOOT_EMAP;
    if(!any_nonzero(h->config_sha256,32)||!any_nonzero(h->boot_disk_identifier,32))return VF_BOOT_EARG;
    int result=vf_boot_validate_memory_map(map_bytes,map_length,h->descriptor_bytes,h->descriptor_version);
    if(result)return result;
    for(size_t i=0;i<owned_count;i++) {
        if(owned[i].reserved||!valid_range(owned[i].range)||(owned[i].range.base&4095)||(owned[i].range.bytes&4095))return VF_BOOT_ERANGE;
        if(owned[i].kind!=VF_BOOT_OWNED_RAM&&owned[i].kind!=VF_BOOT_OWNED_FRAMEBUFFER)return VF_BOOT_EMEMORY_TYPE;
        for(size_t j=0;j<i;j++)if(overlaps(owned[i].range,owned[j].range))return VF_BOOT_EOVERLAP;
        result=covered(map_bytes,map_length,h->descriptor_bytes,owned[i].range,owned[i].kind);if(result)return result;
    }
    /* Copy individual fields: do not rely on arithmetic across struct members. */
    const struct vf_boot_range ranges[]={h->memory_map,h->rsdp_snapshot,h->board_snapshot,h->core_image,
                                        h->service_bundle,h->config_blob,h->log_ring,h->framebuffer};
    size_t range_count=h->framebuffer.bytes?8:7;
    for(size_t i=0;i<range_count;i++) {
        if(!valid_range(ranges[i])||(ranges[i].base&7))return VF_BOOT_ERANGE;
        if((i==3||i==4)&&((ranges[i].base&4095)||(ranges[i].bytes&4095)))return VF_BOOT_ERANGE;
        for(size_t j=0;j<i;j++)if(overlaps(ranges[i],ranges[j]))return VF_BOOT_EOVERLAP;
        result=owned_range(ranges[i],i==7?VF_BOOT_OWNED_FRAMEBUFFER:VF_BOOT_OWNED_RAM,owned,owned_count);if(result)return result;
    }
    if(h->rsdp_snapshot.bytes<20||h->rsdp_snapshot.bytes>4096||h->board_snapshot.bytes>1024*1024||
       h->config_blob.bytes>1024*1024||h->log_ring.bytes<64)return VF_BOOT_ERANGE;
    if(h->framebuffer.bytes) {
        if(!h->framebuffer_width||!h->framebuffer_height||h->framebuffer_format>1 ||
           h->framebuffer_pitch_bytes<((uint64_t)h->framebuffer_width*4) || (h->framebuffer_pitch_bytes&3) ||
           (uint64_t)h->framebuffer_pitch_bytes*h->framebuffer_height>h->framebuffer.bytes)return VF_BOOT_EFRAMEBUFFER;
    } else if(h->framebuffer.base||h->framebuffer_width||h->framebuffer_height||h->framebuffer_pitch_bytes||
              h->framebuffer_format||h->framebuffer_mode)return VF_BOOT_EFRAMEBUFFER;
    return VF_BOOT_OK;
}
