// Local ordered observation of a real GPU-written coherent GGTT fence slot.
#pragma once
#include <stdint.h>

namespace XeFence {
enum class Status : uint8_t { Ok, Invalid, Unavailable, StaleEpoch, Busy, Exhausted, Corrupt, NotBound };
struct Slot {
    volatile uint64_t *cpu {};
    uint64_t ggtt {}, allocation {}, owner {}, context {}, epoch {};
    uint8_t engineClass {}, instance {}; // hardware IRQ classes: render0/copy3/compute5
};
struct Ops {
    void *opaque {};
    // Validate exact descriptor/GGTT/CPU ownership, prepared direct coherent
    // SMEM, PAT/cache policy and exclusive GPU-write access. No bounce memory.
    bool (*valid)(void *, const Slot &) {};
    bool (*retain)(void *, const Slot &) {};
    void (*release)(void *, const Slot &) {};
    // Hardware quiescence, not timeout, needed before CPU clear/free/reuse.
    bool (*stopped)(void *, const Slot &) {};
};
struct Observation {
    uint64_t owner {}, context {}, epoch {}, ggtt {}, raw {};
    uint32_t sequence {};
    uint8_t engineClass {}, instance {};
    bool acquireOrdered {};
};
// Single serialized workloop owner. The sole device write format is a qword
// GGTT post-sync {sequence32,0}; flush/stall and MI_USER_INTERRUPT are emitted
// by the command builder. CPU never manufactures completion. No sequence wrap.
class Timeline {
public:
    Timeline() = default;
    Timeline(const Timeline &) = delete;
    Timeline &operator=(const Timeline &) = delete;
    Status bind(const Slot &,const Ops &);
    Status published(uint64_t epoch,uint32_t sequence);
    Status observe(uint64_t epoch,Observation &);
    void invalidate(); // retains mapping; reset is not successful completion
    Status close(); // releases only after confirmed context/GT quiescence
    uint64_t address() const { return held_ ? slot_.ggtt : 0; }
    uint32_t lastPublished() const { return published_; }
    bool held() const { return held_; }
private:
    Slot slot_ {}; Ops ops_ {};
    uint32_t published_ {}, observed_ {};
    bool held_ {}, active_ {}, used_ {};
};
}
