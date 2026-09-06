#pragma once

#include "PlatformRuntime.hpp"
#include <memory>
#include <string>
#include <vector>

namespace MellowRT {
#if defined(MELLOW_OPENCL_TESTING)
namespace OpenCLAbi { struct Functions; }
#endif

struct OpenCLDeviceInfo {
    std::string platform, platformVendor, name, vendor, driver, version, extensions;
    uint32_t reportedVendorId {};
    uint32_t reportedDeviceId {};
    uint64_t reportedType {};
    bool deviceIdFromIntelExtension {};
    bool available {};
    bool compilerAvailable {};
};

struct OpenCLExecution {
    bool submissionAttempted {};
    bool submitted {};
    bool eventOwnershipVerified {};
    bool resultsVerified {};
    bool profilingVerified {};
    bool runtimePlanned {};
    bool runtimeCompletionAccepted {};
    bool resourcesReleased {};
    // Ordinary runtime completion does not require a caller's expected answer.
    // This is independent of oracle-based resultsVerified/evidence acceptance.
    bool executionCompleted {};
    uint64_t gpuStart {}, gpuEnd {}, epoch {}, sequence {}, validationRecord {};
    PlanStatus planStatus {PlanStatus::InvalidInput};
    CompletionStatus armStatus {CompletionStatus::InvalidInput};
    CompletionStatus observeStatus {CompletionStatus::InvalidInput};
    std::string buildLog, error;
    std::vector<uint32_t> output;
};

class OpenCLPipeline {
public:
    ~OpenCLPipeline();
    OpenCLPipeline(const OpenCLPipeline &) = delete;
    OpenCLPipeline &operator=(const OpenCLPipeline &) = delete;
    uint64_t compilationSerial() const;
    const std::string &buildLog() const;
private:
    friend class OpenCLProvider;
    OpenCLPipeline();
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

// Actual host OpenCL provider. It owns one context, ordered profiling queue and
// reset epoch. Use inside an externally deadline-limited worker: an installed
// driver can block in a synchronous API, which this library cannot preempt.
//
// Input is explicitly OpenCL C, NOT MSL/AIR/Metal. This first adapter deliberately
// supports one in-place uint buffer argument, bounded source and element counts.
// Device IDs must come from an advertised driver extension, never friendly names.
// No kernel driver, firmware, interop, CPU fallback or display path is installed.
class OpenCLProvider {
public:
    OpenCLProvider();
#if defined(MELLOW_OPENCL_TESTING)
    // Test binary only. Normal production builds expose no injectable loader.
    explicit OpenCLProvider(const OpenCLAbi::Functions &syntheticFunctions);
#endif
    ~OpenCLProvider();
    OpenCLProvider(const OpenCLProvider &) = delete;
    OpenCLProvider &operator=(const OpenCLProvider &) = delete;
    bool initialize(size_t gpuIndex, std::string &error);
    bool executeOpenClC(const std::string &source, const std::string &entry,
                       const std::vector<uint32_t> &input,
                       const std::vector<uint32_t> &expected, OpenCLExecution &result);
    std::shared_ptr<OpenCLPipeline> compileOpenClC(const std::string &source,
                                                 const std::string &entry, std::string &error);
    bool executePipeline(const std::shared_ptr<OpenCLPipeline> &pipeline,
                         const std::vector<uint32_t> &input, OpenCLExecution &result);
    uint64_t pipelineBuildCount() const;
    const ProviderDescriptor &descriptor() const;
    const OpenCLDeviceInfo &device() const;
    const OpenCLExecution &bootstrapEvidence() const;
    // Session invalidation only; this does not reset the physical GPU.
    void invalidateSession();
    static const char *witnessSource();
    static constexpr size_t MaxElements = 4096;
    static constexpr size_t MaxSourceBytes = 65536;
private:
    friend class OpenCLPipeline;
    struct Impl;
    std::shared_ptr<Impl> impl_;
};

} // namespace MellowRT
