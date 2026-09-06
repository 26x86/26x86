#include "XeInterrupt.hpp"

namespace XeInterrupt {
bool Controller::admitted() const { return ops_.admitted && ops_.admitted(ops_.opaque, config_.epoch); }
bool Controller::read(uint32_t reg, uint32_t &v) {
    return admitted() && ops_.mmio.read32 && ops_.mmio.read32(ops_.mmio.opaque,reg,v) && v != 0xffffffffU;
}
bool Controller::write(uint32_t reg,uint32_t v) {
    return admitted() && ops_.mmio.write32 && ops_.mmio.write32(ops_.mmio.opaque,reg,v);
}
bool Controller::update(uint32_t reg,uint32_t mask,uint32_t bits) {
    // Mask registers legitimately read all ones, unlike identity/status MMIO.
    uint32_t v=0;
    return admitted() && ops_.mmio.read32(ops_.mmio.opaque,reg,v) &&
        write(reg,(v & ~mask) | (bits & mask));
}
Status Controller::fail(Status status) {
    __atomic_store_n(&state_,4U,__ATOMIC_RELEASE);
    if (admitted()) write(tileMaster,0); // leave source masked; caller resets
    return status;
}
Status Controller::configure(const Configuration &c,const Ops &o) {
    if (configured_ || !c.epoch || c.vendor!=0x8086 || c.device!=0x7d41 || (c.ccsMask & ~1U) ||
        !o.mmio.read32 || !o.mmio.write32 || !o.mmio.nowMicros || !o.admitted || !o.identity || !o.otherMaster)
        return Status::Invalid;
    config_=c; ops_=o;
    if (!admitted()) return Status::Unavailable;
    configured_=true; // an attempted MMIO write may partially take effect
    // Caller has identified GMD 12.70/PF/tile0 and owns the complete IRQ router.
    // Disable delivery before changing only our engine/GuC enable and mask bits.
    if (!write(tileMaster,0)) return fail(Status::IoFailure);
    uint32_t posted=0;
    if (!read(tileMaster,posted) || (posted & masterEnable)) return fail(Status::IoFailure);
    const uint32_t irqs=engineUser|engineFlush;
    const uint32_t engineBits=(c.render ? irqs<<16 : 0) | (c.copy ? irqs : 0);
    if (!update(0x190030,0x00110011,engineBits) ||
        !update(0x190090,irqs<<16,c.render ? 0 : irqs<<16) ||
        !update(0x1900a0,irqs<<16,c.copy ? 0 : irqs<<16) ||
        !update(0x190048,irqs<<16,c.ccsMask ? irqs<<16 : 0) ||
        !update(0x190100,(irqs<<16)|irqs,c.ccsMask ? 0 : (irqs<<16)|irqs) ||
        !update(0x190038,0x80000000U,0x80000000U) ||
        !update(0x1900e8,0x80000000U,0)) return fail(Status::IoFailure);
    if (!admitted() || !ops_.mmio.read32(ops_.mmio.opaque,0x1900e8,posted)) return fail(Status::IoFailure);
    return Status::Ok;
}
Status Controller::start() {
    if (!configured_ || __atomic_load_n(&state_,__ATOMIC_ACQUIRE)!=0) return Status::Invalid;
    if (!admitted()) return Status::Unavailable;
    return rearm();
}
Status Controller::rearm() {
    __atomic_store_n(&state_,1U,__ATOMIC_RELEASE);
    if (!write(tileMaster,masterEnable)) return fail(Status::IoFailure);
    // A primary interrupt may mask delivery between the atomic state change
    // and our enable write. Restore its mask so a shared/level IRQ cannot storm.
    const uint32_t after=__atomic_load_n(&state_,__ATOMIC_ACQUIRE);
    if (after!=1 && !write(tileMaster,0)) return fail(Status::IoFailure);
    return after==4 ? Status::Faulted : Status::Ok;
}
bool Controller::filter() {
    if (__atomic_load_n(&state_,__ATOMIC_ACQUIRE)!=1 || !admitted()) return false;
    uint32_t level=0;
    if (!read(tileMaster,level)) { fail(Status::IoFailure); return true; }
    if (!(level & 1U)) return false; // tile0 only, no destructive read/ack
    uint32_t expected=1;
    if (!__atomic_compare_exchange_n(&state_,&expected,2U,false,__ATOMIC_ACQ_REL,__ATOMIC_ACQUIRE)) return false;
    if (!write(tileMaster,0)) fail(Status::IoFailure);
    return true;
}
Status Controller::collect() {
    uint32_t tile=0,master=0;
    if (!read(tileMaster,tile) || (tile & masterEnable)) return fail(Status::IoFailure);
    if (tile & ~masterEnable & ~1U) return fail(Status::Unsupported);
    if (!(tile & 1)) { eventCount_=nextEvent_=other_=0; batchReady_=true; return Status::Ok; }
    if (!write(tileMaster,tile & ~masterEnable) || !read(gfxMaster,master) ||
        !write(gfxMaster,master)) return fail(Status::IoFailure);
    eventCount_=nextEvent_=0; other_=master & ~(masterEnable|3U);
    for (unsigned bank=0;bank<2;++bank) {
        if (!(master & (1U<<bank))) continue;
        uint32_t dw=0;
        if (!read(bankStatus+bank*4,dw)) return fail(Status::IoFailure);
        for (unsigned bit=0;bit<32;++bit) {
            if (!(dw & (1U<<bit))) continue;
            if (!write(selectorRegister+bank*4,1U<<bit)) return fail(Status::IoFailure);
            uint32_t identity=0; const uint64_t start=ops_.mmio.nowMicros(ops_.mmio.opaque);
            bool valid=false;
            for (unsigned attempt=0;attempt<10000;++attempt) {
                if (!read(identityRegister+bank*4,identity)) return fail(Status::IoFailure);
                if (identity & identityValid) { valid=true; break; }
                const uint64_t now=ops_.mmio.nowMicros(ops_.mmio.opaque);
                if (now<start || now-start>=100) break;
            }
            // Never acknowledge an invalid identity or its DW bit.
            if (!valid) return fail(Status::Timeout);
            if (!write(identityRegister+bank*4,identity)) return fail(Status::IoFailure);
            events_[eventCount_++]={identity,static_cast<uint8_t>(bank),static_cast<uint8_t>(bit),
                static_cast<uint8_t>((identity>>16)&7),static_cast<uint8_t>((identity>>20)&63),
                static_cast<uint16_t>(identity)};
        }
        // W1C summary only after every selected identity has been captured/acked.
        if (!write(bankStatus+bank*4,dw)) return fail(Status::IoFailure);
    }
    batchReady_=true; return Status::Ok;
}
Status Controller::service() {
    const uint32_t state=__atomic_load_n(&state_,__ATOMIC_ACQUIRE);
    if (state==4) return Status::Faulted;
    if (state!=2 && state!=3) return Status::Empty;
    if (!admitted()) return fail(Status::Unavailable);
    __atomic_store_n(&state_,3U,__ATOMIC_RELEASE);
    if (!batchReady_) { const Status s=collect(); if(s!=Status::Ok) return s; }
    while (nextEvent_<eventCount_) {
        if (!admitted()) return fail(Status::Unavailable);
        const Handling h=ops_.identity(ops_.opaque,config_.epoch,events_[nextEvent_]);
        if (h==Handling::More) return Status::Pending;
        if (h==Handling::Failed) return fail(Status::Unsupported);
        ++nextEvent_;
    }
    if (other_) {
        if (!admitted()) return fail(Status::Unavailable);
        const Handling h=ops_.otherMaster(ops_.opaque,config_.epoch,other_);
        if (h==Handling::More) return Status::Pending;
        if (h==Handling::Failed) return fail(Status::Unsupported);
        other_=0;
    }
    batchReady_=false;
    return rearm();
}
Status Controller::stop() {
    __atomic_store_n(&state_,0U,__ATOMIC_RELEASE);
    if (!configured_) return Status::Ok;
    if (!admitted()) return Status::Unavailable; // no stale-epoch MMIO
    uint32_t posting=0;
    if (!write(tileMaster,0) || !read(tileMaster,posting) || (posting & masterEnable)) return Status::IoFailure;
    configured_=false; batchReady_=false; eventCount_=nextEvent_=other_=0;
    return Status::Ok;
}
}
