// Local research implementation, 2026. See LICENSE and NOTICE.
#include "XePageTableIOKit.hpp"

namespace XeMemory {
Status IOKitPageTable::initialize(IOKitContext &context,uint64_t owner,size_t pages,
                                  uint8_t tablePat,uint16_t patMask) {
    if (started_ || ended_) return Status::Busy;
    if (!owner || !pages || pages>PageTable::MaxPages || tablePat>3 || !(patMask&(1U<<tablePat)))
        return Status::Invalid;
    if (!context.mapper) return Status::Unavailable;
    pins_=makeIOKitPinBackend(context); owner_=owner; patMask_=patMask; started_=true;
    const Status pinned=pins_.pin(pins_.context,owner,pages*PageSize,pin_);
    // Failed IOKit unwind can retain a recoverable pin. release retries actual
    // unpin; never zero/drop that resource descriptor here.
    if (pinned!=Status::Ok) return pin_.cookie?Status::Quarantined:pinned;
    auto *cpu=static_cast<uint8_t *>(kernelBuffer(pin_));
    if (!cpu || !pin_.dmaPages || pin_.pageCount!=pages) return Status::Quarantined;
    for (size_t i=0;i<pages;++i)
        pool_[i]=TablePage {pin_.dmaPages[i],reinterpret_cast<uint64_t *>(cpu+i*PageSize)};
    const Status initialized=tree_.initialize(owner,pool_,pages,tablePat);
    ready_=initialized==Status::Ok;
    return initialized;
}
Status IOKitPageTable::map4K(uint64_t owner,uint64_t va,uint64_t dma,uint8_t pat,bool writable) {
    if (!ready_ || ended_) return Status::Unavailable;
    if (owner!=owner_) return Status::WrongOwner;
    if (pat>15 || !(patMask_&(1U<<pat))) return Status::Unavailable;
    return tree_.map4K(owner,va,dma,pat,writable);
}
Status IOKitPageTable::unmap4K(uint64_t owner,uint64_t va) {
    return ready_ && !ended_?tree_.unmap4K(owner,va):Status::Unavailable;
}
Status IOKitPageTable::lookup(uint64_t owner,uint64_t va,uint64_t &pte) const {
    return ready_ && !ended_?tree_.lookup(owner,va,pte):Status::Unavailable;
}
Status IOKitPageTable::sealForDevice(uint64_t owner,uint64_t &out) {
    if (!ready_ || ended_) return Status::Unavailable;
    if (owner!=owner_) return Status::WrongOwner;
    uint64_t address=0;
    const Status sealed=tree_.seal(owner,address);
    if (sealed!=Status::Ok) return sealed;
    const Status synced=synchronizeForDevice(pin_);
    if (synced!=Status::Ok) return synced;
    __sync_synchronize();
    root_=address; exposed_=true; out=address;
    return Status::Ok;
}
Status IOKitPageTable::release(uint64_t owner,RootRetirement proof) {
    if (!started_ || ended_) return Status::Invalid;
    if (owner!=owner_) return Status::WrongOwner;
    if (exposed_ && (!proof.complete || !proof.complete(proof.opaque,owner_,root_))) return Status::Busy;
    if (pin_.cookie) {
        const Status unpinned=pins_.unpin(pins_.context,pin_);
        if (unpinned!=Status::Ok) return Status::Quarantined;
    }
    ready_=false; exposed_=false; ended_=true;
    return Status::Ok;
}
}
