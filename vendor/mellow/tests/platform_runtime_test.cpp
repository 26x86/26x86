#include "../Runtime/PlatformRuntime.hpp"
#include <stdio.h>
#include <stdlib.h>

using namespace MellowRT;
static unsigned checks = 0;
#define CHECK(expr) do { ++checks; if (!(expr)) { \
    fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #expr); exit(1); } } while (false)

// All descriptors and observations below are synthetic policy fixtures. These
// tests exercise the real policy implementation; they do not execute GPU work.
static ProviderDescriptor provider(uint64_t id, Api api) {
    ProviderDescriptor p {};
    p.id = id;
    p.device = {0x8086, 0x7D41, 1, 42};
    p.api = api;
    p.kind = ProviderKind::Host;
    p.execution = Execution::Hardware;
    p.apiMajor = api == Api::OpenGL ? 4 : 1;
    p.apiMinor = api == Api::OpenGL ? 1 : 2;
    p.resetEpoch = 5;
    p.evidenceEpoch = 5;
    p.validationRecord = 10;
    p.verified = bit(Feature::Compute) | bit(Feature::Render) | bit(Feature::Blit) |
                 bit(Feature::ComputeTranslation) | bit(Feature::RenderTranslation) |
                 bit(Feature::TextureRgba8) | bit(Feature::OrderedQueue);
    p.advertised = p.verified;
    return p;
}
static RoutePlan one(const ProviderDescriptor &p, Step step, bool reference = false) {
    return planWorkload(&p, 1, &step, 1, nullptr, 0, nullptr, 0, {reference});
}
static void routes() {
    auto gl = provider(1, Api::OpenGL);
    const Step compute {Workload::Compute, 0, 0};
    const Step render {Workload::Render, bit(Feature::TextureRgba8), 0};
    CHECK(one(gl, render).status == PlanStatus::Ready);
    CHECK(one(gl, compute).status == PlanStatus::UnsupportedFeatures); // GL 4.1
    gl.apiMinor = 3;
    CHECK(one(gl, compute).status == PlanStatus::Ready);
    auto cl = provider(2, Api::OpenCL);
    CHECK(one(cl, compute).status == PlanStatus::Ready);
    CHECK(one(cl, render).status == PlanStatus::UnsupportedFeatures);
    CHECK(one(cl, {Workload::Blit, 0, 0}).status == PlanStatus::Ready);
    cl.apiMinor = 1;
    CHECK(one(cl, compute).status == PlanStatus::UnsupportedFeatures);
    cl.apiMinor = 2;
    cl.advertised |= bit(Feature::RayTracing);
    CHECK(one(cl, {Workload::Compute, bit(Feature::RayTracing), 0}).status == PlanStatus::UnsupportedFeatures);
    CHECK(one(cl, {Workload::Compute, bit(Feature::ArgumentBuffersTier2), 0}).status == PlanStatus::UnsupportedFeatures);
    cl.verified &= ~bit(Feature::ComputeTranslation);
    CHECK(one(cl, compute).status == PlanStatus::UnsupportedFeatures);
    const Step direct {Workload::Compute, 0, 0, WorkloadInput::OpenClC};
    CHECK(one(cl, direct).status == PlanStatus::Ready);
    CHECK(one(cl, {Workload::Render, 0, 0, WorkloadInput::OpenClC}).status == PlanStatus::UnsupportedFeatures);
    CHECK(one(cl, {Workload::Blit, 0, 0, WorkloadInput::OpenClC}).status == PlanStatus::UnsupportedFeatures);
    CHECK(one(gl, direct).status == PlanStatus::UnsupportedFeatures);
    CHECK(one(provider(9, Api::Native), direct).status == PlanStatus::UnsupportedFeatures);
    CHECK(one(cl, {Workload::Compute, 0, 0, static_cast<WorkloadInput>(255)}).status == PlanStatus::InvalidInput);
    cl = provider(2, Api::OpenCL);
    cl.verified &= ~bit(Feature::OrderedQueue);
    CHECK(one(cl, compute).status == PlanStatus::UnsupportedFeatures);
    cl = provider(2, Api::OpenCL);
    cl.verified |= bit(Feature::RayTracing);
    CHECK(one(cl, compute).status == PlanStatus::InvalidInput);
    cl = provider(2, Api::OpenCL);
    cl.evidenceEpoch = 4;
    CHECK(one(cl, compute).status == PlanStatus::InvalidInput);
    cl = provider(2, Api::OpenCL);
    cl.execution = Execution::Software; // e.g. software GL/CL implementation.
    CHECK(one(cl, compute).status == PlanStatus::UnsupportedFeatures);
    CHECK(one(cl, compute, true).status == PlanStatus::UnsupportedFeatures);
    auto cpu = provider(3, Api::CpuReference);
    cpu.kind = ProviderKind::Reference;
    cpu.execution = Execution::Software;
    CHECK(one(cpu, compute).status == PlanStatus::UnsupportedFeatures);
    CHECK(one(cpu, compute, true).status == PlanStatus::Ready);
    CHECK(one(cpu, compute, true).referenceOnly);
    CHECK(one(gl, compute, true).status == PlanStatus::UnsupportedFeatures);
    CHECK(one(gl, {Workload::Compute, 0, 99}).status == PlanStatus::UnsupportedFeatures);
    CHECK(one(gl, {static_cast<Workload>(255), 0, 0}).status == PlanStatus::InvalidInput);
    CHECK(one(gl, {Workload::Compute, 1ULL << 60, 0}).status == PlanStatus::InvalidInput);
    CHECK(planWorkload(nullptr, 0, &compute, 1, nullptr, 0, nullptr, 0).status == PlanStatus::InvalidInput);
    ProviderDescriptor duplicate[] = {gl, gl};
    CHECK(planWorkload(duplicate, 2, &compute, 1, nullptr, 0, nullptr, 0).status == PlanStatus::InvalidInput);
}
static void interop() {
    ProviderDescriptor p[] = {provider(1, Api::OpenCL), provider(2, Api::OpenGL), provider(3, Api::Native)};
    Step steps[] = {{Workload::Compute, 0, 1}, {Workload::Render, 0, 2}};
    Dependency edge {0, 1, 71, TransferPolicy::SharedOnly};
    auto plan = [&]() { return planWorkload(p, 3, steps, 2, &edge, 1, nullptr, 0); };
    CHECK(plan().status == PlanStatus::TransferUnavailable);
    TransferContract transfer {1, 2, 71, 5, 5, TransferMode::SharedResource, true, true, true, 55};
    auto with = [&]() { return planWorkload(p, 3, steps, 2, &edge, 1, &transfer, 1); };
    CHECK(with().status == PlanStatus::Ready);
    CHECK(with().providers[0] == 1 && with().providers[1] == 2);
    CHECK(with().transfers[0] == TransferMode::SharedResource);
    transfer.orderingVerified = false;
    CHECK(with().status == PlanStatus::TransferUnavailable);
    transfer.orderingVerified = true;
    transfer.contentsPreservedVerified = false;
    CHECK(with().status == PlanStatus::TransferUnavailable);
    transfer.contentsPreservedVerified = true;
    transfer.resourceCompatibilityVerified = false;
    CHECK(with().status == PlanStatus::TransferUnavailable);
    transfer.resourceCompatibilityVerified = true;
    transfer.producerEpoch = 4;
    CHECK(with().status == PlanStatus::TransferUnavailable);
    transfer.producerEpoch = 5;
    transfer.resource = 72;
    CHECK(with().status == PlanStatus::TransferUnavailable);
    transfer.resource = 71;
    transfer.mode = TransferMode::ExplicitCopy;
    CHECK(with().status == PlanStatus::TransferUnavailable);
    edge.policy = TransferPolicy::SharedOrExplicitCopy;
    CHECK(with().status == PlanStatus::Ready);
    CHECK(with().transfers[0] == TransferMode::ExplicitCopy);
    transfer.validationRecord = 0;
    CHECK(with().status == PlanStatus::TransferUnavailable);
    // Backtracking avoids a greedy CL/GL split when only a complete native
    // route can preserve the resource without an external transfer adapter.
    steps[0].requiredProvider = steps[1].requiredProvider = 0;
    CHECK(plan().status == PlanStatus::Ready);
    CHECK(plan().providers[0] == 3 && plan().providers[1] == 3);
    CHECK(plan().transfers[0] == TransferMode::None);
    auto limited = planWorkload(p, 3, steps, 2, &edge, 1, nullptr, 0, {false, 1});
    CHECK(limited.status == PlanStatus::SearchLimit);
    CHECK(limited.searchAttempts == 1);
    CHECK(planWorkload(p, 3, steps, 2, &edge, 1, nullptr, 0, {false, 0}).status == PlanStatus::InvalidInput);
    CHECK(planWorkload(p, 3, steps, 2, &edge, 1, nullptr, 0, {false, MaxSearchAttempts + 1}).status == PlanStatus::InvalidInput);
    edge.producer = 1;
    CHECK(plan().status == PlanStatus::InvalidInput);
    edge.producer = 0;
    edge.resource = 0;
    CHECK(plan().status == PlanStatus::InvalidInput);
}
static void completion() {
    auto p = provider(1, Api::OpenCL);
    SubmissionToken token {1, 42, 5, 7, 10};
    CompletionTracker tracker;
    CHECK(tracker.armAfterSubmission(p, token) == CompletionStatus::Accepted);
    CHECK(tracker.state() == CompletionState::Pending);
    CHECK(tracker.armAfterSubmission(p, token) == CompletionStatus::AlreadyPending);
    CompletionObservation event {token, ObservationKind::CpuReference, 100, 200, 55, true};
    CHECK(tracker.observe(event) == CompletionStatus::NonGpuObservation);
    CHECK(tracker.state() == CompletionState::Pending);
    event.kind = ObservationKind::GpuCompletion;
    event.token.sequence = 9;
    CHECK(tracker.observe(event) == CompletionStatus::WrongSubmission);
    event.token = token;
    event.token.deviceInstance = 43;
    CHECK(tracker.observe(event) == CompletionStatus::WrongSubmission);
    event.token = token;
    event.token.epoch = 4;
    CHECK(tracker.observe(event) == CompletionStatus::StaleEpoch);
    event.token = token;
    event.gpuEnd = event.gpuStart;
    CHECK(tracker.observe(event) == CompletionStatus::IncompleteEvidence);
    event.gpuEnd = 200;
    event.resultsVerified = false;
    CHECK(tracker.observe(event) == CompletionStatus::IncompleteEvidence);
    event.resultsVerified = true;
    CHECK(tracker.observe(event) == CompletionStatus::Accepted);
    CHECK(tracker.state() == CompletionState::GpuEvidenceAccepted);
    CHECK(tracker.observe(event) == CompletionStatus::NotPending);
    CHECK(tracker.armAfterSubmission(p, token) == CompletionStatus::WrongSubmission);
    ++token.sequence;
    CHECK(tracker.armAfterSubmission(p, token) == CompletionStatus::Accepted);
    CHECK(tracker.invalidateForReset(6) == CompletionStatus::Accepted);
    CHECK(tracker.state() == CompletionState::Reset);
    event.token = token;
    CHECK(tracker.observe(event) == CompletionStatus::StaleEpoch);
    CHECK(tracker.armAfterSubmission(p, token) == CompletionStatus::StaleEpoch);
    CHECK(tracker.invalidateForReset(6) == CompletionStatus::StaleEpoch);
    p.resetEpoch = p.evidenceEpoch = token.epoch = 6;
    token.sequence = 1;
    CHECK(tracker.armAfterSubmission(p, token) == CompletionStatus::Accepted);
    event.token = token;
    CHECK(tracker.observe(event) == CompletionStatus::Accepted);
    ++token.queue;
    CHECK(tracker.armAfterSubmission(p, token) == CompletionStatus::WrongSubmission);
    p = provider(3, Api::CpuReference);
    p.kind = ProviderKind::Reference;
    p.execution = Execution::Software;
    token = {3, 42, 5, 8, 1};
    CompletionTracker reference;
    CHECK(reference.armAfterSubmission(p, token) == CompletionStatus::InvalidInput);
    CHECK(reference.armAfterSubmission(p, token, true) == CompletionStatus::Accepted);
    event = {token, ObservationKind::GpuCompletion, 10, 20, 55, true};
    CHECK(reference.observe(event) == CompletionStatus::InvalidInput);
    event.kind = ObservationKind::CpuReference;
    CHECK(reference.observe(event) == CompletionStatus::Accepted);
    CHECK(reference.state() == CompletionState::ReferenceComplete);
}
static void cache() {
    JitCacheIdentity key {};
    key.targetApi = Api::OpenCL;
    key.device = {0x10de, 0x2204, 1, 100}; // Identity example, no support claim.
    Digest256 JitCacheIdentity::*fields[] = {
        &JitCacheIdentity::source, &JitCacheIdentity::entryPoints, &JitCacheIdentity::frontend,
        &JitCacheIdentity::lowering, &JitCacheIdentity::backend, &JitCacheIdentity::driver,
        &JitCacheIdentity::target, &JitCacheIdentity::options,
        &JitCacheIdentity::specialization, &JitCacheIdentity::resourceAbi
    };
    CHECK(!validCacheIdentity(key));
    for (auto field : fields) (key.*field).bytes[0] = 1;
    CHECK(validCacheIdentity(key));
    CHECK(sameCacheIdentity(key, key));
    for (auto field : fields) {
        auto changed = key;
        (changed.*field).bytes[31] = 2;
        CHECK(!sameCacheIdentity(key, changed));
        (changed.*field) = {};
        CHECK(!validCacheIdentity(changed));
    }
    auto changed = key;
    changed.device.deviceId++;
    CHECK(!sameCacheIdentity(key, changed));
    changed = key;
    changed.targetApi = Api::OpenGL;
    CHECK(!sameCacheIdentity(key, changed));
    changed = key;
    changed.input = ShaderInput::Air;
    CHECK(!sameCacheIdentity(key, changed));
    changed = key;
    changed.schema++;
    CHECK(!validCacheIdentity(changed));
    changed = key;
    changed.device.vendorId = 0;
    CHECK(!validCacheIdentity(changed));
}
int main() {
    routes(); interop(); completion(); cache();
    printf("PASS: %u policy checks (synthetic adapters; no GPU execution or Metal conformance)\n", checks);
}
