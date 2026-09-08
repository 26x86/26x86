/* Independently authored public APFS layout and checksum cross-check. */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

typedef uint64_t oid_t;
typedef uint64_t xid_t;
typedef int64_t paddr_t;
typedef unsigned char uuid_t[16];
typedef struct { uint8_t o_cksum[8]; oid_t o_oid; xid_t o_xid;
    uint32_t o_type; uint32_t o_subtype; } obj_phys_t;
typedef struct { paddr_t pr_start_paddr; uint64_t pr_block_count; } prange_t;
typedef struct {
    obj_phys_t nx_o;
    uint32_t nx_magic, nx_block_size;
    uint64_t nx_block_count, nx_features, nx_readonly_compatible_features;
    uint64_t nx_incompatible_features;
    uuid_t nx_uuid;
    oid_t nx_next_oid;
    xid_t nx_next_xid;
    uint32_t nx_xp_desc_blocks, nx_xp_data_blocks;
    paddr_t nx_xp_desc_base, nx_xp_data_base;
    uint32_t nx_xp_desc_next, nx_xp_data_next, nx_xp_desc_index, nx_xp_desc_len;
    uint32_t nx_xp_data_index, nx_xp_data_len;
    oid_t nx_spaceman_oid, nx_omap_oid, nx_reaper_oid;
    uint32_t nx_test_type, nx_max_file_systems;
    oid_t nx_fs_oid[100];
    uint64_t nx_counters[32];
    prange_t nx_blocked_out_prange;
    oid_t nx_evict_mapping_tree_oid;
    uint64_t nx_flags;
    paddr_t nx_efi_jumpstart;
    uuid_t nx_fusion_uuid;
    prange_t nx_keylocker;
    uint64_t nx_ephemeral_info[4];
    oid_t nx_test_oid, nx_fusion_mt_oid, nx_fusion_wbc_oid;
    prange_t nx_fusion_wbc;
    uint64_t nx_newest_mounted_version;
    prange_t nx_mkb_locker;
} nx_superblock_t;
typedef struct {
    obj_phys_t nej_o;
    uint32_t nej_magic, nej_version, nej_efi_file_len, nej_num_extents;
    uint64_t nej_reserved[16];
    prange_t nej_rec_extents[];
} nx_efi_jumpstart_t;

#define OFFSET(T, F) printf("\"" #F "\":%zu,\n", offsetof(T, F))

/* This positional-weight calculation is independent of the Rust rolling sum. */
static void checksum_case(size_t size, unsigned pattern, int last) {
    const uint64_t m = UINT32_MAX;
    const size_t n = (size - 8) / 4;
    uint64_t a = 0, b = 0;
    for (size_t i = 0; i < n; ++i) {
        uint32_t word = 0;
        if (pattern == 1) word = (uint32_t)(i * UINT64_C(0x9e3779b1) + 0xfedcba98);
        if (pattern == 2) word = UINT32_MAX;
        a = (a + word) % m;
        b = (b + (uint64_t)(n - i) * word) % m;
    }
    const uint64_t lo = m - ((a + b) % m);
    const uint64_t hi = m - ((a + lo) % m);
    const uint64_t r1 = (a + lo + hi) % m;
    const uint64_t r2 = (b + 2 * a + 2 * lo + hi) % m;
    printf("{\"size\":%zu,\"pattern\":%u,\"checksum\":\"%016llx\",\"residue\":[%llu,%llu]}%s\n",
        size, pattern, (unsigned long long)((hi << 32) | lo),
        (unsigned long long)r1, (unsigned long long)r2, last ? "" : ",");
}

int main(void) {
    _Static_assert(sizeof(paddr_t) == 8 && (paddr_t)-1 < 0, "signed paddr");
    _Static_assert(sizeof(obj_phys_t) == 32, "object header");
    _Static_assert(sizeof(prange_t) == 16, "range");
    _Static_assert(sizeof(nx_superblock_t) == 1408, "superblock");
    _Static_assert(sizeof(nx_efi_jumpstart_t) == 176, "jumpstart prefix");
    printf("{\"sizes\":{\"obj_phys\":%zu,\"prange\":%zu,\"nx_superblock\":%zu,\"nx_efi_jumpstart\":%zu},\n\"offsets\":{\n",
        sizeof(obj_phys_t), sizeof(prange_t), sizeof(nx_superblock_t), sizeof(nx_efi_jumpstart_t));
    OFFSET(obj_phys_t, o_oid); OFFSET(obj_phys_t, o_xid);
    OFFSET(obj_phys_t, o_type); OFFSET(obj_phys_t, o_subtype);
    OFFSET(nx_superblock_t, nx_magic); OFFSET(nx_superblock_t, nx_block_size);
    OFFSET(nx_superblock_t, nx_block_count); OFFSET(nx_superblock_t, nx_features);
    OFFSET(nx_superblock_t, nx_readonly_compatible_features);
    OFFSET(nx_superblock_t, nx_incompatible_features); OFFSET(nx_superblock_t, nx_uuid);
    OFFSET(nx_superblock_t, nx_flags); OFFSET(nx_superblock_t, nx_efi_jumpstart);
    OFFSET(nx_superblock_t, nx_fusion_uuid); OFFSET(nx_superblock_t, nx_fusion_mt_oid);
    OFFSET(nx_superblock_t, nx_fusion_wbc_oid); OFFSET(nx_superblock_t, nx_fusion_wbc);
    OFFSET(nx_efi_jumpstart_t, nej_magic); OFFSET(nx_efi_jumpstart_t, nej_version);
    OFFSET(nx_efi_jumpstart_t, nej_efi_file_len); OFFSET(nx_efi_jumpstart_t, nej_num_extents);
    OFFSET(nx_efi_jumpstart_t, nej_reserved); OFFSET(nx_efi_jumpstart_t, nej_rec_extents);
    printf("\"pr_block_count\":%zu},\n\"checksums\":[\n", offsetof(prange_t, pr_block_count));
    checksum_case(4096, 0, 0); checksum_case(4096, 1, 0);
    checksum_case(65536, 1, 0); checksum_case(4096, 2, 1);
    puts("]}");
    return 0;
}
