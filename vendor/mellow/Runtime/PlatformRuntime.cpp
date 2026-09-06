#include "PlatformRuntime.hpp"

namespace MellowRT {
bool sameDevice(const DeviceIdentity &a, const DeviceIdentity &b) {
    return a.vendorId == b.vendorId && a.deviceId == b.deviceId &&
           a.revision == b.revision && a.instance == b.instance;
}
namespace {
bool validProvider(const ProviderDescriptor &p) {
    if (!p.id || !p.device.instance || !p.resetEpoch ||
        p.evidenceEpoch != p.resetEpoch || !p.validationRecord ||
        (p.verified & ~p.advertised) || (p.advertised & ~KnownFeatures)) return false;
    if (p.api == Api::CpuReference)
        return p.kind == ProviderKind::Reference && p.execution == Execution::Software;
    if (p.api != Api::OpenGL && p.api != Api::OpenCL && p.api != Api::Native) return false;
    return (p.kind == ProviderKind::Host || p.kind == ProviderKind::Mellow) &&
           (p.execution == Execution::Hardware || p.execution == Execution::Software) &&
           p.device.vendorId && p.device.deviceId;
}
bool versionAtLeast(const ProviderDescriptor &p, uint16_t major, uint16_t minor) {
    return p.apiMajor > major || (p.apiMajor == major && p.apiMinor >= minor);
}
Features baseline(Workload workload) {
    switch (workload) {
        case Workload::Compute: return bit(Feature::Compute) | bit(Feature::ComputeTranslation);
        case Workload::Render: return bit(Feature::Render) | bit(Feature::RenderTranslation);
        case Workload::Blit: return bit(Feature::Blit);
    }
    return 0;
}
bool supports(const ProviderDescriptor &p, const Step &s, bool reference) {
    if (s.requiredProvider && s.requiredProvider != p.id) return false;
    if (reference) {
        if (p.api != Api::CpuReference) return false;
    } else if (p.execution != Execution::Hardware || p.api == Api::CpuReference) return false;
    if (s.input == WorkloadInput::OpenClC && (p.api != Api::OpenCL || s.workload != Workload::Compute)) return false;
    const Features operations = s.input == WorkloadInput::OpenClC ? bit(Feature::Compute) : baseline(s.workload);
    const Features needed = operations | s.required | bit(Feature::OrderedQueue);
    if ((p.verified & needed) != needed) return false;
    if (p.api == Api::OpenGL) {
        // Core compute shaders arrived in GL 4.3. GL 4.1 availability is not
        // evidence that compute translation can be executed by this provider.
        return s.workload == Workload::Compute ? versionAtLeast(p, 4, 3) : versionAtLeast(p, 4, 1);
    }
    if (p.api == Api::OpenCL)
        return s.workload != Workload::Render && versionAtLeast(p, 1, 2);
    return true;
}
struct Search {
    const ProviderDescriptor *providers;
    size_t providerCount;
    const Step *steps;
    size_t stepCount;
    const Dependency *dependencies;
    size_t dependencyCount;
    const TransferContract *contracts;
    size_t contractCount;
    bool reference;
    size_t budget;
    size_t attempts {};
    bool limitReached {};
    size_t selected[MaxSteps] {};
    TransferMode modes[MaxDependencies] {};

    bool transfer(const Dependency &d, TransferMode &mode) const {
        const auto &a = providers[selected[d.producer]];
        const auto &b = providers[selected[d.consumer]];
        if (a.id == b.id) { mode = TransferMode::None; return true; }
        // Prefer verified sharing. Copies are considered only on caller opt-in.
        for (unsigned pass = 0; pass < 2; ++pass) {
            const auto wanted = pass == 0 ? TransferMode::SharedResource : TransferMode::ExplicitCopy;
            if (wanted == TransferMode::ExplicitCopy && d.policy != TransferPolicy::SharedOrExplicitCopy) continue;
            for (size_t i = 0; i < contractCount; ++i) {
                const auto &c = contracts[i];
                if (c.producerProvider == a.id && c.consumerProvider == b.id &&
                    c.resource == d.resource && c.producerEpoch == a.resetEpoch &&
                    c.consumerEpoch == b.resetEpoch && c.mode == wanted &&
                    c.resourceCompatibilityVerified && c.orderingVerified &&
                    c.contentsPreservedVerified && c.validationRecord) {
                    mode = wanted;
                    return true;
                }
            }
        }
        return false;
    }
    bool choose(size_t step) {
        if (step == stepCount) return true;
        for (size_t i = 0; i < providerCount; ++i) {
            if (attempts == budget) { limitReached = true; return false; }
            ++attempts;
            if (!supports(providers[i], steps[step], reference)) continue;
            selected[step] = i;
            bool compatible = true;
            for (size_t edge = 0; edge < dependencyCount; ++edge) {
                if (dependencies[edge].consumer == step && !transfer(dependencies[edge], modes[edge])) {
                    compatible = false;
                    break;
                }
            }
            if (compatible && choose(step + 1)) return true;
            if (limitReached) return false;
        }
        return false;
    }
};
bool sameToken(const SubmissionToken &a, const SubmissionToken &b) {
    return a.provider == b.provider && a.deviceInstance == b.deviceInstance &&
           a.epoch == b.epoch && a.queue == b.queue && a.sequence == b.sequence;
}
bool validDigest(const Digest256 &d) {
    for (uint8_t byte : d.bytes) if (byte) return true;
    return false;
}
bool sameDigest(const Digest256 &a, const Digest256 &b) {
    for (size_t i = 0; i < sizeof(a.bytes); ++i) if (a.bytes[i] != b.bytes[i]) return false;
    return true;
}
} // namespace

RoutePlan planWorkload(const ProviderDescriptor *providers, size_t providerCount,
                       const Step *steps, size_t stepCount,
                       const Dependency *dependencies, size_t dependencyCount,
                       const TransferContract *contracts, size_t contractCount,
                       PlanOptions options) {
    RoutePlan plan {};
    if (!providers || !providerCount || providerCount > MaxProviders || !steps ||
        !stepCount || stepCount > MaxSteps || dependencyCount > MaxDependencies || contractCount > MaxTransfers ||
        (dependencyCount && !dependencies) || (contractCount && !contracts) ||
        !options.searchBudget || options.searchBudget > MaxSearchAttempts) return plan;
    for (size_t i = 0; i < providerCount; ++i) {
        if (!validProvider(providers[i])) return plan;
        for (size_t j = 0; j < i; ++j) if (providers[j].id == providers[i].id) return plan;
    }
    for (size_t i = 0; i < stepCount; ++i)
        if (!baseline(steps[i].workload) || (steps[i].required & ~KnownFeatures) ||
            (steps[i].input != WorkloadInput::MetalSemantics && steps[i].input != WorkloadInput::OpenClC)) return plan;
    for (size_t i = 0; i < dependencyCount; ++i) {
        const auto &d = dependencies[i];
        if (!d.resource || d.producer >= d.consumer || d.consumer >= stepCount ||
            (d.policy != TransferPolicy::SharedOnly && d.policy != TransferPolicy::SharedOrExplicitCopy)) return plan;
    }
    for (size_t i = 0; i < stepCount; ++i) {
        bool found = false;
        for (size_t j = 0; j < providerCount; ++j) found |= supports(providers[j], steps[i], options.referenceOnly);
        if (!found) { plan.status = PlanStatus::UnsupportedFeatures; return plan; }
    }
    Search search {providers, providerCount, steps, stepCount, dependencies,
                   dependencyCount, contracts, contractCount, options.referenceOnly, options.searchBudget};
    if (!search.choose(0)) {
        plan.status = search.limitReached ? PlanStatus::SearchLimit : PlanStatus::TransferUnavailable;
        plan.searchAttempts = search.attempts;
        return plan;
    }
    plan.status = PlanStatus::Ready;
    plan.stepCount = stepCount;
    plan.dependencyCount = dependencyCount;
    plan.referenceOnly = options.referenceOnly;
    plan.searchAttempts = search.attempts;
    for (size_t i = 0; i < stepCount; ++i) plan.providers[i] = providers[search.selected[i]].id;
    for (size_t i = 0; i < dependencyCount; ++i) plan.transfers[i] = search.modes[i];
    return plan;
}

CompletionStatus CompletionTracker::armAfterSubmission(const ProviderDescriptor &p,
                                                      const SubmissionToken &token,
                                                      bool reference) {
    if (state_ == CompletionState::Pending) return CompletionStatus::AlreadyPending;
    if (!validProvider(p) || !token.queue || !token.sequence || token.provider != p.id ||
        token.deviceInstance != p.device.instance || token.epoch != p.resetEpoch ||
        (reference ? p.api != Api::CpuReference : p.execution != Execution::Hardware))
        return CompletionStatus::InvalidInput;
    if (token.epoch < epochFloor_) return CompletionStatus::StaleEpoch;
    if (token_.provider) {
        if (token_.provider != token.provider || token_.deviceInstance != token.deviceInstance ||
            token_.queue != token.queue ||
            (token_.epoch == token.epoch && token.sequence <= token_.sequence))
            return CompletionStatus::WrongSubmission;
    }
    token_ = token;
    epochFloor_ = token.epoch;
    reference_ = reference;
    state_ = CompletionState::Pending;
    return CompletionStatus::Accepted;
}
CompletionStatus CompletionTracker::observe(const CompletionObservation &event) {
    if (event.token.epoch < epochFloor_ || event.token.epoch != token_.epoch) return CompletionStatus::StaleEpoch;
    if (state_ != CompletionState::Pending) return CompletionStatus::NotPending;
    if (!sameToken(token_, event.token)) return CompletionStatus::WrongSubmission;
    if (!reference_ && event.kind != ObservationKind::GpuCompletion) return CompletionStatus::NonGpuObservation;
    if (reference_ && event.kind != ObservationKind::CpuReference) return CompletionStatus::InvalidInput;
    if (!event.validationRecord || !event.resultsVerified ||
        (!reference_ && (!event.gpuStart || event.gpuEnd <= event.gpuStart)))
        return CompletionStatus::IncompleteEvidence;
    state_ = reference_ ? CompletionState::ReferenceComplete : CompletionState::GpuEvidenceAccepted;
    return CompletionStatus::Accepted;
}
CompletionStatus CompletionTracker::invalidateForReset(uint64_t epoch) {
    if (!epoch || epoch <= epochFloor_) return CompletionStatus::StaleEpoch;
    epochFloor_ = epoch;
    state_ = CompletionState::Reset;
    return CompletionStatus::Accepted;
}

bool validCacheIdentity(const JitCacheIdentity &key) {
    if (key.schema != 1 || !key.device.instance || !key.device.vendorId || !key.device.deviceId ||
        (key.targetApi != Api::OpenGL && key.targetApi != Api::OpenCL && key.targetApi != Api::Native) ||
        (key.input != ShaderInput::MslSource && key.input != ShaderInput::Air &&
         key.input != ShaderInput::SpirV && key.input != ShaderInput::OpenClC && key.input != ShaderInput::Glsl)) return false;
    return validDigest(key.source) && validDigest(key.entryPoints) && validDigest(key.frontend) &&
           validDigest(key.lowering) && validDigest(key.backend) && validDigest(key.driver) &&
           validDigest(key.target) && validDigest(key.options) && validDigest(key.specialization) &&
           validDigest(key.resourceAbi);
}
bool sameCacheIdentity(const JitCacheIdentity &a, const JitCacheIdentity &b) {
    return validCacheIdentity(a) && validCacheIdentity(b) && a.schema == b.schema &&
           a.input == b.input && a.targetApi == b.targetApi && sameDevice(a.device, b.device) &&
           sameDigest(a.source, b.source) && sameDigest(a.entryPoints, b.entryPoints) &&
           sameDigest(a.frontend, b.frontend) && sameDigest(a.lowering, b.lowering) &&
           sameDigest(a.backend, b.backend) && sameDigest(a.driver, b.driver) &&
           sameDigest(a.target, b.target) && sameDigest(a.options, b.options) &&
           sameDigest(a.specialization, b.specialization) && sameDigest(a.resourceAbi, b.resourceAbi);
}
} // namespace MellowRT
