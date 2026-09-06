/* 26x86 first-party code; repository LICENSE.txt applies. */
#ifndef VF_DMAR_H
#define VF_DMAR_H
#include <stddef.h>
#include <stdint.h>
#define VF_DMAR_MAX_UNITS 32u
#define VF_DMAR_MAX_RMRR 64u
#define VF_DMAR_MAX_SCOPES 256u
#define VF_DMAR_MAX_PATH 16u
#define VF_DMAR_MAX_ATSR 32u
enum vf_dmar_error { VF_DMAR_OK, VF_DMAR_FORMAT, VF_DMAR_CHECKSUM,
    VF_DMAR_UNSUPPORTED, VF_DMAR_LIMIT, VF_DMAR_CONFLICT };
struct vf_dmar_range { uint64_t base, bytes; };
struct vf_dmar_scope {
    uint16_t segment, owner_index;
    uint8_t owner_type, type, enumeration_id, start_bus, path_count;
    uint8_t path[VF_DMAR_MAX_PATH][2];
};
struct vf_dmar_unit { uint64_t registers; uint16_t segment; uint8_t include_all; };
struct vf_dmar_rmrr { uint64_t base, limit; uint16_t segment; };
struct vf_dmar_snapshot {
    uint32_t unit_count, rmrr_count, scope_count, atsr_count, rhsa_count;
    uint8_t address_bits, interrupt_remap_reported;
    struct vf_dmar_unit units[VF_DMAR_MAX_UNITS];
    struct vf_dmar_rmrr rmrr[VF_DMAR_MAX_RMRR];
    struct vf_dmar_scope scopes[VF_DMAR_MAX_SCOPES];
};
/* Parse a copied table, never dereference MMIO addresses. Output is zero on
 * failure except invalid input/output aliasing: return FORMAT without writing
 * either buffer. Inputs and output must be disjoint, including protected_ranges.
 * Table advertisement is NOT enabled VT-d/IR or requester isolation.
 * protected_ranges is a root-owned acquisition ledger, not guest input.
 * PCI bridge traversal, ACS/alias groups and live unit capabilities are separate. */
int vf_dmar_parse(const uint8_t *table, size_t bytes,
                  const struct vf_dmar_range *protected_ranges, size_t count,
                  struct vf_dmar_snapshot *out);
#endif
