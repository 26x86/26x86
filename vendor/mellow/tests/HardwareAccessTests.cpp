#include "../Mellow/HardwareAccess.hpp"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

using namespace MellowHardware;

static void testMmio() {
    // Reads must be read-only. Rejected writes must not touch any DWORD,
    // especially inherited "indirect ports" at DWORD indices 14 and 15.
    volatile uint32_t bar[32];
    for (unsigned i = 0; i < 32; ++i) bar[i] = 0xABCD0000U + i;
    for (uint64_t offset = 0; offset < 160; ++offset) {
        uint32_t result = 0xFEEDCAFEU;
        const bool expected = offset < 128 && offset % 4 == 0;
        assert(read32(bar, sizeof(bar), offset, result) == expected);
        assert(result == (expected ? 0xABCD0000U + offset / 4 : 0xFEEDCAFEU));
        for (unsigned i = 0; i < 32; ++i) assert(bar[i] == 0xABCD0000U + i);
        assert(write32(bar, sizeof(bar), offset, 0x87654321U) == expected);
        for (unsigned i = 0; i < 32; ++i) {
            const uint32_t wanted = expected && i == offset / 4 ? 0x87654321U : 0xABCD0000U + i;
            assert(bar[i] == wanted);
            bar[i] = 0xABCD0000U + i;
        }
    }
    uint32_t output = 17;
    assert(!read32(nullptr, sizeof(bar), 0, output) && output == 17);
    assert(!write32(nullptr, sizeof(bar), 0, 7));
    for (uint64_t length = 0; length < 4; ++length) {
        assert(!read32(bar, length, 0, output));
        assert(!write32(bar, length, 0, 7));
    }
    assert(containsAligned(4, 0, 4, 4));
    assert(!containsAligned(4, 1, 4, 1));
    assert(!containsAligned(4, 4, 4, 4));
    assert(!containsAligned(UINT64_MAX, UINT64_MAX - 3, 4, 4));
    assert(containsAligned(UINT64_MAX, UINT64_MAX - 7, 4, 4));
    assert(!containsAligned(128, 0, 0, 4));
    assert(!containsAligned(128, 0, 4, 0));
    assert(!read32(bar, sizeof(bar), UINT64_MAX - 3, output));
    assert(!write32(bar, sizeof(bar), UINT64_MAX - 3, 7));
    assert(output == 17);
}

static void testConfig() {
    const uint32_t bdf = 0x00001000U; // 00:02.0
    const uint16_t physical = 0x7D41U;
    const uint32_t original32 = 0x7D418086U;
    const uint32_t spoof = 0x9A49U;
    for (unsigned offset = 0; offset < 256; ++offset) {
        assert(spoofConfig32(bdf, bdf, offset, original32, physical, spoof) ==
               (offset < 4 ? 0x9A498086U : original32));
        assert(spoofConfig16(bdf, bdf, offset, physical, physical, spoof) ==
               (offset == 2 || offset == 3 ? spoof : physical));
    }
    // Distinct BDF and extended config pages must retain their original bytes.
    for (unsigned bit = 8; bit < 28; ++bit) {
        const uint32_t other = bdf ^ (1U << bit);
        assert(spoofConfig32(other, bdf, 0, original32, physical, spoof) == original32);
        assert(spoofConfig16(other, bdf, 2, physical, physical, spoof) == physical);
    }
    const uint32_t invalidIds[] = {0, 0xFFFFU, 0x10000U, UINT32_MAX};
    for (auto id : invalidIds) {
        assert(spoofConfig32(bdf, bdf, 0, original32, physical, id) == original32);
        assert(spoofConfig16(bdf, bdf, 2, physical, physical, id) == physical);
    }
    assert(spoofConfig32(bdf, bdf, 0, UINT32_MAX, physical, spoof) == UINT32_MAX);
    assert(spoofConfig16(bdf, bdf, 2, UINT16_MAX, physical, spoof) == UINT16_MAX);
    assert(spoofConfig32(bdf, bdf, 0, 0x7D411002U, physical, spoof) == 0x7D411002U);
    assert(spoofConfig32(bdf, bdf, 0, 0x12348086U, physical, spoof) == 0x12348086U);
    assert(spoofConfig16(bdf, bdf, 0, 0x8086U, physical, spoof) == 0x8086U);
}

static void testDsm() {
    // Exact Intel Xe allowed set; sweep all GMS and GGMS encodings.
    for (uint32_t ggms = 0; ggms < 4; ++ggms) {
        for (uint32_t gms = 0; gms < 256; ++gms) {
            uint32_t bytes = 0xDEADBEEFU;
            const bool expected = ggms == 3 && (gms <= 4 || (gms >= 0xF0 && gms <= 0xFE));
            assert(decodeDsmReservation((gms << 8) | (ggms << 6), bytes) == expected);
            if (!expected) assert(bytes == 0xDEADBEEFU);
            else {
                const uint32_t mib = gms <= 4 ? gms * 32 : (gms - 0xEF) * 4;
                assert(bytes == mib * 1024 * 1024);
                assert(bytes <= 128U * 1024 * 1024);
            }
        }
    }
    uint32_t bytes = 1;
    assert(!decodeDsmReservation(UINT32_MAX, bytes) && bytes == 1);
    assert(decodeDsmReservation(0x01C0, bytes) && bytes == 32U * 1024 * 1024);
    assert(decodeDsmReservation(0xF0C0, bytes) && bytes == 4U * 1024 * 1024);
    assert(decodeDsmReservation(0x00C0, bytes) && bytes == 0);
}

int main() {
    testMmio();
    testConfig();
    testDsm();
    puts("PASS HardwareAccess: MMIO side effects/boundaries/overflow; PCI scope/alignment/failure; 1024 GMS/GGMS combinations");
}
