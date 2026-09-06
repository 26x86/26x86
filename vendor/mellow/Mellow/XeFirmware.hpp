// Copyright (c) 2026. Local development; repository LICENSE applies.
#pragma once
#include <stddef.h>
#include <stdint.h>

namespace MellowXe {
enum class FirmwareError : uint8_t {
    None, NullInput, TruncatedHeader, HeaderArithmetic, EmptyPayload,
    TruncatedPayload, UnsupportedRelease
};
struct FirmwareVersion {
    uint8_t major {}, minor {}, patch {};
    uint32_t packed() const { return (uint32_t(major) << 16) | (uint32_t(minor) << 8) | patch; }
};
// Metadata only: parsing is NOT RSA validation, firmware upload or authentication.
struct FirmwareInfo {
    FirmwareVersion release {}, submission {};
    uint64_t ucodeOffset {}, ucodeBytes {}, rsaOffset {}, rsaBytes {}, minimumBytes {};
    uint32_t privateDataBytes {}, moduleVendor {}, headerVersion {};
    uint16_t declaredDeviceId {};
    uint8_t buildType {}, securityVersion {};
    bool deviceInfoValid {}, securityInfoValid {}, belowRecommended {};
};
constexpr uint16_t targetDeviceId = 0x7D41;
constexpr const char *gucFirmwarePath = "i915/mtl_guc_70.bin";
constexpr uint32_t gucMinimumRelease = 0x461D02;    // Linux Xe: 70.29.2
constexpr uint32_t gucRecommendedRelease = 0x463500; // pinned Linux: 70.53.0
FirmwareError parseGuCCss(const uint8_t *data, size_t length, FirmwareInfo &info);
const char *firmwareErrorName(FirmwareError error);
}
