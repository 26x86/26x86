// Local diagnostic lifecycle, 2026. See repository LICENSE and NOTICE.
#include "TahoeDiagnosticProtocol.hpp"
#include "RuntimeReadiness.hpp"
namespace MellowDiagnostic {
bool Session::initialize(Identity id, bool bar, XeMemory::Backend backend, uint64_t evidence) {
    if (state_ != MellowDiagCold || stopped_ || !bar || id.vendor != 0x8086 ||
        id.device != 0x7d41 || id.architecture != 12 || id.release != 70) return false;
    identity_ = id; backend_ = backend;
    evidence_ = evidence & (MellowRuntime::BootOptIn | MellowRuntime::PhysicalIdentity7D41 |
        MellowRuntime::Bar0Mapped | MellowRuntime::GmdArchitecture1270);
    state_ = MellowDiagReady;
    return true;
}
bool Session::open(uint64_t owner) {
    if (!owner || owner_ || stopped_ || state_ != MellowDiagReady || hasResources()) return false;
    owner_ = owner; return true;
}
uint32_t Session::releaseAllocation() {
    if (!hasResources()) return MellowDiagOk;
    if (!backend_.unpin || backend_.unpin(backend_.context, pin_) != XeMemory::Status::Ok || hasResources()) {
        state_ = MellowDiagFaulted; return MellowDiagQuarantined;
    }
    handle_ = bytes_ = 0; state_ = stopped_ ? MellowDiagStopped : MellowDiagReady;
    return MellowDiagOk;
}
uint32_t Session::close(uint64_t owner) {
    if (!owns(owner)) return MellowDiagInvalid;
    owner_ = 0;
    return releaseAllocation();
}
uint32_t Session::stop() {
    stopped_ = true; owner_ = 0;
    const uint32_t status = releaseAllocation();
    if (status == MellowDiagOk) state_ = MellowDiagStopped;
    return status;
}
void Session::describe(uint32_t status, MellowDiagReply &out) const {
    MellowDiagReply reply {};
    reply.version = MELLOW_DIAG_ABI_VERSION; reply.size = sizeof(reply);
    reply.status = status; reply.state = state_;
    if (!stopped_ && state_ != MellowDiagCold) {
        reply.diagnosticCapabilities = MellowDiagBar0Read;
        if (backend_.pin && backend_.unpin && state_ != MellowDiagFaulted)
            reply.diagnosticCapabilities |= MellowDiagPreparedDma;
    }
    reply.allocationHandle = handle_; reply.allocationBytes = bytes_; reply.pageCount = pin_.pageCount;
    reply.vendor = identity_.vendor; reply.device = identity_.device;
    reply.gmdArchitecture = identity_.architecture; reply.gmdRelease = identity_.release;
    reply.readinessEvidence = evidence_;
    // Zero GPU/Metal capability is intentional: prepared memory is not a GPU job.
    out = reply;
}
void Session::call(uint64_t owner, uint32_t selector, const MellowDiagRequest &in, MellowDiagReply &out) {
    uint32_t status = MellowDiagInvalid;
    if (in.version != MELLOW_DIAG_ABI_VERSION || in.size != sizeof(in) || in.reserved ||
        selector > MellowDiagRelease || (selector == MellowDiagQuery && (in.handle || in.bytes)) ||
        (selector == MellowDiagAllocate && (in.handle || !in.bytes || in.bytes > MELLOW_DIAG_MAX_BYTES || (in.bytes & 4095))) ||
        (selector == MellowDiagRelease && (!in.handle || in.bytes))) { describe(status, out); return; }
    if (!owns(owner) || stopped_) { describe(MellowDiagUnavailable, out); return; }
    if (selector == MellowDiagQuery) { describe(MellowDiagOk, out); return; }
    if (selector == MellowDiagRelease) {
        status = in.handle == handle_ && hasResources() ? releaseAllocation() : static_cast<uint32_t>(MellowDiagInvalid);
        describe(status, out); return;
    }
    if (state_ != MellowDiagReady || hasResources()) { describe(MellowDiagBusy, out); return; }
    if (!backend_.pin || !backend_.unpin) { describe(MellowDiagUnavailable, out); return; }
    if (!nextHandle_ || nextHandle_ == UINT64_MAX) { describe(MellowDiagUnavailable, out); return; }
    const auto result = backend_.pin(backend_.context, owner_, in.bytes, pin_);
    if (result != XeMemory::Status::Ok) {
        if (hasResources()) state_ = MellowDiagFaulted;
        describe(hasResources() ? MellowDiagQuarantined : MellowDiagBackendFailure, out); return;
    }
    bool valid = pin_.cookie && pin_.dmaPages && pin_.pageCount == in.bytes / 4096;
    if (valid) for (size_t i = 0; i < pin_.pageCount; ++i)
        valid &= !(pin_.dmaPages[i] & 4095) && pin_.dmaPages[i] < XeMemory::DmaLimit;
    if (!valid) {
        status = releaseAllocation();
        describe(status == MellowDiagOk ? static_cast<uint32_t>(MellowDiagBackendFailure) : status, out); return;
    }
    handle_ = nextHandle_++; bytes_ = in.bytes; state_ = MellowDiagAllocated;
    describe(MellowDiagOk, out);
}
}
