/* SPDX-License-Identifier: BSD-4-Clause; repository LICENSE.txt applies.
 * Host UNIT tests with synthetic root tables. No actual CPU/DMA/device access.
 */
#include "vf_policy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned checks;
#define CHECK(x) do { ++checks; if (!(x)) { \
    fprintf(stderr, "policy check failed at line %d: %s\n", __LINE__, #x); \
    exit(1); } } while (0)
static struct vf_msg_header header(void) {
    struct vf_msg_header h = {0};
    h.magic = VF_MSG_MAGIC; h.abi_major = 1; h.header_bytes = 64;
    h.message_bytes = 64; h.family = VF_FAMILY_ROOT;
    h.opcode = VF_OP_GRANT_CREATE; h.request_id = UINT64_C(0x123456789abcdef0);
    return h;
}
static void put(uint8_t *p, uint64_t value, unsigned bytes) {
    for (unsigned i = 0; i < bytes; ++i) p[i] = (uint8_t)(value >> (8u * i));
}
static void test_header(void) {
    struct vf_msg_header h = header(), copy, bad;
    uint8_t raw[66] = {0}, *p = raw + 1;
    CHECK(vf_validate_header_shape(&h) == VF_OK);
    put(p, VF_MSG_MAGIC, 4); put(p + 4, 1, 2); put(p + 6, 64, 2);
    put(p + 8, 64, 4); put(p + 12, VF_FAMILY_ROOT, 2);
    put(p + 14, VF_OP_GRANT_CREATE, 2); put(p + 16, h.request_id, 8);
    CHECK(vf_decode_header(p, 64, &copy) == VF_OK);
    CHECK(copy.request_id == h.request_id && copy.object == 0 && copy.reserved0 == 0);
    for (uint32_t n = 0; n < 80; ++n) if (n != 64) {
        memset(&copy, 0xff, sizeof(copy));
        CHECK(vf_decode_header(p, n, &copy) == VF_EABI);
        CHECK(copy.magic == 0 && copy.payload_grant == 0);
    }
    CHECK(vf_decode_header(NULL, 64, &copy) != VF_OK);
    CHECK(vf_decode_header(p, 64, NULL) != VF_OK);
    for (unsigned bit = 0; bit < 32; ++bit) {
        bad = h; bad.magic ^= UINT32_C(1) << bit;
        CHECK(vf_validate_header_shape(&bad) == VF_EABI);
        bad = h; bad.flags = UINT32_C(1) << bit;
        CHECK(vf_validate_header_shape(&bad) != VF_OK);
    }
    for (unsigned bit = 0; bit < 64; ++bit) {
        bad = h; bad.reserved0 = UINT64_C(1) << bit;
        CHECK(vf_validate_header_shape(&bad) == VF_EABI);
    }
    bad = h; bad.abi_major = 2; CHECK(vf_validate_header_shape(&bad) == VF_EABI);
    bad = h; bad.header_bytes = 72; CHECK(vf_validate_header_shape(&bad) == VF_EABI);
    bad = h; bad.message_bytes = 65; CHECK(vf_validate_header_shape(&bad) == VF_EABI);
    bad = h; bad.family = 99; CHECK(vf_validate_header_shape(&bad) == VF_ENOTSUP);
    bad = h; bad.opcode = 0; CHECK(vf_validate_header_shape(&bad) == VF_ENOTSUP);
    bad = h; bad.opcode = 10; CHECK(vf_validate_header_shape(&bad) == VF_ENOTSUP);
    bad = h; bad.payload_offset = 8; CHECK(vf_validate_header_shape(&bad) != VF_OK);
    bad = h; bad.payload_grant = 1; CHECK(vf_validate_header_shape(&bad) != VF_OK);
    h.payload_grant = vf_make_handle(1, 1); h.payload_bytes = 8;
    CHECK(vf_validate_header_shape(&h) == VF_OK);
    for (uint64_t offset = 1; offset < 8; ++offset) {
        bad = h; bad.payload_offset = offset;
        CHECK(vf_validate_header_shape(&bad) != VF_OK);
    }
    bad = h; bad.payload_bytes = VF_PAYLOAD_MAX;
    CHECK(vf_validate_header_shape(&bad) == VF_OK);
    ++bad.payload_bytes; CHECK(vf_validate_header_shape(&bad) == VF_ERANGE);
    bad = h; bad.payload_offset = UINT64_MAX - 7;
    CHECK(vf_validate_header_shape(&bad) == VF_ERANGE);
    --bad.payload_bytes; CHECK(vf_validate_header_shape(&bad) == VF_OK);
    /* In-place decode is safe after copy-in; no raw unaligned struct cast. */
    memcpy(&copy, p, 64);
    CHECK(vf_decode_header((const uint8_t *)&copy, 64, &copy) == VF_OK);
}
static struct vf_cap_entry cap(void) {
    struct vf_cap_entry c = {0};
    c.slot = 4; c.generation = 7; c.holder_cell = 2; c.object_type = VF_OBJECT_GRANT;
    c.rights = VF_RIGHT_READ | VF_RIGHT_WRITE | VF_RIGHT_DUP;
    c.state = VF_CAP_LIVE; c.object_id = 99; c.valid_from = 10; c.expires_at = 20;
    return c;
}
static void test_caps_grants(void) {
    struct vf_cap_entry table[2] = {cap(), cap()}, clone;
    struct vf_grant_entry grants[2] = {0};
    const struct vf_cap_entry *found;
    const struct vf_grant_entry *grant_found;
    struct vf_msg_header h = header();
    uint64_t handle = vf_make_handle(4, 7);
    CHECK(vf_make_handle(0, 1) == 0 && vf_make_handle(1, 0) == 0);
    CHECK(vf_cap_lookup(table, 1, 2, handle, VF_OBJECT_GRANT, VF_RIGHT_READ, 10, &found) == VF_OK);
    CHECK(found == &table[0]);
    CHECK(vf_cap_lookup(table, 1, 3, handle, VF_OBJECT_GRANT, VF_RIGHT_READ, 10, &found) == VF_ESTALE);
    CHECK(found == NULL);
    CHECK(vf_cap_lookup(table, 1, 2, vf_make_handle(4, 6), VF_OBJECT_GRANT, 1, 10, &found) == VF_ESTALE);
    CHECK(vf_cap_lookup(table, 1, 2, UINT64_C(4), VF_OBJECT_GRANT, 1, 10, &found) == VF_ESTALE);
    CHECK(vf_cap_lookup(table, 1, 2, handle, VF_OBJECT_DEVICE, 1, 10, &found) == VF_EPERM);
    CHECK(vf_cap_lookup(table, 1, 2, handle, VF_OBJECT_GRANT, VF_RIGHT_DMA, 10, &found) == VF_EPERM);
    CHECK(vf_cap_lookup(table, 1, 2, handle, VF_OBJECT_GRANT, 1, 9, &found) == VF_ESTALE);
    CHECK(vf_cap_lookup(table, 1, 2, handle, VF_OBJECT_GRANT, 1, 20, &found) == VF_ESTALE);
    CHECK(vf_cap_lookup(table, 2, 2, handle, VF_OBJECT_GRANT, 1, 10, &found) == VF_EAMBIG);
    CHECK(vf_cap_lookup(table, 1, 2, handle, VF_OBJECT_GRANT, 256, 10, &found) == VF_EINVAL);
    CHECK(vf_cap_dup_restricted(table, 1, 2, handle, 3, 5, 8, VF_RIGHT_READ, 19, 11, &clone) == VF_OK);
    CHECK(clone.object_id == 99 && clone.rights == VF_RIGHT_READ && clone.holder_cell == 3);
    CHECK(clone.expires_at == 19 && clone.valid_from == 11 && clone.generation == 8);
    CHECK(vf_cap_dup_restricted(table, 1, 2, handle, 3, 5, 8, VF_RIGHT_DMA, 19, 11, &clone) == VF_EPERM);
    CHECK(clone.object_id == 0);
    CHECK(vf_cap_dup_restricted(table, 1, 2, handle, 3, 5, 8, VF_RIGHT_READ, 21, 11, &clone) == VF_EPERM);
    CHECK(vf_cap_dup_restricted(table, 1, 2, handle, 2, 4, 8, 1, 19, 11, &clone) == VF_EAMBIG);
    CHECK(vf_cap_dup_restricted(table, 1, 2, handle, 3, 5, 8, 1, 19, 11, &table[0]) == VF_EINVAL);
    CHECK(table[0].object_id == 99);
    table[0].rights &= ~VF_RIGHT_DUP;
    CHECK(vf_cap_dup_restricted(table, 1, 2, handle, 3, 5, 8, 1, 19, 11, &clone) == VF_EPERM);
    grants[0].cap = cap(); grants[0].owner_cell = 8; grants[0].state = VF_GRANT_LIVE;
    grants[0].bytes = 64; h.payload_grant = handle; h.payload_bytes = 8;
    /* Shape success cannot stand in for the following failed authority checks. */
    CHECK(vf_validate_header_shape(&h) == VF_OK);
    CHECK(vf_validate_payload_grant(&h, grants, 1, 2, VF_RIGHT_READ, 11, &grant_found) == VF_OK);
    CHECK(grant_found == &grants[0]);
    CHECK(vf_validate_payload_grant(&h, grants, 1, 8, VF_RIGHT_READ, 11, &grant_found) == VF_ESTALE);
    CHECK(vf_validate_payload_grant(&h, grants, 1, 2, VF_RIGHT_READ, 20, &grant_found) == VF_ESTALE);
    h.payload_offset = 56;
    CHECK(vf_validate_payload_grant(&h, grants, 1, 2, VF_RIGHT_WRITE, 11, &grant_found) == VF_OK);
    h.payload_bytes = 9;
    CHECK(vf_validate_payload_grant(&h, grants, 1, 2, VF_RIGHT_READ, 11, &grant_found) == VF_ERANGE);
    h.payload_bytes = 8; grants[0].cap.rights = VF_RIGHT_READ;
    CHECK(vf_validate_payload_grant(&h, grants, 1, 2, VF_RIGHT_WRITE, 11, &grant_found) == VF_EPERM);
    grants[1] = grants[0];
    CHECK(vf_validate_payload_grant(&h, grants, 2, 2, VF_RIGHT_READ, 11, &grant_found) == VF_EAMBIG);
    grants[0].cpu_refs = 1; grants[0].dma_refs = 1;
    grants[0].pages_pinned = grants[0].dma_ever_mapped = 1;
    grants[0].device_drained = grants[0].ept_invalidated = grants[0].iotlb_invalidated = 1;
    CHECK(vf_grant_begin_revoke(&grants[0], 2) == VF_EPERM);
    CHECK(vf_grant_begin_revoke(&grants[0], 8) == VF_OK);
    CHECK(grants[0].ept_invalidated == 0 && grants[0].device_drained == 0 && grants[0].iotlb_invalidated == 0);
    CHECK(vf_validate_payload_grant(&h, grants, 1, 2, VF_RIGHT_READ, 11, &grant_found) == VF_ESTALE);
    CHECK(vf_grant_reclaim_ready(&grants[0]) == VF_EBUSY);
    grants[0].cpu_refs = grants[0].dma_refs = 0;
    grants[0].ept_invalidated = grants[0].iotlb_invalidated = 1;
    CHECK(vf_grant_reclaim_ready(&grants[0]) == VF_EBUSY);
    grants[0].device_drained = 1;
    CHECK(vf_grant_reclaim_ready(&grants[0]) == VF_OK);
    grants[0].pages_pinned = 0;
    CHECK(vf_grant_reclaim_ready(&grants[0]) == VF_EBUSY);
    grants[0].pages_pinned = 1; grants[0].dma_refs = UINT32_MAX;
    CHECK(vf_grant_reclaim_ready(&grants[0]) == VF_EBUSY);
    CHECK(vf_grant_begin_revoke(&grants[0], 8) == VF_ESTALE);
}
static struct vf_partition_record partition(void) {
    struct vf_partition_record p = {0};
    memcpy(p.identity.serial, "SYNTHETIC", 9);
    p.identity.disk_guid[0] = 1; p.identity.partition_guid[0] = 2;
    p.identity.sector_bytes = 512;
    p.disk_blocks = 1000; p.usable_first_lba = 34; p.usable_blocks = 933;
    p.first_lba = 64; p.blocks = 8; p.device_generation = 7;
    p.controller_approved = p.gpt_verified = p.online = 1;
    return p;
}
static void test_block(void) {
    struct vf_partition_record records[2] = {partition(), partition()};
    struct vf_partition_selector selector = records[0].identity, wrong;
    struct vf_block_binding binding;
    struct vf_block_plan plan;
    struct vf_block_request r = {0};
    CHECK(vf_bind_partition_exact(&selector, records, 1, &binding) == VF_OK);
    CHECK(binding.partition.first_lba == 64 && binding.partition.blocks == 8);
    CHECK(vf_bind_partition_exact(&selector, records, 0, &binding) == VF_ENOENT);
    records[1].controller_approved = 0;
    CHECK(vf_bind_partition_exact(&selector, records, 2, &binding) == VF_EAMBIG);
    CHECK(binding.partition.blocks == 0);
    for (unsigned field = 0; field < 4; ++field) {
        wrong = selector;
        if (field == 0) wrong.serial[0] = 'X';
        if (field == 1) wrong.disk_guid[0] = 9;
        if (field == 2) wrong.partition_guid[0] = 9;
        if (field == 3) wrong.sector_bytes = 4096;
        CHECK(vf_bind_partition_exact(&wrong, records, 1, &binding) == VF_ENOENT);
    }
    records[0].gpt_verified = 0;
    CHECK(vf_bind_partition_exact(&selector, records, 1, &binding) == VF_EBINDING);
    records[0] = partition(); records[0].first_lba = 33;
    CHECK(vf_bind_partition_exact(&selector, records, 1, &binding) == VF_ERANGE);
    records[0] = partition(); records[0].blocks = UINT64_MAX;
    CHECK(vf_bind_partition_exact(&selector, records, 1, &binding) == VF_ERANGE);
    records[0] = partition();
    CHECK(vf_bind_partition_exact(&selector, records, 1, &binding) == VF_OK);
    r.opcode = VF_BLOCK_READ; r.sector_bytes = 512;
    for (uint64_t lba = 0; lba < 11; ++lba) for (uint64_t n = 0; n < 11; ++n) {
        r.guest_lba = lba; r.blocks = n;
        if (n != 0 && lba < 8 && lba + n <= 8) {
            CHECK(vf_plan_block_request(&binding, 7, &r, &plan) == VF_OK);
            CHECK(plan.physical_lba >= 64 && plan.physical_lba + n <= 72);
            CHECK(plan.bytes == 512 * n);
        } else {
            CHECK(vf_plan_block_request(&binding, 7, &r, &plan) == VF_ERANGE);
            CHECK(plan.physical_lba == 0 && plan.bytes == 0);
        }
    }
    r.guest_lba = UINT64_MAX; r.blocks = 1;
    CHECK(vf_plan_block_request(&binding, 7, &r, &plan) == VF_ERANGE);
    r.guest_lba = 0; r.blocks = UINT64_MAX;
    CHECK(vf_plan_block_request(&binding, 7, &r, &plan) == VF_ERANGE);
    r.blocks = 1;
    CHECK(vf_plan_block_request(&binding, 8, &r, &plan) == VF_ESTALE);
    r.sector_bytes = 4096;
    CHECK(vf_plan_block_request(&binding, 7, &r, &plan) == VF_EBINDING);
    r.sector_bytes = 512; r.opcode = 4;
    CHECK(vf_plan_block_request(&binding, 7, &r, &plan) == VF_ENOTSUP);
    r.opcode = VF_BLOCK_WRITE; binding.read_only = 1;
    CHECK(vf_plan_block_request(&binding, 7, &r, &plan) == VF_EPERM);
    binding.read_only = 0; binding.partition.identity.read_only = 1;
    CHECK(vf_plan_block_request(&binding, 7, &r, &plan) == VF_EPERM);
    binding.partition.identity.read_only = 0; r.flags = VF_BLOCK_FUA;
    CHECK(vf_plan_block_request(&binding, 7, &r, &plan) == VF_ENOTSUP);
    binding.partition.fua_verified = 1;
    CHECK(vf_plan_block_request(&binding, 7, &r, &plan) == VF_OK);
    r.opcode = VF_BLOCK_READ;
    CHECK(vf_plan_block_request(&binding, 7, &r, &plan) == VF_ENOTSUP);
    r.opcode = VF_BLOCK_FLUSH; r.flags = 0; r.blocks = 0;
    binding.read_only = 1;
    CHECK(vf_plan_block_request(&binding, 7, &r, &plan) == VF_OK);
    CHECK(plan.opcode == VF_BLOCK_FLUSH && plan.blocks == 0 && plan.bytes == 0);
    r.blocks = 1; CHECK(vf_plan_block_request(&binding, 7, &r, &plan) == VF_EINVAL);
    /* A valid enormous partition still cannot produce a wrapped byte count. */
    records[0] = partition(); records[0].disk_blocks = UINT64_MAX;
    records[0].usable_blocks = UINT64_MAX - 34;
    records[0].blocks = UINT64_MAX - 64;
    CHECK(vf_bind_partition_exact(&selector, records, 1, &binding) == VF_OK);
    r.opcode = VF_BLOCK_READ; r.blocks = UINT64_MAX / 512 + 1;
    CHECK(vf_plan_block_request(&binding, 7, &r, &plan) == VF_ERANGE);
}
static void test_serial(void) {
    struct vf_partition_record p = partition();
    struct vf_partition_selector s;
    struct vf_block_binding b;
    const uint8_t invalid[][5] = {
        {0xc0,0xaf,0}, {0xe0,0x80,0xaf,0}, {0xed,0xa0,0x80,0},
        {0xf4,0x90,0x80,0x80,0}, {0x80,0}, {0xe2,0x82,0},
        {' ', 'a',0}, {'a',' ',0}, {'a',0x7f,0}, {'a',0x1f,0},
        {0xc2,0x85,'a',0}, {'a',0xe3,0x80,0x80,0}
    };
    for (unsigned i = 0; i < sizeof(invalid)/sizeof(invalid[0]); ++i) {
        s = p.identity; memset(s.serial, 0, sizeof(s.serial));
        memcpy(s.serial, invalid[i], sizeof(invalid[i]));
        CHECK(vf_bind_partition_exact(&s, &p, 1, &b) == VF_EINVAL);
    }
    memset(p.identity.serial, 0, sizeof(p.identity.serial));
    for (unsigned i = 0; i < 85; ++i) {
        p.identity.serial[3*i] = 0xed; p.identity.serial[3*i+1] = 0x95;
        p.identity.serial[3*i+2] = 0x9c; /* U+D55C, 255 total bytes. */
    }
    s = p.identity;
    CHECK(vf_bind_partition_exact(&s, &p, 1, &b) == VF_OK);
    p.identity.serial[255] = 'x'; s = p.identity;
    CHECK(vf_bind_partition_exact(&s, &p, 1, &b) == VF_EINVAL);
    memset(p.identity.serial, 0, sizeof(p.identity.serial));
    memcpy(p.identity.serial, "a\302\240b", 4); s = p.identity;
    CHECK(vf_bind_partition_exact(&s, &p, 1, &b) == VF_OK); /* Interior NBSP. */
}
static struct vf_cpu_capability cpu(uint32_t id) {
    struct vf_cpu_capability c = {0};
    c.logical_id = id; c.max_basic_leaf = 7;
    c.intel_vendor = c.sse_state_managed = c.xstate_managed = 1;
    c.leaf1_ecx = (1u << 20) | (1u << 26) | (1u << 27) | (1u << 28);
    c.leaf1_edx = (1u << 24) | (1u << 25) | (1u << 26);
    c.leaf7_ebx = 1u << 5; c.ext_80000001_edx = (1u << 20) | (1u << 29);
    c.xcr0 = c.xstate_save_mask = 7;
    return c;
}
static void test_cpu(void) {
    struct vf_cpu_capability c[2] = {cpu(0), cpu(1)};
    struct vf_codegen_choice choice;
    CHECK(vf_select_common_codegen(c, 2, &choice) == VF_OK && choice.tier == VF_CODEGEN_AVX2);
    c[1].leaf7_ebx = 0;
    CHECK(vf_select_common_codegen(c, 2, &choice) == VF_OK && choice.tier == VF_CODEGEN_AVX);
    for (unsigned bit = 26; bit <= 28; ++bit) {
        c[1] = cpu(1); c[1].leaf1_ecx &= ~(1u << bit);
        CHECK(vf_select_common_codegen(c, 2, &choice) == VF_OK && choice.tier == VF_CODEGEN_SSE42);
    }
    for (unsigned bit = 0; bit < 3; ++bit) {
        c[1] = cpu(1); c[1].xcr0 &= ~(UINT64_C(1) << bit);
        CHECK(vf_select_common_codegen(c, 2, &choice) == VF_OK && choice.tier == VF_CODEGEN_SSE42);
    }
    c[1] = cpu(1); c[1].xstate_save_mask = 3;
    CHECK(vf_select_common_codegen(c, 2, &choice) == VF_OK && choice.tier == VF_CODEGEN_SSE42);
    c[1] = cpu(1); c[1].xstate_managed = 0;
    CHECK(vf_select_common_codegen(c, 2, &choice) == VF_OK && choice.tier == VF_CODEGEN_SSE42);
    c[1] = cpu(1); c[1].max_basic_leaf = 1;
    CHECK(vf_select_common_codegen(c, 2, &choice) == VF_OK && choice.tier == VF_CODEGEN_AVX);
    c[1] = cpu(1); c[1].leaf1_ecx &= ~(1u << 20);
    CHECK(vf_select_common_codegen(c, 2, &choice) == VF_ECPU && choice.tier == 0);
    c[1] = cpu(1); c[1].intel_vendor = 0;
    CHECK(vf_select_common_codegen(c, 2, &choice) == VF_ECPU);
    c[1] = cpu(1); c[1].sse_state_managed = 0;
    CHECK(vf_select_common_codegen(c, 2, &choice) == VF_ECPU);
    c[1] = cpu(0);
    CHECK(vf_select_common_codegen(c, 2, &choice) == VF_EINVAL);
    CHECK(vf_select_common_codegen(c, 0, &choice) == VF_EINVAL);
    /* Extra XSTATE components may be managed, but never advertised as codegen. */
    c[0] = cpu(0); c[1] = cpu(1);
    c[0].xcr0 = c[1].xcr0 = c[0].xstate_save_mask = c[1].xstate_save_mask = UINT64_MAX;
    CHECK(vf_select_common_codegen(c, 2, &choice) == VF_OK && choice.common_xstate == 7);
}
static void test_vmx(void) {
    uint64_t msrs[2]; uint32_t result;
    /* Each selected bit: 0=must zero, 1=either, 2=must one. Exhaust all pairs
     * and desired/optional/forbidden decisions; check a truth-table oracle. */
    for (unsigned bit = 0; bit < 32; ++bit) {
        uint32_t mask = UINT32_C(1) << bit;
        for (unsigned a = 0; a < 3; ++a) for (unsigned b = 0; b < 3; ++b) {
            msrs[0] = ((uint64_t)(a == 0 ? UINT32_MAX & ~mask : UINT32_MAX) << 32) | (a == 2 ? mask : 0);
            msrs[1] = ((uint64_t)(b == 0 ? UINT32_MAX & ~mask : UINT32_MAX) << 32) | (b == 2 ? mask : 0);
            for (unsigned policy = 0; policy < 4; ++policy) {
                uint32_t required = policy == 1 ? mask : 0;
                uint32_t optional = policy == 2 ? mask : 0;
                uint32_t forbidden = policy == 3 ? mask : 0;
                int valid_zero = a != 2 && b != 2 && policy != 1;
                int valid_one = a != 0 && b != 0 && policy != 3;
                vf_status status = vf_vmx_combine_controls(msrs, 2, required, optional, forbidden, &result);
                CHECK((status == VF_OK) == (valid_zero || valid_one));
                if (status == VF_OK) {
                    CHECK((result & mask) != 0 ? valid_one : valid_zero);
                    CHECK((result & ~mask) == 0);
                    if (policy == 2 && valid_one) CHECK((result & mask) != 0);
                } else CHECK(result == 0);
            }
        }
    }
    msrs[0] = 1; CHECK(vf_vmx_combine_controls(msrs, 1, 0, 0, 0, &result) == VF_EVMX);
    msrs[0] = UINT64_MAX;
    CHECK(vf_vmx_combine_controls(msrs, 1, 1, 0, 1, &result) == VF_EINVAL);
    CHECK(vf_vmx_combine_controls(msrs, 0, 0, 0, 0, &result) == VF_EINVAL);
    CHECK(vf_vmx_validate_fixed_bits(5, 1, 7) == VF_OK);
    CHECK(vf_vmx_validate_fixed_bits(4, 1, 7) == VF_EVMX);
    CHECK(vf_vmx_validate_fixed_bits(9, 1, 7) == VF_EVMX);
    CHECK(vf_vmx_validate_fixed_bits(1, 1, 0) == VF_EVMX);
}
int main(void) {
    test_header(); test_caps_grants(); test_block(); test_serial(); test_cpu(); test_vmx();
    printf("{\"test\":\"vsk-policy\",\"level\":\"UNIT\",\"passed\":true,\"checks\":%u,\"hardware_verified\":false}\n", checks);
    return 0;
}
