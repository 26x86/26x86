// SPDX-License-Identifier: MIT
#include "RenderObjects.hpp"
#include <algorithm>
#include <cmath>
#include <utility>

namespace MellowMTL {
namespace {
bool failRender(Error &e, ErrorCode code, const std::string &message) { e = {code, message}; return false; }
bool finite(const std::array<float, 4> &v) { for (auto f : v) if (!std::isfinite(f)) return false; return true; }
}
RenderDevice::RenderDevice() : provider_(std::make_shared<MellowRT::OpenGLProvider>()) {}
std::shared_ptr<RenderDevice> RenderDevice::createOpenGL(Error &e, bool visible, uint32_t width, uint32_t height) {
    e = {}; auto d = std::shared_ptr<RenderDevice>(new RenderDevice()); std::string message;
    if (!d->provider_->initialize(message, visible, width, height)) { failRender(e, ErrorCode::Execution, message); return {}; }
    return d;
}
std::shared_ptr<RenderTexture> RenderDevice::newTexture(uint32_t width, uint32_t height, Error &e) {
    e = {};
    if (!width || !height || width > MellowRT::OpenGLProvider::MaxDimension || height > MellowRT::OpenGLProvider::MaxDimension) {
        failRender(e, ErrorCode::InvalidArgument, "RGBA8 texture dimensions must be 1-2048"); return {};
    }
    return std::shared_ptr<RenderTexture>(new RenderTexture(shared_from_this(), width, height));
}
std::shared_ptr<RenderLibrary> RenderDevice::newLibraryWithSource(const std::string &source, Error &e) {
    e = {};
    if (source.empty() || source.size() > MellowRT::RenderShaderJit::MaxSourceBytes) { failRender(e, ErrorCode::InvalidArgument, "Render source must contain 1-65536 bytes"); return {}; }
    return std::shared_ptr<RenderLibrary>(new RenderLibrary(shared_from_this(), source));
}
std::shared_ptr<RenderPipeline> RenderDevice::newRenderPipeline(const std::shared_ptr<RenderFunction> &v,
                                                              const std::shared_ptr<RenderFunction> &f, Error &e) {
    e = {};
    if (!v || !f) { failRender(e, ErrorCode::InvalidArgument, "Both shader functions are required"); return {}; }
    if (v->device_.get() != this || f->device_.get() != this) { failRender(e, ErrorCode::WrongDevice, "Functions belong to a different device"); return {}; }
    if (v->stage() != MellowRT::RenderShaderJit::Stage::Vertex || f->stage() != MellowRT::RenderShaderJit::Stage::Fragment) {
        failRender(e, ErrorCode::InvalidArgument, "Vertex/fragment stage mismatch"); return {};
    }
    std::lock_guard<std::mutex> guard(submissionMutex_); std::string message;
    auto program = provider_->compile(v->compiled_.glslSource, f->compiled_.glslSource, message);
    if (!program) { failRender(e, ErrorCode::Compilation, message); return {}; }
    return std::shared_ptr<RenderPipeline>(new RenderPipeline(shared_from_this(), v, f, program));
}
std::shared_ptr<RenderCommandQueue> RenderDevice::newCommandQueue() { return std::shared_ptr<RenderCommandQueue>(new RenderCommandQueue(shared_from_this())); }
MellowRT::OpenGLDeviceInfo RenderDevice::hardware() const { return provider_->deviceInfo(); }
uint64_t RenderDevice::pipelineBuildCount() const { return provider_->pipelineBuildCount(); }
RenderTexture::RenderTexture(std::shared_ptr<RenderDevice> d, uint32_t w, uint32_t h) : device_(std::move(d)), width_(w), height_(h) {}
std::vector<uint8_t> RenderTexture::read(Error &e) const {
    e = {}; std::lock_guard<std::mutex> lock(mutex_);
    if (!sequence_) { failRender(e, ErrorCode::InvalidState, "Texture has no completed GPU content"); return {}; }
    return rgba_;
}
uint64_t RenderTexture::contentSequence() const { std::lock_guard<std::mutex> lock(mutex_); return sequence_; }
RenderLibrary::RenderLibrary(std::shared_ptr<RenderDevice> d, std::string s) : device_(std::move(d)), source_(std::move(s)) {}
std::shared_ptr<RenderFunction> RenderLibrary::newFunction(const std::string &entry, MellowRT::RenderShaderJit::Stage stage, Error &e) {
    e = {}; auto compiled = MellowRT::RenderShaderJit::compileMsl(source_, entry, stage);
    if (!compiled.success) { failRender(e, ErrorCode::Compilation, compiled.diagnostics.empty() ? "Render translation failed" : compiled.diagnostics.front()); return {}; }
    return std::shared_ptr<RenderFunction>(new RenderFunction(device_, shared_from_this(), std::move(compiled)));
}
RenderFunction::RenderFunction(std::shared_ptr<RenderDevice> d, std::shared_ptr<RenderLibrary> l, MellowRT::RenderShaderJit::CompileResult c)
    : device_(std::move(d)), library_(std::move(l)), compiled_(std::move(c)) {}
RenderPipeline::RenderPipeline(std::shared_ptr<RenderDevice> d, std::shared_ptr<RenderFunction> v,
                               std::shared_ptr<RenderFunction> f, std::shared_ptr<MellowRT::OpenGLPipeline> p)
    : device_(std::move(d)), vertex_(std::move(v)), fragment_(std::move(f)), compiled_(std::move(p)) {}
uint64_t RenderPipeline::compilationSerial() const { return compiled_->compilationSerial(); }
const std::string &RenderPipeline::buildLog() const { return compiled_->buildLog(); }
RenderCommandQueue::RenderCommandQueue(std::shared_ptr<RenderDevice> d) : device_(std::move(d)) {}
std::shared_ptr<RenderCommandBuffer> RenderCommandQueue::commandBuffer() { return std::shared_ptr<RenderCommandBuffer>(new RenderCommandBuffer(device_)); }
RenderCommandBuffer::RenderCommandBuffer(std::shared_ptr<RenderDevice> d) : device_(std::move(d)) {}
std::shared_ptr<RenderEncoder> RenderCommandBuffer::renderCommandEncoder(const RenderPassDescriptor &p, Error &e) {
    e = {};
    if (status_ != CommandStatus::NotEnqueued && status_ != CommandStatus::Executable) { failRender(e, ErrorCode::InvalidState, "Command buffer cannot begin another encoder"); return {}; }
    if (!p.colorTexture || !finite(p.clearColor)) { failRender(e, ErrorCode::InvalidArgument, "A texture and finite clear color are required"); return {}; }
    if (p.colorTexture->device_ != device_) { failRender(e, ErrorCode::WrongDevice, "Render texture belongs to a different device"); return {}; }
    if (!draws_.empty() && draws_.back().present) { failRender(e, ErrorCode::InvalidState, "Presentation must be the final pass"); return {}; }
    status_ = CommandStatus::Encoding;
    return std::shared_ptr<RenderEncoder>(new RenderEncoder(shared_from_this(), p));
}
bool RenderCommandBuffer::present(Error &e) {
    e = {};
    if (status_ != CommandStatus::Executable || draws_.empty() || draws_.back().present)
        return failRender(e, ErrorCode::InvalidState, "Presentation needs a completed final encoder and can be requested once");
    draws_.back().present = true; return true;
}
bool RenderCommandBuffer::commit(Error &e) {
    e = {};
    if (status_ != CommandStatus::Executable || draws_.empty()) return failRender(e, ErrorCode::InvalidState, "End a nonempty render encoder before commit");
    status_ = CommandStatus::Committed;
    std::lock_guard<std::mutex> submit(device_->submissionMutex_);
    for (const auto &draw : draws_) {
        auto texture = draw.pass.colorTexture;
        std::lock_guard<std::mutex> lock(texture->mutex_);
        MellowRT::OpenGLRenderOptions options;
        options.width = texture->width_; options.height = texture->height_;
        options.present = draw.present; options.params = draw.params; options.clearColor = draw.pass.clearColor;
        MellowRT::OpenGLFrame frame;
        const bool ok = device_->provider_->render(draw.pipeline->compiled_, options, frame);
        const size_t stride = static_cast<size_t>(texture->width_) * 4;
        if (!ok || !frame.renderSubmitted || !frame.fenceSignaled || !frame.readbackCompleted || !frame.resourcesReleased ||
            !frame.epoch || !frame.sequence || frame.width != texture->width_ || frame.height != texture->height_ ||
            frame.rgba.size() != stride * texture->height_ || (draw.present && !frame.swapCompleted)) {
            status_ = CommandStatus::Error; failure_ = {ErrorCode::Execution, frame.error.empty() ? "Render completion contract failed" : frame.error};
            e = failure_; frame.rgba.clear(); executions_.push_back(std::move(frame)); return false;
        }
        std::vector<uint8_t> topLeft(frame.rgba.size());
        for (size_t y = 0; y < texture->height_; ++y)
            std::copy_n(frame.rgba.data() + (texture->height_ - 1 - y) * stride, stride, topLeft.data() + y * stride);
        texture->rgba_ = std::move(topLeft); texture->sequence_ = frame.sequence;
        // The texture owns the sole retained readback; telemetry does not duplicate
        // up to 16 MiB for each pass in a long-lived command buffer.
        frame.rgba.clear(); frame.rgba.shrink_to_fit(); executions_.push_back(std::move(frame));
    }
    status_ = CommandStatus::Completed; return true;
}
bool RenderCommandBuffer::waitUntilCompleted(Error &e) const {
    e = {}; if (status_ == CommandStatus::Completed) return true;
    if (status_ == CommandStatus::Error) { e = failure_; return false; }
    return failRender(e, ErrorCode::InvalidState, "Synchronous command buffer has not completed");
}
RenderEncoder::RenderEncoder(std::shared_ptr<RenderCommandBuffer> c, RenderPassDescriptor p) : command_(std::move(c)), pass_(std::move(p)) {}
RenderEncoder::~RenderEncoder() {
    if (!ended_ && command_->status_ == CommandStatus::Encoding) { command_->status_ = CommandStatus::Error; command_->failure_ = {ErrorCode::InvalidState, "Render encoder was abandoned"}; }
}
bool RenderEncoder::active(Error &e) const { return (!ended_ && command_->status_ == CommandStatus::Encoding) || failRender(e, ErrorCode::InvalidState, "Render encoder is not active"); }
bool RenderEncoder::setRenderPipeline(const std::shared_ptr<RenderPipeline> &p, Error &e) {
    e = {}; if (!active(e)) return false;
    if (!p) return failRender(e, ErrorCode::InvalidArgument, "Render pipeline is null");
    if (p->device_ != command_->device_) return failRender(e, ErrorCode::WrongDevice, "Render pipeline belongs to a different device");
    pipeline_ = p; return true;
}
bool RenderEncoder::setSharedParameters(const std::array<float, 4> &p, Error &e) {
    e = {}; if (!active(e)) return false;
    if (!finite(p)) return failRender(e, ErrorCode::InvalidArgument, "Parameters must be finite");
    params_ = p; return true;
}
bool RenderEncoder::drawPrimitives(PrimitiveType primitive, uint32_t first, uint32_t count, Error &e) {
    e = {}; if (!active(e)) return false;
    if (!pipeline_) return failRender(e, ErrorCode::InvalidState, "Set a pipeline before drawing");
    if (primitive != PrimitiveType::Triangle || first || count != 3) return failRender(e, ErrorCode::Unsupported, "Only triangle vertexStart=0, vertexCount=3 is admitted");
    if (drew_ || command_->draws_.size() >= 16) return failRender(e, ErrorCode::Unsupported, "One draw per clearing pass, at most 16 passes per command buffer");
    command_->draws_.push_back({pipeline_, pass_, params_, false}); drew_ = true; return true;
}
bool RenderEncoder::endEncoding(Error &e) {
    e = {}; if (!active(e)) return false;
    if (!drew_) return failRender(e, ErrorCode::InvalidState, "Render pass has no draw");
    ended_ = true; command_->status_ = CommandStatus::Executable; return true;
}
}
