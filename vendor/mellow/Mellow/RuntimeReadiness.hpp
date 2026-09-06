// Fail-closed readiness policy for the experimental Xe-LPG runtime.
// This module does not touch hardware and does not claim that any evidence
// exists. A provider owner sets a bit only after validating that proof.
#pragma once

#include <stdint.h>

namespace MellowRuntime {

enum Evidence : uint64_t {
    BootOptIn                 = 1ULL << 0,
    VesaDisabled              = 1ULL << 1,
    PhysicalIdentity7D41      = 1ULL << 2,
    Bar0Mapped                = 1ULL << 3,
    GmdArchitecture1270       = 1ULL << 4,
    GtForceWakeHeld           = 1ULL << 5,
    GgttPublisherOwned        = 1ULL << 6,
    GgttTlbInvalidated        = 1ULL << 7,
    PatMocsValidated          = 1ULL << 8,
    FullAdsValidated          = 1ULL << 9,
    GucAuthenticated          = 1ULL << 10,
    GucTransportStarted       = 1ULL << 11,
    InterruptSourceStarted    = 1ULL << 12,
    FenceStoragePublished     = 1ULL << 13,
    ContextBackendBound       = 1ULL << 14,
    EvidenceJobCompleted      = 1ULL << 15,
    KernelAcceleratorProvider = 1ULL << 16,
    UserMetalPluginLoaded     = 1ULL << 17,
    PrivateAbiMatched         = 1ULL << 18,
    ShaderCompilerConnected   = 1ULL << 19,
};

constexpr uint64_t ConfigurationMask = BootOptIn | VesaDisabled;
constexpr uint64_t PhysicalMask = PhysicalIdentity7D41 | Bar0Mapped |
                                  GmdArchitecture1270 | GtForceWakeHeld;
constexpr uint64_t AddressSpaceMask = GgttPublisherOwned |
                                      GgttTlbInvalidated |
                                      PatMocsValidated | FullAdsValidated;
constexpr uint64_t FirmwareMask = GucAuthenticated | GucTransportStarted;
constexpr uint64_t SubmissionPrerequisiteMask = InterruptSourceStarted |
                                                FenceStoragePublished |
                                                ContextBackendBound;
constexpr uint64_t ExecutionMask = SubmissionPrerequisiteMask |
                                   EvidenceJobCompleted;
constexpr uint64_t KernelProviderMask = KernelAcceleratorProvider;
constexpr uint64_t UserspaceMask = UserMetalPluginLoaded |
                                   PrivateAbiMatched |
                                   ShaderCompilerConnected;
constexpr uint64_t AllEvidenceMask = ConfigurationMask | PhysicalMask |
                                     AddressSpaceMask | FirmwareMask |
                                     ExecutionMask | KernelProviderMask |
                                     UserspaceMask;

enum class Stage : uint8_t {
    Configuration,
    PhysicalProvider,
    AddressSpace,
    Firmware,
    Execution,
    KernelProvider,
    Userspace,
    Ready,
};

struct Decision {
    Stage stage {Stage::Configuration};
    uint64_t verified {};
    uint64_t missing {AllEvidenceMask};
    bool mayAttemptBar0Mapping {};
    bool mayAttemptGucAuthentication {};
    bool maySubmitContext {};
    bool mayPublishAccelerator {};
    bool mayAdvertiseMetal {};
};

Decision evaluate(uint64_t verifiedEvidence);
const char *stageName(Stage stage);
const char *evidenceName(Evidence evidence);
Evidence firstMissing(uint64_t missingMask);

// This build has no IOKit owner that constructs and retains the MMIO, GGTT,
// GuC, IRQ, fence, context and IOAccelerator objects as one reset epoch.
// A boot argument must never substitute for that missing owner.
constexpr bool BackendOwnerIntegrated = false;

constexpr bool contains(uint64_t value, uint64_t required) {
    return (value & required) == required;
}

inline Decision evaluate(uint64_t verifiedEvidence) {
    Decision result {};
    result.verified = verifiedEvidence & AllEvidenceMask;
    result.missing = AllEvidenceMask & ~result.verified;

    const bool configuration = contains(result.verified, ConfigurationMask);
    const bool physicalIdentity = contains(result.verified,
                                           ConfigurationMask |
                                           PhysicalIdentity7D41);
    const bool physical = configuration && contains(result.verified, PhysicalMask);
    const bool addressSpace = physical && contains(result.verified, AddressSpaceMask);
    const bool firmware = addressSpace && contains(result.verified, FirmwareMask);
    const bool submissionPrerequisites = firmware &&
        contains(result.verified, SubmissionPrerequisiteMask);
    const bool execution = submissionPrerequisites &&
                           contains(result.verified, ExecutionMask);
    const bool kernelProvider = execution &&
                                contains(result.verified, KernelProviderMask);
    const bool userspace = kernelProvider && contains(result.verified, UserspaceMask);

    result.mayAttemptBar0Mapping = physicalIdentity;
    result.mayAttemptGucAuthentication = addressSpace;
    result.maySubmitContext = submissionPrerequisites;
    result.mayPublishAccelerator = execution;
    result.mayAdvertiseMetal = userspace;

    result.stage = !configuration ? Stage::Configuration :
                   !physical ? Stage::PhysicalProvider :
                   !addressSpace ? Stage::AddressSpace :
                   !firmware ? Stage::Firmware :
                   !execution ? Stage::Execution :
                   !kernelProvider ? Stage::KernelProvider :
                   !userspace ? Stage::Userspace : Stage::Ready;
    return result;
}

inline const char *stageName(Stage stage) {
    switch (stage) {
        case Stage::Configuration: return "configuration";
        case Stage::PhysicalProvider: return "physical-provider";
        case Stage::AddressSpace: return "address-space";
        case Stage::Firmware: return "firmware";
        case Stage::Execution: return "execution";
        case Stage::KernelProvider: return "kernel-provider";
        case Stage::Userspace: return "userspace";
        case Stage::Ready: return "ready";
    }
    return "invalid";
}

inline const char *evidenceName(Evidence evidence) {
    switch (evidence) {
        case BootOptIn: return "boot-opt-in";
        case VesaDisabled: return "vesa-disabled";
        case PhysicalIdentity7D41: return "physical-8086-7d41";
        case Bar0Mapped: return "bar0-mapped";
        case GmdArchitecture1270: return "gmd-12.70";
        case GtForceWakeHeld: return "gt-forcewake-held";
        case GgttPublisherOwned: return "ggtt-publisher-owned";
        case GgttTlbInvalidated: return "ggtt-tlb-invalidated";
        case PatMocsValidated: return "pat-mocs-validated";
        case FullAdsValidated: return "full-ads-validated";
        case GucAuthenticated: return "guc-authenticated";
        case GucTransportStarted: return "guc-transport-started";
        case InterruptSourceStarted: return "interrupt-source-started";
        case FenceStoragePublished: return "fence-storage-published";
        case ContextBackendBound: return "context-backend-bound";
        case EvidenceJobCompleted: return "evidence-job-completed";
        case KernelAcceleratorProvider: return "kernel-accelerator-provider";
        case UserMetalPluginLoaded: return "user-metal-plugin-loaded";
        case PrivateAbiMatched: return "private-abi-matched";
        case ShaderCompilerConnected: return "shader-compiler-connected";
    }
    return "invalid";
}

inline Evidence firstMissing(uint64_t missingMask) {
    const uint64_t bounded = missingMask & AllEvidenceMask;
    for (uint8_t bit = 0; bit < 20; ++bit) {
        const uint64_t candidate = 1ULL << bit;
        if (bounded & candidate)
            return static_cast<Evidence>(candidate);
    }
    return static_cast<Evidence>(0);
}

} // namespace MellowRuntime
