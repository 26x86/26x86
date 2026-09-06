#include "XeContextExecution.hpp"
namespace XeContext {
bool EvidenceExecution::allowed() const {
    return backend_.admitted && backend_.admitted(backend_.opaque,context_,policy_);
}
unsigned EvidenceExecution::retainedVmUses() const {unsigned n=0;for(bool h:vmHeld_)n+=h;return n;}
bool EvidenceExecution::releaseVm() {
    bool ok=true;
    for(size_t i=6;i>0;--i)if(vmHeld_[i-1]) {
        if(vm_.releaseUse(context_.owner,handles_[i-1])==XeMemory::Status::Ok)vmHeld_[i-1]=false;
        else ok=false;
    }
    return ok;
}
ExecutionStatus EvidenceExecution::fail(ExecutionStatus s) {state_=ExecutionState::Failed;return s;}
ExecutionStatus EvidenceExecution::begin(const XeZebin::Image &image,const LiveContext &c,
    const XeMemory::Handle (&handles)[6],const XeDispatch::Policy &p,uint32_t nonce,uint32_t count,
    bool depthWa,uint64_t now,uint64_t deadline) {
    if(attempted_)return ExecutionStatus::Busy;
    attempted_=true;context_=c;policy_=p;deadline_=deadline;lastNow_=now;
    for(size_t i=0;i<6;++i)handles_[i]=handles[i];
    if(!c.owner || !c.epoch || !c.allocation || !c.id || c.id>=65535 ||
       !c.ggttContext || (c.ggttContext&4095U) || !c.ggttRing || (c.ggttRing&4095U) ||
       !c.ringCpu || (reinterpret_cast<uintptr_t>(c.ringCpu)&3U) || !c.lrcTailCpu ||
       (reinterpret_cast<uintptr_t>(c.lrcTailCpu)&3U) || c.ringBytes<4096 || c.ringBytes>2097152 ||
       (c.ringBytes&(c.ringBytes-1)) || uint64_t(c.ggttContext)+ImageBytes>(1ULL<<32) ||
       uint64_t(c.ggttRing)+c.ringBytes>(1ULL<<32) || c.descriptor!=(uint64_t(c.ggttContext)|0x119ULL) ||
       (uint64_t(c.ggttContext)<uint64_t(c.ggttRing)+c.ringBytes && uint64_t(c.ggttRing)<uint64_t(c.ggttContext)+ImageBytes) ||
       depthWa!=c.depthStallWorkaround || deadline<=now || !backend_.freshStopped || !backend_.retainContext || !backend_.releaseContext ||
       !backend_.stageHeaps || !backend_.synchronizeContext || !backend_.quiesced)
        return fail(ExecutionStatus::Invalid);
    if(!allowed() || !backend_.freshStopped(backend_.opaque,context_))return fail(ExecutionStatus::Unavailable);
    XeFence::Observation initial;
    if(fence_.lastPublished()!=0 || fence_.observe(c.epoch,initial)!=XeFence::Status::Ok ||
       initial.owner!=c.owner || initial.context!=c.id || initial.epoch!=c.epoch ||
       initial.engineClass!=0 || initial.instance!=0 || !initial.acquireOrdered || initial.raw!=0 ||
       initial.ggtt!=fence_.address())
        return fail(ExecutionStatus::Unavailable);
    if(!backend_.retainContext(backend_.opaque,context_))return fail(ExecutionStatus::Unavailable);
    contextHeld_=true;state_=ExecutionState::Held;
    for(size_t i=0;i<6;++i) {
        if(vm_.retainUse(c.owner,handles_[i])!=XeMemory::Status::Ok)return fail(ExecutionStatus::Unavailable);
        vmHeld_[i]=true;
    }
    if(XeDispatch::prepareBoundEvidence(image,vm_,c.owner,handles_,p,nonce,count,prepared_)!=XeDispatch::Error::None)
        return fail(ExecutionStatus::Invalid);
    if(!allowed() || !backend_.freshStopped(backend_.opaque,context_) ||
       !backend_.stageHeaps(backend_.opaque,context_,handles_,prepared_))return fail(ExecutionStatus::Unavailable);
    XeDispatch::RingJob job;
    if(XeDispatch::encodeRenderRingJob(prepared_.layout.batch,uint32_t(fence_.address()),1,depthWa,job)!=XeDispatch::Error::None)
        return fail(ExecutionStatus::Invalid);
    // From here even a failure after tail publication retains all resources.
    if(!allowed() || !backend_.freshStopped(backend_.opaque,context_) || *context_.lrcTailCpu!=0)
        return fail(ExecutionStatus::Unavailable);
    uint32_t next=0;
    if(appendRing(context_.ringCpu,c.ringBytes,0,0,job.words,job.count,next)!=Error::None)
        return fail(ExecutionStatus::Invalid);
    if(fence_.published(c.epoch,1)!=XeFence::Status::Ok)return fail(ExecutionStatus::Unavailable);
    __sync_synchronize();*context_.lrcTailCpu=next;__sync_synchronize();
    if(!backend_.synchronizeContext(backend_.opaque,context_) || !allowed())return fail(ExecutionStatus::Quarantined);
    XeGuC::Action action;
    if(XeGuC::encodeRegister(c.id,0,1,c.descriptor,action)!=XeGuC::Status::Ok)return fail(ExecutionStatus::Invalid);
    if(guc_.send(action,now,deadline,registration_)!=XeGuC::Status::Ok)return fail(ExecutionStatus::Quarantined);
    state_=ExecutionState::Registered;
    return poll(now);
}
ExecutionStatus EvidenceExecution::poll(uint64_t now) {
    if(state_==ExecutionState::Completed)return ExecutionStatus::Ok;
    if(state_==ExecutionState::Closed || state_==ExecutionState::Idle)return ExecutionStatus::Invalid;
    // Failed/time-out jobs may still complete later; no retry can republish work.
    if(now<lastNow_)return fail(ExecutionStatus::Quarantined);
    lastNow_=now;
    if(!allowed())return fail(ExecutionStatus::Quarantined);
    if(state_==ExecutionState::Registered) {
        XeGuC::Reply reply;
        if(guc_.query(registration_,reply)!=XeGuC::Status::Ok || reply.state==XeGuC::ReplyState::Failure)
            return fail(ExecutionStatus::Quarantined);
        if(now>=deadline_)return fail(ExecutionStatus::Timeout);
        XeGuC::Action mode;
        XeGuC::encodeMode(context_.id,true,mode);
        auto sent=guc_.send(mode,now,deadline_,enable_);
        if(sent==XeGuC::Status::Busy)return ExecutionStatus::Busy;
        if(sent!=XeGuC::Status::Ok)return fail(ExecutionStatus::Quarantined);
        // Single LRC: MODE_SET(enable) itself schedules the published ring.
        // Do not send another SCHED_CONTEXT as though enable were inert.
        state_=ExecutionState::Enabling;
    }
    if(state_==ExecutionState::Enabling || state_==ExecutionState::Running) {
        XeGuC::Reply registration,reply;
        if(guc_.query(registration_,registration)!=XeGuC::Status::Ok ||
           registration.state==XeGuC::ReplyState::Failure ||
           guc_.query(enable_,reply)!=XeGuC::Status::Ok || reply.state==XeGuC::ReplyState::Failure ||
           reply.state==XeGuC::ReplyState::Retry)return fail(ExecutionStatus::Quarantined);
        if(reply.state==XeGuC::ReplyState::Success)state_=ExecutionState::Running;
    }
    XeFence::Observation observed;
    if(fence_.observe(context_.epoch,observed)!=XeFence::Status::Ok || !observed.acquireOrdered ||
       observed.owner!=context_.owner || observed.context!=context_.id || observed.epoch!=context_.epoch ||
       observed.engineClass!=0 || observed.instance!=0 || observed.ggtt!=fence_.address())
        return fail(ExecutionStatus::Quarantined);
    if(observed.sequence==1 && enable_.epoch) {
        if(!releaseVm())return fail(ExecutionStatus::Quarantined);
        state_=ExecutionState::Completed;return ExecutionStatus::Ok;
    }
    if(now>=deadline_)return fail(ExecutionStatus::Timeout);
    return state_==ExecutionState::Failed ? ExecutionStatus::Quarantined : ExecutionStatus::Pending;
}
ExecutionStatus EvidenceExecution::close() {
    if(state_==ExecutionState::Closed)return ExecutionStatus::Ok;
    if(!attempted_)return ExecutionStatus::Invalid;
    if(contextHeld_) {
        if(!backend_.quiesced(backend_.opaque,context_))return ExecutionStatus::Busy;
        // Fence has its own independent proof of the same hardware quiescence.
        if(fence_.close()!=XeFence::Status::Ok)return ExecutionStatus::Busy;
        if(!releaseVm())return fail(ExecutionStatus::Quarantined);
        if(!backend_.releaseContext(backend_.opaque,context_))return fail(ExecutionStatus::Quarantined);
        contextHeld_=false;
    }
    state_=ExecutionState::Closed;return ExecutionStatus::Ok;
}
}
