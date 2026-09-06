#pragma once

#include <stddef.h>
#include <stdint.h>

// User-space policy contracts. No API calls, shader compilation, GPU submission,
// hardware attestation, or capability discovery happen in this library. Only a
// trusted provider adapter may populate verification fields after runtime tests.
namespace MellowRT {

enum class Api : uint8_t { OpenGL, OpenCL, Native, CpuReference };
enum class ProviderKind : uint8_t { Host, Mellow, Reference };
enum class Execution : uint8_t { Hardware, Software };
enum class Workload : uint8_t { Compute, Render, Blit };
enum class WorkloadInput : uint8_t { MetalSemantics, OpenClC };
enum class Feature : uint64_t {
    Compute = 1ULL << 0, Render = 1ULL << 1, Blit = 1ULL << 2,
    ComputeTranslation = 1ULL << 3, RenderTranslation = 1ULL << 4,
    ManagedStorage = 1ULL << 5, TextureRgba8 = 1ULL << 6,
    ArgumentBuffersTier2 = 1ULL << 7, SharedEvents = 1ULL << 8,
    SimdGroupOperations = 1ULL << 9, MeshShaders = 1ULL << 10,
    RayTracing = 1ULL << 11, OrderedQueue = 1ULL << 12
};
using Features = uint64_t;
constexpr Features bit(Feature feature) { return static_cast<Features>(feature); }
constexpr Features KnownFeatures = (1ULL << 13) - 1;

struct DeviceIdentity {
    uint16_t vendorId {};
    uint16_t deviceId {};
    uint32_t revision {};
    uint64_t instance {}; // Adapter's stable identity for this physical device.
};
bool sameDevice(const DeviceIdentity &, const DeviceIdentity &);

struct ProviderDescriptor {
    uint64_t id {}; // Unique within one planner invocation.
    DeviceIdentity device {};
    Api api {Api::CpuReference};
    ProviderKind kind {ProviderKind::Reference};
    Execution execution {Execution::Software};
    uint16_t apiMajor {};
    uint16_t apiMinor {};
    uint64_t resetEpoch {};
    uint64_t evidenceEpoch {};
    uint64_t validationRecord {}; // Reference into adapter-owned evidence store.
    Features advertised {};
    Features verified {};
};

enum class TransferPolicy : uint8_t { SharedOnly, SharedOrExplicitCopy };
enum class TransferMode : uint8_t { None, SharedResource, ExplicitCopy };
struct Step {
    Workload workload {Workload::Compute};
    Features required {}; // Every semantic/format requirement of this workload.
    uint64_t requiredProvider {}; // Zero lets the planner select a provider.
    WorkloadInput input {WorkloadInput::MetalSemantics};
};
struct Dependency {
    size_t producer {};
    size_t consumer {};
    uint64_t resource {}; // Identity from the caller's resource ownership model.
    TransferPolicy policy {TransferPolicy::SharedOnly};
};
struct TransferContract {
    uint64_t producerProvider {};
    uint64_t consumerProvider {};
    uint64_t resource {};
    uint64_t producerEpoch {};
    uint64_t consumerEpoch {};
    TransferMode mode {TransferMode::None};
    bool resourceCompatibilityVerified {};
    bool orderingVerified {};
    bool contentsPreservedVerified {};
    uint64_t validationRecord {};
};

constexpr size_t MaxProviders = 8;
constexpr size_t MaxSteps = 8;
constexpr size_t MaxDependencies = 16;
constexpr size_t MaxTransfers = 32;
constexpr size_t MaxSearchAttempts = 8192;
enum class PlanStatus : uint8_t {
    Ready, InvalidInput, UnsupportedFeatures, TransferUnavailable, SearchLimit
};
struct PlanOptions {
    // Selects an explicitly requested reference run. It is never a fallback
    // and excludes hardware providers when true.
    bool referenceOnly {};
    size_t searchBudget {MaxSearchAttempts};
};
struct RoutePlan {
    PlanStatus status {PlanStatus::InvalidInput};
    size_t stepCount {};
    size_t dependencyCount {};
    uint64_t providers[MaxSteps] {};
    TransferMode transfers[MaxDependencies] {};
    bool referenceOnly {};
    size_t searchAttempts {};
};

// Every inter-step resource hazard must be supplied as a Dependency. In-provider
// dependencies require the adapter's ordered-queue contract. Cross-provider
// dependencies require an explicit, per-resource transfer contract. Neither
// IOSurface existence nor matching PCI IDs imply interoperability.
RoutePlan planWorkload(const ProviderDescriptor *, size_t providerCount,
                       const Step *, size_t stepCount,
                       const Dependency *, size_t dependencyCount,
                       const TransferContract *, size_t transferCount,
                       PlanOptions = {});

struct SubmissionToken {
    uint64_t provider {};
    uint64_t deviceInstance {};
    uint64_t epoch {};
    uint64_t queue {};
    uint64_t sequence {};
};
enum class ObservationKind : uint8_t { GpuCompletion, CpuReference };
struct CompletionObservation {
    SubmissionToken token {};
    ObservationKind kind {ObservationKind::CpuReference};
    uint64_t gpuStart {};
    uint64_t gpuEnd {};
    uint64_t validationRecord {};
    bool resultsVerified {};
};
enum class CompletionState : uint8_t {
    Empty, Pending, GpuEvidenceAccepted, ReferenceComplete, Reset
};
enum class CompletionStatus : uint8_t {
    Accepted, InvalidInput, NotPending, AlreadyPending, StaleEpoch, WrongSubmission,
    NonGpuObservation, IncompleteEvidence
};

// This validates correlation and policy of trusted adapter observations only.
// GpuEvidenceAccepted is NOT an attestation that physical execution occurred.
// The adapter must validate its event source, GPU timestamps, and readback.
// One tracker belongs to one provider/device/queue and is not thread safe.
class CompletionTracker {
public:
    CompletionStatus armAfterSubmission(const ProviderDescriptor &,
                                        const SubmissionToken &,
                                        bool explicitReferenceRun = false);
    CompletionStatus observe(const CompletionObservation &);
    CompletionStatus invalidateForReset(uint64_t newEpoch);
    CompletionState state() const { return state_; }
private:
    SubmissionToken token_ {};
    CompletionState state_ {CompletionState::Empty};
    bool reference_ {};
    uint64_t epochFloor_ {};
};

struct Digest256 { uint8_t bytes[32] {}; };
enum class ShaderInput : uint8_t { MslSource, Air, SpirV, OpenClC, Glsl };
struct JitCacheIdentity {
    uint32_t schema {1};
    ShaderInput input {ShaderInput::MslSource};
    Api targetApi {Api::CpuReference};
    DeviceIdentity device {};
    Digest256 source {};       // Full source/container plus linked libraries.
    Digest256 entryPoints {};  // Entry names, stages and reflection contract.
    Digest256 frontend {};     // Front end executable + version + AIR dialect.
    Digest256 lowering {};     // Mellow IR/lowering/compiler executable version.
    Digest256 backend {};      // Target compiler binary and build/version.
    Digest256 driver {};       // Driver/provider build and capability profile.
    Digest256 target {};       // Architecture/features/OS/ABI/IR environment.
    Digest256 options {};      // Canonical flags, optimization and math modes.
    Digest256 specialization {};
    Digest256 resourceAbi {};  // Layout, binding, format and calling conventions.
};
bool validCacheIdentity(const JitCacheIdentity &);
// Exact key comparison; no compiler, cache I/O, or non-cryptographic hash shortcut.
bool sameCacheIdentity(const JitCacheIdentity &, const JitCacheIdentity &);

} // namespace MellowRT
