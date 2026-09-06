// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Mellow contributors. See Drivers/PortedXe/LICENSE.MIT.
#include "../Drivers/PortedXe/XePageTable.hpp"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
using namespace Mellow::PortedXe;
static unsigned checks;
#define CHECK(condition) do { ++checks; if (!(condition)) { fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #condition); exit(1); } } while (false)

static void fixedVectors() {
    uint64_t pte = 0;
    CHECK(encodeGgtt(0x12345000, 0, false, 52, pte) == Status::Ok && pte == 0x12345001);
    CHECK(encodeGgtt(0x12345000, 1, false, 52, pte) == Status::Ok && pte == 0x0010000012345001ULL);
    CHECK(encodeGgtt(0x12345000, 3, true, 52, pte) == Status::Ok && pte == 0x0030000012345003ULL);
    CHECK(encodePpgtt(0x12345000, 15, 0, false, 52, pte) == Status::Ok && pte == 0x400000001234509bULL);
    CHECK(encodePpgtt(0x200000, 4, 1, false, 52, pte) == Status::Ok && pte == 0x201083);
    CHECK(encodePpgtt(0x40000000, 15, 2, false, 52, pte) == Status::Ok && pte == 0x400000004000109bULL);
    CHECK(encodePpgtt(0x1000, 0, 0, true, 52, pte) == Status::Ok && pte == 0x1803);
    CHECK(encodePpgtt(0x12345000, 15, 0, false, 52, pte, false) == Status::Ok && pte == 0x4000000012345099ULL);
    CHECK(encodePde(0x2000, 3, 52, pte) == Status::Ok && pte == 0x201b);
    pte = 0xf00d;
    CHECK(encodeGgtt(1, 0, false, 52, pte) == Status::InvalidAddress && pte == 0xf00d);
    CHECK(encodeGgtt(1ULL << 52, 0, false, 52, pte) == Status::InvalidAddress && pte == 0xf00d);
    CHECK(encodeGgtt(1ULL << 40, 0, false, 40, pte) == Status::InvalidAddress && pte == 0xf00d);
    CHECK(encodeGgtt(0, 4, false, 52, pte) == Status::InvalidPat && pte == 0xf00d);
    CHECK(encodePpgtt(0x1000, 0, 1, false, 52, pte) == Status::InvalidAddress && pte == 0xf00d);
    CHECK(encodePpgtt(0x200000, 0, 2, false, 52, pte) == Status::InvalidAddress && pte == 0xf00d);
    CHECK(encodePpgtt(0, 16, 0, false, 52, pte) == Status::InvalidPat && pte == 0xf00d);
    CHECK(encodePpgtt(0, 0, 3, false, 52, pte) == Status::InvalidLevel && pte == 0xf00d);
    CHECK(encodePde(0, 4, 52, pte) == Status::InvalidPat && pte == 0xf00d);
    CHECK(encodePde(0, 0, 64, pte) == Status::InvalidAddress && pte == 0xf00d);
    CHECK(encodePde(0, 0, 0, pte) == Status::InvalidAddress && pte == 0xf00d);
    CHECK(encodePde(0x000ffffffffff000ULL, 3, 52, pte) == Status::Ok && pte == 0x000ffffffffff01bULL);
}

static uint64_t randomValue(uint64_t &state) {
    state ^= state << 13; state ^= state >> 7; state ^= state << 17; return state;
}
static void independentBitVectors() {
    // Independent table-driven bit placement, not calls into production helpers.
    const unsigned patPositions[3][4] = {{3, 4, 7, 62}, {3, 4, 12, 62}, {3, 4, 12, 62}};
    uint64_t seed = 0x347286918acde025ULL;
    for (unsigned level = 0; level != 3; ++level) {
        const unsigned shift = 12 + level * 9;
        for (unsigned pat = 0; pat != 16; ++pat) {
            for (unsigned i = 0; i != 128; ++i) {
                uint64_t address = randomValue(seed) & 0x000fffffffffffffULL;
                address &= ~((uint64_t(1) << shift) - 1);
                const bool devmem = i & 1;
                uint64_t expected = address + 3;
                for (unsigned bit = 0; bit != 4; ++bit)
                    if ((pat >> bit) & 1) expected += uint64_t(1) << patPositions[level][bit];
                if (level) expected += 128;
                if (devmem) expected += 2048;
                uint64_t actual = 0;
                CHECK(encodePpgtt(address, pat, level, devmem, 52, actual) == Status::Ok);
                CHECK(actual == expected);
                CHECK((actual & 0x000fffffffffffffULL & ~((uint64_t(1) << shift) - 1)) == address);
            }
        }
    }
}

// Explicit simulated MMIO/TLB/DMA boundary. This is NOT a Xe GPU model.
// Writes change a host staging aperture; invalidate commits it to the simulated
// page walker. Pins remain owned until every visible PTE has been cleared.
struct SimulatedBoundary {
    static constexpr uint64_t Base = 0x10000;
    uint64_t staging[64] {}, visible[64] {};
    unsigned pins {}, writes {}, invalidations {}, releases {};
    unsigned failWriteAt {};
    bool failPin {}, failInvalidate {};
    static bool pin(void *opaque, uint64_t lease) {
        auto &s = *static_cast<SimulatedBoundary *>(opaque);
        if (s.failPin || lease != 17 || s.pins) return false;
        ++s.pins; return true;
    }
    static void release(void *opaque, uint64_t lease) {
        auto &s = *static_cast<SimulatedBoundary *>(opaque);
        CHECK(lease == 17 && s.pins == 1);
        for (auto pte : s.visible) CHECK(pte == 0);
        --s.pins; ++s.releases;
    }
    static bool write(void *opaque, uint64_t address, uint64_t pte) {
        auto &s = *static_cast<SimulatedBoundary *>(opaque);
        CHECK(s.pins == 1);
        ++s.writes;
        if (s.failWriteAt == s.writes) return false;
        if (address < Base || address >= Base + sizeof(s.staging) / 8 * 4096 || (address & 4095)) return false;
        s.staging[(address - Base) / 4096] = pte;
        return true;
    }
    static bool invalidate(void *opaque) {
        auto &s = *static_cast<SimulatedBoundary *>(opaque);
        CHECK(s.pins == 1);
        if (s.failInvalidate) return false;
        memcpy(s.visible, s.staging, sizeof(s.visible));
        ++s.invalidations; return true;
    }
    GgttIo io() { return {this, pin, release, write, invalidate}; }
    uint64_t walk(uint64_t address) const {
        if (address < Base || address >= Base + 64 * 4096) return UINT64_MAX;
        uint64_t pte = visible[(address - Base) / 4096];
        return (pte & 1) ? (pte & 0x000ffffffffff000ULL) + (address & 4095) : UINT64_MAX;
    }
};
static const DmaSegment Scatter[] = {{0x120000, 8192}, {0x880000, 4096}, {0xff0000, 8192}};

static void mappingLifetime() {
    SimulatedBoundary sim;
    GgttMapping mapping;
    CHECK(mapping.unmap() == Status::NotBound);
    CHECK(mapping.bind(sim.io(), sim.Base, 5 * 4096, 17, Scatter, 3, 2, 48) == Status::Ok);
    CHECK(mapping.state() == MappingState::Bound && mapping.mappedBytes() == 5 * 4096);
    CHECK(sim.pins == 1 && sim.invalidations == 1 && sim.releases == 0 && sim.writes == 5);
    CHECK(sim.walk(sim.Base + 7) == 0x120007);
    CHECK(sim.walk(sim.Base + 4096 + 19) == 0x121013);
    CHECK(sim.walk(sim.Base + 8192 + 4095) == 0x880fff);
    CHECK(sim.walk(sim.Base + 3 * 4096) == 0xff0000);
    CHECK(sim.walk(sim.Base + 4 * 4096) == 0xff1000);
    CHECK(sim.walk(sim.Base + 5 * 4096) == UINT64_MAX);
    CHECK(mapping.bind(sim.io(), sim.Base, 4096, 17, Scatter, 1, 0, 48) == Status::Busy);
    sim.failInvalidate = true;
    CHECK(mapping.unmap() == Status::IoFailure);
    CHECK(mapping.state() == MappingState::Faulted && sim.pins == 1 && sim.releases == 0);
    CHECK(sim.walk(sim.Base) == 0x120000); // Old TLB view: still pinned.
    sim.failInvalidate = false;
    CHECK(mapping.unmap() == Status::Ok && mapping.state() == MappingState::Empty);
    CHECK(sim.walk(sim.Base) == UINT64_MAX && sim.pins == 0 && sim.releases == 1);
    CHECK(mapping.mappedBytes() == 0 && mapping.unmap() == Status::NotBound);
}
static void rejectedInputsAndFaults() {
    SimulatedBoundary sim;
    GgttMapping mapping;
    DmaSegment bad[] = {{0x120000, 4096}, {0x800001, 4096}};
    CHECK(mapping.bind(sim.io(), sim.Base, 8192, 17, bad, 2, 0, 48) == Status::InvalidAddress);
    CHECK(sim.pins == 0 && sim.writes == 0);
    CHECK(mapping.bind(sim.io(), sim.Base, 4096, 17, Scatter, 3, 0, 48) == Status::InvalidAddress);
    CHECK(mapping.bind(sim.io(), sim.Base, 5 * 4096, 17, Scatter, 3, 4, 48) == Status::InvalidPat);
    CHECK(mapping.bind(sim.io(), UINT64_MAX - 4095, 8192, 17, Scatter, 3, 0, 48) == Status::InvalidArgument);
    CHECK(mapping.bind(sim.io(), 1ULL << 32, 4096, 17, Scatter, 3, 0, 48) == Status::InvalidArgument);
    CHECK(mapping.bind({}, sim.Base, 5 * 4096, 17, Scatter, 3, 0, 48) == Status::InvalidArgument);
    sim.failPin = true;
    CHECK(mapping.bind(sim.io(), sim.Base, 5 * 4096, 17, Scatter, 3, 0, 48) == Status::PinFailed);
    CHECK(mapping.state() == MappingState::Empty && sim.pins == 0 && sim.writes == 0);
    sim.failPin = false;
    sim.failWriteAt = 2;
    CHECK(mapping.bind(sim.io(), sim.Base, 5 * 4096, 17, Scatter, 3, 0, 48) == Status::IoFailure);
    CHECK(mapping.state() == MappingState::Faulted && sim.pins == 1 && sim.releases == 0);
    CHECK(sim.walk(sim.Base) == UINT64_MAX); // Not committed by invalidation.
    sim.failWriteAt = 0;
    CHECK(mapping.unmap() == Status::Ok && sim.pins == 0);
    sim.failInvalidate = true;
    CHECK(mapping.bind(sim.io(), sim.Base, 5 * 4096, 17, Scatter, 3, 0, 48) == Status::IoFailure);
    CHECK(mapping.state() == MappingState::Faulted && sim.pins == 1);
    sim.failWriteAt = sim.writes + 1;
    CHECK(mapping.unmap() == Status::IoFailure && sim.pins == 1);
    sim.failWriteAt = 0;
    sim.failInvalidate = false;
    CHECK(mapping.unmap() == Status::Ok && sim.pins == 0 && sim.releases == 2);
}
int main() {
    fixedVectors(); independentBitVectors(); mappingLifetime(); rejectedInputsAndFaults();
    printf("{\"status\":\"PASS_PORTED_XE_ALGORITHMS_SIMULATED_BOUNDARIES\",\"checks\":%u,\"upstream_functions_executed\":6,\"simulated_mmio_dma\":true,\"hardware_execution\":false,\"darwin_driver_loaded\":false,\"metal_tested\":false}\n", checks);
    return 0;
}
