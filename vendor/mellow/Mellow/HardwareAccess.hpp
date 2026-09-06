// Copyright (c) 2026. Local Mellow 7D41 development changes.
// Distributed under the repository's LICENSE.
#pragma once

#include <stdint.h>

// OS-independent decisions shared by the real MMIO/PCI path and host tests.
// Validating a mapping does not establish a register's power/forcewake state.
namespace MellowHardware {

constexpr bool containsAligned(uint64_t length, uint64_t offset,
                               uint64_t width, uint64_t alignment) {
    return width != 0 && alignment != 0 && offset % alignment == 0 &&
           width <= length && offset <= length - width;
}

inline bool read32(volatile uint32_t *base, uint64_t length,
                   uint64_t byteOffset, uint32_t &value) {
    if (!base || !containsAligned(length, byteOffset, 4, 4)) return false;
    value = base[byteOffset / 4];
    return true;
}

inline bool write32(volatile uint32_t *base, uint64_t length,
                    uint64_t byteOffset, uint32_t value) {
    if (!base || !containsAligned(length, byteOffset, 4, 4)) return false;
    base[byteOffset / 4] = value;
    return true;
}

// IOPCIAddressSpace: BDF occupies bits 23:8; extended register page bits 27:24.
// Only the admitted device's conventional config page may be spoofed.
constexpr bool isDeviceConfigSpace(uint32_t requested, uint32_t deviceBdf) {
    return (requested & 0x0FFFFF00U) == (deviceBdf & 0x00FFFF00U);
}

constexpr bool validSpoofId(uint32_t device) {
    return device != 0 && device < 0xFFFFU;
}

// Apple's configRead16/32 ignore the low 1/2 offset bits respectively.
// Preserve failed/absent-device reads and values from any other register.
inline uint16_t spoofConfig16(uint32_t space, uint32_t deviceBdf, uint8_t offset,
                              uint16_t original, uint16_t physicalId,
                              uint32_t spoofId) {
    if (!isDeviceConfigSpace(space, deviceBdf) || (offset & ~1U) != 2U ||
        original != physicalId || !validSpoofId(spoofId)) return original;
    return static_cast<uint16_t>(spoofId);
}

inline uint32_t spoofConfig32(uint32_t space, uint32_t deviceBdf, uint8_t offset,
                              uint32_t original, uint16_t physicalId,
                              uint32_t spoofId) {
    if (!isDeviceConfigSpace(space, deviceBdf) || (offset & ~3U) != 0U ||
        (original & 0xFFFFU) != 0x8086U || (original >> 16) != physicalId ||
        !validSpoofId(spoofId)) return original;
    return (original & 0xFFFFU) | (spoofId << 16);
}

constexpr uint32_t graphicsControl = 0x108040U;

// Xe-LPG total DSM reservation, before WOPCM/GSC reservations. This is NOT
// allocator-usable size. Intel's xe_ttm_stolen_mgr requires GGMS=3 and these
// GMS encodings; unsupported/absent-device values must not invent memory.
inline bool decodeDsmReservation(uint32_t ggc, uint32_t &bytes) {
    if (ggc == 0xFFFFFFFFU || (ggc & 0xC0U) != 0xC0U) return false;
    const uint32_t gms = (ggc >> 8) & 0xFFU;
    uint32_t mib;
    if (gms <= 4U) mib = gms * 32U;
    else if (gms >= 0xF0U && gms <= 0xFEU) mib = (gms - 0xF0U + 1U) * 4U;
    else return false;
    bytes = mib * 1024U * 1024U;
    return true;
}

} // namespace MellowHardware
