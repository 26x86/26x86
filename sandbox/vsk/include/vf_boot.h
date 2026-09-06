/* SPDX-License-Identifier: BSD-4-Clause; repository LICENSE.txt applies. */
#ifndef VSK_VF_BOOT_H
#define VSK_VF_BOOT_H
#include <stddef.h>
#include <stdint.h>

/* VF-SPEC-001 section 4. Values describe the stage being entered. */
enum vf_boot_stage {
    VF_BOOT_EFI_ENTRY=0, VF_BOOT_LOAD_CONFIG_AND_SIGNED_BUNDLE,
    VF_BOOT_VALIDATE_CONFIG_AND_PLATFORM_POLICY, VF_BOOT_SNAPSHOT_FIRMWARE_TABLES,
    VF_BOOT_EXIT_BOOT_SERVICES, VF_BOOT_ROOT_MEMORY_AND_CPU_INIT,
    VF_BOOT_QUIESCE_AND_QUARANTINE_DEVICES, VF_BOOT_ENABLE_VTD_AND_INTERRUPT_REMAP,
    VF_BOOT_ENABLE_VMX_AND_CREATE_CELLS, VF_BOOT_START_APPROVED_DRIVERS,
    VF_BOOT_RESOLVE_AND_FREEZE_MACHINE, VF_BOOT_VALIDATE_EXACT_GUEST_PROFILE,
    VF_BOOT_RUN_ARM64_GUEST, VF_BOOT_STAGE_COUNT, VF_BOOT_FAILED=255
};
enum vf_boot_error {
    VF_BOOT_OK=0, VF_BOOT_EARG=-1, VF_BOOT_EVERSION=-2, VF_BOOT_ERANGE=-3,
    VF_BOOT_EOVERLAP=-4, VF_BOOT_EMEMORY_TYPE=-5, VF_BOOT_EUNOWNED=-6,
    VF_BOOT_EMAP=-7, VF_BOOT_EFRAMEBUFFER=-8, VF_BOOT_EORDER=-9,
    VF_BOOT_EFAILED=-10, VF_BOOT_EFIRMWARE_LIFETIME=-11,
    VF_BOOT_ESIGNATURE_VERIFIER_UNAVAILABLE=-12, VF_BOOT_EPLATFORM_MEASUREMENT_UNAVAILABLE=-13,
    VF_BOOT_EFIRMWARE_SNAPSHOT_UNAVAILABLE=-14, VF_BOOT_EEBS_UNAVAILABLE=-15,
    VF_BOOT_EROOT_INIT_UNAVAILABLE=-16, VF_BOOT_EQUARANTINE_UNAVAILABLE=-17,
    VF_BOOT_EVTD_IR_UNAVAILABLE=-18, VF_BOOT_EVMX_EPT_UNAVAILABLE=-19,
    VF_BOOT_EDRIVER_VERIFICATION_UNAVAILABLE=-20, VF_BOOT_EMACHINE_FREEZE_UNAVAILABLE=-21,
    VF_BOOT_EGUEST_PROFILE_VERIFIER_UNAVAILABLE=-22, VF_BOOT_EGUEST_RUNTIME_UNAVAILABLE=-23
};
struct vf_boot_state {
    uint32_t stage, failed_stage;
    int32_t error;
    uint32_t ebs_exited;
};
void vf_boot_init(struct vf_boot_state *);
int vf_boot_expected_next(uint32_t current, uint32_t next);
int vf_boot_advance(struct vf_boot_state *, uint32_t next);
int vf_boot_fail(struct vf_boot_state *, int error);
/* Records the result of a real EBS call by the trusted EFI adapter. It makes no
 * call itself, and a supplied success value is NOT hardware/boot evidence. */
int vf_boot_record_ebs_result(struct vf_boot_state *, uint64_t efi_status);
int vf_boot_firmware_calls_allowed(const struct vf_boot_state *);
int vf_boot_authorized(const struct vf_boot_state *); /* Always false in M0. */

#define VF_BOOT_HANDOFF_VERSION 1u
#define VF_BOOT_MAX_DESCRIPTORS 4096u
#define VF_BOOT_MAX_OWNED_EXTENTS 64u
#define VF_BOOT_EFI_DESCRIPTOR_VERSION 1u
#define VF_BOOT_PAGE_BYTES UINT64_C(4096)
struct vf_boot_range { uint64_t base, bytes; };
enum vf_boot_owner_kind { VF_BOOT_OWNED_RAM=1, VF_BOOT_OWNED_FRAMEBUFFER=2 };
/* Trusted allocation/resource ledger input, never a config.plist declaration.
 * This validator checks consistency; it does not prove the ledger's provenance. */
struct vf_boot_owned_extent {
    struct vf_boot_range range;
    uint32_t kind, reserved;
};
struct vf_boot_handoff {
    uint32_t handoff_version, struct_bytes;
    uint32_t descriptor_bytes, descriptor_version;
    uint64_t memory_map_key;
    struct vf_boot_range memory_map, rsdp_snapshot, board_snapshot;
    struct vf_boot_range core_image, service_bundle, config_blob, log_ring;
    struct vf_boot_range framebuffer;
    uint32_t framebuffer_width, framebuffer_height, framebuffer_pitch_bytes;
    uint32_t framebuffer_format, framebuffer_mode, reserved0;
    uint8_t config_sha256[32], boot_disk_identifier[32];
};
_Static_assert(sizeof(struct vf_boot_range)==16,"range wire size");
_Static_assert(sizeof(struct vf_boot_owned_extent)==24,"ownership record size");
_Static_assert(offsetof(struct vf_boot_handoff,memory_map)==24,"handoff ranges offset");
_Static_assert(offsetof(struct vf_boot_handoff,config_sha256)==176,"handoff hash offset");
_Static_assert(sizeof(struct vf_boot_handoff)==240,"handoff v1 wire size");
/* Descriptor byte layout is EFI_MEMORY_DESCRIPTOR v1, with its supplied stride
 * (40..256, multiple of 8). No casts or dereferences of physical addresses. */
int vf_boot_validate_memory_map(const void *bytes, size_t length,
                                uint32_t descriptor_bytes, uint32_t version);
/* map_bytes is an already bounded caller-owned snapshot of h->memory_map.
 * All snapshots stay pinned until a future root ownership transfer completes.
 * Successful return proves shape/range/ledger consistency only; no signature,
 * hardware measurement, framebuffer preservation, DMA isolation or boot grant. */
int vf_boot_validate_handoff(const struct vf_boot_handoff *h,
                              const void *map_bytes, size_t map_length,
                              const struct vf_boot_owned_extent *owned, size_t owned_count);
#endif
