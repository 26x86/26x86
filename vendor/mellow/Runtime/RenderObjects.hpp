// SPDX-License-Identifier: MIT
#pragma once
#include "MetalObjects.hpp"
#include "OpenGLProvider.hpp"
#include "RenderShaderJit.hpp"
#include <array>

// Explicit render objects extending the MellowMTL C++ API. These do not replace
// Metal.framework. The render device owns a GL provider; compute/GL sharing is
// not inferred, and no Apple family/WindowServer capability is advertised.
namespace MellowMTL {
class RenderDevice; class RenderTexture; class RenderLibrary; class RenderFunction;
class RenderPipeline; class RenderCommandQueue; class RenderCommandBuffer; class RenderEncoder;
enum class PrimitiveType { Triangle };
struct RenderPassDescriptor {
    std::shared_ptr<RenderTexture> colorTexture;
    std::array<float, 4> clearColor {0.f, 0.f, 0.f, 0.f};
};
class RenderDevice : public std::enable_shared_from_this<RenderDevice> {
public:
    static std::shared_ptr<RenderDevice> createOpenGL(Error &, bool visible = false,
                                                    uint32_t windowWidth = 640, uint32_t windowHeight = 480);
    std::shared_ptr<RenderTexture> newTexture(uint32_t width, uint32_t height, Error &);
    std::shared_ptr<RenderLibrary> newLibraryWithSource(const std::string &, Error &);
    std::shared_ptr<RenderPipeline> newRenderPipeline(const std::shared_ptr<RenderFunction> &vertex,
                                                     const std::shared_ptr<RenderFunction> &fragment, Error &);
    std::shared_ptr<RenderCommandQueue> newCommandQueue();
    MellowRT::OpenGLDeviceInfo hardware() const;
    uint64_t pipelineBuildCount() const;
private:
    friend class RenderCommandBuffer;
    RenderDevice();
    std::shared_ptr<MellowRT::OpenGLProvider> provider_;
    std::mutex submissionMutex_;
};
class RenderTexture {
public:
    uint32_t width() const { return width_; }
    uint32_t height() const { return height_; }
    // Explicit copied RGBA8 result, row zero is the top row. No CPU initializer
    // is accepted as GPU output; read fails before a successful rendered pass.
    std::vector<uint8_t> read(Error &) const;
    uint64_t contentSequence() const;
private:
    friend class RenderDevice; friend class RenderEncoder; friend class RenderCommandBuffer;
    RenderTexture(std::shared_ptr<RenderDevice>, uint32_t, uint32_t);
    std::shared_ptr<RenderDevice> device_;
    const uint32_t width_, height_;
    mutable std::mutex mutex_;
    std::vector<uint8_t> rgba_;
    uint64_t sequence_ {};
};
class RenderLibrary : public std::enable_shared_from_this<RenderLibrary> {
public:
    std::shared_ptr<RenderFunction> newFunction(const std::string &entry, MellowRT::RenderShaderJit::Stage, Error &);
private:
    friend class RenderDevice;
    RenderLibrary(std::shared_ptr<RenderDevice>, std::string);
    std::shared_ptr<RenderDevice> device_;
    std::string source_;
};
class RenderFunction {
public:
    const std::string &name() const { return compiled_.entry; }
    MellowRT::RenderShaderJit::Stage stage() const { return compiled_.stage; }
private:
    friend class RenderLibrary; friend class RenderDevice;
    RenderFunction(std::shared_ptr<RenderDevice>, std::shared_ptr<RenderLibrary>, MellowRT::RenderShaderJit::CompileResult);
    std::shared_ptr<RenderDevice> device_;
    std::shared_ptr<RenderLibrary> library_;
    MellowRT::RenderShaderJit::CompileResult compiled_;
};
class RenderPipeline {
public:
    uint64_t compilationSerial() const;
    const std::string &buildLog() const;
private:
    friend class RenderDevice; friend class RenderEncoder; friend class RenderCommandBuffer;
    RenderPipeline(std::shared_ptr<RenderDevice>, std::shared_ptr<RenderFunction>,
                   std::shared_ptr<RenderFunction>, std::shared_ptr<MellowRT::OpenGLPipeline>);
    std::shared_ptr<RenderDevice> device_;
    std::shared_ptr<RenderFunction> vertex_, fragment_;
    std::shared_ptr<MellowRT::OpenGLPipeline> compiled_;
};
class RenderCommandQueue {
public:
    std::shared_ptr<RenderCommandBuffer> commandBuffer();
private:
    friend class RenderDevice;
    explicit RenderCommandQueue(std::shared_ptr<RenderDevice>);
    std::shared_ptr<RenderDevice> device_;
};
class RenderCommandBuffer : public std::enable_shared_from_this<RenderCommandBuffer> {
public:
    std::shared_ptr<RenderEncoder> renderCommandEncoder(const RenderPassDescriptor &, Error &);
    bool present(Error &); // Requests a window swap of the final pass; not scanout proof.
    bool commit(Error &);  // Synchronous, driver work executes on the provider's private thread.
    bool waitUntilCompleted(Error &) const;
    CommandStatus status() const { return status_; }
    const std::vector<MellowRT::OpenGLFrame> &executions() const { return executions_; }
private:
    friend class RenderCommandQueue; friend class RenderEncoder;
    explicit RenderCommandBuffer(std::shared_ptr<RenderDevice>);
    struct Draw { std::shared_ptr<RenderPipeline> pipeline; RenderPassDescriptor pass; std::array<float, 4> params {}; bool present {}; };
    std::shared_ptr<RenderDevice> device_;
    CommandStatus status_ {CommandStatus::NotEnqueued};
    Error failure_;
    std::vector<Draw> draws_;
    std::vector<MellowRT::OpenGLFrame> executions_;
};
class RenderEncoder {
public:
    ~RenderEncoder();
    bool setRenderPipeline(const std::shared_ptr<RenderPipeline> &, Error &);
    // This subset explicitly binds the SAME float4 to buffer(0) in both stages.
    // Independent per-stage bindings are not silently treated as shared data.
    bool setSharedParameters(const std::array<float, 4> &, Error &);
    bool drawPrimitives(PrimitiveType, uint32_t vertexStart, uint32_t vertexCount, Error &);
    bool endEncoding(Error &);
private:
    friend class RenderCommandBuffer;
    RenderEncoder(std::shared_ptr<RenderCommandBuffer>, RenderPassDescriptor);
    bool active(Error &) const;
    std::shared_ptr<RenderCommandBuffer> command_;
    RenderPassDescriptor pass_;
    std::shared_ptr<RenderPipeline> pipeline_;
    std::array<float, 4> params_ {};
    bool drew_ {}, ended_ {};
};
}
