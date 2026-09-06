// Local research implementation. See docs/XE-MMIO.md and LICENSE/NOTICE.
#include "XeMmioAccess.hpp"

namespace MellowXe {
static constexpr uint32_t gmdId=0xD8C, control[2]={0xA188,0xA278}, ack[2]={0xDFC,0xD84};
static constexpr uint32_t kernelBit=1, kernelMask=1U<<16;
MmioStatus ForceWake::initialize(MmioAccess access) {
    if (initialized_) return MmioStatus::Busy;
    if (!access.read32 || !access.write32 || !access.nowMicros || !access.delayMicros) return MmioStatus::Unavailable;
    uint32_t raw=0;
    if (!access.read32(access.opaque,gmdId,raw) || raw==0xFFFFFFFFU) return MmioStatus::IoFailure;
    GraphicsIp info {static_cast<uint16_t>(raw>>22),static_cast<uint8_t>((raw>>14)&255),
                     static_cast<uint8_t>((raw>>6)&255),static_cast<uint8_t>(raw&63)};
    // The implementation below is pinned to the MTL/Xe-LPG 12.70 register
    // protocol; PCI ID or a compiler-selected target alone cannot admit it.
    if (info.architecture!=12 || info.release!=70) return MmioStatus::UnsupportedIp;
    io_=access; ip_=info; initialized_=true;
    return MmioStatus::Ok;
}
MmioStatus ForceWake::shutdown() {
    if (!canDetach()) return MmioStatus::Busy;
    io_=MmioAccess {}; ip_=GraphicsIp {}; initialized_=false;
    return MmioStatus::Ok;
}
MmioStatus ForceWake::wait(uint32_t reg,bool awake) {
    const uint64_t start=io_.nowMicros(io_.opaque);
    uint64_t previous=start;
    for (unsigned attempt=0;attempt<=1000;++attempt) {
        uint32_t value=0;
        if (!io_.read32(io_.opaque,reg,value) || value==0xFFFFFFFFU) return MmioStatus::IoFailure;
        if (((value&kernelBit)!=0)==awake) return MmioStatus::Ok;
        const uint64_t now=io_.nowMicros(io_.opaque);
        if (now<previous) return MmioStatus::ClockRegression;
        previous=now;
        if (now-start>=50000 || attempt==1000) return MmioStatus::Timeout;
        io_.delayMicros(io_.opaque,50);
    }
    return MmioStatus::Timeout;
}
MmioStatus ForceWake::acquire(WakeDomain domain) {
    const unsigned index=static_cast<unsigned>(domain);
    if (index>1) return MmioStatus::Invalid;
    if (!initialized_) return MmioStatus::Unavailable;
    if (faulted_) return MmioStatus::Faulted;
    if (index==1 && !refs_[0]) return MmioStatus::Busy;
    if (refs_[index]==UINT32_MAX) return MmioStatus::Busy;
    if (refs_[index]) { ++refs_[index]; return MmioStatus::Ok; }
    uint32_t value=0;
    if (!io_.read32(io_.opaque,ack[index],value) || value==0xFFFFFFFFU) return MmioStatus::IoFailure;
    // Never adopt somebody else's kernel-bit hold and later release it.
    if (value&kernelBit) return MmioStatus::Busy;
    // A failing backend can have issued the write before detecting an error.
    // Keep the mapping quarantined rather than assume the hardware stayed idle.
    if (!io_.write32(io_.opaque,control[index],kernelMask|kernelBit)) {
        faulted_=true; return MmioStatus::IoFailure;
    }
    const MmioStatus result=wait(ack[index],true);
    if (result!=MmioStatus::Ok) {
        const bool cleared=io_.write32(io_.opaque,control[index],kernelMask);
        if (!cleared || wait(ack[index],false)!=MmioStatus::Ok) faulted_=true;
        return result;
    }
    refs_[index]=1;
    return MmioStatus::Ok;
}
MmioStatus ForceWake::release(WakeDomain domain) {
    const unsigned index=static_cast<unsigned>(domain);
    if (index>1) return MmioStatus::Invalid;
    if (!initialized_) return MmioStatus::Unavailable;
    if (faulted_) return MmioStatus::Faulted;
    if (!refs_[index] || (index==0 && refs_[index]==1 && refs_[1])) return MmioStatus::Busy;
    if (refs_[index]>1) { --refs_[index]; return MmioStatus::Ok; }
    if (!io_.write32(io_.opaque,control[index],kernelMask)) { faulted_=true; return MmioStatus::IoFailure; }
    const MmioStatus result=wait(ack[index],false);
    if (result!=MmioStatus::Ok) { faulted_=true; return result; }
    refs_[index]=0;
    return MmioStatus::Ok;
}
bool ForceWake::held(WakeDomain domain) const {
    const unsigned index=static_cast<unsigned>(domain);
    return initialized_ && !faulted_ && index<2 && refs_[index]!=0;
}
}
