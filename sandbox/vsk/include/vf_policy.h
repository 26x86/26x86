/* SPDX-License-Identifier: BSD-4-Clause; repository LICENSE.txt applies.
 * Freestanding M0 policy. All tables/measurements and caller_cell arguments
 * come from trusted root state, never from payload owner_id claims. The caller
 * holds its root table lock from authorization through reference acquisition
 * or device submission. These helpers do not install EPT/IOMMU mappings.
 * Output objects must be private and disjoint from input tables/objects;
 * vf_decode_header alone supports input/output overlap through copy-in.
 */
#ifndef VF_POLICY_H
#define VF_POLICY_H
#include "vf_abi.h"

#define VF_POLICY_TABLE_MAX UINT32_C(4096)
#define VF_RIGHT_READ UINT32_C(1)
#define VF_RIGHT_WRITE UINT32_C(2)
#define VF_RIGHT_MAP UINT32_C(4)
#define VF_RIGHT_DMA UINT32_C(8)
#define VF_RIGHT_NOTIFY UINT32_C(16)
#define VF_RIGHT_DUP UINT32_C(32)
#define VF_RIGHT_REVOKE UINT32_C(64)
#define VF_RIGHT_RESET UINT32_C(128)
#define VF_RIGHT_ALL UINT32_C(255)
#define VF_OBJECT_GRANT UINT32_C(1)
#define VF_OBJECT_DEVICE UINT32_C(2)
#define VF_OBJECT_ENDPOINT UINT32_C(3)
#define VF_OBJECT_BLOCK UINT32_C(4)
#define VF_CAP_LIVE UINT32_C(1)
#define VF_CAP_REVOKED UINT32_C(2)

/* Internal root metadata, not wire ABI. Handles encode generation:slot, with
 * both halves nonzero. A slot is scoped to holder_cell. No generation wraps. */
struct vf_cap_entry {
    uint32_t slot, generation, holder_cell, object_type;
    uint32_t rights, state;
    uint64_t object_id, valid_from, expires_at;
};
uint64_t vf_make_handle(uint32_t slot, uint32_t generation);
vf_status vf_cap_lookup(const struct vf_cap_entry *table, uint32_t count,
    uint32_t caller_cell, uint64_t handle, uint32_t object_type,
    uint32_t rights, uint64_t now, const struct vf_cap_entry **out);
/* Produces metadata only; root reserves a fresh destination slot/generation
 * atomically. A duplicate grant capability MUST reference the same canonical
 * grant object/lifecycle; copying a lifecycle into an independent grant is
 * forbidden. Root must fan out revocation to all capability views under lock.
 * This M0 helper is not a global object-table/revocation implementation. */
vf_status vf_cap_dup_restricted(const struct vf_cap_entry *table, uint32_t count,
    uint32_t caller_cell, uint64_t handle, uint32_t target_cell,
    uint32_t new_slot, uint32_t new_generation, uint32_t rights,
    uint64_t expires_at, uint64_t now, struct vf_cap_entry *out);

#define VF_GRANT_LIVE UINT32_C(1)
#define VF_GRANT_REVOKING UINT32_C(2)
/* A locked root view of a canonical grant object plus the holder capability.
 * Refcounts, revocation state and acknowledgements belong to that shared object,
 * not to each capability independently. Refresh this view before each check. */
struct vf_grant_entry {
    struct vf_cap_entry cap;
    uint64_t bytes;
    uint32_t owner_cell, state, cpu_refs, dma_refs;
    uint8_t pages_pinned, dma_ever_mapped, device_drained;
    uint8_t ept_invalidated, iotlb_invalidated;
};
vf_status vf_validate_payload_grant(const struct vf_msg_header *header,
    const struct vf_grant_entry *table, uint32_t count, uint32_t caller_cell,
    uint32_t required_rights, uint64_t now, const struct vf_grant_entry **out);
vf_status vf_grant_begin_revoke(struct vf_grant_entry *grant,
                                uint32_t caller_cell);
/* Eligibility check only. Actual page unpin/reuse remains a root operation. */
vf_status vf_grant_reclaim_ready(const struct vf_grant_entry *grant);

#define VF_SERIAL_BYTES UINT32_C(256)
/* GUIDs here are normalized canonical UUID bytes, not raw mixed-endian GPT
 * fields. Discovery must validate real GPT CRCs/ranges/primary-backup agreement.
 * Serial is strict UTF-8 <=255 bytes plus NUL, with zero trailing padding. No
 * trimming; C0/DEL and leading/trailing Unicode whitespace are rejected. */
struct vf_partition_selector {
    uint8_t serial[VF_SERIAL_BYTES], disk_guid[16], partition_guid[16];
    uint32_t sector_bytes, read_only;
};
struct vf_partition_record {
    struct vf_partition_selector identity;
    uint64_t disk_blocks, usable_first_lba, usable_blocks;
    uint64_t first_lba, blocks, device_generation;
    uint8_t controller_approved, gpt_verified, online, fua_verified;
};
struct vf_block_binding {
    struct vf_partition_record partition;
    uint32_t read_only;
};
#define VF_BLOCK_FUA UINT32_C(1)
struct vf_block_request {
    uint16_t opcode;
    uint32_t sector_bytes, flags;
    uint64_t guest_lba, blocks;
};
struct vf_block_plan {
    uint16_t opcode;
    uint32_t flags;
    uint64_t physical_lba, blocks, bytes;
};
vf_status vf_bind_partition_exact(const struct vf_partition_selector *selector,
    const struct vf_partition_record *inventory, uint32_t count,
    struct vf_block_binding *out);
vf_status vf_plan_block_request(const struct vf_block_binding *binding,
    uint64_t current_device_generation, const struct vf_block_request *request,
    struct vf_block_plan *out);

/* CPUID/MSR snapshots are per logical CPU. *_managed flags attest to the root's
 * configured save/restore policy, not simply hardware CPUID support. */
#define VF_CODEGEN_SSE42 UINT32_C(1)
#define VF_CODEGEN_AVX UINT32_C(2)
#define VF_CODEGEN_AVX2 UINT32_C(3)
struct vf_cpu_capability {
    uint32_t logical_id, max_basic_leaf;
    uint32_t leaf1_ecx, leaf1_edx, leaf7_ebx, ext_80000001_edx;
    uint8_t intel_vendor, sse_state_managed, xstate_managed;
    uint64_t xcr0, xstate_save_mask;
};
struct vf_codegen_choice {
    uint32_t tier;
    uint64_t common_xstate;
};
vf_status vf_select_common_codegen(const struct vf_cpu_capability *cpus,
    uint32_t count, struct vf_codegen_choice *out);
/* SDM volume 3C appendix A: low MSR bits require 1, high bits permit 1.
 * Use TRUE control MSRs when IA32_VMX_BASIC[55] supports them. The caller
 * selects the correct control class and checks dependencies between classes. */
vf_status vf_vmx_combine_controls(const uint64_t *capability_msrs,
    uint32_t count, uint32_t required, uint32_t optional, uint32_t forbidden,
    uint32_t *out);
vf_status vf_vmx_validate_fixed_bits(uint64_t value, uint64_t fixed0,
                                     uint64_t fixed1);
#endif
