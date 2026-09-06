// Synthetic ICD fixture for production adapter state/failure regression only.
// All kernel work in THIS binary is simulated on the CPU. Never GPU evidence.
#include "../Runtime/OpenCLProvider.hpp"
#include "../Runtime/OpenCLAbi.hpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

using namespace MellowRT;
using namespace MellowRT::OpenCLAbi;
static unsigned checks {};
#define CHECK(x) do { ++checks; if (!(x)) { std::fprintf(stderr, "FAIL %d: %s\n", __LINE__, #x); std::exit(1); } } while (false)
enum class Mode { Intel, MissingIdentity, IdentityQueryFails, NoPlatforms, ContextFails, WrongBootstrap };
static Mode mode = Mode::Intel;
static bool failFinish {}, failEventRelease {}, failBuild {}, failKernel {};
static unsigned enqueues {}, releases {}, eventReleases {}, identityQueries {};
static int platformTag, deviceTag, contextTag, queueTag, programTag, kernelTag, memoryTag, eventTag;
static std::vector<uint32_t> memory;

template<typename T> static Int put(const T &value, size_t size, void *output, size_t *actual) {
    if (actual) *actual = sizeof(value);
    if (!output) return Success;
    if (size < sizeof(value)) return -30;
    std::memcpy(output, &value, sizeof(value));
    return Success;
}
static Int putText(const std::string &value, size_t size, void *output, size_t *actual) {
    if (actual) *actual = value.size() + 1;
    if (!output) return Success;
    if (size < value.size() + 1) return -30;
    std::memcpy(output, value.c_str(), value.size() + 1);
    return Success;
}
static Int MELLOW_CL_CALL platforms(UInt, Handle *output, UInt *count) {
    if (count) *count = mode == Mode::NoPlatforms ? 0 : 1;
    if (mode == Mode::NoPlatforms) return PlatformNotFound;
    if (output) output[0] = &platformTag;
    return Success;
}
static Int MELLOW_CL_CALL platformInfo(Handle, UInt, size_t size, void *output, size_t *actual) {
    return putText("SYNTHETIC ICD: NO GPU", size, output, actual);
}
static Int MELLOW_CL_CALL devices(Handle, Bits type, UInt, Handle *output, UInt *count) {
    if (type != Gpu) return DeviceNotFound;
    if (count) *count = 1;
    if (output) output[0] = &deviceTag;
    return Success;
}
static Int MELLOW_CL_CALL deviceInfo(Handle, UInt parameter, size_t size, void *output, size_t *actual) {
    switch (parameter) {
        case DeviceType: return put<Bits>(Gpu, size, output, actual);
        case VendorId: return put<UInt>(mode == Mode::MissingIdentity ? 0x10DE : 0x8086, size, output, actual);
        case DeviceAvailable: case CompilerAvailable: return put<UInt>(1, size, output, actual);
        case IntelDeviceId:
            ++identityQueries;
            if (mode == Mode::IdentityQueryFails) return -30;
            return put<UInt>(0x7D41, size, output, actual);
        case DeviceExtensions:
            return putText(mode == Mode::MissingIdentity ? "" : "cl_intel_device_attribute_query", size, output, actual);
        default: return putText("Synthetic fixture", size, output, actual);
    }
}
static Handle MELLOW_CL_CALL createContext(const intptr_t *, UInt, const Handle *, ContextCallback, void *, Int *status) {
    *status = mode == Mode::ContextFails ? -5 : Success;
    return mode == Mode::ContextFails ? nullptr : &contextTag;
}
static Handle MELLOW_CL_CALL createQueue(Handle, Handle, Bits, Int *status) { *status = Success; return &queueTag; }
static Int MELLOW_CL_CALL queueInfo(Handle, UInt parameter, size_t size, void *output, size_t *actual) {
    if (parameter == QueueProperties) return put<Bits>(ProfilingQueue, size, output, actual);
    return put<Handle>(parameter == QueueContext ? &contextTag : &deviceTag, size, output, actual);
}
static Handle MELLOW_CL_CALL createProgram(Handle, UInt, const char **, const size_t *, Int *status) { *status = Success; return &programTag; }
static Int MELLOW_CL_CALL build(Handle, UInt, const Handle *, const char *, BuildCallback, void *) { return failBuild ? -11 : Success; }
static Int MELLOW_CL_CALL buildInfo(Handle, Handle, UInt, size_t size, void *output, size_t *actual) { return putText("", size, output, actual); }
static Handle MELLOW_CL_CALL createKernel(Handle, const char *, Int *status) {
    *status = failKernel ? -46 : Success; return failKernel ? nullptr : &kernelTag;
}
static Handle MELLOW_CL_CALL createBuffer(Handle, Bits, size_t size, void *input, Int *status) {
    auto words = static_cast<uint32_t *>(input);
    memory.assign(words, words + size / sizeof(uint32_t));
    *status = Success;
    return &memoryTag;
}
static Int MELLOW_CL_CALL setArg(Handle, UInt, size_t, const void *) { return Success; }
static Int MELLOW_CL_CALL enqueue(Handle, Handle, UInt, const size_t *, const size_t *, const size_t *, UInt, const Handle *, Handle *event) {
    ++enqueues;
    for (auto &word : memory) word = word * 7 + (mode == Mode::WrongBootstrap ? 4 : 3);
    *event = &eventTag;
    return Success;
}
static Int MELLOW_CL_CALL waitEvent(UInt, const Handle *) { return Success; }
static Int MELLOW_CL_CALL eventInfo(Handle, UInt parameter, size_t size, void *output, size_t *actual) {
    if (parameter == EventQueue) return put<Handle>(&queueTag, size, output, actual);
    if (parameter == EventContext) return put<Handle>(&contextTag, size, output, actual);
    if (parameter == EventCommand) return put<UInt>(KernelCommand, size, output, actual);
    return put<Int>(Success, size, output, actual);
}
static Int MELLOW_CL_CALL profiling(Handle, UInt parameter, size_t size, void *output, size_t *actual) {
    return put<uint64_t>(enqueues * 100 + (parameter == ProfileStart ? 1 : 20), size, output, actual);
}
static Int MELLOW_CL_CALL readBuffer(Handle, Handle, UInt, size_t, size_t size, void *output, UInt, const Handle *, Handle *) {
    if (size > memory.size() * sizeof(uint32_t)) return -30;
    std::memcpy(output, memory.data(), size);
    return Success;
}
static Int MELLOW_CL_CALL finish(Handle) { return failFinish ? -5 : Success; }
static Int MELLOW_CL_CALL release(Handle object) {
    ++releases;
    if (object == &eventTag) {
        ++eventReleases;
        if (failEventRelease) return -5;
    }
    return Success;
}
static Functions fixture() {
    Functions f {};
    f.GetPlatformIDs = platforms; f.GetPlatformInfo = platformInfo;
    f.GetDeviceIDs = devices; f.GetDeviceInfo = deviceInfo;
    f.CreateContext = createContext; f.CreateCommandQueue = createQueue; f.GetCommandQueueInfo = queueInfo;
    f.CreateProgramWithSource = createProgram; f.BuildProgram = build; f.GetProgramBuildInfo = buildInfo;
    f.CreateKernel = createKernel; f.CreateBuffer = createBuffer; f.SetKernelArg = setArg;
    f.EnqueueNDRangeKernel = enqueue; f.WaitForEvents = waitEvent; f.GetEventInfo = eventInfo;
    f.GetEventProfilingInfo = profiling; f.EnqueueReadBuffer = readBuffer; f.Finish = finish;
    f.ReleaseEvent = f.ReleaseMemObject = f.ReleaseKernel = f.ReleaseProgram = f.ReleaseCommandQueue = f.ReleaseContext = release;
    return f;
}

int main() {
    OpenCLProvider provider(fixture());
    std::string error;
    CHECK(provider.initialize(0, error));
    CHECK(provider.device().reportedDeviceId == 0x7D41);
    CHECK(provider.bootstrapEvidence().resourcesReleased);
    const auto firstEpoch = provider.descriptor().resetEpoch;
    const auto firstSequence = provider.bootstrapEvidence().sequence;
    CHECK(!provider.initialize(0, error)); // Redundant initialize preserves live session.
    CHECK(provider.descriptor().verified != 0);
    provider.invalidateSession();
    mode = Mode::MissingIdentity;
    const auto queries = identityQueries;
    CHECK(!provider.initialize(0, error));
    CHECK(identityQueries == queries); // Must not query an unadvertised extension.
    CHECK(provider.device().reportedVendorId == 0x10DE);
    CHECK(provider.device().reportedDeviceId == 0);
    CHECK(!provider.device().deviceIdFromIntelExtension);
    CHECK(!provider.bootstrapEvidence().submitted);
    CHECK(provider.bootstrapEvidence().output.empty());
    CHECK(provider.descriptor().device.deviceId == 0 && provider.descriptor().verified == 0);
    CHECK(provider.descriptor().resetEpoch > firstEpoch);
    mode = Mode::IdentityQueryFails;
    CHECK(!provider.initialize(0, error));
    CHECK(provider.device().reportedDeviceId == 0);
    CHECK(!provider.device().deviceIdFromIntelExtension);
    CHECK(!provider.bootstrapEvidence().submitted);
    mode = Mode::NoPlatforms;
    CHECK(!provider.initialize(0, error));
    CHECK(provider.device().reportedVendorId == 0 && provider.device().name.empty());
    CHECK(!provider.bootstrapEvidence().submitted);
    mode = Mode::ContextFails;
    CHECK(!provider.initialize(0, error));
    CHECK(!provider.bootstrapEvidence().submitted);
    CHECK(provider.descriptor().verified == 0);
    mode = Mode::WrongBootstrap;
    CHECK(!provider.initialize(0, error));
    CHECK(provider.bootstrapEvidence().submitted && !provider.bootstrapEvidence().resultsVerified);
    CHECK(provider.descriptor().verified == 0);
    mode = Mode::Intel;
    CHECK(provider.initialize(0, error));
    CHECK(error.empty());
    CHECK(provider.bootstrapEvidence().sequence > firstSequence);
    CHECK(provider.descriptor().resetEpoch > firstEpoch);
    const std::vector<uint32_t> input {1, 2, 3, 4}, expected {10, 17, 24, 31};
    OpenCLExecution result;
    CHECK(provider.executeOpenClC(OpenCLProvider::witnessSource(), "mellow_witness", input, expected, result));
    CHECK(result.resourcesReleased && result.runtimeCompletionAccepted);
    failFinish = true;
    CHECK(!provider.executeOpenClC(OpenCLProvider::witnessSource(), "mellow_witness", input, expected, result));
    CHECK(result.submitted && result.resultsVerified);
    CHECK(!result.resourcesReleased && !result.runtimeCompletionAccepted);
    CHECK(provider.descriptor().verified == 0);
    failFinish = false;
    CHECK(provider.initialize(0, error));
    const auto priorEventReleases = eventReleases;
    failEventRelease = true;
    CHECK(!provider.executeOpenClC(OpenCLProvider::witnessSource(), "mellow_witness", input, expected, result));
    CHECK(result.submitted && !result.resourcesReleased && !result.runtimeCompletionAccepted);
    CHECK(eventReleases == priorEventReleases + 1); // No destructor double-release.
    CHECK(provider.descriptor().verified == 0);
    failEventRelease = false;
    CHECK(provider.initialize(0, error));
    CHECK(provider.executeOpenClC(OpenCLProvider::witnessSource(), "mellow_witness", input, expected, result));
    CHECK(result.runtimeCompletionAccepted && result.resourcesReleased);
    failBuild = true;
    auto rejectedBuild = provider.compileOpenClC(OpenCLProvider::witnessSource(), "mellow_witness", error);
    CHECK(!rejectedBuild && !error.empty());
    CHECK(provider.pipelineBuildCount() == 0 && provider.descriptor().verified != 0);
    failBuild = false;
    failKernel = true;
    auto rejectedKernel = provider.compileOpenClC(OpenCLProvider::witnessSource(), "mellow_witness", error);
    CHECK(!rejectedKernel && !error.empty());
    CHECK(provider.pipelineBuildCount() == 0 && provider.descriptor().verified != 0);
    failKernel = false;
    auto pipeline = provider.compileOpenClC(OpenCLProvider::witnessSource(), "mellow_witness", error);
    CHECK(bool(pipeline) && pipeline->compilationSerial() == 1);
    CHECK(provider.executePipeline(pipeline, input, result));
    CHECK(result.executionCompleted && result.output == expected && result.resourcesReleased);
    CHECK(!result.resultsVerified && !result.runtimeCompletionAccepted); // No caller oracle supplied.
    CHECK(provider.executePipeline(pipeline, input, result));
    CHECK(provider.pipelineBuildCount() == 1); // Compiled program/kernel reused.
    provider.invalidateSession();
    CHECK(!provider.executePipeline(pipeline, input, result) && !result.submitted);
    CHECK(provider.initialize(0, error));
    CHECK(!provider.executePipeline(pipeline, input, result) && !result.submitted); // Old epoch cannot revive.
    auto current = provider.compileOpenClC(OpenCLProvider::witnessSource(), "mellow_witness", error);
    CHECK(bool(current) && current->compilationSerial() == 2);
    CHECK(provider.executePipeline(current, input, result) && result.executionCompleted);
    {
        OpenCLProvider other(fixture());
        CHECK(other.initialize(0, error));
        CHECK(!other.executePipeline(current, input, result) && !result.submitted);
    }
    failEventRelease = true;
    CHECK(!provider.executePipeline(current, input, result));
    CHECK(!result.executionCompleted && !result.runtimeCompletionAccepted);
    CHECK(provider.descriptor().verified == 0);
    failEventRelease = false;
    std::shared_ptr<OpenCLPipeline> survivor;
    unsigned afterProviderDestroy {};
    {
        auto temporary = std::make_unique<OpenCLProvider>(fixture());
        CHECK(temporary->initialize(0, error));
        survivor = temporary->compileOpenClC(OpenCLProvider::witnessSource(), "mellow_witness", error);
        CHECK(bool(survivor));
        const auto beforeProviderDestroy = releases;
        temporary.reset();
        CHECK(releases == beforeProviderDestroy); // Pipeline retains context/queue + API owner.
        CHECK(survivor->compilationSerial() == 1 && survivor->buildLog().empty());
        afterProviderDestroy = releases;
    }
    survivor.reset();
    CHECK(releases == afterProviderDestroy + 4); // kernel/program then queue/context.
    std::printf("PASS: %u synthetic ICD state/cleanup regressions; no hardware GPU execution\n", checks);
}
