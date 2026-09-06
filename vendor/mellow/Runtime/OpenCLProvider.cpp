#include "OpenCLProvider.hpp"
#include "OpenCLAbi.hpp"
#include <cstring>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <utility>
#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <dlfcn.h>
#endif

namespace MellowRT {
using namespace OpenCLAbi;
namespace {
void require(bool condition, const std::string &message) {
    if (!condition) throw std::runtime_error(message);
}
void checked(Int status, const char *operation) {
    require(status == Success, std::string(operation) + ": OpenCL status " + std::to_string(status));
}
class Library {
public:
    Library() {
#if defined(_WIN32)
        handle_ = LoadLibraryExW(L"OpenCL.dll", nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32);
#elif defined(__APPLE__)
        handle_ = dlopen("/System/Library/Frameworks/OpenCL.framework/OpenCL", RTLD_NOW | RTLD_LOCAL);
#else
        handle_ = dlopen("libOpenCL.so.1", RTLD_NOW | RTLD_LOCAL);
#endif
        require(handle_ != nullptr, "OpenCL loader is unavailable; no driver installation attempted");
    }
    ~Library() {
        if (handle_) {
#if defined(_WIN32)
            FreeLibrary(handle_);
#else
            dlclose(handle_);
#endif
        }
    }
    template<typename T> void load(T &function, const char *name) {
#if defined(_WIN32)
        const auto address = GetProcAddress(handle_, name);
#else
        const auto address = dlsym(handle_, name);
#endif
        require(address != nullptr, std::string("OpenCL symbol unavailable: ") + name);
        static_assert(sizeof(function) == sizeof(address), "dynamic function ABI");
        std::memcpy(&function, &address, sizeof(function));
    }
private:
#if defined(_WIN32)
    HMODULE handle_ {};
#else
    void *handle_ {};
#endif
};
template<typename F> std::string textInfo(F function, Handle object, UInt parameter) {
    size_t size {};
    checked(function(object, parameter, 0, nullptr, &size), "information length");
    require(size <= 1024 * 1024, "OpenCL information exceeds bounded size");
    std::vector<char> result(size ? size : 1, 0);
    checked(function(object, parameter, result.size(), result.data(), nullptr), "information string");
    require(result.back() == 0, "OpenCL information is not terminated");
    return result.data();
}
template<typename T, typename F> T scalarInfo(F function, Handle object, UInt parameter) {
    T value {};
    size_t size {};
    checked(function(object, parameter, sizeof(value), &value, &size), "information scalar");
    require(size == sizeof(value), "OpenCL scalar ABI size mismatch");
    return value;
}
bool hasExtension(const std::string &extensions, const std::string &wanted) {
    std::istringstream input(extensions);
    std::string extension;
    while (input >> extension) if (extension == wanted) return true;
    return false;
}
constexpr char Witness[] =
    "__kernel void mellow_witness(__global uint *x) { size_t i = get_global_id(0); x[i] = x[i] * 7u + 3u; }\n";
}

struct OpenCLProvider::Impl {
    std::shared_ptr<Library> library;
    Functions api {};
#if defined(MELLOW_OPENCL_TESTING)
    Functions syntheticApi {};
    bool synthetic {};
#endif
    Handle device {}, context {}, queue {};
    ProviderDescriptor provider {};
    OpenCLDeviceInfo info {};
    OpenCLExecution bootstrap {};
    CompletionTracker completion {};
    uint64_t epoch {1}, sequence {}, record {}, compilations {};
    bool ready {};

    ~Impl() { close(); }
    void close() {
        if (queue) { api.Finish(queue); api.ReleaseCommandQueue(queue); queue = nullptr; }
        if (context) { api.ReleaseContext(context); context = nullptr; }
    }
    void invalidate() {
        ready = false;
        provider.verified = 0;
        provider.validationRecord = 0;
        if (epoch != std::numeric_limits<uint64_t>::max()) ++epoch;
        provider.resetEpoch = epoch;
        provider.evidenceEpoch = 0;
        completion.invalidateForReset(epoch);
        close();
    }
    void initialize(size_t gpuIndex) {
        require(!ready && !context && !queue, "Provider is already initialized");
        // A new attempt must not inherit discovery or evidence from any earlier
        // GPU, including when this attempt fails before context creation.
        info = {};
        bootstrap = {};
        provider = {};
        device = nullptr;
        completion = {};
        api = {};
        library.reset();
        require(epoch != std::numeric_limits<uint64_t>::max(), "Session epoch exhausted");
#if defined(MELLOW_OPENCL_TESTING)
        if (synthetic) {
            api = syntheticApi;
#define MELLOW_CHECK(name, result, ...) require(api.name != nullptr, "Missing synthetic OpenCL function " #name);
            MELLOW_CL_FUNCTIONS(MELLOW_CHECK)
#undef MELLOW_CHECK
        } else
#endif
        {
            library = std::make_shared<Library>();
#define MELLOW_LOAD(name, result, ...) library->load(api.name, "cl" #name);
            MELLOW_CL_FUNCTIONS(MELLOW_LOAD)
#undef MELLOW_LOAD
        }
        UInt count {};
        const auto platformStatus = api.GetPlatformIDs(0, nullptr, &count);
        require(platformStatus != PlatformNotFound && count, "No OpenCL platform available");
        checked(platformStatus, "clGetPlatformIDs");
        require(count <= 64, "Platform count exceeds probe bound");
        std::vector<Handle> platforms(count);
        checked(api.GetPlatformIDs(count, platforms.data(), nullptr), "clGetPlatformIDs");
        std::vector<std::pair<Handle, Handle>> devices;
        for (Handle platform : platforms) {
            count = 0;
            const auto deviceStatus = api.GetDeviceIDs(platform, Gpu, 0, nullptr, &count);
            if (deviceStatus == DeviceNotFound) continue;
            checked(deviceStatus, "clGetDeviceIDs(GPU)");
            require(count <= 64 && devices.size() + count <= 128, "Device count exceeds probe bound");
            if (!count) continue;
            std::vector<Handle> current(count);
            checked(api.GetDeviceIDs(platform, Gpu, count, current.data(), nullptr), "clGetDeviceIDs(GPU)");
            for (Handle item : current) devices.emplace_back(platform, item);
        }
        require(gpuIndex < devices.size(), "Requested OpenCL GPU index unavailable; CPU fallback disabled");
        Handle platform = devices[gpuIndex].first;
        device = devices[gpuIndex].second;
        info.platform = textInfo(api.GetPlatformInfo, platform, 0x0902);
        info.platformVendor = textInfo(api.GetPlatformInfo, platform, 0x0903);
        info.name = textInfo(api.GetDeviceInfo, device, DeviceName);
        info.vendor = textInfo(api.GetDeviceInfo, device, DeviceVendor);
        info.driver = textInfo(api.GetDeviceInfo, device, DriverVersion);
        info.version = textInfo(api.GetDeviceInfo, device, DeviceVersion);
        info.extensions = textInfo(api.GetDeviceInfo, device, DeviceExtensions);
        info.reportedType = scalarInfo<Bits>(api.GetDeviceInfo, device, DeviceType);
        info.reportedVendorId = scalarInfo<UInt>(api.GetDeviceInfo, device, VendorId);
        info.available = scalarInfo<UInt>(api.GetDeviceInfo, device, DeviceAvailable) != 0;
        info.compilerAvailable = scalarInfo<UInt>(api.GetDeviceInfo, device, CompilerAvailable) != 0;
        require((info.reportedType & Gpu) && !(info.reportedType & Cpu), "Driver device is not exclusively GPU classified");
        require(info.available && info.compilerAvailable, "GPU/compiler unavailable");
        if (hasExtension(info.extensions, "cl_intel_device_attribute_query")) {
            info.reportedDeviceId = scalarInfo<UInt>(api.GetDeviceInfo, device, IntelDeviceId);
            info.deviceIdFromIntelExtension = true;
        }
        require(info.reportedDeviceId && info.reportedDeviceId <= 0xFFFF &&
                info.reportedVendorId && info.reportedVendorId <= 0xFFFF,
                "Driver did not expose a usable device ID; policy identity will not be fabricated");
        Int status {};
        context = api.CreateContext(nullptr, 1, &device, nullptr, nullptr, &status);
        checked(status, "clCreateContext");
        require(context, "clCreateContext returned null");
        queue = api.CreateCommandQueue(context, device, ProfilingQueue, &status);
        checked(status, "clCreateCommandQueue");
        require(queue, "clCreateCommandQueue returned null");
        require(scalarInfo<Handle>(api.GetCommandQueueInfo, queue, QueueContext) == context &&
                scalarInfo<Handle>(api.GetCommandQueueInfo, queue, QueueDevice) == device &&
                scalarInfo<Bits>(api.GetCommandQueueInfo, queue, QueueProperties) == ProfilingQueue,
                "Queue ownership/profiling/in-order properties do not match");
        // Handles identify this adapter's live runtime objects, never a PCI
        // address or a cross-process identity. Driver reset detection relies on
        // OpenCL errors; every such submitted-work failure invalidates the epoch.
        provider = {};
        provider.id = static_cast<uint64_t>(reinterpret_cast<uintptr_t>(queue));
        provider.device = {static_cast<uint16_t>(info.reportedVendorId),
                           static_cast<uint16_t>(info.reportedDeviceId), 0,
                           static_cast<uint64_t>(reinterpret_cast<uintptr_t>(device))};
        provider.api = Api::OpenCL;
        provider.kind = ProviderKind::Host;
        provider.execution = Execution::Hardware;
        provider.apiMajor = 1;
        provider.apiMinor = 2; // Successfully built OpenCL C 1.2 is the supported route.
        provider.resetEpoch = epoch;
        provider.advertised = bit(Feature::Compute) | bit(Feature::OrderedQueue);
        std::vector<uint32_t> input(256), expected(256);
        for (size_t i = 0; i < input.size(); ++i) { input[i] = static_cast<uint32_t>(i * 13 + 1); expected[i] = input[i] * 7 + 3; }
        // Bootstrap is an explicit unadvertised hardware validation dispatch.
        // Only after its event, readback and ownership checks pass may a provider
        // validation record be published to the workload planner.
        dispatch(Witness, "mellow_witness", input, expected, bootstrap, false);
        require(bootstrap.resultsVerified && bootstrap.profilingVerified && bootstrap.eventOwnershipVerified,
                "Bootstrap did not validate GPU compute/ordered queue");
        provider.evidenceEpoch = epoch;
        provider.validationRecord = ++record;
        provider.verified = provider.advertised;
        bootstrap.validationRecord = provider.validationRecord;
        completion = CompletionTracker {};
        ready = true;
    }

    struct CommandResources {
        Impl &owner;
        std::vector<std::pair<Functions::ReleaseEventFn, Handle>> objects;
        ~CommandResources() {
            if (objects.empty()) return;
            if (owner.queue) owner.api.Finish(owner.queue);
            for (auto i = objects.rbegin(); i != objects.rend(); ++i) i->first(i->second);
        }
        void finalize() {
            std::string errors;
            const auto drainStatus = owner.api.Finish(owner.queue);
            if (drainStatus != Success) errors = "clFinish: OpenCL status " + std::to_string(drainStatus);
            for (auto i = objects.rbegin(); i != objects.rend(); ++i) {
                const auto status = i->first(i->second);
                if (status != Success) errors += "; OpenCL object release status " + std::to_string(status);
            }
            objects.clear(); // Every release attempted once; destructor must not repeat it.
            require(errors.empty(), errors);
        }
        Handle own(Handle object, Int status, Functions::ReleaseEventFn release, const char *operation) {
            checked(status, operation);
            require(object != nullptr, std::string(operation) + " returned null");
            objects.emplace_back(release, object);
            return object;
        }
    };
    void dispatch(const std::string &source, const std::string &entry,
                  const std::vector<uint32_t> &input, const std::vector<uint32_t> &expected,
                  OpenCLExecution &result, bool useRuntime) {
        require(context && queue, "OpenCL session not active");
        require(!source.empty() && source.size() <= MaxSourceBytes && source.find('\0') == std::string::npos,
                "OpenCL C source is empty, oversized or contains embedded NUL");
        require(!entry.empty() && entry.size() <= 128 && entry.find('\0') == std::string::npos,
                "Kernel entry name invalid");
        require(!input.empty() && input.size() <= MaxElements && expected.size() == input.size(),
                "Input/reference sizes invalid or oversized");
        if (useRuntime) {
            const Step step {Workload::Compute, 0, provider.id, WorkloadInput::OpenClC};
            const auto plan = planWorkload(&provider, 1, &step, 1, nullptr, 0, nullptr, 0);
            result.planStatus = plan.status;
            require(plan.status == PlanStatus::Ready && plan.providers[0] == provider.id && !plan.referenceOnly,
                    "MellowRuntime denied the direct OpenCL C route");
            result.runtimePlanned = true;
        }
        CommandResources resources {*this, {}};
        Int status {};
        const char *text = source.c_str();
        const size_t sourceSize = source.size();
        Handle program = api.CreateProgramWithSource(context, 1, &text, &sourceSize, &status);
        resources.own(program, status, api.ReleaseProgram, "clCreateProgramWithSource");
        const auto buildStatus = api.BuildProgram(program, 1, &device, "-cl-std=CL1.2", nullptr, nullptr);
        size_t logSize {};
        checked(api.GetProgramBuildInfo(program, device, ProgramBuildLog, 0, nullptr, &logSize), "build log size");
        require(logSize <= 1024 * 1024, "Build log too large");
        std::vector<char> log(logSize ? logSize : 1, 0);
        checked(api.GetProgramBuildInfo(program, device, ProgramBuildLog, log.size(), log.data(), nullptr), "build log");
        require(log.back() == 0, "Build log not terminated");
        result.buildLog = log.data();
        checked(buildStatus, "clBuildProgram");
        Handle kernel = api.CreateKernel(program, entry.c_str(), &status);
        resources.own(kernel, status, api.ReleaseKernel, "clCreateKernel");
        executeKernel(resources, kernel, input, &expected, result, useRuntime);
    }
    void executeKernel(CommandResources &resources, Handle kernel,
                       const std::vector<uint32_t> &input, const std::vector<uint32_t> *expected,
                       OpenCLExecution &result, bool useRuntime) {
        Int status {};
        auto initial = input;
        Handle buffer = api.CreateBuffer(context, ReadWriteCopy, initial.size() * sizeof(uint32_t), initial.data(), &status);
        resources.own(buffer, status, api.ReleaseMemObject, "clCreateBuffer");
        checked(api.SetKernelArg(kernel, 0, sizeof(buffer), &buffer), "clSetKernelArg");
        require(sequence != std::numeric_limits<uint64_t>::max(), "Queue sequence exhausted");
        const SubmissionToken token {provider.id, provider.device.instance, epoch,
                                     static_cast<uint64_t>(reinterpret_cast<uintptr_t>(queue)), ++sequence};
        const size_t globalSize = input.size();
        Handle event {};
        result.submissionAttempted = true;
        checked(api.EnqueueNDRangeKernel(queue, kernel, 1, nullptr, &globalSize, nullptr, 0, nullptr, &event),
                "clEnqueueNDRangeKernel");
        result.submitted = true;
        resources.own(event, Success, api.ReleaseEvent, "kernel event");
        result.epoch = epoch;
        result.sequence = sequence;
        if (useRuntime && expected) {
            result.armStatus = completion.armAfterSubmission(provider, token);
            require(result.armStatus == CompletionStatus::Accepted, "Runtime rejected actual submission token");
        }
        checked(api.WaitForEvents(1, &event), "clWaitForEvents");
        require(scalarInfo<Handle>(api.GetEventInfo, event, EventQueue) == queue &&
                scalarInfo<Handle>(api.GetEventInfo, event, EventContext) == context &&
                scalarInfo<UInt>(api.GetEventInfo, event, EventCommand) == KernelCommand &&
                scalarInfo<Int>(api.GetEventInfo, event, EventStatus) == Success,
                "Event queue/context/type/completion differs from the submitted kernel");
        result.eventOwnershipVerified = true;
        result.output.resize(input.size());
        checked(api.EnqueueReadBuffer(queue, buffer, 1, 0, result.output.size() * sizeof(uint32_t),
                                      result.output.data(), 0, nullptr, nullptr), "clEnqueueReadBuffer");
        result.resultsVerified = expected && result.output == *expected;
        result.gpuStart = scalarInfo<uint64_t>(api.GetEventProfilingInfo, event, ProfileStart);
        result.gpuEnd = scalarInfo<uint64_t>(api.GetEventProfilingInfo, event, ProfileEnd);
        result.profilingVerified = result.gpuStart && result.gpuEnd > result.gpuStart;
        if (expected) require(result.resultsVerified, "GPU readback does not match supplied reference");
        require(result.profilingVerified, "GPU profiling interval is missing or invalid");
        resources.finalize();
        result.resourcesReleased = true;
        if (useRuntime && expected) {
            result.validationRecord = ++record;
            const CompletionObservation observed {token, ObservationKind::GpuCompletion,
                                                   result.gpuStart, result.gpuEnd,
                                                   result.validationRecord, result.resultsVerified};
            result.observeStatus = completion.observe(observed);
            require(result.observeStatus == CompletionStatus::Accepted &&
                    completion.state() == CompletionState::GpuEvidenceAccepted,
                    "Runtime rejected observed GPU completion");
            result.runtimeCompletionAccepted = true;
        }
        result.executionCompleted = true;
    }
};

struct OpenCLPipeline::Impl {
    std::shared_ptr<OpenCLProvider::Impl> owner;
    std::shared_ptr<Library> library;
    Functions api {};
    Handle program {}, kernel {}, context {};
    uint64_t epoch {}, serial {};
    std::string log;
    ~Impl() {
        if (kernel) api.ReleaseKernel(kernel);
        if (program) api.ReleaseProgram(program);
    }
};
OpenCLPipeline::OpenCLPipeline() : impl_(std::make_unique<Impl>()) {}
OpenCLPipeline::~OpenCLPipeline() = default;
uint64_t OpenCLPipeline::compilationSerial() const { return impl_->serial; }
const std::string &OpenCLPipeline::buildLog() const { return impl_->log; }

OpenCLProvider::OpenCLProvider() : impl_(std::make_shared<Impl>()) {}
#if defined(MELLOW_OPENCL_TESTING)
OpenCLProvider::OpenCLProvider(const OpenCLAbi::Functions &functions) : impl_(std::make_shared<Impl>()) {
    impl_->synthetic = true;
    impl_->syntheticApi = functions;
}
#endif
OpenCLProvider::~OpenCLProvider() = default;
bool OpenCLProvider::initialize(size_t index, std::string &error) {
    error.clear();
    if (impl_->ready) { error = "Provider is already initialized"; return false; }
    try { impl_->initialize(index); return true; }
    catch (const std::exception &failure) { error = failure.what(); impl_->invalidate(); return false; }
}
bool OpenCLProvider::executeOpenClC(const std::string &source, const std::string &entry,
                                  const std::vector<uint32_t> &input, const std::vector<uint32_t> &expected,
                                  OpenCLExecution &result) {
    result = {};
    try {
        require(impl_->ready, "Provider has no current validated substrate");
        impl_->dispatch(source, entry, input, expected, result, true);
        return true;
    } catch (const std::exception &failure) {
        result.error = failure.what();
        if (result.submissionAttempted) impl_->invalidate();
        return false;
    }
}
std::shared_ptr<OpenCLPipeline> OpenCLProvider::compileOpenClC(const std::string &source,
                                                           const std::string &entry, std::string &error) {
    error.clear();
    try {
        require(impl_->ready && impl_->context && impl_->queue, "Provider has no current validated substrate");
        require(!source.empty() && source.size() <= MaxSourceBytes && source.find('\0') == std::string::npos,
                "OpenCL C source invalid");
        require(!entry.empty() && entry.size() <= 128 && entry.find('\0') == std::string::npos, "Kernel entry invalid");
        auto pipeline = std::shared_ptr<OpenCLPipeline>(new OpenCLPipeline());
        auto &compiled = *pipeline->impl_;
        compiled.owner = impl_;
        compiled.library = impl_->library;
        compiled.api = impl_->api;
        compiled.context = impl_->context;
        compiled.epoch = impl_->epoch;
        const char *text = source.c_str();
        const size_t length = source.size();
        Int status {};
        compiled.program = compiled.api.CreateProgramWithSource(compiled.context, 1, &text, &length, &status);
        checked(status, "clCreateProgramWithSource");
        require(compiled.program, "Program creation returned null");
        const auto build = compiled.api.BuildProgram(compiled.program, 1, &impl_->device, "-cl-std=CL1.2", nullptr, nullptr);
        size_t size {};
        checked(compiled.api.GetProgramBuildInfo(compiled.program, impl_->device, ProgramBuildLog, 0, nullptr, &size), "build log size");
        require(size <= 1024 * 1024, "Build log too large");
        std::vector<char> log(size ? size : 1, 0);
        checked(compiled.api.GetProgramBuildInfo(compiled.program, impl_->device, ProgramBuildLog, log.size(), log.data(), nullptr), "build log");
        require(log.back() == 0, "Build log not terminated");
        compiled.log = log.data();
        require(build == Success, "OpenCL pipeline compilation failed: " + compiled.log);
        compiled.kernel = compiled.api.CreateKernel(compiled.program, entry.c_str(), &status);
        checked(status, "clCreateKernel");
        require(compiled.kernel, "Kernel creation returned null");
        require(impl_->compilations != std::numeric_limits<uint64_t>::max(), "Pipeline build serial exhausted");
        compiled.serial = ++impl_->compilations;
        return pipeline;
    } catch (const std::exception &failure) { error = failure.what(); return {}; }
}
bool OpenCLProvider::executePipeline(const std::shared_ptr<OpenCLPipeline> &pipeline,
                                    const std::vector<uint32_t> &input, OpenCLExecution &result) {
    result = {};
    try {
        require(impl_->ready && pipeline && pipeline->impl_, "Provider/pipeline unavailable");
        const auto &compiled = *pipeline->impl_;
        require(compiled.owner.get() == impl_.get() && compiled.context == impl_->context &&
                compiled.epoch == impl_->epoch && compiled.library == impl_->library,
                "Pipeline belongs to another provider or invalidated epoch");
        require(!input.empty() && input.size() <= MaxElements, "Input size invalid");
        const Step step {Workload::Compute, 0, impl_->provider.id, WorkloadInput::OpenClC};
        const auto plan = planWorkload(&impl_->provider, 1, &step, 1, nullptr, 0, nullptr, 0);
        result.planStatus = plan.status;
        require(plan.status == PlanStatus::Ready && plan.providers[0] == impl_->provider.id && !plan.referenceOnly,
                "MellowRuntime denied compiled OpenCL route");
        result.runtimePlanned = true;
        Impl::CommandResources resources {*impl_, {}};
        impl_->executeKernel(resources, compiled.kernel, input, nullptr, result, true);
        return result.executionCompleted;
    } catch (const std::exception &failure) {
        result.error = failure.what();
        if (result.submissionAttempted) impl_->invalidate();
        return false;
    }
}
uint64_t OpenCLProvider::pipelineBuildCount() const { return impl_->compilations; }
const ProviderDescriptor &OpenCLProvider::descriptor() const { return impl_->provider; }
const OpenCLDeviceInfo &OpenCLProvider::device() const { return impl_->info; }
const OpenCLExecution &OpenCLProvider::bootstrapEvidence() const { return impl_->bootstrap; }
void OpenCLProvider::invalidateSession() { impl_->invalidate(); }
const char *OpenCLProvider::witnessSource() { return Witness; }
} // namespace MellowRT
