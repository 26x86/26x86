/* SPDX-License-Identifier: BSD-4-Clause; repository LICENSE.txt applies. */
#include "vf_bundle.h"
#include "../crypto/monocypher/monocypher-ed25519.h"
#include "../crypto/bearssl/bearssl_hash.h"

static void vf_zero(void *out, size_t bytes)
{
    volatile uint8_t *p = out;
    size_t i;
    for (i = 0; i < bytes; ++i) p[i] = 0;
}
static void vf_copy_bytes(void *out, const void *input, size_t bytes)
{
    volatile uint8_t *d = out;
    const uint8_t *s = input;
    size_t i;
    for (i = 0; i < bytes; ++i) d[i] = s[i];
}
static uint16_t vf_u16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}
static uint32_t vf_u32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8)
        | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static uint64_t vf_u64(const uint8_t *p)
{
    return (uint64_t)vf_u32(p) | ((uint64_t)vf_u32(p + 4) << 32);
}
static int vf_all_zero(const uint8_t *p, size_t bytes)
{
    uint8_t sum = 0;
    size_t i;
    for (i = 0; i < bytes; ++i) sum |= p[i];
    return sum == 0;
}

vf_status vf_bundle_sha256(const uint8_t *data, size_t bytes, uint8_t out[32])
{
    br_sha256_context ctx;
    if (out == NULL) return VF_EINVAL;
    vf_zero(out, 32);
    if ((data == NULL && bytes != 0) || bytes > UINT64_MAX / 8)
        return VF_EINVAL;
    br_sha256_init(&ctx);
    br_sha256_update(&ctx, data, bytes);
    br_sha256_out(&ctx, out);
    crypto_wipe(&ctx, sizeof(ctx));
    return VF_OK;
}
vf_status vf_bundle_sha512(const uint8_t *data, size_t bytes, uint8_t out[64])
{
    if (out == NULL) return VF_EINVAL;
    vf_zero(out, 64);
    if (data == NULL && bytes != 0) return VF_EINVAL;
    crypto_sha512(out, data, bytes);
    return VF_OK;
}
vf_status vf_bundle_ed25519_verify(const uint8_t *message, size_t bytes,
    const uint8_t public_key[32], const uint8_t signature[64])
{
    if (public_key == NULL || signature == NULL ||
        (message == NULL && bytes != 0)) return VF_EINVAL;
    /* Reject obvious unprovisioned anchors. This is not a key-provisioning
     * protocol: the trusted loader must pin a properly generated public key.
     * Monocypher implements RFC8032's cofactored verification equation. */
    if (vf_all_zero(public_key, 32) ||
        (public_key[0] == 1 && vf_all_zero(public_key + 1, 31)))
        return VF_BUNDLE_EAUTH;
    return crypto_ed25519_check(signature, public_key, message, bytes) == 0
        ? VF_OK : VF_BUNDLE_EAUTH;
}

static vf_status vf_parse_authenticated(const uint8_t *wire, uint32_t bytes,
    const struct vf_bundle_policy *policy, struct vf_bundle_manifest *out)
{
    static const uint8_t magic[16] = "VSK-BUNDLE-v1\0\0";
    uint32_t count, i;
    uint64_t epoch;
    if (crypto_verify16(wire, magic) != 0 || vf_u16(wire + 16) != 1 ||
        vf_u16(wire + 18) != 64 || vf_u16(wire + 20) != 128 ||
        vf_u16(wire + 22) != 1 || vf_u32(wire + 24) != bytes ||
        !vf_all_zero(wire + 32, 8) || !vf_all_zero(wire + 52, 12))
        return VF_EABI;
    count = vf_u32(wire + 28);
    if (count < 3 || count > VF_BUNDLE_MAX_ENTRIES ||
        bytes != VF_BUNDLE_HEADER_BYTES + count * VF_BUNDLE_ENTRY_BYTES)
        return VF_EABI;
    epoch = vf_u64(wire + 40);
    if (epoch == 0) return VF_EABI;
    if (epoch < policy->minimum_release_epoch) return VF_BUNDLE_EROLLBACK;
    if (vf_u32(wire + 48) != policy->expected_target_major) return VF_ENOTSUP;
    for (i = 0; i < count; ++i) {
        const uint8_t *p = wire + VF_BUNDLE_HEADER_BYTES +
            (size_t)i * VF_BUNDLE_ENTRY_BYTES;
        struct vf_bundle_entry *entry = &out->entries[i];
        uint32_t role = vf_u32(p), instance = vf_u32(p + 4);
        uint64_t blob_bytes = vf_u64(p + 8);
        if (!vf_all_zero(p + 112, 16) || blob_bytes == 0) return VF_EABI;
        if (i == 0) {
            if (role != VF_BUNDLE_ROLE_CONFIG || instance != 0 ||
                blob_bytes > VF_BUNDLE_CONFIG_MAX) return VF_EABI;
        } else if (i == 1) {
            if (role != VF_BUNDLE_ROLE_CORE || instance != 0 ||
                blob_bytes > VF_BUNDLE_IMAGE_MAX) return VF_EABI;
        } else {
            if (role != VF_BUNDLE_ROLE_SERVICE || instance < 1 || instance > 64 ||
                blob_bytes > VF_BUNDLE_IMAGE_MAX ||
                (i > 2 && instance <= out->entries[i - 1].instance))
                return VF_EABI;
        }
        entry->role = role;
        entry->instance = instance;
        entry->bytes = blob_bytes;
        vf_copy_bytes(entry->sha256, p + 16, 32);
        vf_copy_bytes(entry->sha512, p + 48, 64);
    }
    out->release_epoch = epoch;
    out->target_major = policy->expected_target_major;
    out->entry_count = count;
    return vf_bundle_sha256(wire, bytes, out->manifest_sha256);
}

vf_status vf_bundle_authenticate_manifest(const uint8_t *manifest,
    uint32_t manifest_bytes, const uint8_t *signature, uint32_t signature_bytes,
    const struct vf_bundle_policy *policy, struct vf_bundle_manifest *out)
{
    vf_status status;
    if (out == NULL) return VF_EINVAL;
    vf_zero(out, sizeof(*out));
    if (manifest == NULL || signature == NULL || policy == NULL ||
        signature_bytes != 64 || manifest_bytes < VF_BUNDLE_HEADER_BYTES ||
        manifest_bytes > VF_BUNDLE_MAX_MANIFEST_BYTES ||
        policy->minimum_release_epoch == 0 ||
        (policy->expected_target_major != 26 && policy->expected_target_major != 27))
        return VF_EINVAL;
    status = vf_bundle_ed25519_verify(manifest, manifest_bytes,
        policy->trusted_public_key, signature);
    if (status == VF_OK)
        status = vf_parse_authenticated(manifest, manifest_bytes, policy, out);
    if (status != VF_OK) vf_zero(out, sizeof(*out));
    return status;
}

vf_status vf_bundle_verify(const uint8_t *manifest, uint32_t manifest_bytes,
    const uint8_t *signature, uint32_t signature_bytes,
    const struct vf_bundle_policy *policy, const struct vf_bundle_blob *blobs,
    uint32_t blob_count, struct vf_bundle_manifest *out)
{
    vf_status status = vf_bundle_authenticate_manifest(manifest, manifest_bytes,
        signature, signature_bytes, policy, out);
    uint32_t i, j;
    uint8_t sha256[32], sha512[64];
    if (status != VF_OK) return status;
    if (blobs == NULL || blob_count != out->entry_count) {
        status = VF_EINVAL;
        goto fail;
    }
    for (i = 0; i < out->entry_count; ++i) {
        const struct vf_bundle_entry *entry = &out->entries[i];
        const struct vf_bundle_blob *found = NULL;
        for (j = 0; j < blob_count; ++j) {
            if (blobs[j].role == entry->role && blobs[j].instance == entry->instance) {
                if (found != NULL) { status = VF_EAMBIG; goto fail; }
                found = &blobs[j];
            }
        }
        if (found == NULL) { status = VF_ENOENT; goto fail; }
        if (found->bytes != entry->bytes || found->data == NULL ||
            found->bytes > SIZE_MAX) { status = VF_BUNDLE_EINTEGRITY; goto fail; }
        status = vf_bundle_sha256(found->data, (size_t)found->bytes, sha256);
        if (status != VF_OK) goto fail;
        status = vf_bundle_sha512(found->data, (size_t)found->bytes, sha512);
        if (status != VF_OK) goto fail;
        if (crypto_verify32(sha256, entry->sha256) != 0 ||
            crypto_verify64(sha512, entry->sha512) != 0) {
            status = VF_BUNDLE_EINTEGRITY;
            goto fail;
        }
    }
    return VF_OK;
fail:
    vf_zero(out, sizeof(*out));
    return status;
}
