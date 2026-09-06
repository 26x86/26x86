#pragma once
#include "XeGuCFirmware.hpp"
#include "XeMmioIOKit.hpp"
#include "XeMemoryIOKit.hpp"

namespace XeGuCFirmware {
struct IOKitProofs {
    void *opaque {};
    bool (*ownsEpoch)(void *,uint64_t,uint64_t) {};
    bool (*quiesced)(void *,uint64_t,uint64_t) {};
    bool (*retainGgtt)(void *,const Region &,bool) {};
    bool (*releaseGgtt)(void *,const Region &) {};
    bool (*mappingPublished)(void *,const Region &,uint64_t) {};
    bool (*readPat3)(void *,uint32_t &) {};
    bool (*fullAdsValid)(void *,const Plan &,const MellowXe::FirmwareInfo &) {};
};
// Real IOKit binding. Caller retains device/MMIO/proofs, holds GT forcewake and
// one shared sleepable serialization domain. Nothing attaches/runs by default.
// The owner must prevent reset/power changes while a load/reset call is active.
class IOKitBinding {
public:
    IOKitBinding(IOPCIDevice &device,MellowXe::IOKitMmio &mmio,IOKitProofs proofs)
        : device_(device),mmio_(mmio),proofs_(proofs) {}
    IOKitBinding(const IOKitBinding &) = delete;
    IOKitBinding &operator=(const IOKitBinding &) = delete;
    Backend backend();
private:
    IOPCIDevice &device_;
    MellowXe::IOKitMmio &mmio_;
    IOKitProofs proofs_ {};
    static bool admitted(void *,uint64_t,uint64_t);
    static bool quiesced(void *,uint64_t,uint64_t);
    static bool retain(void *,const Region &,bool);
    static bool release(void *,const Region &);
    static bool synchronize(void *,const Region &);
    static bool readPat(void *,uint32_t &);
    static bool published(void *,const Region &,uint64_t);
    static bool ads(void *,const Plan &,const MellowXe::FirmwareInfo &);
};
}
