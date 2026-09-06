// Local research modifications, 2026. See the repository LICENSE and NOTICE.
#pragma once
#include <stddef.h>
#include <stdint.h>

namespace MellowPattern {
enum class Status { Invalid, NotFound, Unique, Ambiguous };
struct Match { Status status; size_t offset; };

inline bool validAddressRange(uintptr_t address, size_t length) {
    return address != 0 && length != 0 && length - 1 <= UINTPTR_MAX - address;
}

// The caller supplies a readable mapped image. This helper checks all integer
// extents; it cannot prove that an arbitrary virtual address is mapped.
inline Match findUnique(const uint8_t *image, size_t length,
                        const uint8_t *pattern, const uint8_t *mask, size_t width) {
    if (!image || !pattern || !width || width > length)
        return {Status::Invalid, 0};
    if (mask) {
        bool constrained = false;
        for (size_t i = 0; i < width; ++i) constrained |= mask[i] != 0;
        if (!constrained) return {Status::Invalid, 0};
    }
    Match result {Status::NotFound, 0};
    const size_t last = length - width;
    for (size_t offset = 0;; ++offset) {
        bool equal = true;
        for (size_t i = 0; i < width; ++i) {
            const uint8_t bits = mask ? mask[i] : 0xFF;
            if ((image[offset + i] & bits) != (pattern[i] & bits)) {
                equal = false;
                break;
            }
        }
        if (equal) {
            if (result.status == Status::Unique) return {Status::Ambiguous, 0};
            result = {Status::Unique, offset};
        }
        // Avoid overflow even if a caller describes the largest size_t range.
        if (offset == last) break;
    }
    return result;
}
}
