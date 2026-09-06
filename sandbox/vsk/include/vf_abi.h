/* SPDX-License-Identifier: BSD-4-Clause; repository LICENSE.txt applies.
 * VF-SPEC-001 v0.1 section 16. These are wire constants, not C enum values.
 * A known namespace/opcode does not imply an implemented operation.
 */
#ifndef VF_ABI_H
#define VF_ABI_H
#include <stdint.h>
#include <stddef.h>

#define VF_MSG_MAGIC UINT32_C(0x314d4656)
#define VF_ABI_MAJOR UINT16_C(1)
#define VF_MSG_BYTES UINT32_C(64)
#define VF_PAYLOAD_MAX UINT32_C(16777216)

/* Project-assigned family IDs; the source spec leaves their values open. */
#define VF_FAMILY_ROOT UINT16_C(1)
#define VF_FAMILY_BLOCK UINT16_C(2)
#define VF_FAMILY_SGPU UINT16_C(3)
#define VF_OP_CAP_DUP_RESTRICTED UINT16_C(1)
#define VF_OP_GRANT_CREATE UINT16_C(2)
#define VF_OP_GRANT_REVOKE UINT16_C(3)
#define VF_OP_CELL_NOTIFY UINT16_C(4)
#define VF_OP_DEVICE_MAP_MMIO UINT16_C(5)
#define VF_OP_DEVICE_DMA_MAP UINT16_C(6)
#define VF_OP_DEVICE_DMA_UNMAP UINT16_C(7)
#define VF_OP_DEVICE_IRQ_BIND UINT16_C(8)
#define VF_OP_DEVICE_QUIESCE_RESET UINT16_C(9)
#define VF_BLOCK_READ UINT16_C(1)
#define VF_BLOCK_WRITE UINT16_C(2)
#define VF_BLOCK_FLUSH UINT16_C(3)
#define VF_SGPU_QUERY_CAPS UINT16_C(1)
#define VF_SGPU_CREATE_RESOURCE UINT16_C(2)
#define VF_SGPU_DESTROY_RESOURCE UINT16_C(3)
#define VF_SGPU_CREATE_PIPELINE UINT16_C(4)
#define VF_SGPU_SUBMIT_COMMAND_LIST UINT16_C(5)
#define VF_SGPU_QUERY_OR_WAIT_TIMELINE UINT16_C(6)
#define VF_SGPU_PRESENT UINT16_C(7)

struct vf_msg_header {
    _Alignas(8) uint32_t magic;
    uint16_t abi_major;
    uint16_t header_bytes;
    uint32_t message_bytes;
    uint16_t family;
    uint16_t opcode;
    uint64_t request_id;
    uint64_t object;
    uint64_t payload_grant;
    uint64_t payload_offset;
    uint32_t payload_bytes;
    uint32_t flags;
    uint64_t reserved0;
};
_Static_assert(sizeof(struct vf_msg_header) == 64, "VF message size");
_Static_assert(_Alignof(struct vf_msg_header) == 8, "VF message alignment");
_Static_assert(offsetof(struct vf_msg_header, abi_major) == 4, "VF major offset");
_Static_assert(offsetof(struct vf_msg_header, header_bytes) == 6, "VF header offset");
_Static_assert(offsetof(struct vf_msg_header, message_bytes) == 8, "VF size offset");
_Static_assert(offsetof(struct vf_msg_header, family) == 12, "VF family offset");
_Static_assert(offsetof(struct vf_msg_header, opcode) == 14, "VF opcode offset");
_Static_assert(offsetof(struct vf_msg_header, request_id) == 16, "VF request offset");
_Static_assert(offsetof(struct vf_msg_header, object) == 24, "VF object offset");
_Static_assert(offsetof(struct vf_msg_header, payload_grant) == 32, "VF grant offset");
_Static_assert(offsetof(struct vf_msg_header, payload_offset) == 40, "VF range offset");
_Static_assert(offsetof(struct vf_msg_header, payload_bytes) == 48, "VF payload offset");
_Static_assert(offsetof(struct vf_msg_header, flags) == 52, "VF flags offset");
_Static_assert(offsetof(struct vf_msg_header, reserved0) == 56, "VF reserved offset");

typedef int32_t vf_status;
#define VF_OK ((vf_status)0)
#define VF_EINVAL ((vf_status)-1)
#define VF_EABI ((vf_status)-2)
#define VF_ENOTSUP ((vf_status)-3)
#define VF_ESTALE ((vf_status)-4)
#define VF_EPERM ((vf_status)-5)
#define VF_ERANGE ((vf_status)-6)
#define VF_EBUSY ((vf_status)-7)
#define VF_ENOENT ((vf_status)-8)
#define VF_EAMBIG ((vf_status)-9)
#define VF_ECPU ((vf_status)-10)
#define VF_EVMX ((vf_status)-11)
#define VF_EBINDING ((vf_status)-12)

/* Copy-in and little-endian decode, then shape validation. Never authenticates
 * a caller, capability, grant, payload contents, or boot permission. */
vf_status vf_decode_header(const uint8_t *bytes, uint32_t byte_count,
                           struct vf_msg_header *out);
vf_status vf_validate_header_shape(const struct vf_msg_header *header);
#endif
