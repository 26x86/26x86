/* SPDX-License-Identifier: BSD-4-Clause; repository LICENSE.txt applies.
 * M0 policy checks only. No hardware register access or security fallback.
 */
#include "vf_policy.h"

static void vf_clear(void *output, uint32_t bytes) {
    volatile uint8_t *p = (volatile uint8_t *)output;
    while (bytes != 0) { *p++ = 0; --bytes; }
}
static void vf_copy(void *output, const void *input, uint32_t bytes) {
    volatile uint8_t *dst = (volatile uint8_t *)output;
    const volatile uint8_t *src = (const volatile uint8_t *)input;
    while (bytes != 0) { *dst++ = *src++; --bytes; }
}
static uint16_t vf_le16(const uint8_t *p) {
    return (uint16_t)((uint16_t)p[0] | (uint16_t)((uint16_t)p[1] << 8));
}
static uint32_t vf_le32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static uint64_t vf_le64(const uint8_t *p) {
    return (uint64_t)vf_le32(p) | ((uint64_t)vf_le32(p + 4) << 32);
}
static int vf_known_opcode(uint16_t family, uint16_t opcode) {
    if (family == VF_FAMILY_ROOT) return opcode >= 1 && opcode <= 9;
    if (family == VF_FAMILY_BLOCK) return opcode >= 1 && opcode <= 3;
    if (family == VF_FAMILY_SGPU) return opcode >= 1 && opcode <= 7;
    return 0;
}
vf_status vf_validate_header_shape(const struct vf_msg_header *h) {
    if (h == NULL) return VF_EINVAL;
    if (h->magic != VF_MSG_MAGIC || h->abi_major != VF_ABI_MAJOR ||
        h->header_bytes != VF_MSG_BYTES || h->message_bytes != VF_MSG_BYTES ||
        h->reserved0 != 0) return VF_EABI;
    if (h->flags != 0) return VF_EINVAL;
    if (!vf_known_opcode(h->family, h->opcode)) return VF_ENOTSUP;
    if (h->payload_bytes == 0)
        return h->payload_grant == 0 && h->payload_offset == 0 ? VF_OK : VF_EINVAL;
    if (h->payload_grant == 0 || (h->payload_offset & UINT64_C(7)) != 0)
        return VF_EINVAL;
    if (h->payload_bytes > VF_PAYLOAD_MAX ||
        (uint64_t)h->payload_bytes > UINT64_MAX - h->payload_offset)
        return VF_ERANGE;
    return VF_OK;
}
vf_status vf_decode_header(const uint8_t *bytes, uint32_t count,
                           struct vf_msg_header *out) {
    uint8_t copy[64];
    struct vf_msg_header h;
    vf_status status;
    if (out == NULL) return VF_EINVAL;
    if (bytes == NULL || count != 64) {
        vf_clear(out, (uint32_t)sizeof(*out)); return VF_EABI;
    }
    for (uint32_t i = 0; i < 64; ++i) copy[i] = bytes[i];
    h.magic = vf_le32(copy); h.abi_major = vf_le16(copy + 4);
    h.header_bytes = vf_le16(copy + 6); h.message_bytes = vf_le32(copy + 8);
    h.family = vf_le16(copy + 12); h.opcode = vf_le16(copy + 14);
    h.request_id = vf_le64(copy + 16); h.object = vf_le64(copy + 24);
    h.payload_grant = vf_le64(copy + 32); h.payload_offset = vf_le64(copy + 40);
    h.payload_bytes = vf_le32(copy + 48); h.flags = vf_le32(copy + 52);
    h.reserved0 = vf_le64(copy + 56);
    status = vf_validate_header_shape(&h);
    if (status != VF_OK) { vf_clear(out, (uint32_t)sizeof(*out)); return status; }
    vf_copy(out, &h, (uint32_t)sizeof(h));
    return VF_OK;
}

uint64_t vf_make_handle(uint32_t slot, uint32_t generation) {
    return slot != 0 && generation != 0 ? ((uint64_t)generation << 32) | slot : 0;
}
static vf_status vf_check_cap(const struct vf_cap_entry *cap, uint32_t caller,
    uint64_t handle, uint32_t type, uint32_t rights, uint64_t now) {
    if (cap->holder_cell != caller) return VF_EPERM;
    if (cap->slot == 0 || cap->generation == 0 ||
        vf_make_handle(cap->slot, cap->generation) != handle ||
        cap->state != VF_CAP_LIVE) return VF_ESTALE;
    if (cap->valid_from >= cap->expires_at || now < cap->valid_from ||
        now >= cap->expires_at) return VF_ESTALE;
    if (cap->object_id == 0 || cap->object_type != type ||
        (cap->rights & ~VF_RIGHT_ALL) != 0 || (rights & ~cap->rights) != 0)
        return VF_EPERM;
    return VF_OK;
}
vf_status vf_cap_lookup(const struct vf_cap_entry *table, uint32_t count,
    uint32_t caller, uint64_t handle, uint32_t type, uint32_t rights,
    uint64_t now, const struct vf_cap_entry **out) {
    const struct vf_cap_entry *found = NULL;
    vf_status status;
    if (out == NULL) return VF_EINVAL;
    *out = NULL;
    if ((table == NULL && count != 0) || count > VF_POLICY_TABLE_MAX ||
        caller == 0 || type < VF_OBJECT_GRANT || type > VF_OBJECT_BLOCK ||
        (rights & ~VF_RIGHT_ALL) != 0) return VF_EINVAL;
    if ((uint32_t)handle == 0 || (uint32_t)(handle >> 32) == 0) return VF_ESTALE;
    for (uint32_t i = 0; i < count; ++i) {
        if (table[i].holder_cell == caller && table[i].slot == (uint32_t)handle) {
            if (found != NULL) return VF_EAMBIG;
            found = &table[i];
        }
    }
    if (found == NULL) return VF_ESTALE;
    status = vf_check_cap(found, caller, handle, type, rights, now);
    if (status == VF_OK) *out = found;
    return status;
}
vf_status vf_cap_dup_restricted(const struct vf_cap_entry *table, uint32_t count,
    uint32_t caller, uint64_t handle, uint32_t target_cell,
    uint32_t new_slot, uint32_t new_generation, uint32_t rights,
    uint64_t expires_at, uint64_t now, struct vf_cap_entry *out) {
    const struct vf_cap_entry *source = NULL;
    uint32_t type = 0;
    vf_status status;
    if (out == NULL) return VF_EINVAL;
    /* The destination must be separate unpublished metadata. */
    if (table == NULL || count == 0 || count > VF_POLICY_TABLE_MAX) {
        vf_clear(out, (uint32_t)sizeof(*out)); return VF_EINVAL;
    }
    for (uint32_t i = 0; i < count; ++i) if (out == &table[i]) return VF_EINVAL;
    vf_clear(out, (uint32_t)sizeof(*out));
    if (target_cell == 0 || new_slot == 0 || new_generation == 0 ||
        (rights & ~VF_RIGHT_ALL) != 0) return VF_EINVAL;
    for (uint32_t i = 0; i < count; ++i) {
        if (table[i].holder_cell == caller && table[i].slot == (uint32_t)handle)
            type = table[i].object_type;
        if (table[i].holder_cell == target_cell && table[i].slot == new_slot)
            return VF_EAMBIG;
    }
    if (type == 0) return VF_ESTALE;
    status = vf_cap_lookup(table, count, caller, handle, type,
                           rights | VF_RIGHT_DUP, now, &source);
    if (status != VF_OK) return status;
    if (expires_at <= now || expires_at > source->expires_at) return VF_EPERM;
    vf_copy(out, source, (uint32_t)sizeof(*out));
    out->slot = new_slot; out->generation = new_generation;
    out->holder_cell = target_cell; out->rights = rights;
    out->valid_from = now; out->expires_at = expires_at;
    return VF_OK;
}
vf_status vf_validate_payload_grant(const struct vf_msg_header *h,
    const struct vf_grant_entry *table, uint32_t count, uint32_t caller,
    uint32_t rights, uint64_t now, const struct vf_grant_entry **out) {
    const struct vf_grant_entry *found = NULL;
    vf_status status;
    if (out == NULL) return VF_EINVAL;
    *out = NULL;
    if ((table == NULL && count != 0) || count > VF_POLICY_TABLE_MAX ||
        caller == 0 || rights == 0 ||
        (rights & ~(VF_RIGHT_READ | VF_RIGHT_WRITE)) != 0) return VF_EINVAL;
    status = vf_validate_header_shape(h);
    if (status != VF_OK) return status;
    if (h->payload_bytes == 0) return VF_OK;
    for (uint32_t i = 0; i < count; ++i) {
        if (table[i].cap.holder_cell == caller &&
            table[i].cap.slot == (uint32_t)h->payload_grant) {
            if (found != NULL) return VF_EAMBIG;
            found = &table[i];
        }
    }
    if (found == NULL) return VF_ESTALE;
    status = vf_check_cap(&found->cap, caller, h->payload_grant,
                          VF_OBJECT_GRANT, rights, now);
    if (status != VF_OK) return status;
    if (found->state != VF_GRANT_LIVE || found->owner_cell == 0) return VF_ESTALE;
    if (h->payload_offset > found->bytes ||
        (uint64_t)h->payload_bytes > found->bytes - h->payload_offset)
        return VF_ERANGE;
    *out = found;
    return VF_OK;
}
vf_status vf_grant_begin_revoke(struct vf_grant_entry *grant, uint32_t caller) {
    if (grant == NULL || caller == 0) return VF_EINVAL;
    if (grant->owner_cell != caller) return VF_EPERM;
    if (grant->state != VF_GRANT_LIVE || grant->cap.state != VF_CAP_LIVE)
        return VF_ESTALE;
    grant->cap.state = VF_CAP_REVOKED;
    grant->state = VF_GRANT_REVOKING;
    /* Old acknowledgements cannot satisfy this new revocation. */
    grant->ept_invalidated = 0;
    grant->iotlb_invalidated = 0;
    grant->device_drained = 0;
    return VF_OK;
}
vf_status vf_grant_reclaim_ready(const struct vf_grant_entry *grant) {
    if (grant == NULL) return VF_EINVAL;
    if (grant->state != VF_GRANT_REVOKING || grant->cap.state != VF_CAP_REVOKED)
        return VF_ESTALE;
    if (grant->cpu_refs != 0 || grant->dma_refs != 0 || grant->ept_invalidated != 1)
        return VF_EBUSY;
    if (grant->dma_ever_mapped > 1 || grant->pages_pinned > 1 ||
        grant->device_drained > 1 || grant->iotlb_invalidated > 1) return VF_EINVAL;
    if (grant->dma_ever_mapped != 0 && (grant->pages_pinned != 1 ||
        grant->device_drained != 1 || grant->iotlb_invalidated != 1)) return VF_EBUSY;
    return VF_OK;
}

static int vf_equal(const uint8_t *a, const uint8_t *b, uint32_t count) {
    for (uint32_t i = 0; i < count; ++i) if (a[i] != b[i]) return 0;
    return 1;
}
static int vf_nonzero(const uint8_t *p, uint32_t count) {
    for (uint32_t i = 0; i < count; ++i) if (p[i] != 0) return 1;
    return 0;
}
static int vf_unicode_space(uint32_t c) {
    return c == 0x20 || c == 0x85 || c == 0xa0 || c == 0x1680 ||
        (c >= 0x2000 && c <= 0x200a) || c == 0x2028 || c == 0x2029 ||
        c == 0x202f || c == 0x205f || c == 0x3000;
}
static int vf_valid_serial(const uint8_t *s) {
    uint32_t bytes = 0, i = 0, first = 0, last = 0;
    while (bytes < VF_SERIAL_BYTES && s[bytes] != 0) ++bytes;
    if (bytes == 0 || bytes == VF_SERIAL_BYTES) return 0;
    for (uint32_t j = bytes; j < VF_SERIAL_BYTES; ++j) if (s[j] != 0) return 0;
    while (i < bytes) {
        uint32_t c, more, minimum;
        uint8_t lead = s[i++];
        if (lead < 0x80) { c = lead; more = 0; minimum = 0; }
        else if (lead >= 0xc2 && lead <= 0xdf) { c = lead & 0x1fu; more = 1; minimum = 0x80; }
        else if (lead >= 0xe0 && lead <= 0xef) { c = lead & 0x0fu; more = 2; minimum = 0x800; }
        else if (lead >= 0xf0 && lead <= 0xf4) { c = lead & 7u; more = 3; minimum = 0x10000; }
        else return 0;
        if (more > bytes - i) return 0;
        for (uint32_t j = 0; j < more; ++j) {
            if ((s[i] & 0xc0u) != 0x80u) return 0;
            c = (c << 6) | (s[i++] & 0x3fu);
        }
        if (c < minimum || c > 0x10ffff || (c >= 0xd800 && c <= 0xdfff) ||
            c < 0x20 || c == 0x7f) return 0;
        if (first == 0) first = c;
        last = c;
    }
    return !vf_unicode_space(first) && !vf_unicode_space(last);
}
static int vf_valid_selector(const struct vf_partition_selector *s) {
    return vf_valid_serial(s->serial) && vf_nonzero(s->disk_guid, 16) &&
        vf_nonzero(s->partition_guid, 16) && s->read_only <= 1 &&
        (s->sector_bytes == 512 || s->sector_bytes == 4096);
}
static int vf_same_partition(const struct vf_partition_selector *a,
                              const struct vf_partition_selector *b) {
    return vf_equal(a->serial, b->serial, VF_SERIAL_BYTES) &&
        vf_equal(a->disk_guid, b->disk_guid, 16) &&
        vf_equal(a->partition_guid, b->partition_guid, 16) &&
        a->sector_bytes == b->sector_bytes;
}
static vf_status vf_check_partition(const struct vf_partition_record *p) {
    if (!vf_valid_selector(&p->identity) || p->controller_approved != 1 ||
        p->gpt_verified != 1 || p->online != 1 || p->fua_verified > 1 ||
        p->device_generation == 0) return VF_EBINDING;
    if (p->usable_first_lba == 0 || p->usable_blocks == 0 ||
        p->usable_first_lba >= p->disk_blocks ||
        p->usable_blocks > p->disk_blocks - p->usable_first_lba ||
        p->first_lba < p->usable_first_lba || p->blocks == 0)
        return VF_ERANGE;
    if (p->first_lba - p->usable_first_lba >= p->usable_blocks ||
        p->blocks > p->usable_blocks - (p->first_lba - p->usable_first_lba))
        return VF_ERANGE;
    return VF_OK;
}
vf_status vf_bind_partition_exact(const struct vf_partition_selector *selector,
    const struct vf_partition_record *inventory, uint32_t count,
    struct vf_block_binding *out) {
    const struct vf_partition_record *found = NULL;
    vf_status status;
    if (out == NULL) return VF_EINVAL;
    vf_clear(out, (uint32_t)sizeof(*out));
    if (selector == NULL || !vf_valid_selector(selector) ||
        (inventory == NULL && count != 0) || count > VF_POLICY_TABLE_MAX)
        return VF_EINVAL;
    for (uint32_t i = 0; i < count; ++i) {
        if (vf_same_partition(selector, &inventory[i].identity)) {
            if (found != NULL) return VF_EAMBIG;
            found = &inventory[i];
        }
    }
    if (found == NULL) return VF_ENOENT;
    status = vf_check_partition(found);
    if (status != VF_OK) return status;
    vf_copy(&out->partition, found, (uint32_t)sizeof(*found));
    out->read_only = selector->read_only | found->identity.read_only;
    return VF_OK;
}
vf_status vf_plan_block_request(const struct vf_block_binding *binding,
    uint64_t current_generation, const struct vf_block_request *request,
    struct vf_block_plan *out) {
    const struct vf_partition_record *p;
    vf_status status;
    if (out == NULL) return VF_EINVAL;
    vf_clear(out, (uint32_t)sizeof(*out));
    if (binding == NULL || request == NULL || binding->read_only > 1) return VF_EINVAL;
    p = &binding->partition;
    status = vf_check_partition(p);
    if (status != VF_OK) return status;
    if (current_generation != p->device_generation) return VF_ESTALE;
    if (request->sector_bytes != p->identity.sector_bytes) return VF_EBINDING;
    if ((request->flags & ~VF_BLOCK_FUA) != 0) return VF_ENOTSUP;
    if (request->opcode == VF_BLOCK_FLUSH) {
        if (request->guest_lba != 0 || request->blocks != 0 || request->flags != 0)
            return VF_EINVAL;
        out->opcode = VF_BLOCK_FLUSH;
        return VF_OK; /* A plan, never a claim of durable completion. */
    }
    if (request->opcode != VF_BLOCK_READ && request->opcode != VF_BLOCK_WRITE)
        return VF_ENOTSUP;
    if (request->opcode == VF_BLOCK_WRITE &&
        (binding->read_only != 0 || p->identity.read_only != 0)) return VF_EPERM;
    if (request->flags != 0 && (request->opcode != VF_BLOCK_WRITE ||
        p->fua_verified != 1)) return VF_ENOTSUP;
    if (request->guest_lba >= p->blocks || request->blocks == 0 ||
        request->blocks > p->blocks - request->guest_lba ||
        request->blocks > UINT64_MAX / p->identity.sector_bytes) return VF_ERANGE;
    /* Partition validation proved these two additions cannot overflow. */
    out->physical_lba = p->first_lba + request->guest_lba;
    out->blocks = request->blocks;
    out->bytes = request->blocks * p->identity.sector_bytes;
    out->opcode = request->opcode; out->flags = request->flags;
    return VF_OK;
}

vf_status vf_select_common_codegen(const struct vf_cpu_capability *cpus,
    uint32_t count, struct vf_codegen_choice *out) {
    uint32_t tier = VF_CODEGEN_AVX2;
    uint64_t common_xstate = UINT64_MAX;
    const uint32_t sse_context = (UINT32_C(1) << 24) | (UINT32_C(1) << 25) |
                                 (UINT32_C(1) << 26);
    const uint32_t long_nx = (UINT32_C(1) << 29) | (UINT32_C(1) << 20);
    const uint32_t avx_bits = (UINT32_C(1) << 26) | (UINT32_C(1) << 27) |
                              (UINT32_C(1) << 28);
    if (out == NULL) return VF_EINVAL;
    vf_clear(out, (uint32_t)sizeof(*out));
    if (cpus == NULL || count == 0 || count > VF_POLICY_TABLE_MAX) return VF_EINVAL;
    for (uint32_t i = 0; i < count; ++i) {
        const struct vf_cpu_capability *c = &cpus[i];
        uint32_t local = VF_CODEGEN_SSE42;
        for (uint32_t j = 0; j < i; ++j)
            if (cpus[j].logical_id == c->logical_id) return VF_EINVAL;
        if (c->intel_vendor != 1 || c->sse_state_managed != 1 ||
            c->xstate_managed > 1 || c->max_basic_leaf < 1 ||
            (c->leaf1_ecx & (UINT32_C(1) << 20)) == 0 ||
            (c->leaf1_edx & sse_context) != sse_context ||
            (c->ext_80000001_edx & long_nx) != long_nx) return VF_ECPU;
        if ((c->leaf1_ecx & avx_bits) == avx_bits && c->xstate_managed == 1 &&
            (c->xcr0 & UINT64_C(7)) == UINT64_C(7) &&
            (c->xstate_save_mask & c->xcr0) == c->xcr0) {
            local = VF_CODEGEN_AVX;
            if (c->max_basic_leaf >= 7 &&
                (c->leaf7_ebx & (UINT32_C(1) << 5)) != 0) local = VF_CODEGEN_AVX2;
        }
        if (local < tier) tier = local;
        common_xstate &= c->xcr0 & c->xstate_save_mask;
    }
    out->tier = tier;
    out->common_xstate = tier == VF_CODEGEN_SSE42 ? UINT64_C(3) : (common_xstate & UINT64_C(7));
    return VF_OK;
}
vf_status vf_vmx_combine_controls(const uint64_t *msrs, uint32_t count,
    uint32_t required, uint32_t optional, uint32_t forbidden, uint32_t *out) {
    uint32_t must_one = 0, can_one = UINT32_MAX;
    if (out == NULL) return VF_EINVAL;
    *out = 0;
    if (msrs == NULL || count == 0 || count > VF_POLICY_TABLE_MAX ||
        ((required | optional) & forbidden) != 0) return VF_EINVAL;
    for (uint32_t i = 0; i < count; ++i) {
        uint32_t low = (uint32_t)msrs[i], high = (uint32_t)(msrs[i] >> 32);
        if ((low & ~high) != 0) return VF_EVMX;
        must_one |= low;
        can_one &= high;
    }
    if ((must_one & ~can_one) != 0 || (required & ~can_one) != 0 ||
        (must_one & forbidden) != 0) return VF_EVMX;
    *out = (required | optional | must_one) & can_one & ~forbidden;
    return VF_OK;
}
vf_status vf_vmx_validate_fixed_bits(uint64_t value, uint64_t fixed0,
                                     uint64_t fixed1) {
    if ((fixed0 & ~fixed1) != 0 || (value & fixed0) != fixed0 ||
        (value & ~fixed1) != 0) return VF_EVMX;
    return VF_OK;
}
