/* SPDX-License-Identifier: BSD-4-Clause; repository LICENSE.txt applies. */
#ifndef VF_EFI_HANDOFF_H
#define VF_EFI_HANDOFF_H

#include <stddef.h>
#include <stdint.h>

#include "vf_abi.h"
#include "vf_boot.h"

/* UEFI status values used by the small, callback-based handoff adapter.  The
 * adapter never casts a host status into a vf_status or treats a fixture
 * receipt as an EBS result. */
#define VF_EFI_SUCCESS UINT64_C(0)
#define VF_EFI_INVALID_PARAMETER (UINT64_C(1) << 63 | UINT64_C(2))
#define VF_EFI_BUFFER_TOO_SMALL (UINT64_C(1) << 63 | UINT64_C(5))

#define VF_EFI_MAP_MIN_BYTES UINT64_C(40)
#define VF_EFI_MAP_MAX_BYTES (UINT64_C(1024) * 1024)
#define VF_EFI_MAP_MAX_RETRIES 4u

typedef uint64_t (*vf_efi_get_memory_map_fn)(uint64_t *map_bytes, void *map,
                                              uint64_t *map_key,
                                              uint64_t *descriptor_bytes,
                                              uint32_t *descriptor_version);
typedef uint64_t (*vf_efi_exit_boot_services_fn)(void *image_handle,
                                                 uint64_t map_key);

/* Caller-owned storage and the exact final map returned by firmware.  The
 * storage must remain pinned until a future root ownership transfer; this
 * helper does not allocate, copy to an untrusted address, or retain a pointer
 * to firmware-owned memory. */
struct vf_efi_map_snapshot {
    void *storage;
    uint64_t capacity;
    uint64_t bytes;
    uint64_t map_key;
    uint64_t descriptor_bytes;
    uint32_t descriptor_version;
    uint32_t capture_attempts;
};

/* Capture and validate one map into caller-owned storage.  A buffer-too-small
 * response is VF_ERANGE; callers choose a bounded larger buffer and retry.
 * Output is zeroed on every non-alias failure.  Success proves only map shape and
 * arithmetic consistency, not ownership, DMA quiescence, or hardware trust. */
vf_status vf_efi_capture_memory_map(vf_efi_get_memory_map_fn get_map,
                                    void *storage, uint64_t capacity,
                                    struct vf_efi_map_snapshot *out);

/* Call ExitBootServices using a freshly captured map.  EFI's stale-key error
 * is retried up to max_attempts without poisoning the boot state.  A success
 * records EBS exactly once in the caller's state; no Boot Services call is
 * made afterwards by this function.  The state must already be at
 * VF_BOOT_EXIT_BOOT_SERVICES and must not have exited EBS. */
vf_status vf_efi_exit_boot_services(vf_efi_get_memory_map_fn get_map,
                                    vf_efi_exit_boot_services_fn exit_bs,
                                    void *image_handle, void *storage,
                                    uint64_t capacity,
                                    uint32_t max_attempts,
                                    struct vf_efi_map_snapshot *out,
                                    struct vf_boot_state *state);

#endif
