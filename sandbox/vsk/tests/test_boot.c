/* SPDX-License-Identifier: BSD-4-Clause. Synthetic UNIT fixtures, never admission evidence. */
#include "vf_boot.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
#define CHECK(x) do {++checks;if(!(x)){fprintf(stderr,"test_boot:%d: %s\n",__LINE__,#x);exit(1);}}while(0)
static void put32(uint8_t *p,uint32_t v) {for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(v>>(i*8));}
static void put64(uint8_t *p,uint64_t v) {for(unsigned i=0;i<8;i++)p[i]=(uint8_t)(v>>(i*8));}
static void descriptor(uint8_t *p,uint32_t type,uint64_t base,uint64_t pages) {
    memset(p,0,48);put32(p,type);put64(p+8,base);put64(p+24,pages);put64(p+32,8);
}
static struct vf_boot_handoff fixture(void) {
    struct vf_boot_handoff h={0};h.handoff_version=1;h.struct_bytes=sizeof(h);
    h.descriptor_bytes=48;h.descriptor_version=1;h.memory_map_key=42;
    h.memory_map=(struct vf_boot_range){0x100000,144};
    h.rsdp_snapshot=(struct vf_boot_range){0x101000,36};
    h.board_snapshot=(struct vf_boot_range){0x102000,256};
    h.core_image=(struct vf_boot_range){0x104000,0x4000};
    h.service_bundle=(struct vf_boot_range){0x108000,0x2000};
    h.config_blob=(struct vf_boot_range){0x10a000,100};
    h.log_ring=(struct vf_boot_range){0x10b000,4096};
    h.framebuffer=(struct vf_boot_range){0x80000000,65536};
    h.framebuffer_width=64;h.framebuffer_height=64;h.framebuffer_pitch_bytes=256;
    h.config_sha256[0]=1;h.boot_disk_identifier[0]=2;return h;
}
int main(void) {
    struct vf_boot_state s;vf_boot_init(&s);CHECK(s.stage==VF_BOOT_EFI_ENTRY);
    CHECK(vf_boot_firmware_calls_allowed(&s));CHECK(!vf_boot_authorized(&s));
    CHECK(!vf_boot_advance(&s,VF_BOOT_LOAD_CONFIG_AND_SIGNED_BUNDLE));
    CHECK(vf_boot_advance(&s,VF_BOOT_VALIDATE_CONFIG_AND_PLATFORM_POLICY)==VF_BOOT_ESIGNATURE_VERIFIER_UNAVAILABLE);
    CHECK(s.stage==VF_BOOT_FAILED);CHECK(s.failed_stage==VF_BOOT_LOAD_CONFIG_AND_SIGNED_BUNDLE);
    CHECK(!vf_boot_firmware_calls_allowed(&s));CHECK(!vf_boot_authorized(&s));
    CHECK(vf_boot_advance(&s,VF_BOOT_SNAPSHOT_FIRMWARE_TABLES)==VF_BOOT_EFAILED);
    CHECK(vf_boot_fail(&s,VF_BOOT_EARG)==VF_BOOT_EFAILED);
    vf_boot_init(&s);CHECK(vf_boot_advance(&s,VF_BOOT_RUN_ARM64_GUEST)==VF_BOOT_EORDER);
    vf_boot_init(&s);CHECK(vf_boot_advance(&s,VF_BOOT_EFI_ENTRY)==VF_BOOT_EORDER);
    for(uint32_t i=0;i<VF_BOOT_STAGE_COUNT;i++) {
        CHECK(!vf_boot_expected_next(i,i));
        if(i+1<VF_BOOT_STAGE_COUNT)CHECK(vf_boot_expected_next(i,i+1));
        if(i+2<VF_BOOT_STAGE_COUNT)CHECK(!vf_boot_expected_next(i,i+2));
        /* Explicitly forged UNIT states can never authorize boot. */
        s=(struct vf_boot_state){i,0,0,1};CHECK(!vf_boot_authorized(&s));
        CHECK(!vf_boot_firmware_calls_allowed(&s));
    }
    CHECK(!vf_boot_expected_next(UINT32_MAX,0));CHECK(!vf_boot_authorized(NULL));
    vf_boot_init(&s);CHECK(vf_boot_record_ebs_result(&s,0)==VF_BOOT_EFIRMWARE_LIFETIME);
    s=(struct vf_boot_state){VF_BOOT_EXIT_BOOT_SERVICES,0,0,0};
    CHECK(vf_boot_firmware_calls_allowed(&s));CHECK(!vf_boot_record_ebs_result(&s,0));
    CHECK(!vf_boot_firmware_calls_allowed(&s));CHECK(!vf_boot_authorized(&s));
    CHECK(vf_boot_record_ebs_result(&s,0)==VF_BOOT_EFIRMWARE_LIFETIME);
    s=(struct vf_boot_state){VF_BOOT_EXIT_BOOT_SERVICES,0,0,0};
    CHECK(vf_boot_record_ebs_result(&s,UINT64_C(1)<<63)==VF_BOOT_EEBS_UNAVAILABLE);
    CHECK(!vf_boot_firmware_calls_allowed(&s));
    s=(struct vf_boot_state){VF_BOOT_ENABLE_VTD_AND_INTERRUPT_REMAP,0,0,1};
    CHECK(vf_boot_advance(&s,VF_BOOT_ENABLE_VMX_AND_CREATE_CELLS)==VF_BOOT_EVMX_EPT_UNAVAILABLE);

    uint8_t map[144], mutated[144];
    descriptor(map,2,0x100000,64);descriptor(map+48,11,0x80000000,16);descriptor(map+96,0,0,256);
    struct vf_boot_owned_extent owned[2]={{{0x100000,0x40000},VF_BOOT_OWNED_RAM,0},
                                          {{0x80000000,65536},VF_BOOT_OWNED_FRAMEBUFFER,0}};
    struct vf_boot_handoff h=fixture(), changed;
    CHECK(vf_boot_validate_memory_map(map,sizeof(map),48,1)==VF_BOOT_OK);
    CHECK(vf_boot_validate_handoff(&h,map,sizeof(map),owned,2)==VF_BOOT_OK);
    CHECK(vf_boot_validate_memory_map(map,sizeof(map),48,2)==VF_BOOT_EVERSION);
    CHECK(vf_boot_validate_memory_map(map,sizeof(map),39,1)==VF_BOOT_EMAP);
    CHECK(vf_boot_validate_memory_map(map,sizeof(map),44,1)==VF_BOOT_EMAP);
    CHECK(vf_boot_validate_memory_map(map,143,48,1)==VF_BOOT_EMAP);
    CHECK(vf_boot_validate_memory_map(map,0,48,1)==VF_BOOT_EMAP);
    CHECK(vf_boot_validate_memory_map(map,(VF_BOOT_MAX_DESCRIPTORS+1u)*48u,48,1)==VF_BOOT_EMAP);
    memcpy(mutated,map,sizeof(map));put64(mutated+24,0);
    CHECK(vf_boot_validate_memory_map(mutated,sizeof(mutated),48,1)==VF_BOOT_EMAP);
    memcpy(mutated,map,sizeof(map));put64(mutated+8,0x100001);
    CHECK(vf_boot_validate_memory_map(mutated,sizeof(mutated),48,1)==VF_BOOT_EMAP);
    memcpy(mutated,map,sizeof(map));put64(mutated+24,UINT64_MAX/4096+1);
    CHECK(vf_boot_validate_memory_map(mutated,sizeof(mutated),48,1)==VF_BOOT_EMAP);
    memcpy(mutated,map,sizeof(map));put64(mutated+8,UINT64_MAX-4095);put64(mutated+24,1);
    CHECK(vf_boot_validate_memory_map(mutated,sizeof(mutated),48,1)==VF_BOOT_EMAP);
    memcpy(mutated,map,sizeof(map));put64(mutated+48+8,0x100000);
    CHECK(vf_boot_validate_memory_map(mutated,sizeof(mutated),48,1)==VF_BOOT_EOVERLAP);
    memcpy(mutated,map,sizeof(map));put32(mutated,16);
    CHECK(vf_boot_validate_memory_map(mutated,sizeof(mutated),48,1)==VF_BOOT_EMAP);
    put32(mutated,0x70000000);
    CHECK(vf_boot_validate_memory_map(mutated,sizeof(mutated),48,1)==VF_BOOT_OK);
    CHECK(vf_boot_validate_handoff(&h,mutated,sizeof(mutated),owned,2)==VF_BOOT_EMEMORY_TYPE);
    const uint32_t denied[]={0,3,4,5,6,7,8,9,10,11,12,13,14,15};
    for(size_t i=0;i<sizeof(denied)/sizeof(denied[0]);i++) {
        memcpy(mutated,map,sizeof(map));put32(mutated,denied[i]);
        CHECK(vf_boot_validate_handoff(&h,mutated,sizeof(mutated),owned,2)==VF_BOOT_EMEMORY_TYPE);
    }
    memcpy(mutated,map,sizeof(map));put64(mutated+32,UINT64_C(1)<<63);
    CHECK(vf_boot_validate_handoff(&h,mutated,sizeof(mutated),owned,2)==VF_BOOT_EMEMORY_TYPE);
    changed=h;changed.struct_bytes--;
    CHECK(vf_boot_validate_handoff(&changed,map,sizeof(map),owned,2)==VF_BOOT_EVERSION);
    changed=h;changed.memory_map.bytes--;
    CHECK(vf_boot_validate_handoff(&changed,map,sizeof(map),owned,2)==VF_BOOT_EMAP);
    changed=h;changed.config_blob.base=0x200000;
    CHECK(vf_boot_validate_handoff(&changed,map,sizeof(map),owned,2)==VF_BOOT_EUNOWNED);
    changed=h;changed.config_blob.base=UINT64_MAX-7;changed.config_blob.bytes=16;
    CHECK(vf_boot_validate_handoff(&changed,map,sizeof(map),owned,2)==VF_BOOT_ERANGE);
    changed=h;changed.config_blob=h.rsdp_snapshot;
    CHECK(vf_boot_validate_handoff(&changed,map,sizeof(map),owned,2)==VF_BOOT_EOVERLAP);
    changed=h;changed.core_image.base++;
    CHECK(vf_boot_validate_handoff(&changed,map,sizeof(map),owned,2)==VF_BOOT_ERANGE);
    changed=h;changed.framebuffer_pitch_bytes=252;
    CHECK(vf_boot_validate_handoff(&changed,map,sizeof(map),owned,2)==VF_BOOT_EFRAMEBUFFER);
    changed=h;changed.framebuffer_height=UINT32_MAX;
    CHECK(vf_boot_validate_handoff(&changed,map,sizeof(map),owned,2)==VF_BOOT_EFRAMEBUFFER);
    changed=h;changed.framebuffer_format=3;
    CHECK(vf_boot_validate_handoff(&changed,map,sizeof(map),owned,2)==VF_BOOT_EFRAMEBUFFER);
    changed=h;changed.framebuffer.bytes=0;
    CHECK(vf_boot_validate_handoff(&changed,map,sizeof(map),owned,2)==VF_BOOT_EFRAMEBUFFER);
    changed=h;changed.framebuffer=(struct vf_boot_range){0,0};changed.framebuffer_width=0;
    changed.framebuffer_height=0;changed.framebuffer_pitch_bytes=0;
    CHECK(vf_boot_validate_handoff(&changed,map,sizeof(map),owned,2)==VF_BOOT_OK);
    owned[1].range.base=0x100000;
    CHECK(vf_boot_validate_handoff(&h,map,sizeof(map),owned,2)==VF_BOOT_EOVERLAP);
    owned[1].range.base=0x80000000;owned[0].range.bytes+=4096;
    CHECK(vf_boot_validate_handoff(&h,map,sizeof(map),owned,2)==VF_BOOT_EMAP);
    owned[0].range.bytes-=4096;owned[0].reserved=1;
    CHECK(vf_boot_validate_handoff(&h,map,sizeof(map),owned,2)==VF_BOOT_ERANGE);
    printf("{\"test\":\"boot\",\"level\":\"UNIT\",\"passed\":true,\"checks\":%u,\"hardware_verified\":false}\n",checks);
    return 0;
}
