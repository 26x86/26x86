// Copyright (c) 2026. Local development; repository LICENSE applies.
#pragma once
#include "XeFirmware.hpp"

namespace MellowXe {
enum class SubmitError : uint8_t {
    None, UnsupportedBackend, NotReady, InvalidArgument, InvalidCommand,
    Ownership, InvalidMapping, ResourceBusy, Capacity, Rejected,
    AcceptanceUnknown, StaleGeneration, InvalidObservation, QuiesceFailed,
    SequenceExhausted, ClockRegression
};
enum class JobState : uint8_t { Free, Submitted, AcceptanceUnknown, Completed, TimedOut, Reset };
enum class QueueState : uint8_t { Inactive, Ready, NeedsReset };
enum class BackendAcceptance : uint8_t { Accepted, Rejected, Unknown };
constexpr unsigned maxJobs = 32, maxResources = 8, maxBatchWords = 64;
constexpr uint32_t miNoop = 0x00000000U;
constexpr uint32_t miBatchBufferEnd = 0x05000000U;
// Verified MI encodings, only a bootstrap NOOP...END stream. No compute/Metal
// shader, ELF, SPIR-V, privileged register-write or nested batch is accepted.
SubmitError validateBootstrapBatch(const uint32_t *words, unsigned count);

struct Resource {
    // mappingGeneration identifies the VM allocation handle, NOT the queue's
    // reset epoch. retain must resolve id/generation in the authoritative VM.
    uint64_t id {}, owner {}, mappingGeneration {}, gpuAddress {}, bytes {};
    bool gpuReadable {}, pinned {};
};
struct FenceToken { uint64_t generation {}; uint32_t sequence {}; };
struct BatchSnapshot {
    FenceToken fence {};
    uint64_t owner {}, context {}, deadline {};
    uint32_t engine {};
    uint32_t words[maxBatchWords] {};
    unsigned wordCount {};
    Resource resources[maxResources] {};
    unsigned resourceCount {};
};
enum ReadyBits : uint32_t {
    DeviceIdentityAndGmdVerified = 1U << 0, DmaReady = 1U << 1,
    PageTablesReady = 1U << 2, GuCAuthenticated = 1U << 3,
    ContextRegistered = 1U << 4, InterruptsReady = 1U << 5,
    CoherentFenceReady = 1U << 6, SubmissionAbiCompatible = 1U << 7
};
constexpr uint32_t requiredReadyBits = (1U << 8) - 1;
struct Readiness { uint64_t generation {}, owner {}, context {}; uint32_t engine {}, flags {}; };
struct FenceObservation {
    uint64_t generation {}, owner {}, context {};
    uint32_t engine {};
    uint32_t completedSequence {};
    bool valid {}, acquireOrdered {};
};
// Hardware boundary. No implementation is provided for 7D41 yet. Future adapter
// must really program/authenticate GuC, submit a mapped immutable batch and
// read an acquire-ordered HW seqno. IRQ arrival alone is not completion.
// Calls are serialized by the owning IOWorkLoop/command gate; no reentrancy.
struct SubmissionBackend {
    void *opaque {};
    SubmitError (*readiness)(void *, const FirmwareInfo &, uint64_t generation, uint64_t owner,
                            uint64_t context, uint32_t engine, Readiness &) {};
    bool (*retain)(void *, const Resource &) {};
    void (*release)(void *, const Resource &) {};
    BackendAcceptance (*submit)(void *, const BatchSnapshot &) {};
    SubmitError (*readFence)(void *, uint64_t generation, uint64_t owner,
                            uint64_t context, uint32_t engine, FenceObservation &) {};
    bool (*quiesce)(void *, uint64_t generation, uint64_t owner, uint64_t context, uint32_t engine) {};
};
struct JobResult { JobState state {JobState::Free}; bool resourcesHeld {}; FenceToken token {}; };

// Bounded allocation-free state machine. It manages software ownership and
// fence lifecycle; it does not implement GuC hardware transport. Allocate off
// the kernel stack (~16 KiB), serialize every call, and quiesce before teardown.
class SubmissionQueue {
public:
    SubmissionQueue(uint64_t owner, uint64_t context, SubmissionBackend backend, uint32_t engine = 0);
    SubmissionQueue(const SubmissionQueue &) = delete;
    SubmissionQueue &operator=(const SubmissionQueue &) = delete;
    SubmitError activate(const FirmwareInfo &firmware);
    SubmitError submit(const uint32_t *words, unsigned wordCount, const Resource *resources,
                       unsigned resourceCount, uint64_t now, uint64_t deadline, FenceToken &token);
    SubmitError onInterrupt(uint64_t irqGeneration, uint64_t now);
    SubmitError expire(uint64_t now);
    SubmitError reset(uint64_t now);
    SubmitError query(FenceToken token, JobResult &result) const;
    SubmitError retire(FenceToken token);
    QueueState state() const { return state_; }
    uint64_t generation() const { return generation_; }
private:
#ifdef MELLOW_XE_TESTS
    friend struct SubmissionQueueTestAccess;
#endif
    struct Job { BatchSnapshot batch {}; JobState state {JobState::Free}; bool held {}; };
    Job jobs_[maxJobs] {};
    SubmissionBackend backend_ {};
    uint64_t owner_ {}, context_ {}, generation_ {1}, lastTime_ {};
    uint32_t engine_ {};
    uint32_t nextSequence_ {1}, lastSubmitted_ {}, lastObserved_ {};
    bool exhausted_ {};
    QueueState state_ {QueueState::Inactive};
    bool completeBackend() const;
    bool tick(uint64_t now);
    void release(Job &job);
    Job *find(FenceToken token);
    const Job *find(FenceToken token) const;
};
// Default factory is deliberately unavailable; not a mock pretending to be HW.
inline SubmissionBackend unavailableSubmissionBackend() { return {}; }
}
