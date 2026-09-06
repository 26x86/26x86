// SPDX-License-Identifier: MIT
#pragma once
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

namespace MellowRT {
struct OpenGLDeviceInfo {
    std::string vendor, renderer, version, shadingLanguageVersion;
    int major {}, minor {}, pixelFormat {};
    bool acceleratedPixelFormat {}, softwareRendererRejected {}, coreProfile {};
    bool visibleWindow {};
    // WGL driver strings do not establish physical PCI ownership.
    bool physicalPciIdentityVerified {};
};
struct OpenGLRenderOptions {
    uint32_t width {256}, height {256};
    bool present {};
    std::array<float, 4> clearColor {0.f, 0.f, 0.f, 0.f};
    // Optional GLSL uniform vec4 mellow_params; an optimized-out uniform is fine.
    std::array<float, 4> params {0.f, 0.f, 0.f, 0.f};
};
struct OpenGLFrame {
    uint32_t width {}, height {};
    uint64_t epoch {}, sequence {};
    bool renderSubmitted {}, fenceSignaled {}, readbackCompleted {}, resourcesReleased {};
    bool swapCompleted {}, displayScanoutVerified {};
    bool swapIntervalKnown {};
    int swapInterval {};
    std::vector<uint8_t> rgba; // RGBA8, tightly packed; row zero is bottom-left.
    std::string error;
};
class OpenGLProvider;
class OpenGLPipeline {
public:
    ~OpenGLPipeline();
    OpenGLPipeline(const OpenGLPipeline &) = delete;
    OpenGLPipeline &operator=(const OpenGLPipeline &) = delete;
    uint64_t compilationSerial() const;
    const std::string &buildLog() const;
private:
    friend class OpenGLProvider;
    OpenGLPipeline();
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

// Actual Windows WGL render substrate, not an Apple Metal/WindowServer driver.
// A private thread owns the isolated window/context and serializes all GL calls.
// No ambient GL context is changed. Other operating systems fail explicitly.
// Driver calls may block; applications must use an externally timed worker.
class OpenGLProvider {
public:
    OpenGLProvider();
    ~OpenGLProvider();
    OpenGLProvider(const OpenGLProvider &) = delete;
    OpenGLProvider &operator=(const OpenGLProvider &) = delete;
    bool initialize(std::string &error, bool visible = false,
                    uint32_t windowWidth = 640, uint32_t windowHeight = 480);
    std::shared_ptr<OpenGLPipeline> compile(const std::string &vertexGlsl,
                                           const std::string &fragmentGlsl, std::string &error);
    bool render(const std::shared_ptr<OpenGLPipeline> &, const OpenGLRenderOptions &, OpenGLFrame &);
    OpenGLDeviceInfo deviceInfo() const;
    uint64_t pipelineBuildCount() const;
    void invalidateSession(); // Context lifetime invalidation, not a physical GPU reset.
    static constexpr uint32_t MaxDimension = 2048;
    static constexpr size_t MaxSourceBytes = 65536;
private:
    friend class OpenGLPipeline;
    struct Impl;
    std::shared_ptr<Impl> impl_;
};
}
