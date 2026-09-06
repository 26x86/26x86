#include "XeFence.hpp"

namespace XeFence {
Status Timeline::bind(const Slot &s,const Ops &ops) {
    if (used_ || !s.cpu || (reinterpret_cast<uintptr_t>(s.cpu)&7) || !s.ggtt || (s.ggtt&7) ||
        s.ggtt>0xfffffff8ULL || !s.allocation || !s.owner || !s.context || !s.epoch ||
        (s.engineClass!=0 && s.engineClass!=3 && s.engineClass!=5) || s.instance!=0 ||
        !ops.valid || !ops.retain || !ops.release || !ops.stopped) return Status::Invalid;
    if (!ops.valid(ops.opaque,s) || !ops.stopped(ops.opaque,s)) return Status::Unavailable;
    if (!ops.retain(ops.opaque,s)) return Status::Unavailable;
    slot_=s; ops_=ops; held_=used_=true;
    if (!ops_.valid(ops_.opaque,slot_) || !ops_.stopped(ops_.opaque,slot_)) return Status::Unavailable;
    *slot_.cpu=0; __sync_synchronize(); // CPU initialization only while stopped
    published_=observed_=0; active_=true; return Status::Ok;
}
Status Timeline::published(uint64_t epoch,uint32_t sequence) {
    if (!held_ || !active_) return Status::NotBound;
    if (epoch!=slot_.epoch) return Status::StaleEpoch;
    if (!ops_.valid(ops_.opaque,slot_)) { active_=false; return Status::Unavailable; }
    if (published_==0xffffffffU) return Status::Exhausted;
    if (!sequence || sequence!=published_+1) return Status::Invalid;
    published_=sequence; return Status::Ok;
}
Status Timeline::observe(uint64_t epoch,Observation &out) {
    out={};
    if (!held_ || !active_) return Status::NotBound;
    if (epoch!=slot_.epoch) return Status::StaleEpoch;
    if (!ops_.valid(ops_.opaque,slot_)) { active_=false; return Status::Unavailable; }
    // The x86_64 aligned qword load is atomic. Fences order CPU observation of
    // direct coherent DMA writes; they are not GPU cache flush instructions.
    __sync_synchronize(); const uint64_t raw=*slot_.cpu; __sync_synchronize();
    if (!ops_.valid(ops_.opaque,slot_)) { active_=false; return Status::Unavailable; }
    if ((raw>>32) || raw>published_ || raw<observed_) { active_=false; return Status::Corrupt; }
    observed_=static_cast<uint32_t>(raw);
    out={slot_.owner,slot_.context,slot_.epoch,slot_.ggtt,raw,observed_,slot_.engineClass,slot_.instance,true};
    return Status::Ok;
}
void Timeline::invalidate() { active_=false; }
Status Timeline::close() {
    if (!held_) return Status::Ok;
    active_=false;
    if (!ops_.stopped(ops_.opaque,slot_)) return Status::Busy;
    ops_.release(ops_.opaque,slot_); held_=false; slot_={}; return Status::Ok;
}
}
