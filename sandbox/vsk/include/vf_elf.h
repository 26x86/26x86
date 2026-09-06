/* SPDX-License-Identifier: BSD-4-Clause; repository LICENSE.txt applies. */
#ifndef VSK_VF_ELF_H
#define VSK_VF_ELF_H
#include <stddef.h>
#include <stdint.h>
#define VF_ELF_MAX_SEGMENTS 16u
#define VF_ELF_MAX_IMAGE_BYTES (UINT64_C(64)*1024*1024)
#define VF_ELF_READ 4u
#define VF_ELF_WRITE 2u
#define VF_ELF_EXECUTE 1u
enum vf_elf_error { VF_ELF_OK=0, VF_ELF_EARG=-1, VF_ELF_EFORMAT=-2,
    VF_ELF_EUNSUPPORTED=-3, VF_ELF_ERANGE=-4, VF_ELF_EWX=-5,
    VF_ELF_EOVERLAP=-6, VF_ELF_EENTRY=-7, VF_ELF_ELIMIT=-8, VF_ELF_EPLAN=-9 };
struct vf_elf_segment {
    uint64_t file_offset, file_bytes, memory_bytes, virtual_address, image_offset;
    uint32_t flags, reserved;
};
struct vf_elf_plan {
    uint32_t version, segment_count;
    uint64_t file_bytes, image_base, image_bytes, entry_offset, budget_bytes;
    struct vf_elf_segment segments[VF_ELF_MAX_SEGMENTS];
};
/* Static ET_EXEC, EM_X86_64, little endian, 48-bit canonical VA only. No runtime
 * relocations, interpreter, dynamic loader, TLS or executable stack. Limits are
 * an implementation bound, not a claim that the root 4 MiB target is measured.
 * On error out is cleared, except alias misuse preserves both input and output.
 * All file data must be a bounded, immutable root-owned snapshot. */
int vf_elf_make_plan(const void *file,size_t file_bytes,uint64_t max_image_bytes,
                     struct vf_elf_plan *out);
/* Revalidates both file structure and plan before any destination write. Copies
 * segments and zeros the entire image span (including BSS and gaps). Does not
 * allocate, map, set permissions, call firmware, or dereference ELF p_paddr.
 * Caller must authenticate BEFORE calling, keep the input immutable, allocate
 * private RW+NX memory, then seal per-segment pages per plan before entry.
 * Copy success is not signature/hardware verification or boot authorization.
 * Destination, input and plan must be disjoint. Only image_bytes are written.
 * ET_EXEC is not relocated: map the resulting image at image_base for execution.
 */
int vf_elf_copy(const void *file,size_t file_bytes,const struct vf_elf_plan *plan,
                void *destination,size_t destination_bytes);
#endif
