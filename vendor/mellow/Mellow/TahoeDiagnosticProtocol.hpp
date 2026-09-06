// Local diagnostic lifecycle, 2026. See repository LICENSE and NOTICE.
#pragma once
#include "TahoeDiagnosticABI.h"
#include "XeMemory.hpp"
namespace MellowDiagnostic {
struct Identity { uint32_t vendor {}, device {}, architecture {}, release {}; };
// All calls are serialized by the IOService's sleepable mutex. No callback may
// publish GPU mappings or start DMA; these are prepared, unpublished buffers.
class Session {
public:
    Session() = default;
    Session(const Session &) = delete;
    Session &operator=(const Session &) = delete;
    bool initialize(Identity identity, bool barMapped, XeMemory::Backend backend, uint64_t evidence);
    bool open(uint64_t owner);
    uint32_t close(uint64_t owner);
    uint32_t stop();
    bool owns(uint64_t owner) const { return owner && owner_ == owner; }
    bool hasResources() const { return pin_.cookie || pin_.dmaPages || pin_.pageCount; }
    bool quarantined() const { return state_ == MellowDiagFaulted && hasResources(); }
    void call(uint64_t owner, uint32_t selector, const MellowDiagRequest &, MellowDiagReply &);
private:
    Identity identity_ {};
    XeMemory::Backend backend_ {};
    XeMemory::Pin pin_ {};
    uint64_t owner_ {}, nextHandle_ {1}, handle_ {}, bytes_ {}, evidence_ {};
    uint32_t state_ {MellowDiagCold};
    bool stopped_ {};
    uint32_t releaseAllocation();
    void describe(uint32_t status, MellowDiagReply &) const;
};
}
