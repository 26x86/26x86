// Local research modifications, 2026. See the repository LICENSE and NOTICE.
#pragma once
namespace MellowStartup {
enum class Admission { UnsupportedKernel, ExplicitTahoeTrialRequired, VesaConflict, NativeBackendUnavailable, ResearchTrial };
inline Admission evaluate(unsigned darwinMajor, bool tahoeTrial, bool vesa,
                          bool nativeBackendRequested, bool backendOwnerIntegrated) {
    if (darwinMajor < 22 || darwinMajor > 25) return Admission::UnsupportedKernel;
    if (vesa) return Admission::VesaConflict;
    if (darwinMajor == 25 && !tahoeTrial) return Admission::ExplicitTahoeTrialRequired;
    if (nativeBackendRequested && !backendOwnerIntegrated) return Admission::NativeBackendUnavailable;
    return Admission::ResearchTrial;
}
}
