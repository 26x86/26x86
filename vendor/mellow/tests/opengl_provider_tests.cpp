// Actual driver acceptance; no mock GL entry points and no software fallback.
#include "../Runtime/OpenGLProvider.hpp"
#include "opencl_runtime_sha256.hpp"
#include <cmath>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <thread>
#include <chrono>
using namespace MellowRT;
static unsigned checks {}, negativeChecks {};
static void check(bool condition, const std::string &message) {
    ++checks; if (!condition) throw std::runtime_error(message);
}
static void reject(bool condition, const std::string &message) { ++negativeChecks; check(condition, message); }
static std::string quote(const std::string &text) {
    std::ostringstream out; out << '"';
    const char *hex = "0123456789abcdef";
    for (unsigned char c : text) {
        if (c == '"' || c == '\\') out << '\\' << c;
        else if (c < 32) out << "\\u00" << hex[c >> 4] << hex[c & 15];
        else out << c;
    }
    out << '"'; return out.str();
}
static const char Vertex[] = R"GLSL(#version 330 core
const vec2 positions[3] = vec2[3](vec2(-1.0,-1.0),vec2(3.0,-1.0),vec2(-1.0,3.0));
void main() { gl_Position=vec4(positions[gl_VertexID],0.0,1.0); }
)GLSL";
static const char Fragment[] = R"GLSL(#version 330 core
uniform vec4 mellow_params;
uniform vec2 mellow_viewport;
out vec4 color;
void main() {
    float r=gl_FragCoord.x < mellow_viewport.x*0.5 ? mellow_params.x : mellow_params.y;
    float g=gl_FragCoord.y < mellow_viewport.y*0.5 ? mellow_params.z : mellow_params.w;
    color=vec4(r,g,0.0,1.0);
}
)GLSL";
static std::vector<uint8_t> reference(uint32_t seed, unsigned iteration) {
    const auto bits = (seed ^ iteration) & 15;
    std::vector<uint8_t> bytes;
    for (unsigned y = 0; y < 48; ++y) for (unsigned x = 0; x < 64; ++x) {
        bytes.push_back(((bits >> (x < 32 ? 0 : 1)) & 1) ? 255 : 0);
        bytes.push_back(((bits >> (y < 24 ? 2 : 3)) & 1) ? 255 : 0);
        bytes.push_back(0); bytes.push_back(255);
    }
    return bytes;
}
int main(int argc, char **argv) {
    std::string reportPath;
    unsigned frames = 1000, completed = 0;
    uint32_t seed = 17;
    bool render = false, visible = false, passed = false;
    std::ostringstream evidence;
    try {
        for (int i = 1; i < argc; ++i) {
            const std::string option(argv[i]);
            if (option == "--render") render = true;
            else if (option == "--visible") visible = true;
            else if (i + 1 < argc && option == "--report") reportPath = argv[++i];
            else if (i + 1 < argc && option == "--seed") seed = static_cast<uint32_t>(std::stoul(argv[++i]));
            else if (i + 1 < argc && option == "--frames") {
                const auto count = std::stoul(argv[++i]);
                if (!count || count > 10000) throw std::runtime_error("Frames must be 1-10000");
                frames = static_cast<unsigned>(count);
            } else throw std::runtime_error("Unknown argument");
        }
        if (!render || reportPath.empty()) throw std::runtime_error("Explicit --render and --report required");
        OpenCLTestSha256 empty;
        check(empty.hex() == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "SHA empty vector failed");
        const uint8_t abc[] = {'a','b','c'}; empty.append(abc, 3);
        check(empty.hex() == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "SHA abc vector failed");
        OpenGLProvider provider;
        std::string error;
        check(provider.initialize(error, visible, 640, 480), error);
        const auto info = provider.deviceInfo();
        evidence << ",\"device\":{\"vendor\":" << quote(info.vendor) << ",\"renderer\":" << quote(info.renderer)
                 << ",\"version\":" << quote(info.version) << ",\"glsl_version\":" << quote(info.shadingLanguageVersion)
                 << ",\"major\":" << info.major << ",\"minor\":" << info.minor << ",\"pixel_format\":" << info.pixelFormat
                 << ",\"accelerated_pixel_format\":" << std::boolalpha << info.acceleratedPixelFormat
                 << ",\"software_renderer_rejected\":" << info.softwareRendererRejected
                 << ",\"core_profile\":" << info.coreProfile << '}';
        check(info.acceleratedPixelFormat && info.softwareRendererRejected && info.coreProfile, "Hardware ICD/core evidence missing");
        reject(!provider.initialize(error), "Redundant initialization accepted");
        reject(!provider.compile("invalid GLSL", Fragment, error) && !error.empty(), "Invalid GLSL accepted");
        check(provider.pipelineBuildCount() == 0, "Failed shader counted as compiled pipeline");
        auto pipeline = provider.compile(Vertex, Fragment, error);
        check(bool(pipeline), error);
        check(pipeline->compilationSerial() == 1, "Pipeline compilation serial missing");
        OpenGLRenderOptions options;
        options.width = 64; options.height = 48; options.present = visible;
        OpenGLFrame failed;
        auto bad = options; bad.width = 0;
        reject(!provider.render(pipeline, bad, failed) && !failed.renderSubmitted, "Zero size accepted");
        bad = options; bad.width = 2049;
        reject(!provider.render(pipeline, bad, failed) && !failed.renderSubmitted, "Oversized texture accepted");
        bad = options; bad.params[0] = std::numeric_limits<float>::quiet_NaN();
        reject(!provider.render(pipeline, bad, failed) && !failed.renderSubmitted, "NaN uniform accepted");
        reject(!provider.render({}, options, failed) && !failed.renderSubmitted, "Null pipeline accepted");
        {
            OpenGLProvider other;
            check(other.initialize(error), error);
            reject(!other.render(pipeline, options, failed) && !failed.renderSubmitted, "Foreign-context pipeline accepted");
            auto hidden = other.compile(Vertex, Fragment, error);
            check(bool(hidden), error);
            auto presentHidden = options; presentHidden.present = true;
            reject(!other.render(hidden, presentHidden, failed) && !failed.renderSubmitted, "Hidden presentation accepted");
        }
        OpenCLTestSha256 expectedHash, actualHash;
        uint64_t firstSequence {}, lastSequence {}, epoch {};
        std::ostringstream samples;
        samples << '[';
        const auto started = std::chrono::steady_clock::now();
        for (unsigned iteration = 0; iteration < frames; ++iteration) {
            const auto bits = (seed ^ iteration) & 15;
            for (size_t i = 0; i < 4; ++i) options.params[i] = static_cast<float>((bits >> i) & 1);
            OpenGLFrame frame;
            bool success {};
            if (iteration == 0) {
                // Public calls may originate from a different thread; the GL worker remains owner.
                std::thread caller([&] { success = provider.render(pipeline, options, frame); }); caller.join();
            } else success = provider.render(pipeline, options, frame);
            check(success, frame.error);
            check(frame.renderSubmitted && frame.fenceSignaled && frame.readbackCompleted && frame.resourcesReleased, "Incomplete frame evidence");
            check(frame.swapCompleted == visible && !frame.displayScanoutVerified, "Swap/physical scanout evidence conflated");
            check(frame.width == 64 && frame.height == 48, "Frame dimensions mismatch");
            const auto expected = reference(seed, iteration);
            check(frame.rgba == expected, "GPU RGBA8 readback differs from independent quadrant pattern");
            if (!iteration) { firstSequence = frame.sequence; epoch = frame.epoch; }
            check(frame.epoch == epoch && frame.sequence == firstSequence + iteration, "Frame epoch/sequence mismatch");
            lastSequence = frame.sequence;
            expectedHash.append(expected.data(), expected.size()); actualHash.append(frame.rgba.data(), frame.rgba.size());
            if (iteration == 0 || iteration == frames - 1) {
                if (iteration) samples << ',';
                OpenCLTestSha256 sampleHash; sampleHash.append(frame.rgba.data(), frame.rgba.size());
                samples << std::boolalpha << "{\"iteration\":" << iteration << ",\"epoch\":" << frame.epoch << ",\"sequence\":" << frame.sequence
                        << ",\"render_submitted\":" << frame.renderSubmitted << ",\"fence_signaled\":" << frame.fenceSignaled
                        << ",\"readback_completed\":" << frame.readbackCompleted << ",\"resources_released\":" << frame.resourcesReleased
                        << ",\"swap_completed\":" << frame.swapCompleted << ",\"scanout_verified\":" << frame.displayScanoutVerified
                        << ",\"swap_interval_known\":" << frame.swapIntervalKnown << ",\"swap_interval\":" << frame.swapInterval
                        << ",\"rgba_sha256\":" << quote(sampleHash.hex()) << '}';
            }
            ++completed;
        }
        samples << ']';
        check(provider.pipelineBuildCount() == 1, "Native program was rebuilt per frame");
        provider.invalidateSession();
        const auto cleared = provider.deviceInfo();
        check(cleared.vendor.empty() && cleared.renderer.empty() && !cleared.acceleratedPixelFormat &&
              !cleared.coreProfile && !cleared.visibleWindow, "Invalidated context retained live device claims");
        reject(!provider.render(pipeline, options, failed) && !failed.renderSubmitted, "Stale epoch pipeline submitted");
        reject(!provider.initialize(error, false, 0, 480) && provider.deviceInfo().renderer.empty() &&
               !provider.deviceInfo().acceleratedPixelFormat, "Failed reinitialization restored old identity");
        check(provider.initialize(error), error);
        reject(!provider.render(pipeline, options, failed) && !failed.renderSubmitted, "Old pipeline revived in a new context");
        std::shared_ptr<OpenGLPipeline> retained;
        {
            auto temporary = std::make_unique<OpenGLProvider>();
            check(temporary->initialize(error), error);
            retained = temporary->compile(Vertex, Fragment, error);
            check(bool(retained), error);
        }
        check(retained->compilationSerial() == 1, "Pipeline did not outlive provider facade");
        retained.reset(); // Owning worker cleans program/context/window on its original thread.
        const auto elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
        evidence << ",\"seed\":" << seed << ",\"frames_completed\":" << completed << ",\"pipeline_build_count\":" << provider.pipelineBuildCount()
                 << ",\"first_sequence\":" << firstSequence << ",\"last_sequence\":" << lastSequence << ",\"epoch\":" << epoch
                 << ",\"expected_stream_sha256\":" << quote(expectedHash.hex()) << ",\"readback_stream_sha256\":" << quote(actualHash.hex())
                 << ",\"samples\":" << samples.str() << ",\"all_frames_correlated\":true,\"all_rgba_patterns_verified\":true"
                 << ",\"elapsed_seconds\":" << elapsed;
        passed = completed == frames;
    } catch (const std::exception &failure) { evidence << ",\"error\":" << quote(failure.what()); }
    if (reportPath.empty()) return 2;
    std::ofstream report(reportPath, std::ios::binary);
    report << std::boolalpha << "{\"schema_version\":1,\"passed\":" << passed << ",\"requested_frames\":" << frames
           << ",\"visible_window_requested\":" << visible << ",\"checks\":" << checks << ",\"negative_checks\":" << negativeChecks
           << ",\"width\":64,\"height\":48,\"row_origin\":\"bottom-left\",\"native_macos_execution\":false,"
              "\"windowserver_acceleration_verified\":false,\"display_scanout_verified\":false,\"physical_pci_identity_verified\":false"
           << evidence.str() << "}\n";
    report.close();
    if (!report) return 1;
    std::cout << (passed ? "PASS" : "FAIL") << ": actual WGL/OpenGL triangle, fence, RGBA8 readback; visible swap requested=" << visible << '\n';
    return passed ? 0 : 1;
}
