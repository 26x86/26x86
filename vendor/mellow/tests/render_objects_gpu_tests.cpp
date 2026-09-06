// Actual MSL object/driver execution only. Pixel oracle lives in the supervisor.
#include "../Runtime/RenderObjects.hpp"
#include "render_fixture.hpp"
#include "opencl_runtime_sha256.hpp"
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <chrono>
using namespace MellowMTL;
using MellowRT::RenderShaderJit::Stage;
static unsigned checks {};
static std::vector<std::string> negatives;
static void check(bool condition, const std::string &message) {
    ++checks; if (!condition) throw std::runtime_error(message);
}
static void reject(const std::string &name, bool condition) { check(condition, name); negatives.push_back(name); }
static std::string quote(const std::string &text) {
    std::ostringstream out; out << '"'; const char *hex = "0123456789abcdef";
    for (unsigned char c : text) {
        if (c == '"' || c == '\\') out << '\\' << c;
        else if (c < 32) out << "\\u00" << hex[c >> 4] << hex[c & 15];
        else out << c;
    }
    out << '"'; return out.str();
}
static void encode(const std::shared_ptr<RenderCommandBuffer> &work,
                   const std::shared_ptr<RenderPipeline> &pipeline,
                   const std::shared_ptr<RenderTexture> &texture, const std::array<float, 4> &params) {
    Error error;
    auto encoder = work->renderCommandEncoder({texture, {0,0,0,0}}, error);
    check(bool(encoder), error.message);
    check(encoder->setRenderPipeline(pipeline, error), error.message);
    check(encoder->setSharedParameters(params, error), error.message);
    check(encoder->drawPrimitives(PrimitiveType::Triangle, 0, 3, error), error.message);
    check(encoder->endEncoding(error), error.message);
}
int main(int argc, char **argv) {
    std::string reportPath, streamPath;
    unsigned requested = 1000, completed {};
    uint32_t seed = 1;
    bool render {}, visible {}, passed {};
    std::ostringstream evidence;
    OpenCLTestSha256 rawHash;
    try {
        for (int i = 1; i < argc; ++i) {
            const std::string option(argv[i]);
            if (option == "--render") render = true;
            else if (option == "--visible") visible = true;
            else if (i + 1 < argc && option == "--report") reportPath = argv[++i];
            else if (i + 1 < argc && option == "--raw") streamPath = argv[++i];
            else if (i + 1 < argc && option == "--seed") seed = static_cast<uint32_t>(std::stoul(argv[++i]));
            else if (i + 1 < argc && option == "--frames") {
                const auto count = std::stoul(argv[++i]);
                if (!count || count > 10000) throw std::runtime_error("Frame count outside 1-10000");
                requested = static_cast<unsigned>(count);
            } else throw std::runtime_error("Unknown argument");
        }
        if (!render || reportPath.empty() || streamPath.empty()) throw std::runtime_error("Explicit --render --report --raw required");
        std::ofstream raw(streamPath, std::ios::binary | std::ios::trunc);
        check(bool(raw), "Cannot open bounded RGBA stream output");
        Error error;
        auto device = RenderDevice::createOpenGL(error, visible, 640, 480);
        check(bool(device), error.message);
        const auto info = device->hardware();
        evidence << std::boolalpha << ",\"device\":{\"vendor\":" << quote(info.vendor) << ",\"renderer\":" << quote(info.renderer)
                 << ",\"version\":" << quote(info.version) << ",\"glsl_version\":" << quote(info.shadingLanguageVersion)
                 << ",\"major\":" << info.major << ",\"minor\":" << info.minor << ",\"pixel_format\":" << info.pixelFormat
                 << ",\"accelerated_pixel_format\":" << info.acceleratedPixelFormat << ",\"core_profile\":" << info.coreProfile
                 << ",\"software_renderer_rejected\":" << info.softwareRendererRejected << '}';
        auto texture = device->newTexture(64, 48, error);
        check(bool(texture), error.message);
        reject("read_before_gpu", texture->read(error).empty() && error.code == ErrorCode::InvalidState && texture->contentSequence() == 0);
        reject("zero_texture", !device->newTexture(0, 48, error));
        auto library = device->newLibraryWithSource(MellowRenderFixture, error);
        check(bool(library), error.message);
        auto vertex = library->newFunction("triangleVertex", Stage::Vertex, error);
        check(bool(vertex), error.message);
        auto fragment = library->newFunction("gradientFragment", Stage::Fragment, error);
        check(bool(fragment), error.message);
        reject("wrong_function_stage", !library->newFunction("gradientFragment", Stage::Vertex, error));
        reject("null_function", !device->newRenderPipeline({}, fragment, error));
        reject("swapped_stages", !device->newRenderPipeline(fragment, vertex, error));
        auto pipeline = device->newRenderPipeline(vertex, fragment, error);
        check(bool(pipeline), error.message);
        check(pipeline->compilationSerial() == 1 && device->pipelineBuildCount() == 1, "Native render program not compiled once");
        std::weak_ptr<RenderLibrary> weakLibrary = library;
        std::weak_ptr<RenderFunction> weakVertex = vertex, weakFragment = fragment;
        library.reset(); vertex.reset(); fragment.reset();
        check(!weakLibrary.expired() && !weakVertex.expired() && !weakFragment.expired(), "Pipeline failed to retain functions/library");
        auto queue = device->newCommandQueue();
        auto control = queue->commandBuffer();
        reject("empty_commit", !control->commit(error));
        reject("present_before_encoding", !control->present(error));
        reject("wait_before_completion", !control->waitUntilCompleted(error));
        reject("null_attachment", !control->renderCommandEncoder({}, error));
        RenderPassDescriptor invalidPass {texture, {0,0,0, std::numeric_limits<float>::quiet_NaN()}};
        reject("nonfinite_clear", !control->renderCommandEncoder(invalidPass, error));
        {
            auto abandoned = queue->commandBuffer();
            { auto e = abandoned->renderCommandEncoder({texture, {0,0,0,0}}, error); check(bool(e), error.message); }
            reject("abandoned_encoder", abandoned->status() == CommandStatus::Error && !abandoned->commit(error));
        }
        auto encoder = control->renderCommandEncoder({texture, {0,0,0,0}}, error);
        check(bool(encoder), error.message);
        reject("commit_active_encoder", !control->commit(error));
        reject("draw_without_pipeline", !encoder->drawPrimitives(PrimitiveType::Triangle, 0, 3, error));
        reject("null_pipeline", !encoder->setRenderPipeline({}, error));
        reject("end_empty_encoder", !encoder->endEncoding(error));
        check(encoder->setRenderPipeline(pipeline, error), error.message);
        reject("nonfinite_parameters", !encoder->setSharedParameters({0,0,0,std::numeric_limits<float>::infinity()}, error));
        reject("unsupported_primitive", !encoder->drawPrimitives(static_cast<PrimitiveType>(99), 0, 3, error));
        reject("unsafe_vertex_start", !encoder->drawPrimitives(PrimitiveType::Triangle, 1, 3, error));
        reject("unsafe_vertex_count", !encoder->drawPrimitives(PrimitiveType::Triangle, 0, 4, error));
        {
            auto other = RenderDevice::createOpenGL(error);
            check(bool(other), error.message);
            auto otherTexture = other->newTexture(64, 48, error);
            auto foreignWork = queue->commandBuffer();
            reject("foreign_texture", !foreignWork->renderCommandEncoder({otherTexture, {0,0,0,0}}, error));
            auto otherLibrary = other->newLibraryWithSource(MellowRenderFixture, error);
            auto otherVertex = otherLibrary->newFunction("triangleVertex", Stage::Vertex, error);
            auto otherFragment = otherLibrary->newFunction("gradientFragment", Stage::Fragment, error);
            check(bool(otherVertex) && bool(otherFragment), error.message);
            reject("foreign_function", !device->newRenderPipeline(otherVertex, otherFragment, error));
            auto otherPipeline = other->newRenderPipeline(otherVertex, otherFragment, error);
            check(bool(otherPipeline), error.message);
            reject("foreign_pipeline", !encoder->setRenderPipeline(otherPipeline, error));
        }
        check(encoder->drawPrimitives(PrimitiveType::Triangle, 0, 3, error), error.message);
        reject("second_draw_in_pass", !encoder->drawPrimitives(PrimitiveType::Triangle, 0, 3, error));
        check(encoder->endEncoding(error), error.message);
        reject("duplicate_end_encoding", !encoder->endEncoding(error));
        reject("ended_encoder_mutation", !encoder->setSharedParameters({0,0,0,0}, error));
        check(control->present(error), error.message);
        reject("duplicate_present", !control->present(error));
        reject("pass_after_present", !control->renderCommandEncoder({texture, {0,0,0,0}}, error));
        encoder.reset(); control.reset(); // Unsubmitted control work produces no GPU result.
        check(texture->contentSequence() == 0, "Encoding alone marked texture content as GPU completed");
        uint64_t firstSequence {}, lastSequence {}, epoch {};
        std::weak_ptr<RenderPipeline> retained;
        std::ostringstream samples; samples << '[';
        const auto start = std::chrono::steady_clock::now();
        for (unsigned i = 0; i < requested; ++i) {
            const uint32_t r = seed + static_cast<uint32_t>(i * 0x9e3779b9u);
            const std::array<float, 4> params {
                (static_cast<int>(r & 15u) - 7) * .005f,
                (static_cast<int>((r >> 4) & 15u) - 7) * .005f,
                static_cast<float>((r >> 8) & 255u) / 255.f,
                1.f / 64.f};
            auto work = queue->commandBuffer();
            encode(work, pipeline, texture, params);
            check(work->status() == CommandStatus::Executable, "Render buffer not executable after encoding");
            if (visible) check(work->present(error), error.message);
            if (i == requested - 1) {
                retained = pipeline; pipeline.reset();
                check(!retained.expired(), "Encoded command did not retain its pipeline");
            }
            check(work->commit(error), error.message);
            check(work->status() == CommandStatus::Completed && work->waitUntilCompleted(error), "Render completion state incorrect");
            check(!work->commit(error) && work->status() == CommandStatus::Completed, "Repeated render commit admitted");
            check(work->executions().size() == 1, "Unexpected render pass count");
            const auto &frame = work->executions().front();
            check(frame.renderSubmitted && frame.fenceSignaled && frame.readbackCompleted && frame.resourcesReleased, "Incomplete native frame correlation");
            check(frame.swapCompleted == visible && !frame.displayScanoutVerified, "Swap acceptance confused with physical scanout");
            check(frame.rgba.empty(), "Telemetry unexpectedly duplicated the texture readback");
            if (!i) { firstSequence = frame.sequence; epoch = frame.epoch; }
            check(frame.epoch == epoch && frame.sequence == firstSequence + i && texture->contentSequence() == frame.sequence,
                  "Texture/frame epoch or sequence mismatch");
            const auto rgba = texture->read(error);
            check(error.code == ErrorCode::None && rgba.size() == 64 * 48 * 4, "Texture readback invalid");
            raw.write(reinterpret_cast<const char *>(rgba.data()), static_cast<std::streamsize>(rgba.size()));
            check(bool(raw), "Actual RGBA stream write failed");
            rawHash.append(rgba.data(), rgba.size());
            lastSequence = frame.sequence;
            if (!i || i == requested - 1) {
                if (i) samples << ',';
                OpenCLTestSha256 sampleHash; sampleHash.append(rgba.data(), rgba.size());
                samples << std::boolalpha << "{\"iteration\":" << i << ",\"epoch\":" << frame.epoch << ",\"sequence\":" << frame.sequence
                        << ",\"texture_sequence\":" << texture->contentSequence() << ",\"render_submitted\":" << frame.renderSubmitted
                        << ",\"fence_signaled\":" << frame.fenceSignaled << ",\"readback_completed\":" << frame.readbackCompleted
                        << ",\"resources_released\":" << frame.resourcesReleased << ",\"swap_completed\":" << frame.swapCompleted
                        << ",\"scanout_verified\":" << frame.displayScanoutVerified << ",\"rgba_sha256\":" << quote(sampleHash.hex()) << '}';
            }
            ++completed;
        }
        samples << ']';
        raw.close(); check(bool(raw), "RGBA stream finalization failed");
        check(device->pipelineBuildCount() == 1, "Driver program recompiled during repeated frames");
        check(retained.expired(), "Finished command unexpectedly retained pipeline after owner release");
        const auto elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
        evidence << ",\"first_sequence\":" << firstSequence << ",\"last_sequence\":" << lastSequence << ",\"epoch\":" << epoch
                 << ",\"pipeline_build_count\":" << device->pipelineBuildCount() << ",\"samples\":" << samples.str()
                 << ",\"all_frame_completions_correlated\":true,\"runtime_received_pixel_oracle\":false"
                 << ",\"msl_stages_translated\":2,\"native_program_compilations\":1,\"elapsed_seconds\":" << elapsed;
        passed = completed == requested;
    } catch (const std::exception &failure) { evidence << ",\"error\":" << quote(failure.what()); }
    if (reportPath.empty()) return 2;
    std::ofstream report(reportPath, std::ios::binary);
    report << std::boolalpha << "{\"schema_version\":1,\"passed\":" << passed << ",\"seed\":" << seed
           << ",\"requested_frames\":" << requested << ",\"frames_completed\":" << completed
           << ",\"visible_requested\":" << visible << ",\"checks\":" << checks << ",\"negative_checks\":[";
    for (size_t i = 0; i < negatives.size(); ++i) { if (i) report << ','; report << quote(negatives[i]); }
    report << "],\"raw_stream_sha256\":" << quote(rawHash.hex()) << ",\"width\":64,\"height\":48,\"row_origin\":\"top-left\","
              "\"portable_mellow_object_api\":true,\"apple_metal_abi_registered\":false,\"native_macos_execution\":false,"
              "\"windowserver_acceleration_verified\":false,\"display_scanout_verified\":false"
           << evidence.str() << "}\n";
    report.close();
    if (!report) return 1;
    std::cout << (passed ? "PASS" : "FAIL") << ": MSL render objects -> native OpenGL program -> GPU RGBA stream (CPU pixel oracle runs separately)\n";
    return passed ? 0 : 1;
}
