/* SPDX-License-Identifier: BSD-4-Clause; repository LICENSE.txt applies. */
#ifndef VF_BUNDLE_H
#define VF_BUNDLE_H
#include "vf_abi.h"

#define VF_BUNDLE_HEADER_BYTES UINT32_C(64)
#define VF_BUNDLE_ENTRY_BYTES UINT32_C(128)
#define VF_BUNDLE_MAX_ENTRIES UINT32_C(66)
#define VF_BUNDLE_MAX_MANIFEST_BYTES UINT32_C(8512)
#define VF_BUNDLE_CONFIG_MAX UINT64_C(1048576)
#define VF_BUNDLE_IMAGE_MAX UINT64_C(67108864)
#define VF_BUNDLE_ROLE_CONFIG UINT32_C(1)
#define VF_BUNDLE_ROLE_CORE UINT32_C(2)
#define VF_BUNDLE_ROLE_SERVICE UINT32_C(3)
#define VF_BUNDLE_EAUTH ((vf_status)-30)
#define VF_BUNDLE_EINTEGRITY ((vf_status)-31)
#define VF_BUNDLE_EROLLBACK ((vf_status)-32)

/* Deterministic wire v1, all integers little-endian, no native struct casts:
 * HEADER 64: magic[16] = "VSK-BUNDLE-v1\0\0\0" at 0;
 * u16 version=1/size=64/entry_size=128/signature_alg=1 at 16/18/20/22;
 * u32 manifest_size/count/flags=0/reserved=0 at 24/28/32/36;
 * u64 nonzero release_epoch at 40; u32 target_major=26|27 at 48;
 * 12 zero bytes at 52.
 * ENTRY 128: u32 role/instance at 0/4; u64 nonzero blob_size at 8;
 * SHA-256[32] at 16; SHA-512[64] at 48; 16 zero bytes at 112.
 * Entries strictly sorted by (role,instance). Exactly config(1,0), core(2,0),
 * and 1..64 services(3,1..64). Both hashes mandatory. No paths, keys or trust
 * flags in the manifest. Pure RFC8032 Ed25519 signs the exact entire manifest;
 * the fixed magic is its domain separator. Detached signature is exactly 64B.
 */

struct vf_bundle_policy {
    /* Provisioned by the trusted loader/build, never copied from this bundle.
     * Must be a properly generated Ed25519 public key. No test/product toggle.
     * Authenticating its provenance is the caller's boot-chain obligation. */
    uint8_t trusted_public_key[32];
    uint64_t minimum_release_epoch;
    uint32_t expected_target_major;
};
struct vf_bundle_entry {
    uint32_t role, instance;
    uint64_t bytes;
    uint8_t sha256[32], sha512[64];
};
struct vf_bundle_manifest {
    uint64_t release_epoch;
    uint32_t target_major, entry_count;
    uint8_t manifest_sha256[32];
    struct vf_bundle_entry entries[VF_BUNDLE_MAX_ENTRIES];
};
struct vf_bundle_blob {
    uint32_t role, instance;
    const uint8_t *data;
    uint64_t bytes;
};

/* All input bytes/policy/blob mappings must be root-owned, stable and immutable
 * throughout validation AND subsequent use. No concurrent mutation or DMA.
 * Outputs must be disjoint from every input and readable/writable for their
 * declared extent; these C helpers do not probe arbitrary addresses. Outputs
 * are zeroed on failure. No function grants platform/VMX/device/boot authority.
 * No allocation, file I/O, callbacks, cryptographic key generation or signing.
 */
vf_status vf_bundle_authenticate_manifest(const uint8_t *manifest,
    uint32_t manifest_bytes, const uint8_t *signature, uint32_t signature_bytes,
    const struct vf_bundle_policy *policy, struct vf_bundle_manifest *out);
/* Authenticate before using signed sizes to allocate/load fixed role paths.
 * Then call full verification again over those exact immutable loaded bytes.
 * A parsed/authenticated metadata struct is not a reusable bearer token. */
vf_status vf_bundle_verify(const uint8_t *manifest, uint32_t manifest_bytes,
    const uint8_t *signature, uint32_t signature_bytes,
    const struct vf_bundle_policy *policy, const struct vf_bundle_blob *blobs,
    uint32_t blob_count, struct vf_bundle_manifest *out);

/* Public primitive wrappers for test/loader hashing; zero-length input may be
 * NULL, nonempty input may not. Hash outputs must not alias inputs. */
vf_status vf_bundle_sha256(const uint8_t *data, size_t bytes, uint8_t out[32]);
vf_status vf_bundle_sha512(const uint8_t *data, size_t bytes, uint8_t out[64]);
vf_status vf_bundle_ed25519_verify(const uint8_t *message, size_t bytes,
    const uint8_t public_key[32], const uint8_t signature[64]);
#endif
