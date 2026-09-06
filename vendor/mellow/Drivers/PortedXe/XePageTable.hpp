// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Mellow contributors. See LICENSE.MIT.
#pragma once
#include <stddef.h>
#include <stdint.h>

namespace Mellow { namespace PortedXe {

enum class Status : uint8_t {
    Ok, InvalidAddress, InvalidPat, InvalidLevel, InvalidArgument,
    Busy, PinFailed, IoFailure, NotBound
};

// Xe-LPG encoding only. addressBits is the adapter's established DMA width,
// capped by upstream's 52-bit PTE address field. No PAT register programming,
// cache-mode selection, device detection, or allocation occurs here.
// Output is unchanged on failure. DMA addresses must already be pinned/mapped.
Status encodeGgtt(uint64_t dma, uint16_t pat, bool devmem,
                  uint8_t addressBits, uint64_t &out);
Status encodePpgtt(uint64_t dma, uint16_t pat, uint32_t level, bool devmem,
                   uint8_t addressBits, uint64_t &out, bool writable = true);
Status encodePde(uint64_t dma, uint16_t pat, uint8_t addressBits, uint64_t &out);

struct DmaSegment { uint64_t address; uint64_t length; };
struct GgttIo {
    void *context {};
    // Retain pins and DMA/IOMMU mapping for the caller's lease. A failed retain
    // must leave no ownership. release is called only after clear+invalidation.
    bool (*retain)(void *, uint64_t lease) {};
    void (*release)(void *, uint64_t lease) {};
    // Address is the GGTT virtual page address, NOT an MMIO register offset.
    // Adapter resolves the actual GSM mapping and required write workaround.
    bool (*writePte)(void *, uint64_t ggttAddress, uint64_t pte) {};
    // Must finish posting/order of all writes and all relevant GT invalidations.
    // Returning true without real completion is invalid on a hardware adapter.
    bool (*barrierAndInvalidate)(void *) {};
};
enum class MappingState : uint8_t { Empty, Bound, Faulted };

// Source-derived GGTT system-SG mapping and clear loops with explicit ownership.
// This class admits only ranges below 4 GiB. It does not allocate a GGTT range.
// The caller reserves an exclusive
// range and serializes all access. No scratch page is used: unmap writes zero.
// Real DRM/TTM, IOKit, MMIO and GuC adapters are outside this portable subsystem.
class GgttMapping {
public:
    GgttMapping() = default;
    GgttMapping(const GgttMapping &) = delete;
    GgttMapping &operator=(const GgttMapping &) = delete;
    // Must successfully unmap before destroying. Faulted mappings retain pins
    // because partial writes may still be visible to the GPU; caller must retry
    // unmap or implement a separately verified full device-reset teardown.
    Status bind(const GgttIo &, uint64_t ggttStart, uint64_t reservedBytes,
                uint64_t lease, const DmaSegment *, size_t segmentCount,
                uint16_t pat, uint8_t addressBits);
    Status unmap();
    MappingState state() const { return state_; }
    uint64_t mappedBytes() const { return bytes_; }
private:
    GgttIo io_ {};
    MappingState state_ {MappingState::Empty};
    uint64_t start_ {}, bytes_ {}, lease_ {};
};

} } // namespace Mellow::PortedXe
