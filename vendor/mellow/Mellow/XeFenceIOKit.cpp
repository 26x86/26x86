#include "XeFenceIOKit.hpp"

namespace XeFence {
bool IOKitSlot::valid(void *p,const Slot &s) {
    auto &self=*static_cast<IOKitSlot *>(p);
    return self.prepared_ && self.map_ && self.descriptor_ &&
        reinterpret_cast<uintptr_t>(s.cpu)==self.map_->getVirtualAddress()+self.offset_ &&
        self.proofs_.valid(self.proofs_.opaque,self.descriptor_,self.offset_,s);
}
bool IOKitSlot::retain(void *p,const Slot &s) {
    auto &self=*static_cast<IOKitSlot *>(p);
    if (self.pinned_ || !self.proofs_.retainGgtt(self.proofs_.opaque,s)) return false;
    self.pinned_=true; return true;
}
void IOKitSlot::release(void *p,const Slot &s) {
    auto &self=*static_cast<IOKitSlot *>(p);
    if (self.pinned_) { self.proofs_.releaseGgtt(self.proofs_.opaque,s); self.pinned_=false; }
}
bool IOKitSlot::stopped(void *p,const Slot &s) {
    auto &self=*static_cast<IOKitSlot *>(p);
    return self.proofs_.stopped(self.proofs_.opaque,s);
}
Status IOKitSlot::attach(IOMemoryDescriptor *d,uint64_t offset,Slot slot,const MappingProofs &proofs) {
    if (descriptor_ || !d || (offset&7) || d->getLength()<8 || offset>d->getLength()-8 ||
        !proofs.valid || !proofs.stopped || !proofs.retainGgtt || !proofs.releaseGgtt) return Status::Invalid;
    d->retain(); descriptor_=d; offset_=offset; proofs_=proofs;
    if (d->prepare(kIODirectionInOut)!=kIOReturnSuccess) { descriptor_->release(); descriptor_=nullptr; return Status::Unavailable; }
    prepared_=true; map_=d->map();
    if (!map_ || !map_->getVirtualAddress() || map_->getLength()<8 || offset>map_->getLength()-8) {
        detach(); return Status::Unavailable;
    }
    slot.cpu=reinterpret_cast<volatile uint64_t *>(map_->getVirtualAddress()+offset);
    const Status status=timeline_.bind(slot,{this,valid,retain,release,stopped});
    if (status!=Status::Ok) detach(); // failed quiescence retains live backing
    return status;
}
Status IOKitSlot::detach() {
    const Status status=timeline_.close();
    if (status!=Status::Ok) return status;
    if (map_) { map_->release(); map_=nullptr; }
    if (descriptor_) {
        if (prepared_ && descriptor_->complete(kIODirectionInOut)!=kIOReturnSuccess) return Status::Unavailable;
        prepared_=false; descriptor_->release(); descriptor_=nullptr;
    }
    return Status::Ok;
}
}
