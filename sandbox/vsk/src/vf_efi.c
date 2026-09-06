/* SPDX-License-Identifier: BSD-4-Clause; repository LICENSE.txt applies. */
#include "vf_efi.h"

static void clear_bytes(void *output, size_t bytes)
{
    volatile uint8_t *p = output;
    while (bytes != 0) {
        *p++ = 0;
        --bytes;
    }
}

static int spans_overlap(const void *left, uint64_t left_bytes,
                         const void *right, uint64_t right_bytes)
{
    uintptr_t a = (uintptr_t)left;
    uintptr_t b = (uintptr_t)right;
    if (left_bytes == 0 || right_bytes == 0)
        return 0;
    if (left_bytes - 1 > UINTPTR_MAX - a ||
        right_bytes - 1 > UINTPTR_MAX - b)
        return 1;
    return a <= b + right_bytes - 1 && b <= a + left_bytes - 1;
}

static vf_status map_failure(struct vf_boot_state *state, vf_status detail)
{
    if (state == NULL)
        return VF_EINVAL;
    /* The map is the firmware-lifetime prerequisite for EBS.  Keep the
     * externally visible state fail-closed even when the detailed vf_status
     * is returned to the caller. */
    (void)vf_boot_fail(state, VF_BOOT_EEBS_UNAVAILABLE);
    return detail == VF_OK ? VF_EBINDING : detail;
}

vf_status vf_efi_capture_memory_map(vf_efi_get_memory_map_fn get_map,
                                    void *storage, uint64_t capacity,
                                    struct vf_efi_map_snapshot *out)
{
    uint64_t bytes, key = 0, descriptor_bytes = 0;
    uint32_t descriptor_version = 0;
    uint64_t status;
    vf_status shape;

    if (out == NULL)
        return VF_EINVAL;
    if (get_map == NULL || storage == NULL ||
        capacity < VF_EFI_MAP_MIN_BYTES || capacity > VF_EFI_MAP_MAX_BYTES)
        return VF_EINVAL;
    if (spans_overlap(storage, capacity, out, sizeof(*out)))
        return VF_EINVAL;
    clear_bytes(out, sizeof(*out));

    bytes = capacity;
    status = get_map(&bytes, storage, &key, &descriptor_bytes,
                     &descriptor_version);
    if (status != VF_EFI_SUCCESS)
        return status == VF_EFI_BUFFER_TOO_SMALL ? VF_ERANGE : VF_EBINDING;
    if (bytes == 0 || bytes > capacity || bytes > SIZE_MAX ||
        descriptor_bytes < VF_EFI_MAP_MIN_BYTES || descriptor_bytes > 256 ||
        (descriptor_bytes & 7u) != 0 || descriptor_version !=
        VF_BOOT_EFI_DESCRIPTOR_VERSION || bytes % descriptor_bytes != 0 ||
        bytes / descriptor_bytes > VF_BOOT_MAX_DESCRIPTORS)
        return VF_EABI;

    shape = vf_boot_validate_memory_map(storage, (size_t)bytes,
                                        (uint32_t)descriptor_bytes,
                                        descriptor_version);
    if (shape != VF_BOOT_OK)
        return VF_EABI;

    out->storage = storage;
    out->capacity = capacity;
    out->bytes = bytes;
    out->map_key = key;
    out->descriptor_bytes = descriptor_bytes;
    out->descriptor_version = descriptor_version;
    out->capture_attempts = 1;
    return VF_OK;
}

vf_status vf_efi_exit_boot_services(vf_efi_get_memory_map_fn get_map,
                                    vf_efi_exit_boot_services_fn exit_bs,
                                    void *image_handle, void *storage,
                                    uint64_t capacity,
                                    uint32_t max_attempts,
                                    struct vf_efi_map_snapshot *out,
                                    struct vf_boot_state *state)
{
    struct vf_efi_map_snapshot candidate;
    vf_status captured;

    if (out == NULL || state == NULL || get_map == NULL || exit_bs == NULL ||
        image_handle == NULL || storage == NULL || max_attempts == 0 ||
        max_attempts > VF_EFI_MAP_MAX_RETRIES)
        return VF_EINVAL;
    if (spans_overlap(storage, capacity, out, sizeof(*out)) ||
        spans_overlap(storage, capacity, state, sizeof(*state)))
        return VF_EINVAL;
    clear_bytes(out, sizeof(*out));
    if (state->stage != VF_BOOT_EXIT_BOOT_SERVICES || state->ebs_exited ||
        state->error != 0)
        return VF_EBUSY;

    for (uint32_t attempt = 0; attempt < max_attempts; ++attempt) {
        uint64_t status;
        captured = vf_efi_capture_memory_map(get_map, storage, capacity,
                                             &candidate);
        if (captured != VF_OK)
            return map_failure(state, captured);
        candidate.capture_attempts = attempt + 1;
        status = exit_bs(image_handle, candidate.map_key);
        if (status == VF_EFI_SUCCESS) {
            /* The state update is local and does not call firmware.  If this
             * invariant fails, the caller must stop; it must not attempt a
             * second EBS call after firmware ownership has ended. */
            if (vf_boot_record_ebs_result(state, 0) != VF_BOOT_OK)
                return map_failure(state, VF_EBINDING);
            *out = candidate;
            return VF_OK;
        }
        if (status != VF_EFI_INVALID_PARAMETER || attempt + 1 == max_attempts) {
            (void)vf_boot_record_ebs_result(state, status);
            return VF_EBINDING;
        }
        /* UEFI permits the map to change between GetMemoryMap and
         * ExitBootServices.  Re-enter the loop and capture the new key. */
    }
    return map_failure(state, VF_EBINDING);
}
