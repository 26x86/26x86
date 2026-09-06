#include "../Mellow/kern_model.hpp"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main() {
    assert(isSupportedUltraDevice(0x7D41));
    assert(isSupportedUltraPair(0xB5, 0x7D41));
    assert(!isSupportedUltraDevice(0x9A49)); // injected TGL ID is not hardware evidence
    assert(!isSupportedUltraPair(0xB5, 0x9A49));
    for (unsigned cpu = 0; cpu < 256; ++cpu) {
        assert(isSupportedUltraPair(cpu, 0x7D41) == (cpu == 0xB5));
    }
    for (unsigned id = 0; id < 65536; ++id) {
        assert(isSupportedUltraPair(0xB5, id) == (id == 0x7D41));
    }
    assert(strcmp(getBranding(0x7D41), "Intel Graphics 4-Core (Arrow Lake-U)") == 0);
    assert(findUltraDevice(0) == nullptr && getUltraCompatSubSliceCount(0) == 0);
    assert(isSupportedUltraPair(0xAA, 0x7D40));
    assert(isSupportedUltraPair(0xAC, 0x7D55));
    assert(isSupportedUltraPair(0xC5, 0x7D51));
    assert(isSupportedUltraPair(0xC6, 0x7D67));
    puts("PASS model: exact B5/7D41 pair across all 65536 GPU IDs and 256 CPU models; spoof rejected");
}
