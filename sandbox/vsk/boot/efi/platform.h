/* SPDX-License-Identifier: BSD-4-Clause; repository LICENSE.txt applies. */
#ifndef VSK_EFI_PLATFORM_H
#define VSK_EFI_PLATFORM_H
#include "../../../efi/uefi.h"
#include "../../include/vf_dmar.h"
#include "../../include/vf_efi.h"
struct vf_efi_probe {
    uint32_t leaf1_ecx, leaf1_edx, extended_edx;
    uint32_t map_descriptors, dmar_bytes, rsdp_revision;
    uint64_t memory_map_key;
    uint32_t intel_vendor, hypervisor_reported, vmx_msr_sampled;
    uint64_t feature_control, vmx_basic, ept_vpid_cap;
    int32_t memory_map_status, acpi_status, dmar_status;
    struct vf_dmar_snapshot dmar;
};
/* BSP-only measurement. No VMXON, VT-d writes, platform approval or EBS. */
EFI_STATUS vf_efi_measure(EFI_SYSTEM_TABLE *, struct vf_efi_probe *);
#endif
