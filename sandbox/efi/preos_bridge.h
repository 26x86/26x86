/* SPDX-License-Identifier: BSD-4-Clause; C-owned bridge behind preos_abi.h. */
#ifndef VENFIRE_PREOS_BRIDGE_H
#define VENFIRE_PREOS_BRIDGE_H

#include "jit.h"
#include "preos_abi.h"

#define VF_EFI_EXECUTION_MAGIC UINT64_C(0x5646455845433031) /* "VFEXEC01" */

/* This structure never crosses into Rust by value.  Rust sees it only as an
 * opaque pointer and C validates it before touching the internal JIT state. */
typedef struct {
    uint64_t magic;
    vf_code *code;
    vf_protect protect;
    void *protection_opaque;
    const uint8_t *guest_bytes;
    uint64_t guest_size;
    uint8_t *guest_ram;
    uint64_t guest_ram_size;
    vf_cpu *cpu;
    uint64_t initial_x2;
    uint32_t machine_profile;
    uint32_t reserved;
} vf_efi_execution;

#endif
