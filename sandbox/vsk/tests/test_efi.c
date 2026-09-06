/* SPDX-License-Identifier: BSD-4-Clause; synthetic UEFI callbacks only. */
#include "vf_efi.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned checks;
#define CHECK(expr) do { ++checks; if (!(expr)) { \
    fprintf(stderr, "test_efi:%d: %s\n", __LINE__, #expr); exit(1); \
} } while (0)

static uint8_t map_bytes[96];
static uint64_t map_key = 0x100;
static unsigned get_calls;
static unsigned exit_calls;
static uint64_t exit_statuses[4];
static unsigned exit_status_count;

static void put32(uint8_t *p, uint32_t value)
{
    for (unsigned i = 0; i < 4; ++i)
        p[i] = (uint8_t)(value >> (i * 8));
}

static void put64(uint8_t *p, uint64_t value)
{
    for (unsigned i = 0; i < 8; ++i)
        p[i] = (uint8_t)(value >> (i * 8));
}

static void make_map(void)
{
    memset(map_bytes, 0, sizeof(map_bytes));
    put32(map_bytes, 2);             /* EfiLoaderData */
    put64(map_bytes + 8, 0x100000);
    put64(map_bytes + 24, 1);
    put64(map_bytes + 32, 8);
    put32(map_bytes + 48, 2);
    put64(map_bytes + 56, 0x101000);
    put64(map_bytes + 72, 1);
    put64(map_bytes + 80, 8);
}

static uint64_t fake_get_map(uint64_t *bytes, void *storage, uint64_t *key,
                             uint64_t *descriptor_bytes,
                             uint32_t *descriptor_version)
{
    ++get_calls;
    if (!bytes || !key || !descriptor_bytes || !descriptor_version)
        return VF_EFI_INVALID_PARAMETER;
    *descriptor_bytes = 48;
    *descriptor_version = VF_BOOT_EFI_DESCRIPTOR_VERSION;
    if (!storage || *bytes < sizeof(map_bytes)) {
        *bytes = sizeof(map_bytes);
        return VF_EFI_BUFFER_TOO_SMALL;
    }
    memcpy(storage, map_bytes, sizeof(map_bytes));
    *bytes = sizeof(map_bytes);
    *key = map_key;
    return VF_EFI_SUCCESS;
}

static uint64_t fake_exit(void *image_handle, uint64_t key)
{
    CHECK(image_handle != NULL);
    ++exit_calls;
    CHECK(key == map_key);
    if (exit_calls <= exit_status_count)
        return exit_statuses[exit_calls - 1];
    return VF_EFI_SUCCESS;
}

static void reset_callbacks(void)
{
    get_calls = exit_calls = exit_status_count = 0;
    memset(exit_statuses, 0, sizeof(exit_statuses));
    map_key = 0x100;
    make_map();
}

int main(void)
{
    uint8_t storage[128], small[48];
    struct vf_efi_map_snapshot snapshot;
    struct vf_boot_state state;
    int result;

    reset_callbacks();
    result = vf_efi_capture_memory_map(fake_get_map, storage, sizeof(storage),
                                       &snapshot);
    CHECK(result == VF_OK);
    CHECK(snapshot.storage == storage && snapshot.bytes == sizeof(map_bytes));
    CHECK(snapshot.capacity == sizeof(storage) && snapshot.map_key == 0x100);
    CHECK(snapshot.descriptor_bytes == 48 && snapshot.capture_attempts == 1);
    CHECK(get_calls == 1);

    reset_callbacks();
    result = vf_efi_capture_memory_map(fake_get_map, storage, sizeof(storage),
                                       (struct vf_efi_map_snapshot *)(void *)storage);
    CHECK(result == VF_EINVAL && get_calls == 0);

    reset_callbacks();
    memset(&snapshot, 0xff, sizeof(snapshot));
    result = vf_efi_capture_memory_map(fake_get_map, small, sizeof(small),
                                       &snapshot);
    CHECK(result == VF_ERANGE);
    CHECK(snapshot.storage == NULL && snapshot.bytes == 0 && get_calls == 1);

    reset_callbacks();
    map_bytes[48 + 8] = 1; /* Unaligned second descriptor base. */
    result = vf_efi_capture_memory_map(fake_get_map, storage, sizeof(storage),
                                       &snapshot);
    CHECK(result == VF_EABI);
    CHECK(snapshot.storage == NULL && snapshot.bytes == 0);

    reset_callbacks();
    vf_boot_init(&state);
    state.stage = VF_BOOT_EXIT_BOOT_SERVICES;
    exit_status_count = 2;
    exit_statuses[0] = VF_EFI_INVALID_PARAMETER;
    exit_statuses[1] = VF_EFI_SUCCESS;
    result = vf_efi_exit_boot_services(fake_get_map, fake_exit, (void *)1,
                                       storage, sizeof(storage), 3, &snapshot,
                                       &state);
    CHECK(result == VF_OK);
    CHECK(state.ebs_exited == 1 && state.stage == VF_BOOT_EXIT_BOOT_SERVICES);
    CHECK(exit_calls == 2 && get_calls == 2 && snapshot.capture_attempts == 2);
    CHECK(snapshot.map_key == 0x100);
    CHECK(vf_boot_record_ebs_result(&state, 0) == VF_BOOT_EFIRMWARE_LIFETIME);
    CHECK(exit_calls == 2);

    reset_callbacks();
    vf_boot_init(&state);
    state.stage = VF_BOOT_EXIT_BOOT_SERVICES;
    exit_status_count = 4;
    for (unsigned i = 0; i < 4; ++i)
        exit_statuses[i] = VF_EFI_INVALID_PARAMETER;
    result = vf_efi_exit_boot_services(fake_get_map, fake_exit, (void *)1,
                                       storage, sizeof(storage), 2, &snapshot,
                                       &state);
    CHECK(result == VF_EBINDING);
    CHECK(state.stage == VF_BOOT_FAILED && state.ebs_exited == 0);
    CHECK(exit_calls == 2 && get_calls == 2 && snapshot.bytes == 0);

    reset_callbacks();
    vf_boot_init(&state);
    result = vf_efi_exit_boot_services(fake_get_map, fake_exit, (void *)1,
                                       storage, sizeof(storage), 1, &snapshot,
                                       &state);
    CHECK(result == VF_EBUSY && exit_calls == 0 && get_calls == 0);

    printf("{\"test\":\"efi-handoff\",\"level\":\"UNIT\","
           "\"passed\":true,\"checks\":%u,\"hardware_verified\":false,"
           "\"exit_boot_services_called\":false}\n", checks);
    return 0;
}
