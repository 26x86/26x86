/* SPDX-License-Identifier: BSD-4-Clause; repository LICENSE.txt applies. */
#include "vf_bundle.h"
#include "../crypto/monocypher/monocypher-ed25519.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../crypto/vectors/rfc8032.h"
#include "../crypto/vectors/hashes.h"

static unsigned checks;
#define CHECK(x) do { ++checks; if (!(x)) { \
    fprintf(stderr, "bundle check failed at line %d: %s\n", __LINE__, #x); \
    exit(1); } } while (0)

static size_t unhex(const char *s, uint8_t *out, size_t capacity)
{
    size_t n = strlen(s), i;
    CHECK(n % 2 == 0 && n / 2 <= capacity);
    for (i = 0; i < n / 2; ++i) {
        unsigned value;
        CHECK(sscanf(s + 2 * i, "%2x", &value) == 1);
        out[i] = (uint8_t)value;
    }
    return n / 2;
}
static void put16(uint8_t *p, uint16_t n)
{
    p[0] = (uint8_t)n; p[1] = (uint8_t)(n >> 8);
}
static void put32(uint8_t *p, uint32_t n)
{
    unsigned i;
    for (i = 0; i < 4; ++i) p[i] = (uint8_t)(n >> (8 * i));
}
static void put64(uint8_t *p, uint64_t n)
{
    unsigned i;
    for (i = 0; i < 8; ++i) p[i] = (uint8_t)(n >> (8 * i));
}
static int all_zero(const void *data, size_t bytes)
{
    const uint8_t *p = data;
    size_t i;
    for (i = 0; i < bytes; ++i) if (p[i] != 0) return 0;
    return 1;
}

static void test_primitives(void)
{
    static uint8_t data[1000000];
    uint8_t sha256[32], sha512[64], expected[64];
    uint8_t pk[32], sig[64], changed[64], message[1024];
    size_t i, j, bytes;
    for (i = 0; i < sizeof(data); ++i) data[i] = (uint8_t)i;
    for (i = 0; i < sizeof(vf_hash_vectors) / sizeof(vf_hash_vectors[0]); ++i) {
        const struct vf_hash_vector *v = &vf_hash_vectors[i];
        CHECK(vf_bundle_sha256(data, v->bytes, sha256) == VF_OK);
        CHECK(unhex(v->sha256, expected, sizeof(expected)) == 32);
        CHECK(memcmp(sha256, expected, 32) == 0);
        CHECK(vf_bundle_sha512(data, v->bytes, sha512) == VF_OK);
        CHECK(unhex(v->sha512, expected, sizeof(expected)) == 64);
        CHECK(memcmp(sha512, expected, 64) == 0);
    }
    CHECK(vf_bundle_sha256(NULL, 0, sha256) == VF_OK);
    CHECK(vf_bundle_sha512(NULL, 0, sha512) == VF_OK);
    CHECK(vf_bundle_sha256(NULL, 1, sha256) == VF_EINVAL);
    CHECK(all_zero(sha256, 32));
    CHECK(vf_bundle_sha512(NULL, 1, sha512) == VF_EINVAL);
    CHECK(all_zero(sha512, 64));
    CHECK(vf_bundle_sha256(data, 1, NULL) == VF_EINVAL);
    CHECK(vf_bundle_sha512(data, 1, NULL) == VF_EINVAL);
    CHECK(vf_bundle_sha256(data, SIZE_MAX, sha256) == VF_EINVAL);
    for (i = 0; i < sizeof(vf_rfc_vectors) / sizeof(vf_rfc_vectors[0]); ++i) {
        const struct vf_rfc_vector *v = &vf_rfc_vectors[i];
        CHECK(unhex(v->public_key, pk, sizeof(pk)) == 32);
        CHECK(unhex(v->signature, sig, sizeof(sig)) == 64);
        bytes = unhex(v->message, message, sizeof(message));
        CHECK(vf_bundle_ed25519_verify(message, bytes, pk, sig) == VF_OK);
        if (bytes == 0) CHECK(vf_bundle_ed25519_verify(NULL, 0, pk, sig) == VF_OK);
        for (j = 0; j < 64; ++j) {
            memcpy(changed, sig, sizeof(sig)); changed[j] ^= 1;
            CHECK(vf_bundle_ed25519_verify(message, bytes, pk, changed) == VF_BUNDLE_EAUTH);
        }
        memcpy(changed, sig, sizeof(sig)); memset(changed + 32, 0xff, 32);
        CHECK(vf_bundle_ed25519_verify(message, bytes, pk, changed) == VF_BUNDLE_EAUTH);
        if (bytes != 0) {
            message[bytes - 1] ^= 1;
            CHECK(vf_bundle_ed25519_verify(message, bytes, pk, sig) == VF_BUNDLE_EAUTH);
        }
    }
    CHECK(vf_bundle_ed25519_verify(NULL, 1, pk, sig) == VF_EINVAL);
    CHECK(vf_bundle_ed25519_verify(data, 1, NULL, sig) == VF_EINVAL);
    CHECK(vf_bundle_ed25519_verify(data, 1, pk, NULL) == VF_EINVAL);
    memset(pk, 0, sizeof(pk)); memset(sig, 0, sizeof(sig));
    CHECK(vf_bundle_ed25519_verify(data, 1, pk, sig) == VF_BUNDLE_EAUTH);
    pk[0] = 1;
    CHECK(vf_bundle_ed25519_verify(data, 1, pk, sig) == VF_BUNDLE_EAUTH);
}

struct fixture {
    uint8_t wire[VF_BUNDLE_MAX_MANIFEST_BYTES];
    uint8_t signature[64], secret_key[64];
    struct vf_bundle_policy policy;
    struct vf_bundle_blob blobs[VF_BUNDLE_MAX_ENTRIES];
    uint32_t bytes, count;
};
static const uint8_t config_bytes[] = "<plist>test only</plist>";
static const uint8_t core_bytes[] = {0x7f, 'E', 'L', 'F', 2, 1, 1, 0};
static const uint8_t service_bytes[] = {0x7f, 'E', 'L', 'F', 2, 1, 1, 1};

static void sign_fixture(struct fixture *f)
{
    crypto_ed25519_sign(f->signature, f->secret_key, f->wire, f->bytes);
}
static void init_fixture(struct fixture *f, uint32_t count)
{
    uint8_t seed[32];
    uint32_t i;
    memset(f, 0, sizeof(*f));
    /* Public RFC8032 test seed. Never a production anchor or signing secret. */
    CHECK(unhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
                seed, sizeof(seed)) == 32);
    crypto_ed25519_key_pair(f->secret_key, f->policy.trusted_public_key, seed);
    f->policy.minimum_release_epoch = 7;
    f->policy.expected_target_major = 26;
    f->count = count; f->bytes = 64 + 128 * count;
    memcpy(f->wire, "VSK-BUNDLE-v1\0\0", 16);
    put16(f->wire + 16, 1); put16(f->wire + 18, 64);
    put16(f->wire + 20, 128); put16(f->wire + 22, 1);
    put32(f->wire + 24, f->bytes); put32(f->wire + 28, count);
    put64(f->wire + 40, 7); put32(f->wire + 48, 26);
    for (i = 0; i < count; ++i) {
        struct vf_bundle_blob *b = &f->blobs[i];
        uint8_t *entry = f->wire + 64 + i * 128;
        if (i == 0) {
            b->role = 1; b->data = config_bytes; b->bytes = sizeof(config_bytes);
        } else if (i == 1) {
            b->role = 2; b->data = core_bytes; b->bytes = sizeof(core_bytes);
        } else {
            b->role = 3; b->instance = i - 1;
            b->data = service_bytes; b->bytes = sizeof(service_bytes);
        }
        put32(entry, b->role); put32(entry + 4, b->instance);
        put64(entry + 8, b->bytes);
        CHECK(vf_bundle_sha256(b->data, (size_t)b->bytes, entry + 16) == VF_OK);
        CHECK(vf_bundle_sha512(b->data, (size_t)b->bytes, entry + 48) == VF_OK);
    }
    sign_fixture(f);
}
static vf_status authenticate(const struct fixture *f, struct vf_bundle_manifest *out)
{
    return vf_bundle_authenticate_manifest(f->wire, f->bytes, f->signature, 64,
        &f->policy, out);
}
static vf_status verify(const struct fixture *f, struct vf_bundle_manifest *out)
{
    return vf_bundle_verify(f->wire, f->bytes, f->signature, 64, &f->policy,
        f->blobs, f->count, out);
}
static void expect_authenticated_rejection(struct fixture *f, vf_status status)
{
    struct vf_bundle_manifest out;
    sign_fixture(f);
    memset(&out, 0xa5, sizeof(out));
    CHECK(authenticate(f, &out) == status);
    CHECK(all_zero(&out, sizeof(out)));
}
static void test_manifest(void)
{
    struct fixture base, f;
    struct vf_bundle_manifest out;
    uint32_t i;
    uint8_t changed_blob[sizeof(config_bytes)];
    init_fixture(&base, 3);
    CHECK(authenticate(&base, &out) == VF_OK);
    CHECK(out.release_epoch == 7 && out.target_major == 26 && out.entry_count == 3);
    CHECK(out.entries[2].role == 3 && out.entries[2].instance == 1);
    CHECK(verify(&base, &out) == VF_OK);
    for (i = 0; i < base.bytes; ++i) {
        f = base; f.wire[i] ^= 1;
        CHECK(authenticate(&f, &out) == VF_BUNDLE_EAUTH);
        CHECK(all_zero(&out, sizeof(out)));
    }
    for (i = 0; i < 32; ++i) {
        f = base; f.policy.trusted_public_key[i] ^= 1;
        CHECK(authenticate(&f, &out) == VF_BUNDLE_EAUTH);
    }
    for (i = 0; i < 64; ++i) {
        CHECK(vf_bundle_authenticate_manifest(base.wire, base.bytes, base.signature,
            i, &base.policy, &out) == VF_EINVAL);
        CHECK(vf_bundle_authenticate_manifest(base.wire, i, base.signature,
            64, &base.policy, &out) == VF_EINVAL);
    }
    f = base; f.policy.minimum_release_epoch = 8;
    CHECK(authenticate(&f, &out) == VF_BUNDLE_EROLLBACK);
    f = base; f.policy.expected_target_major = 27;
    CHECK(authenticate(&f, &out) == VF_ENOTSUP);
    f = base; f.policy.minimum_release_epoch = 0;
    CHECK(authenticate(&f, &out) == VF_EINVAL);
    f = base; f.policy.expected_target_major = 25;
    CHECK(authenticate(&f, &out) == VF_EINVAL);
    CHECK(vf_bundle_authenticate_manifest(NULL, base.bytes, base.signature, 64,
        &base.policy, &out) == VF_EINVAL);
    CHECK(vf_bundle_authenticate_manifest(base.wire, base.bytes, NULL, 64,
        &base.policy, &out) == VF_EINVAL);
    CHECK(vf_bundle_authenticate_manifest(base.wire, base.bytes, base.signature, 64,
        NULL, &out) == VF_EINVAL);
    CHECK(authenticate(&base, NULL) == VF_EINVAL);
    f = base; f.bytes = VF_BUNDLE_MAX_MANIFEST_BYTES + 1;
    CHECK(authenticate(&f, &out) == VF_EINVAL);
    /* Valid signatures over malformed structure must still be rejected. */
    for (i = 0; i < 40; ++i) {
        f = base; f.wire[i] ^= 0x80;
        expect_authenticated_rejection(&f, VF_EABI);
    }
    for (i = 52; i < 64; ++i) {
        f = base; f.wire[i] = 1;
        expect_authenticated_rejection(&f, VF_EABI);
    }
    f = base; put64(f.wire + 40, 0);
    expect_authenticated_rejection(&f, VF_EABI);
    f = base; put32(f.wire + 28, UINT32_MAX);
    expect_authenticated_rejection(&f, VF_EABI);
    f = base; put32(f.wire + 48, 28);
    expect_authenticated_rejection(&f, VF_ENOTSUP);
    for (i = 0; i < 3; ++i) {
        uint32_t entry = 64 + i * 128;
        f = base; put32(f.wire + entry, 4);
        expect_authenticated_rejection(&f, VF_EABI);
        f = base; put64(f.wire + entry + 8, 0);
        expect_authenticated_rejection(&f, VF_EABI);
        f = base; put64(f.wire + entry + 8, UINT64_MAX);
        expect_authenticated_rejection(&f, VF_EABI);
        f = base; put32(f.wire + entry + 4, i < 2 ? 1 : 65);
        expect_authenticated_rejection(&f, VF_EABI);
        f = base; f.wire[entry + 127] = 1;
        expect_authenticated_rejection(&f, VF_EABI);
        f = base; f.wire[entry + 16] ^= 1; sign_fixture(&f);
        CHECK(verify(&f, &out) == VF_BUNDLE_EINTEGRITY);
        CHECK(all_zero(&out, sizeof(out)));
        f = base; f.wire[entry + 48] ^= 1; sign_fixture(&f);
        CHECK(verify(&f, &out) == VF_BUNDLE_EINTEGRITY);
    }
    f = base; --f.count;
    CHECK(verify(&f, &out) == VF_EINVAL);
    f = base; f.blobs[1] = f.blobs[0];
    CHECK(verify(&f, &out) == VF_EAMBIG);
    f = base; f.blobs[2].instance = 2;
    CHECK(verify(&f, &out) == VF_ENOENT);
    f = base; f.blobs[0].data = NULL;
    CHECK(verify(&f, &out) == VF_BUNDLE_EINTEGRITY);
    f = base; f.blobs[0].bytes = UINT64_MAX;
    CHECK(verify(&f, &out) == VF_BUNDLE_EINTEGRITY);
    f = base; f.blobs[0] = base.blobs[2]; f.blobs[2] = base.blobs[0];
    CHECK(verify(&f, &out) == VF_OK); /* mapping order need not match wire */
    memcpy(changed_blob, config_bytes, sizeof(changed_blob)); changed_blob[1] ^= 1;
    f = base; f.blobs[0].data = changed_blob;
    CHECK(verify(&f, &out) == VF_BUNDLE_EINTEGRITY);
    /* Authenticating only a manifest does not authenticate detached blobs. */
    CHECK(authenticate(&f, &out) == VF_OK);
    CHECK(vf_bundle_verify(f.wire, f.bytes, f.signature, 64, &f.policy,
        NULL, f.count, &out) == VF_EINVAL);
    CHECK(all_zero(&out, sizeof(out)));
    init_fixture(&f, 66);
    CHECK(verify(&f, &out) == VF_OK);
    CHECK(out.entry_count == 66 && out.entries[65].instance == 64);
    put32(f.wire + 64 + 65 * 128 + 4, 63);
    expect_authenticated_rejection(&f, VF_EABI);
    f = base; f.policy.expected_target_major = 27; put32(f.wire + 48, 27);
    sign_fixture(&f); CHECK(verify(&f, &out) == VF_OK);
}

/* Hosted integration harness only: production verifier has no filesystem or
 * allocator dependency. External public key never comes from the bundle. */
static uint8_t *read_fixture(const char *path, size_t max_bytes, size_t *bytes)
{
    FILE *file = fopen(path, "rb");
    long length;
    uint8_t *data;
    if (file == NULL) return NULL;
    if (fseek(file, 0, SEEK_END) != 0 || (length = ftell(file)) <= 0 ||
        (uint64_t)length > max_bytes || fseek(file, 0, SEEK_SET) != 0) {
        fclose(file); return NULL;
    }
    data = malloc((size_t)length);
    if (data == NULL) { fclose(file); return NULL; }
    if (fread(data, 1, (size_t)length, file) != (size_t)length || fgetc(file) != EOF) {
        free(data); fclose(file); return NULL;
    }
    fclose(file); *bytes = (size_t)length; return data;
}
static int verify_directory(int argc, char **argv)
{
    struct vf_bundle_policy policy = {{0}, 0, 0};
    struct vf_bundle_manifest parsed;
    struct vf_bundle_blob blobs[VF_BUNDLE_MAX_ENTRIES] = {{0, 0, NULL, 0}};
    uint8_t *manifest = NULL, *signature = NULL, *pk = NULL;
    size_t manifest_bytes = 0, sig_bytes = 0, pk_bytes = 0, bytes;
    uint32_t i, count = 0;
    char path[4096], *end;
    vf_status status = VF_EINVAL;
    if (argc != 6 || strcmp(argv[1], "verify") != 0) return 2;
    policy.expected_target_major = (uint32_t)strtoul(argv[4], &end, 10);
    if (*end != '\0' || (policy.expected_target_major != 26 &&
                          policy.expected_target_major != 27)) goto done;
    policy.minimum_release_epoch = strtoull(argv[5], &end, 10);
    if (*end != '\0' || policy.minimum_release_epoch == 0) goto done;
    pk = read_fixture(argv[3], 32, &pk_bytes);
    if (pk == NULL || pk_bytes != 32) goto done;
    memcpy(policy.trusted_public_key, pk, 32);
    if (snprintf(path, sizeof(path), "%s/manifest.vfb", argv[2]) >= (int)sizeof(path)) goto done;
    manifest = read_fixture(path, VF_BUNDLE_MAX_MANIFEST_BYTES, &manifest_bytes);
    if (snprintf(path, sizeof(path), "%s/manifest.sig", argv[2]) >= (int)sizeof(path)) goto done;
    signature = read_fixture(path, 64, &sig_bytes);
    if (manifest == NULL || signature == NULL) goto done;
    status = vf_bundle_authenticate_manifest(manifest, (uint32_t)manifest_bytes,
        signature, (uint32_t)sig_bytes, &policy, &parsed);
    if (status != VF_OK) goto done;
    count = parsed.entry_count;
    for (i = 0; i < count; ++i) {
        const struct vf_bundle_entry *entry = &parsed.entries[i];
        int length;
        if (entry->role == VF_BUNDLE_ROLE_CONFIG)
            length = snprintf(path, sizeof(path), "%s/config.plist", argv[2]);
        else if (entry->role == VF_BUNDLE_ROLE_CORE)
            length = snprintf(path, sizeof(path), "%s/core.elf", argv[2]);
        else
            length = snprintf(path, sizeof(path), "%s/cell-%u.elf", argv[2], entry->instance);
        if (length < 0 || length >= (int)sizeof(path)) { status = VF_EINVAL; goto done; }
        blobs[i].data = read_fixture(path, (size_t)entry->bytes, &bytes);
        if (blobs[i].data == NULL) { status = VF_BUNDLE_EINTEGRITY; goto done; }
        blobs[i].role = entry->role; blobs[i].instance = entry->instance;
        blobs[i].bytes = bytes;
    }
    status = vf_bundle_verify(manifest, (uint32_t)manifest_bytes, signature,
        (uint32_t)sig_bytes, &policy, blobs, count, &parsed);
done:
    for (i = 0; i < count; ++i) free((void *)blobs[i].data);
    free(pk); free(signature); free(manifest);
    printf("{\"test\":\"vsk-bundle-cross\",\"level\":\"UNIT\",\"passed\":%s,"
        "\"status\":%d,\"authenticated_entries\":%u,\"hardware_verified\":false,"
        "\"boot_authorized\":false}\n", status == VF_OK ? "true" : "false",
        status, status == VF_OK ? parsed.entry_count : 0);
    return status == VF_OK ? 0 : 1;
}

int main(int argc, char **argv)
{
    if (argc != 1) return verify_directory(argc, argv);
    test_primitives();
    test_manifest();
    printf("{\"test\":\"vsk-bundle\",\"level\":\"UNIT\",\"passed\":true,"
        "\"checks\":%u,\"hardware_verified\":false,\"boot_authorized\":false}\n", checks);
    return 0;
}
