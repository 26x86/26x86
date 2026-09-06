#include "../Runtime/MetalObjects.hpp"
#include "opencl_runtime_sha256.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>

using namespace MellowMTL;
static unsigned checks {};
static unsigned negativeChecks {};
static void check(bool value, const std::string &message) {
    ++checks;
    if (!value) throw std::runtime_error(message);
}
static void reject(bool value, const std::string &message) { ++negativeChecks; check(value, message); }
static std::string quote(const std::string &input) {
    std::ostringstream text;
    constexpr char hex[] = "0123456789abcdef";
    text << '"';
    for (unsigned char c : input) {
        if (c == '"' || c == '\\') text << '\\' << c;
        else if (c < 32) text << "\\u00" << hex[c >> 4] << hex[c & 15];
        else text << c;
    }
    text << '"';
    return text.str();
}
static void words(std::ostream &out, const std::vector<uint32_t> &values) {
    out << '[';
    for (size_t i = 0; i < values.size(); ++i) { if (i) out << ','; out << values[i]; }
    out << ']';
}
static void eventJson(std::ostream &out, const MellowRT::OpenCLExecution &event) {
    out << std::boolalpha << "{\"epoch\":" << event.epoch << ",\"sequence\":" << event.sequence
        << ",\"gpu_start\":" << event.gpuStart << ",\"gpu_end\":" << event.gpuEnd
        << ",\"submitted\":" << event.submitted << ",\"submission_attempted\":" << event.submissionAttempted
        << ",\"execution_completed\":" << event.executionCompleted << ",\"runtime_planned\":" << event.runtimePlanned
        << ",\"event_ownership_verified\":" << event.eventOwnershipVerified
        << ",\"profiling_verified\":" << event.profilingVerified << ",\"resources_released\":" << event.resourcesReleased
        << ",\"results_verified\":" << event.resultsVerified
        << ",\"runtime_completion_accepted\":" << event.runtimeCompletionAccepted << '}';
}
static void encode(const std::shared_ptr<CommandBuffer> &command, const std::shared_ptr<ComputePipeline> &pipeline,
                   const std::shared_ptr<Buffer> &buffer) {
    Error error;
    auto encoder = command->computeCommandEncoder(error);
    check(bool(encoder), error.message);
    check(encoder->setComputePipeline(pipeline, error), error.message);
    check(encoder->setBuffer(buffer, 0, error), error.message);
    check(encoder->dispatchThreads(buffer->elementCount(), error), error.message);
    check(encoder->endEncoding(error), error.message);
}
static const char Source[] = R"MSL(#include <metal_stdlib>
using namespace metal;
kernel void mellow_objects(device uint *values [[buffer(0)]], uint tid [[thread_position_in_grid]]) {
    uint original = values[tid];
    values[tid] = original * 7u + 3u;
}
)MSL";

int main(int argc, char **argv) {
    bool compute = false;
    std::string reportPath, airPath, bitcodePath, llvmLibrary, entry = "mellow_objects";
    uint32_t seed = 1;
    unsigned iterations = 1000, verified = 0;
    std::ostringstream evidence;
    bool passed = false;
    try {
        for (int i = 1; i < argc; ++i) {
            const std::string arg(argv[i]);
            if (arg == "--compute") compute = true;
            else if (i + 1 < argc && arg == "--report") reportPath = argv[++i];
            else if (i + 1 < argc && arg == "--air-text") airPath = argv[++i];
            else if (i + 1 < argc && arg == "--air-bitcode") bitcodePath = argv[++i];
            else if (i + 1 < argc && arg == "--llvm-library") llvmLibrary = argv[++i];
            else if (i + 1 < argc && arg == "--entry") entry = argv[++i];
            else if (i + 1 < argc && arg == "--seed") seed = static_cast<uint32_t>(std::stoul(argv[++i]));
            else if (i + 1 < argc && arg == "--iterations") {
                const auto requested = std::stoul(argv[++i]);
                if (!requested || requested > 10000) throw std::runtime_error("iterations must be 1-10000");
                iterations = static_cast<unsigned>(requested);
            } else throw std::runtime_error("Unknown argument");
        }
        if (!compute || reportPath.empty()) throw std::runtime_error("Explicit --compute and --report required");
        if ((!airPath.empty() && !bitcodePath.empty()) || (!bitcodePath.empty() && llvmLibrary.empty()))
            throw std::runtime_error("Select one AIR input; bitcode requires --llvm-library");
        Error error;
        auto device = Device::createOpenCL(0, error);
        check(bool(device), error.message);
        const auto hardware = device->hardware();
        evidence << ",\"device_name\":" << quote(hardware.name) << ",\"driver\":" << quote(hardware.driver)
                 << ",\"reported_vendor_id\":" << hardware.reportedVendorId
                 << ",\"reported_device_id\":" << hardware.reportedDeviceId;
        evidence << ",\"bootstrap\":";
        eventJson(evidence, device->bootstrapEvidence());
        std::string source = Source;
        if (!airPath.empty()) {
            std::ifstream input(airPath, std::ios::binary);
            if (!input) throw std::runtime_error("AIR text fixture unavailable");
            source.assign(std::istreambuf_iterator<char>(input), {});
        }
        std::shared_ptr<Library> library;
        if (!bitcodePath.empty()) {
            std::ifstream input(bitcodePath, std::ios::binary);
            if (!input) throw std::runtime_error("AIR bitcode fixture unavailable");
            std::vector<uint8_t> bytes(std::istreambuf_iterator<char>(input), {});
            library = device->newLibraryWithAir(bytes, llvmLibrary, error);
        } else library = airPath.empty() ? device->newLibraryWithSource(source, error) : device->newLibraryWithAirText(source, error);
        check(bool(library), error.message);
        auto function = library->newFunction(entry, error);
        check(bool(function), error.message);
        check(function->reflection().buffers.size() == 1 && function->reflection().buffers[0].index == 0, "Unexpected binding reflection");
        auto pipeline = device->newComputePipeline(function, error);
        check(bool(pipeline), error.message);
        check(device->pipelineBuildCount() == 1 && pipeline->compilationSerial() == 1, "Pipeline did not compile at creation exactly once");
        evidence << ",\"source_kind\":" << quote(!bitcodePath.empty() ? "air-bitcode" : (airPath.empty() ? "msl" : "air-text"))
                 << ",\"entry\":" << quote(entry) << ",\"pipeline_build_log\":" << quote(pipeline->buildLog());
        function.reset(); library.reset();
        auto queue = device->newCommandQueue();
        auto buffer = device->newBuffer(std::vector<uint32_t>(256), error);
        check(bool(buffer), error.message);
        auto command = queue->commandBuffer();
        check(command->status() == CommandStatus::NotEnqueued, "Wrong initial command state");
        reject(!command->commit(error) && command->status() == CommandStatus::NotEnqueued, "Empty command committed");
        auto encoder = command->computeCommandEncoder(error);
        check(bool(encoder) && command->status() == CommandStatus::Encoding, "Encoding state missing");
        reject(!command->commit(error), "Commit accepted active encoder");
        reject(!encoder->dispatchThreads(256, error), "Dispatch accepted without binding/pipeline");
        check(encoder->setComputePipeline(pipeline, error), error.message);
        reject(!encoder->setBuffer(buffer, 1, error), "Unsupported buffer index accepted");
        check(encoder->setBuffer(buffer, 0, error), error.message);
        reject(!encoder->dispatchThreads(257, error), "Out-of-bounds dispatch accepted");
        check(encoder->endEncoding(error), error.message);
        reject(!encoder->dispatchThreads(256, error), "Ended encoder accepted work");
        reject(!command->commit(error), "Zero-dispatch command committed");
        auto abandoned = queue->commandBuffer();
        { auto abandonedEncoder = abandoned->computeCommandEncoder(error); check(bool(abandonedEncoder), error.message); }
        reject(abandoned->status() == CommandStatus::Error && !abandoned->waitUntilCompleted(error), "Abandoned encoder did not error");
        reject(!device->newBuffer({}, error), "Empty buffer admitted");
        reject(!buffer->write(std::vector<uint32_t>(255), error), "Buffer resized");
        auto invalidLibrary = device->newLibraryWithSource("kernel void bad(device float *x [[buffer(0)]], uint i [[thread_position_in_grid]]) { x[i] = 1.0; }", error);
        reject(bool(invalidLibrary) && !invalidLibrary->newFunction("bad", error), "Unsupported shader admitted");
        auto rawAir = device->newLibraryWithAir({0x42,0x43,0xC0,0xDE}, error);
        reject(bool(rawAir) && !rawAir->newFunction("bad", error), "Raw AIR magic treated as valid shader");
        auto second = Device::createOpenCL(0, error);
        check(bool(second), error.message);
        auto foreignBuffer = second->newBuffer(std::vector<uint32_t>(256), error);
        auto foreignCommand = queue->commandBuffer();
        auto foreignEncoder = foreignCommand->computeCommandEncoder(error);
        reject(!foreignEncoder->setBuffer(foreignBuffer, 0, error) && error.code == ErrorCode::WrongDevice, "Cross-device buffer admitted");
        check(foreignEncoder->endEncoding(error), error.message);
        foreignEncoder.reset(); foreignCommand.reset(); foreignBuffer.reset(); second.reset();

        OpenCLTestSha256 inputHash, expectedHash, readbackHash;
        uint64_t firstSequence = 0, lastSequence = 0, epoch = 0, lastGpuEnd = 0;
        const auto started = std::chrono::steady_clock::now();
        std::ostringstream samples;
        samples << '[';
        for (unsigned iteration = 0; iteration < iterations; ++iteration) {
            std::vector<uint32_t> input(256), expected(256);
            for (size_t i = 0; i < input.size(); ++i) {
                input[i] = (seed ^ static_cast<uint32_t>((i + iteration * 263) * 0x9E3779B9ULL)) & 0xFFFF;
                expected[i] = input[i] * 7 + 3;
            }
            check(buffer->write(input, error), error.message);
            auto work = queue->commandBuffer();
            encode(work, pipeline, buffer);
            check(work->status() == CommandStatus::Executable, "Command not executable after endEncoding");
            check(work->commit(error), error.message);
            check(work->status() == CommandStatus::Completed && work->waitUntilCompleted(error), "Command completion missing");
            check(!work->commit(error) && work->status() == CommandStatus::Completed, "Command submitted twice");
            const auto actual = buffer->read();
            check(actual == expected, "Independent reference does not match GPU buffer");
            check(work->executions().size() == 1, "Unexpected dispatch count");
            const auto &event = work->executions().front();
            check(event.submitted && event.submissionAttempted && event.executionCompleted && event.runtimePlanned &&
                  event.eventOwnershipVerified && event.profilingVerified && event.resourcesReleased,
                  "Normal runtime event correlation/cleanup incomplete");
            check(!event.resultsVerified && !event.runtimeCompletionAccepted, "No-oracle runtime falsely claimed arithmetic evidence");
            check(event.gpuStart > 0 && event.gpuEnd > event.gpuStart && event.gpuStart >= lastGpuEnd, "GPU timestamp order invalid");
            if (iteration == 0) { firstSequence = event.sequence; epoch = event.epoch; }
            check(event.epoch == epoch && event.sequence == firstSequence + iteration, "Session sequence/epoch mismatch");
            lastSequence = event.sequence; lastGpuEnd = event.gpuEnd;
            if (iteration == 0 || iteration == iterations - 1) {
                if (iteration) samples << ',';
                samples << "{\"iteration\":" << iteration << ",\"event\":";
                eventJson(samples, event);
                samples << ",\"input\":"; words(samples, input);
                samples << ",\"output\":"; words(samples, actual);
                samples << '}';
            }
            inputHash.words(input); expectedHash.words(expected); readbackHash.words(actual);
            ++verified;
        }
        samples << ']';
        check(device->pipelineBuildCount() == 1, "Pipeline rebuilt during repeated submissions");
        std::vector<uint32_t> twiceInput(256, 2), twiceExpected(256, (2 * 7 + 3) * 7 + 3);
        check(buffer->write(twiceInput, error), error.message);
        auto ordered = queue->commandBuffer();
        encode(ordered, pipeline, buffer); encode(ordered, pipeline, buffer);
        std::weak_ptr<ComputePipeline> retained = pipeline;
        pipeline.reset();
        check(!retained.expired(), "Command did not retain pipeline");
        check(ordered->commit(error) && ordered->executions().size() == 2, error.message);
        check(buffer->read() == twiceExpected, "Cross-encoder buffer ordering failed");
        for (size_t i = 0; i < ordered->executions().size(); ++i) {
            const auto &event = ordered->executions()[i];
            check(event.executionCompleted && event.runtimePlanned && event.eventOwnershipVerified && event.profilingVerified &&
                  event.resourcesReleased && event.submitted && event.submissionAttempted, "Ordered dispatch completion incomplete");
            check(!event.resultsVerified && !event.runtimeCompletionAccepted, "Ordered dispatch fabricated oracle evidence");
            check(event.epoch == epoch && event.sequence == lastSequence + i + 1 &&
                  event.gpuStart >= lastGpuEnd && event.gpuEnd > event.gpuStart, "Ordered dispatch epoch/sequence/profiling invalid");
            lastGpuEnd = event.gpuEnd;
        }
        const auto elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
        evidence << ",\"seed\":" << seed << ",\"verified_iterations\":" << verified
                 << ",\"pipeline_build_count\":" << device->pipelineBuildCount()
                 << ",\"first_sequence\":" << firstSequence << ",\"last_sequence\":" << lastSequence << ",\"epoch\":" << epoch
                 << ",\"input_stream_sha256\":" << quote(inputHash.hex())
                 << ",\"expected_stream_sha256\":" << quote(expectedHash.hex())
                 << ",\"readback_stream_sha256\":" << quote(readbackHash.hex())
                 << ",\"ordered_two_encoder_result_verified\":true,\"elapsed_seconds\":" << elapsed
                 << ",\"runtime_requires_expected_answer\":false,\"native_driver_pipeline_compiled_once\":true"
                 << ",\"negative_checks\":" << negativeChecks << ",\"all_dispatches_correlated\":true"
                 << ",\"all_dispatches_no_oracle\":true,\"samples\":" << samples.str() << ",\"ordered_events\":[";
        eventJson(evidence, ordered->executions()[0]); evidence << ',';
        eventJson(evidence, ordered->executions()[1]); evidence << ']';
        passed = verified == iterations;
    } catch (const std::exception &failure) { evidence << ",\"error\":" << quote(failure.what()); }
    if (reportPath.empty()) return 2;
    std::ofstream report(reportPath, std::ios::binary);
    report << "{\"schema_version\":1,\"passed\":" << (passed ? "true" : "false")
           << ",\"requested_iterations\":" << iterations << ",\"checks\":" << checks
           << ",\"portable_mellow_object_api\":true,\"apple_metal_abi_registered\":false,\"macos_tested\":false,"
              "\"system_mtl_device_registered\":false,\"physical_pci_identity_verified\":false"
           << evidence.str() << "}\n";
    report.close();
    if (!report) return 1;
    std::cout << (passed ? "PASS" : "FAIL") << ": portable Mellow objects -> shader translation -> reusable OpenCL pipeline -> GPU\n";
    return passed ? 0 : 1;
}
