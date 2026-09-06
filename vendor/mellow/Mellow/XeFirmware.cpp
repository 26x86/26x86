// Copyright (c) 2026. Local development; repository LICENSE applies.
// Wire layout: Intel Linux xe/abi/uc_fw_abi.h (MIT), pinned source in docs.
#include "XeFirmware.hpp"
namespace MellowXe {
static uint32_t le32(const uint8_t *p) {
    return uint32_t(p[0]) | (uint32_t(p[1]) << 8) | (uint32_t(p[2]) << 16) | (uint32_t(p[3]) << 24);
}
static FirmwareVersion version(uint32_t value) {
    return {uint8_t(value >> 16), uint8_t(value >> 8), uint8_t(value)};
}
FirmwareError parseGuCCss(const uint8_t *data, size_t length, FirmwareInfo &info) {
    info = {};
    if (!data) return FirmwareError::NullInput;
    if (length < 128) return FirmwareError::TruncatedHeader;
    const uint64_t headerDw = le32(data + 4), totalDw = le32(data + 24);
    const uint64_t keyDw = le32(data + 28), modulusDw = le32(data + 32), exponentDw = le32(data + 36);
    // Compute in 64 bits before subtracting; malicious DWORD values cannot wrap.
    if (headerDw != 32 + keyDw + modulusDw + exponentDw || totalDw < headerDw)
        return FirmwareError::HeaderArithmetic;
    const uint64_t ucode = (totalDw - headerDw) * 4, rsa = keyDw * 4;
    if (!ucode || !rsa) return FirmwareError::EmptyPayload;
    const uint64_t required = 128 + ucode + rsa;
    if (required > length) return FirmwareError::TruncatedPayload;
    const auto release = version(le32(data + 64));
    if (release.major != 70 || release.packed() < gucMinimumRelease)
        return FirmwareError::UnsupportedRelease;
    FirmwareInfo parsed {};
    parsed.release = release;
    parsed.submission = version(le32(data + 68));
    parsed.ucodeOffset = 128; parsed.ucodeBytes = ucode;
    parsed.rsaOffset = 128 + ucode; parsed.rsaBytes = rsa; parsed.minimumBytes = required;
    parsed.privateDataBytes = le32(data + 120);
    parsed.moduleVendor = le32(data + 16); parsed.headerVersion = le32(data + 8);
    const auto headerInfo = le32(data + 116), kernelInfo = le32(data + 124);
    parsed.securityInfoValid = (headerInfo & 0x80000000U) != 0;
    parsed.securityVersion = uint8_t(headerInfo);
    parsed.deviceInfoValid = (kernelInfo & 1U) != 0;
    parsed.declaredDeviceId = uint16_t(kernelInfo >> 16);
    parsed.buildType = uint8_t((kernelInfo >> 2) & 3U);
    parsed.belowRecommended = release.packed() < gucRecommendedRelease;
    // CSS permits truncated modulus/exponent: header, uCode, RSA must exist.
    // The loader must still authenticate with the actual device before use.
    info = parsed;
    return FirmwareError::None;
}
const char *firmwareErrorName(FirmwareError e) {
    switch (e) {
    case FirmwareError::None: return "parsed-not-authenticated";
    case FirmwareError::NullInput: return "null-input";
    case FirmwareError::TruncatedHeader: return "truncated-header";
    case FirmwareError::HeaderArithmetic: return "invalid-size-arithmetic";
    case FirmwareError::EmptyPayload: return "empty-ucode-or-rsa";
    case FirmwareError::TruncatedPayload: return "truncated-payload";
    case FirmwareError::UnsupportedRelease: return "unsupported-release";
    }
    return "invalid-error";
}
}
