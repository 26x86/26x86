#pragma once
#include "XeFence.hpp"
#include <IOKit/IOMemoryDescriptor.h>

namespace XeFence {
struct MappingProofs {
    void *opaque {};
    bool (*valid)(void *,IOMemoryDescriptor *,uint64_t offset,const Slot &) {};
    bool (*stopped)(void *,const Slot &) {};
    // Authoritative GGTT allocator pin: prevents unbind/address reuse while
    // timeline holds it. Descriptor retention alone cannot pin a GGTT mapping.
    bool (*retainGgtt)(void *,const Slot &) {};
    void (*releaseGgtt)(void *,const Slot &) {};
};
class IOKitSlot {
public:
    IOKitSlot() = default;
    IOKitSlot(const IOKitSlot &) = delete;
    IOKitSlot &operator=(const IOKitSlot &) = delete;
    Status attach(IOMemoryDescriptor *,uint64_t offset,Slot identity,const MappingProofs &);
    Status detach();
    Timeline &timeline() { return timeline_; }
private:
    IOMemoryDescriptor *descriptor_ {};
    IOMemoryMap *map_ {};
    uint64_t offset_ {};
    MappingProofs proofs_ {};
    Timeline timeline_ {};
    bool prepared_ {}, pinned_ {};
    static bool valid(void *,const Slot &);
    static bool retain(void *,const Slot &);
    static void release(void *,const Slot &);
    static bool stopped(void *,const Slot &);
};
}
