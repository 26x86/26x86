/* SPDX-License-Identifier: BSD-4-Clause */
#ifndef VENFIRE_HANDOFF_H
#define VENFIRE_HANDOFF_H
#include <stdint.h>
#define VF_HANDOFF_MAGIC UINT64_C(0x3149424146583632)
#define VF_HANDOFF_VERSION 1u
/* OpenCore owns pointed-to storage until StartImage returns. UTF-16 iBoot path;
 * UTF-8 NUL terminated serialized XML dictionaries for the other two pointers.
 * AIC and iBoot are invariant in v1; neither GIC nor UEFI ARM guest is selectable.
 */
typedef struct {
    uint64_t magic;
    uint32_t version, size;
    uint64_t flags, memory_bytes;
    uint32_t cpu_count, target_major;
    uint64_t iboot_path_ptr, smbios_xml_ptr, device_properties_xml_ptr;
} vf_handoff;
_Static_assert(sizeof(vf_handoff)==64,"OpenCore Sandbox ABI v1 size");
#endif
