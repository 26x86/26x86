// Local research implementation, 2026. See LICENSE and NOTICE.
#include "XeMmioIOKit.hpp"
#include "HardwareAccess.hpp"
#include <IOKit/IOLib.h>
#include <kern/clock.h>

namespace MellowXe {
MmioStatus IOKitMmio::attach(IOPCIDevice *device) {
    if (device_ || map_) return MmioStatus::Busy;
    if (!device || device->getBusNumber()!=0 || device->getDeviceNumber()!=2 || device->getFunctionNumber()!=0 ||
        device->configRead16(kIOPCIConfigVendorID)!=0x8086 || device->configRead16(kIOPCIConfigDeviceID)!=0x7D41)
        return MmioStatus::Invalid;
    const uint16_t command=device->configRead16(kIOPCIConfigCommand);
    if (command==0xFFFF || !(command&2)) return MmioStatus::Unavailable;
    auto *mapping=device->mapDeviceMemoryWithRegister(kIOPCIConfigBaseAddress0,kIOMapInhibitCache);
    if (!mapping || mapping->getLength()<0xA27C || !mapping->getVirtualAddress() || (mapping->getVirtualAddress()&3)) {
        if (mapping) mapping->release();
        return MmioStatus::IoFailure;
    }
    device->retain(); device_=device; map_=mapping;
    base_=reinterpret_cast<volatile uint32_t *>(map_->getVirtualAddress()); length_=map_->getLength();
    const MmioStatus status=wake_.initialize(access());
    if (status!=MmioStatus::Ok) {
        base_=nullptr; length_=0; map_->release(); map_=nullptr; device_->release(); device_=nullptr;
    }
    return status;
}
MmioStatus IOKitMmio::detach() {
    if (wake_.shutdown()!=MmioStatus::Ok) return MmioStatus::Busy;
    base_=nullptr; length_=0;
    if (map_) { map_->release(); map_=nullptr; }
    if (device_) { device_->release(); device_=nullptr; }
    return MmioStatus::Ok;
}
MmioAccess IOKitMmio::access() { return {this,read,write,now,delay}; }
bool IOKitMmio::read(void *opaque,uint32_t reg,uint32_t &value) {
    auto &self=*static_cast<IOKitMmio *>(opaque);
    __sync_synchronize();
    const bool valid=MellowHardware::read32(self.base_,self.length_,reg,value);
    __sync_synchronize(); return valid;
}
bool IOKitMmio::write(void *opaque,uint32_t reg,uint32_t value) {
    auto &self=*static_cast<IOKitMmio *>(opaque);
    __sync_synchronize();
    const bool valid=MellowHardware::write32(self.base_,self.length_,reg,value);
    __sync_synchronize(); return valid;
}
uint64_t IOKitMmio::now(void *) {
    uint64_t absolute=0,nanos=0;
    clock_get_uptime(&absolute); absolutetime_to_nanoseconds(absolute,&nanos);
    return nanos/1000;
}
void IOKitMmio::delay(void *,uint32_t micros) { IODelay(micros); }
}
