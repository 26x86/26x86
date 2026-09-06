// One trusted evidence job: real VM holds, native command bytes, GuC and fence.
#pragma once
#include "XeContext.hpp"
#include "XeDispatch.hpp"
#include "XeGuCTransport.hpp"
#include "XeFence.hpp"
namespace XeContext {
enum class ExecutionStatus { Ok, Pending, Invalid, Unavailable, Busy, Timeout, Quarantined };
enum class ExecutionState { Idle, Held, Registered, Enabling, Running, Completed, Failed, Closed };
struct LiveContext {
    uint64_t owner {},epoch {},allocation {};
    uint32_t id {},ggttContext {},ggttRing {},ringBytes {};
    uint32_t *ringCpu {};
    volatile uint32_t *lrcTailCpu {};
    uint64_t descriptor {};
    bool depthStallWorkaround {};
};
struct ExecutionBackend {
    void *opaque {};
    // These driver callbacks are authoritative inspections, never flags or
    // predicates supplied by an IOUserClient. Exact retained GGTT mappings,
    // actual primed context/WA/preemption/PPGTT/TLB/PAT/MOCS/topology, loaded
    // GuC+full ADS and IRQ routing must all be established. No default exists.
    bool (*admitted)(void *,const LiveContext &,const XeDispatch::Policy &) {};
    // Fresh, disabled, unregistered context and empty ring, no concurrent owner.
    bool (*freshStopped)(void *,const LiveContext &) {};
    bool (*retainContext)(void *,const LiveContext &) {};
    bool (*releaseContext)(void *,const LiveContext &) {};
    // Copy immutable staging to the exact six held VM allocations and perform
    // real DMA/coherency synchronization; must not publish a context or tail.
    bool (*stageHeaps)(void *,const LiveContext &,const XeMemory::Handle (&)[6],const XeDispatch::Prepared &) {};
    // Actual direct-coherent ring/LRC visibility barrier after CPU writes.
    bool (*synchronizeContext)(void *,const LiveContext &) {};
    // Hardware stop/reset or disabled+deregistered context acknowledged idle.
    bool (*quiesced)(void *,const LiveContext &) {};
};
// One instance, one job, one reserved sequence (1), one immutable reset epoch.
// Allocate off-stack. VM, GuC transport, fence and backend outlive close().
// All entrypoints and G2H receive dispatch run under the same ownership lock.
// Caller services Transport::receive from the real GuC IRQ/workloop; poll reads
// its correlated control replies and the actual XeFence memory observation.
class EvidenceExecution {
public:
    EvidenceExecution(XeMemory::VirtualMemory &vm,XeGuC::Transport &guc,XeFence::Timeline &fence,
                      ExecutionBackend backend) : vm_(vm),guc_(guc),fence_(fence),backend_(backend) {}
    EvidenceExecution(const EvidenceExecution &)=delete;
    EvidenceExecution &operator=(const EvidenceExecution &)=delete;
    ExecutionStatus begin(const XeZebin::Image &,const LiveContext &,const XeMemory::Handle (&)[6],
        const XeDispatch::Policy &,uint32_t nonce,uint32_t count,bool depthStallWa,uint64_t now,uint64_t deadline);
    ExecutionStatus poll(uint64_t now);
    // Never invents completion. May release after confirmed quiescence even if
    // command acceptance was unknown. A timeout alone cannot make close pass.
    ExecutionStatus close();
    ExecutionState state() const { return state_; }
    unsigned retainedVmUses() const;
    bool contextHeld() const { return contextHeld_; }
private:
    XeMemory::VirtualMemory &vm_;XeGuC::Transport &guc_;XeFence::Timeline &fence_;
    ExecutionBackend backend_ {};LiveContext context_ {};XeDispatch::Policy policy_ {};
    XeMemory::Handle handles_[6] {};bool vmHeld_[6] {},contextHeld_ {},attempted_ {};
    XeDispatch::Prepared prepared_ {};
    XeGuC::Cookie registration_ {},enable_ {};
    uint64_t deadline_ {},lastNow_ {};ExecutionState state_ {ExecutionState::Idle};
    ExecutionStatus fail(ExecutionStatus);
    bool releaseVm();
    bool allowed() const;
};
}
