// Copyright (c) 2026. Local development; repository LICENSE applies.
#include "XeSubmission.hpp"
namespace MellowXe {
SubmitError validateBootstrapBatch(const uint32_t *words, unsigned count) {
    if (!words || !count || count > maxBatchWords) return SubmitError::InvalidArgument;
    for (unsigned i = 0; i < count; ++i) {
        if (words[i] == miBatchBufferEnd)
            return i == count - 1 ? SubmitError::None : SubmitError::InvalidCommand;
        if (words[i] != miNoop) return SubmitError::InvalidCommand;
    }
    return SubmitError::InvalidCommand;
}
SubmissionQueue::SubmissionQueue(uint64_t owner, uint64_t context, SubmissionBackend backend, uint32_t engine)
    : backend_(backend), owner_(owner), context_(context), engine_(engine) {}
bool SubmissionQueue::completeBackend() const {
    return backend_.readiness && backend_.retain && backend_.release && backend_.submit &&
           backend_.readFence && backend_.quiesce;
}
bool SubmissionQueue::tick(uint64_t now) {
    if (now < lastTime_) return false;
    lastTime_ = now; return true;
}
SubmitError SubmissionQueue::activate(const FirmwareInfo &firmware) {
    if (!completeBackend()) return SubmitError::UnsupportedBackend;
    if (!owner_ || !context_ || state_ != QueueState::Inactive) return SubmitError::NotReady;
    if (firmware.release.major != 70 || firmware.release.packed() < gucMinimumRelease ||
        !firmware.ucodeBytes || !firmware.rsaBytes) return SubmitError::InvalidArgument;
    Readiness ready {};
    const auto error = backend_.readiness(backend_.opaque, firmware, generation_, owner_, context_, engine_, ready);
    if (error != SubmitError::None) return error;
    if (ready.generation != generation_ || ready.owner != owner_ || ready.context != context_ || ready.engine != engine_ ||
        (ready.flags & requiredReadyBits) != requiredReadyBits) return SubmitError::NotReady;
    state_ = QueueState::Ready;
    return SubmitError::None;
}
void SubmissionQueue::release(Job &job) {
    if (!job.held) return;
    for (unsigned i = job.batch.resourceCount; i > 0; --i)
        backend_.release(backend_.opaque, job.batch.resources[i-1]);
    job.held = false;
}
SubmissionQueue::Job *SubmissionQueue::find(FenceToken token) {
    for (auto &job : jobs_)
        if (job.state != JobState::Free && job.batch.fence.generation == token.generation &&
            job.batch.fence.sequence == token.sequence) return &job;
    return nullptr;
}
const SubmissionQueue::Job *SubmissionQueue::find(FenceToken token) const {
    for (const auto &job : jobs_)
        if (job.state != JobState::Free && job.batch.fence.generation == token.generation &&
            job.batch.fence.sequence == token.sequence) return &job;
    return nullptr;
}
SubmitError SubmissionQueue::submit(const uint32_t *words, unsigned wordCount,
        const Resource *resources, unsigned resourceCount, uint64_t now, uint64_t deadline,
        FenceToken &token) {
    token = {};
    if (!completeBackend()) return SubmitError::UnsupportedBackend;
    if (state_ != QueueState::Ready) return SubmitError::NotReady;
    if (!tick(now)) return SubmitError::ClockRegression;
    if (deadline <= now || !resources || !resourceCount || resourceCount > maxResources)
        return SubmitError::InvalidArgument;
    if (!words || !wordCount || wordCount > maxBatchWords) return SubmitError::InvalidArgument;
    if (exhausted_) return SubmitError::SequenceExhausted;
    Job *job = nullptr;
    for (auto &candidate : jobs_) if (candidate.state == JobState::Free) { job = &candidate; break; }
    if (!job) return SubmitError::Capacity;
    // Freeze caller-supplied bytes BEFORE validating them (no validate/copy gap).
    *job = {};
    job->batch.fence = {generation_, nextSequence_};
    job->batch.owner = owner_; job->batch.context = context_; job->batch.deadline = deadline;
    job->batch.engine = engine_;
    job->batch.wordCount = wordCount; job->batch.resourceCount = resourceCount;
    for (unsigned i = 0; i < wordCount; ++i) job->batch.words[i] = words[i];
    for (unsigned i = 0; i < resourceCount; ++i) job->batch.resources[i] = resources[i];
    auto validation = validateBootstrapBatch(job->batch.words, wordCount);
    if (validation != SubmitError::None) return validation;
    for (unsigned i = 0; i < resourceCount; ++i) {
        const auto &r = job->batch.resources[i];
        if (!r.id || r.owner != owner_) return SubmitError::Ownership;
        // Raw 48-bit GPU virtual addresses only in this bootstrap policy. A
        // future VM adapter must resolve these handles against its own mappings.
        if (!r.mappingGeneration || !r.bytes || !r.pinned || !r.gpuReadable ||
            (r.gpuAddress & 3U) || r.gpuAddress >= (1ULL << 48) || r.bytes > (1ULL << 48) - r.gpuAddress)
            return SubmitError::InvalidMapping;
        for (unsigned j = 0; j < i; ++j)
            if (job->batch.resources[j].id == r.id) return SubmitError::InvalidArgument;
    }
    unsigned retained = 0;
    for (; retained < resourceCount; ++retained)
        if (!backend_.retain(backend_.opaque, job->batch.resources[retained])) break;
    if (retained != resourceCount) {
        while (retained) backend_.release(backend_.opaque, job->batch.resources[--retained]);
        *job = {}; return SubmitError::ResourceBusy;
    }
    job->held = true;
    const auto accepted = backend_.submit(backend_.opaque, job->batch);
    if (accepted == BackendAcceptance::Rejected) {
        release(*job); *job = {}; return SubmitError::Rejected;
    }
    // A possibly accepted submission cannot release mappings or reuse its seqno.
    token = job->batch.fence;
    lastSubmitted_ = nextSequence_;
    if (nextSequence_ == 0xFFFFFFFFU) exhausted_ = true;
    else ++nextSequence_;
    if (accepted != BackendAcceptance::Accepted) {
        job->state = JobState::AcceptanceUnknown; state_ = QueueState::NeedsReset;
        return SubmitError::AcceptanceUnknown;
    }
    job->state = JobState::Submitted;
    return SubmitError::None;
}
SubmitError SubmissionQueue::expire(uint64_t now) {
    if (!tick(now)) return SubmitError::ClockRegression;
    for (auto &job : jobs_) {
        if (job.state == JobState::Submitted && now >= job.batch.deadline) {
            job.state = JobState::TimedOut; state_ = QueueState::NeedsReset;
            // Timeout does NOT establish that DMA stopped. Keep every resource.
        }
    }
    return SubmitError::None;
}
SubmitError SubmissionQueue::onInterrupt(uint64_t irqGeneration, uint64_t now) {
    if (irqGeneration != generation_) return SubmitError::StaleGeneration;
    if (!completeBackend()) return SubmitError::UnsupportedBackend;
    if (state_ == QueueState::Inactive) return SubmitError::NotReady;
    auto e = expire(now);
    if (e != SubmitError::None) return e;
    FenceObservation observation {};
    e = backend_.readFence(backend_.opaque, generation_, owner_, context_, engine_, observation);
    if (e != SubmitError::None) return e;
    if (!observation.valid || !observation.acquireOrdered || observation.generation != generation_ || observation.owner != owner_ ||
        observation.context != context_ || observation.engine != engine_ || observation.completedSequence < lastObserved_ ||
        observation.completedSequence > lastSubmitted_) return SubmitError::InvalidObservation;
    lastObserved_ = observation.completedSequence;
    for (auto &job : jobs_) {
        if (job.batch.fence.generation != generation_ || job.batch.fence.sequence > lastObserved_) continue;
        if (job.state == JobState::Submitted) { job.state = JobState::Completed; release(job); }
        // A late hardware fence can release DMA ownership, but cannot turn the
        // already delivered timeout/unknown result into successful completion.
        else if (job.state == JobState::TimedOut || job.state == JobState::AcceptanceUnknown) release(job);
    }
    return SubmitError::None;
}
SubmitError SubmissionQueue::reset(uint64_t now) {
    if (!completeBackend()) return SubmitError::UnsupportedBackend;
    if (!tick(now)) return SubmitError::ClockRegression;
    state_ = QueueState::NeedsReset;
    if (generation_ == UINT64_MAX) return SubmitError::SequenceExhausted;
    if (!backend_.quiesce(backend_.opaque, generation_, owner_, context_, engine_)) return SubmitError::QuiesceFailed;
    // Adapter must stop this queue's DMA AND drain its IRQ/deferred callbacks.
    for (auto &job : jobs_) {
        if (job.state == JobState::Submitted || job.state == JobState::AcceptanceUnknown)
            job.state = JobState::Reset;
        release(job);
    }
    ++generation_; nextSequence_ = 1; lastSubmitted_ = lastObserved_ = 0; exhausted_ = false;
    state_ = QueueState::Inactive;
    return SubmitError::None;
}
SubmitError SubmissionQueue::query(FenceToken token, JobResult &result) const {
    result = {};
    const auto *job = find(token);
    if (!job) return SubmitError::StaleGeneration;
    result = {job->state, job->held, job->batch.fence}; return SubmitError::None;
}
SubmitError SubmissionQueue::retire(FenceToken token) {
    auto *job = find(token);
    if (!job) return SubmitError::StaleGeneration;
    if (job->held || job->state == JobState::Submitted) return SubmitError::ResourceBusy;
    *job = {}; return SubmitError::None;
}
}
