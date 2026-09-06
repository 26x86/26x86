// Local 7D41 research implementation, 2026. See LICENSE and NOTICE.
#pragma once
#include "XeMemory.hpp"
#include "XeSubmission.hpp"

namespace XeMemory {
// Authoritative VM resource ownership for MellowXe's submission queue. The
// transport contributes readiness/submit/readFence/quiesce; its retain/release
// fields are intentionally replaced by the VM implementation below. This object,
// the VM, and transport must outlive the queue. Serialize all their calls in one
// domain. It never pins pages, binds a GPU mapping, or claims HW readiness.
class SubmissionMemoryBridge {
public:
    SubmissionMemoryBridge(VirtualMemory &vm, MellowXe::SubmissionBackend transport)
        : vm_(&vm), transport_(transport) {}
    SubmissionMemoryBridge(const SubmissionMemoryBridge &) = delete;
    SubmissionMemoryBridge &operator=(const SubmissionMemoryBridge &) = delete;

    bool faulted() const { return faulted_; }
    Status lastReleaseStatus() const { return lastRelease_; }
    bool resource(uint64_t owner, Handle handle, MellowXe::Resource &out) const {
        const Allocation *a = vm_->inspect(owner, handle);
        if (faulted_ || !a || a->state != State::Bound || !validPin(*a) || handle.slot == SIZE_MAX)
            return false;
        out = {static_cast<uint64_t>(handle.slot) + 1, owner, handle.generation,
               a->address, a->bytes, true, true};
        return true;
    }
    MellowXe::SubmissionBackend backend() {
        if (!transport_.readiness || !transport_.submit || !transport_.readFence || !transport_.quiesce)
            return MellowXe::unavailableSubmissionBackend();
        return {this, readiness, retain, release, submit, readFence, quiesce};
    }
private:
    VirtualMemory *vm_;
    MellowXe::SubmissionBackend transport_;
    bool faulted_ {};
    Status lastRelease_ {Status::Ok};
    static bool validPin(const Allocation &a) {
        return a.pin.cookie && a.pin.dmaPages && a.pin.pageCount == a.bytes / PageSize;
    }
    const Allocation *resolve(const MellowXe::Resource &r, Handle &handle, bool allowRetiring) const {
        if (!r.id || r.id - 1 > SIZE_MAX || !r.owner || !r.mappingGeneration || !r.pinned || !r.gpuReadable)
            return nullptr;
        handle = {static_cast<size_t>(r.id - 1), r.mappingGeneration};
        const Allocation *a = vm_->inspect(r.owner, handle);
        if (!a || (a->state != State::Bound && !(allowRetiring && a->state == State::Retiring)) ||
            a->address != r.gpuAddress || a->bytes != r.bytes || !validPin(*a)) return nullptr;
        return a;
    }
    static MellowXe::SubmitError readiness(void *opaque, const MellowXe::FirmwareInfo &firmware,
        uint64_t generation, uint64_t owner, uint64_t context, uint32_t engine, MellowXe::Readiness &out) {
        auto &self = *static_cast<SubmissionMemoryBridge *>(opaque);
        if (self.faulted_) return MellowXe::SubmitError::NotReady;
        return self.transport_.readiness(self.transport_.opaque, firmware, generation, owner, context, engine, out);
    }
    static bool retain(void *opaque, const MellowXe::Resource &resource) {
        auto &self = *static_cast<SubmissionMemoryBridge *>(opaque);
        Handle handle {};
        return !self.faulted_ && self.resolve(resource, handle, false) &&
               self.vm_->retainUse(resource.owner, handle) == Status::Ok;
    }
    static void release(void *opaque, const MellowXe::Resource &resource) {
        auto &self = *static_cast<SubmissionMemoryBridge *>(opaque);
        Handle handle {};
        const Status status = self.resolve(resource, handle, true)
            ? self.vm_->releaseUse(resource.owner, handle) : Status::Invalid;
        // A void queue callback cannot report failure. Preserve the evidence and
        // refuse new holds rather than clear a counter on a mismatched object.
        if (status != Status::Ok) { self.lastRelease_ = status; self.faulted_ = true; }
    }
    static MellowXe::BackendAcceptance submit(void *opaque, const MellowXe::BatchSnapshot &batch) {
        auto &self = *static_cast<SubmissionMemoryBridge *>(opaque);
        if (self.faulted_) return MellowXe::BackendAcceptance::Rejected;
        return self.transport_.submit(self.transport_.opaque, batch);
    }
    static MellowXe::SubmitError readFence(void *opaque, uint64_t generation, uint64_t owner,
        uint64_t context, uint32_t engine, MellowXe::FenceObservation &out) {
        auto &self = *static_cast<SubmissionMemoryBridge *>(opaque);
        return self.transport_.readFence(self.transport_.opaque, generation, owner, context, engine, out);
    }
    static bool quiesce(void *opaque, uint64_t generation, uint64_t owner, uint64_t context, uint32_t engine) {
        auto &self = *static_cast<SubmissionMemoryBridge *>(opaque);
        return self.transport_.quiesce(self.transport_.opaque, generation, owner, context, engine);
    }
};
}
