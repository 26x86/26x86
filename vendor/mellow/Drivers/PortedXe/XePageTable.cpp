// SPDX-License-Identifier: MIT
/*
 * Copyright © 2021, 2024 Intel Corporation
 * Copyright (c) 2026 Mellow contributors
 * See LICENSE.MIT and provenance.json for exact upstream source and boundaries.
 */
#include "XePageTable.hpp"

namespace Mellow { namespace PortedXe {
namespace {
using u64 = uint64_t;
using u32 = uint32_t;
using u16 = uint16_t;
#define BIT(n) (uint64_t(1) << (n))
#define BIT_ULL(n) BIT(n)
#define GENMASK_ULL(high, low) ((~uint64_t(0) >> (63 - (high))) & (~uint64_t(0) << (low)))
#include "upstream/drivers/gpu/drm/xe/regs/xe_gtt_defs.h"
constexpr u32 MAX_HUGEPTE_LEVEL = 2;

// Private source-compatibility values, not fake IOKit devices or DRM objects.
// They supply exactly the BO properties read by the retained upstream helpers.
struct xe_device {};
struct xe_bo { xe_device *device; bool vram; bool stolenDevmem; };
bool xe_bo_is_vram(const xe_bo *bo) { return bo->vram; }
bool xe_bo_is_stolen_devmem(const xe_bo *bo) { return bo->stolenDevmem; }
xe_device *xe_bo_device(xe_bo *bo) { return bo->device; }
#define xe_assert(device, condition) do { (void)(device); if (!(condition)) __builtin_trap(); } while (false)
#define XE_WARN_ON(condition) do { if (condition) __builtin_trap(); } while (false)
#if defined(__GNUC__) || defined(__clang__)
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#endif
#include "XePteAlgorithms.inc"
#if defined(__GNUC__) || defined(__clang__)
#pragma GCC diagnostic pop
#endif
#undef xe_assert
#undef XE_WARN_ON

bool validAddress(uint64_t address, uint8_t bits, uint32_t shift) {
    if (bits < shift || bits > 52) return false;
    return (address & ((uint64_t(1) << shift) - 1)) == 0 &&
           (address >> bits) == 0;
}
constexpr uint64_t PageSize = 4096;
} // namespace

Status encodeGgtt(uint64_t dma, uint16_t pat, bool devmem,
                  uint8_t addressBits, uint64_t &out) {
    if (!validAddress(dma, addressBits, 12)) return Status::InvalidAddress;
    if (pat > 3) return Status::InvalidPat;
    xe_device device;
    xe_bo bo {&device, devmem, false};
    out = dma | xelpg_ggtt_pte_flags(&bo, pat);
    return Status::Ok;
}

Status encodePpgtt(uint64_t dma, uint16_t pat, uint32_t level, bool devmem,
                   uint8_t addressBits, uint64_t &out, bool writable) {
    if (level > 2) return Status::InvalidLevel;
    if (!validAddress(dma, addressBits, 12 + 9 * level)) return Status::InvalidAddress;
    // Xe-LPG has PAT[3:0]; upstream also handles Xe2 PAT4 in the same helper,
    // but this boundary deliberately rejects Xe2 indices on the Xe-LPG path.
    if (pat > 15) return Status::InvalidPat;
    xe_device device;
    out = xelp_pte_encode_addr(&device, dma, pat, level, devmem, 0);
    // xelp_pte_encode_addr always grants RW. The separate upstream
    // xelp_pte_encode_vma policy (xe_vm.c:1485-1488) grants RW only for writable
    // VMAs; apply that exact bit policy here without modifying either source.
    if (!writable) out &= ~XE_PAGE_RW;
    return Status::Ok;
}

Status encodePde(uint64_t dma, uint16_t pat, uint8_t addressBits, uint64_t &out) {
    if (!validAddress(dma, addressBits, 12)) return Status::InvalidAddress;
    if (pat > 3) return Status::InvalidPat;
    out = dma | XE_PAGE_PRESENT | XE_PAGE_RW | pde_encode_pat_index(pat);
    return Status::Ok;
}

Status GgttMapping::bind(const GgttIo &io, uint64_t start, uint64_t reservedBytes,
                         uint64_t lease, const DmaSegment *segments, size_t count,
                         uint16_t pat, uint8_t addressBits) {
    if (state_ != MappingState::Empty) return Status::Busy;
    if (!io.retain || !io.release || !io.writePte || !io.barrierAndInvalidate ||
        !lease || !segments || !count || count > 65536 || !reservedBytes ||
        (start & (PageSize - 1)) || (reservedBytes & (PageSize - 1)) ||
        reservedBytes > (uint64_t(1) << 32) ||
        start > (uint64_t(1) << 32) - reservedBytes) return Status::InvalidArgument;
    // Validate the complete SG range before acquiring ownership or writing PTEs.
    uint64_t total = 0;
    for (size_t i = 0; i < count; ++i) {
        const auto &segment = segments[i];
        if (!segment.length || (segment.length & (PageSize - 1)) ||
            segment.address > UINT64_MAX - (segment.length - PageSize) ||
            total > reservedBytes || segment.length > reservedBytes - total)
            return Status::InvalidAddress;
        uint64_t temporary;
        auto result = encodeGgtt(segment.address, pat, false, addressBits, temporary);
        if (result != Status::Ok) return result;
        result = encodeGgtt(segment.address + segment.length - PageSize, pat, false, addressBits, temporary);
        if (result != Status::Ok) return result;
        total += segment.length;
    }
    if (!io.retain(io.context, lease)) return Status::PinFailed;
    io_ = io;
    start_ = start;
    bytes_ = total;
    lease_ = lease;
    state_ = MappingState::Faulted; // Any partial update keeps DMA ownership.
    uint64_t address = start;
    // Port of xe_ggtt_map_bo's system-memory scatter/gather branch: one PTE per
    // 4K DMA page, in GGTT address order, regardless of physical contiguity.
    for (size_t i = 0; i < count; ++i) {
        for (uint64_t offset = 0; offset < segments[i].length; offset += PageSize) {
            uint64_t pte;
            const auto result = encodeGgtt(segments[i].address + offset, pat, false, addressBits, pte);
            if (result != Status::Ok) return result;
            if (!io_.writePte(io_.context, address, pte)) return Status::IoFailure;
            address += PageSize;
        }
    }
    if (!io_.barrierAndInvalidate(io_.context)) return Status::IoFailure;
    state_ = MappingState::Bound;
    return Status::Ok;
}

Status GgttMapping::unmap() {
    if (state_ == MappingState::Empty) return Status::NotBound;
    state_ = MappingState::Faulted;
    // Port of xe_ggtt_clear without scratch; release comes strictly after the
    // adapter's ordering/TLB completion, unlike merely zeroing a host shadow.
    for (uint64_t offset = 0; offset < bytes_; offset += PageSize)
        if (!io_.writePte(io_.context, start_ + offset, 0)) return Status::IoFailure;
    if (!io_.barrierAndInvalidate(io_.context)) return Status::IoFailure;
    io_.release(io_.context, lease_);
    io_ = {};
    start_ = bytes_ = lease_ = 0;
    state_ = MappingState::Empty;
    return Status::Ok;
}

} } // namespace Mellow::PortedXe
