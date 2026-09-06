// Local diagnostic ABI, 2026. See repository LICENSE and NOTICE.
#ifndef MELLOW_TAHOE_DIAGNOSTIC_ABI_H
#define MELLOW_TAHOE_DIAGNOSTIC_ABI_H
#include <stdint.h>
#define MELLOW_DIAG_SERVICE "MellowTahoeDiagnostic"
#define MELLOW_DIAG_ABI_VERSION 1U
#define MELLOW_DIAG_CONNECT_TYPE 0x4d440001U
#define MELLOW_DIAG_MAX_BYTES (1024ULL * 1024ULL)
enum MellowDiagSelector { MellowDiagQuery = 0, MellowDiagAllocate = 1, MellowDiagRelease = 2 };
enum MellowDiagStatus { MellowDiagOk = 0, MellowDiagInvalid = 1, MellowDiagUnavailable = 2,
    MellowDiagBusy = 3, MellowDiagBackendFailure = 4, MellowDiagQuarantined = 5 };
enum MellowDiagState { MellowDiagCold = 0, MellowDiagReady = 1, MellowDiagAllocated = 2,
    MellowDiagFaulted = 3, MellowDiagStopped = 4 };
enum MellowDiagCapability { MellowDiagBar0Read = 1, MellowDiagPreparedDma = 2 };
typedef struct MellowDiagRequest {
    uint32_t version, size;
    uint64_t handle, bytes, reserved;
} MellowDiagRequest;
typedef struct MellowDiagReply {
    uint32_t version, size, status, state;
    uint64_t diagnosticCapabilities, allocationHandle, allocationBytes, pageCount;
    uint32_t vendor, device, gmdArchitecture, gmdRelease;
    uint64_t readinessEvidence;
    uint32_t gpuSubmissionSupported, metalSupported;
    uint64_t reserved;
} MellowDiagReply;
#if defined(__cplusplus)
static_assert(sizeof(MellowDiagRequest) == 32, "diagnostic request layout");
static_assert(sizeof(MellowDiagReply) == 88, "diagnostic reply layout");
#endif
#endif
