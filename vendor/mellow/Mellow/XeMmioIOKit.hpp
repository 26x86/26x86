// Local research implementation, 2026. See LICENSE and NOTICE.
#pragma once
#include "XeMmioAccess.hpp"
#include <IOKit/pci/IOPCIDevice.h>

namespace MellowXe {
// Actual IOKit BAR0 mapping and MMIO/time callbacks, not a host mock. Attach only
// on a PCI device exclusively owned by this driver in D0, before ID spoof hooks.
// Mapping/ForceWake references must outlive users of access(). No implicit DMA,
// bus-master enabling, IRQ installation, GuC authentication or ROM write occurs.
class IOKitMmio {
public:
    IOKitMmio() = default;
    IOKitMmio(const IOKitMmio &) = delete;
    IOKitMmio &operator=(const IOKitMmio &) = delete;
    MmioStatus attach(IOPCIDevice *device);
    MmioStatus detach();
    MmioAccess access();
    ForceWake &forceWake() { return wake_; }
private:
    IOPCIDevice *device_ {};
    IOMemoryMap *map_ {};
    volatile uint32_t *base_ {};
    uint64_t length_ {};
    ForceWake wake_ {};
    static bool read(void *,uint32_t,uint32_t &);
    static bool write(void *,uint32_t,uint32_t);
    static uint64_t now(void *);
    static void delay(void *,uint32_t);
};
}
