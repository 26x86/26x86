// SPDX-License-Identifier: MIT
// Explicit Mellow render client. Requires an existing Windows accelerated GL
// driver. No Apple Metal registration or native macOS driver is installed.
#include "../Runtime/RenderObjects.hpp"
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <thread>

static const char *source = R"MSL(
#include <metal_stdlib>
using namespace metal;
vertex float4 vertexMain(uint id [[vertex_id]], constant float4& p [[buffer(0)]]) {
    const float2 positions[3] = {float2(-0.72, -0.52), float2(0.58, -0.32), float2(-0.18, 0.72)};
    return float4(positions[id] + p.xy, 0.5, 1.0);
}
fragment float4 fragmentMain(float4 position [[position]], constant float4& p [[buffer(0)]]) {
    return float4(position.x * p.w, position.y * p.w, p.z, 1.0);
}
)MSL";
int main(int argc, char **argv) {
    if (argc < 2 || argc > 3 || (argc == 3 && std::string(argv[2]) != "--visible")) {
        std::cerr << "Usage: render-msl output.ppm [--visible]\n"; return 2;
    }
    MellowMTL::Error error;
    const auto fail = [&]() { std::cerr << error.message << '\n'; return 1; };
    const bool visible = argc == 3;
    auto device = MellowMTL::RenderDevice::createOpenGL(error, visible, 640, 640);
    if (!device) return fail();
    auto library = device->newLibraryWithSource(source, error); if (!library) return fail();
    auto vertex = library->newFunction("vertexMain", MellowRT::RenderShaderJit::Stage::Vertex, error); if (!vertex) return fail();
    auto fragment = library->newFunction("fragmentMain", MellowRT::RenderShaderJit::Stage::Fragment, error); if (!fragment) return fail();
    auto pipeline = device->newRenderPipeline(vertex, fragment, error); if (!pipeline) return fail();
    auto texture = device->newTexture(512, 512, error); if (!texture) return fail();
    auto queue = device->newCommandQueue();
    const unsigned frames = visible ? 180 : 1;
    const auto start = std::chrono::steady_clock::now();
    for (unsigned i = 0; i < frames; ++i) {
        const float phase = static_cast<float>(i) * 0.035f;
        auto command = queue->commandBuffer();
        auto encoder = command->renderCommandEncoder({texture, {0.025f, 0.04f, 0.07f, 1.f}}, error);
        if (!encoder || !encoder->setRenderPipeline(pipeline, error) ||
            !encoder->setSharedParameters({0.1f * std::sin(phase), 0.07f * std::cos(phase), 0.4f + 0.3f * std::sin(phase), 1.f / 512.f}, error) ||
            !encoder->drawPrimitives(MellowMTL::PrimitiveType::Triangle, 0, 3, error) || !encoder->endEncoding(error) ||
            (visible && !command->present(error)) || !command->commit(error) || !command->waitUntilCompleted(error)) return fail();
        if (visible) std::this_thread::sleep_until(start + std::chrono::microseconds((i + 1) * 16667));
    }
    auto bytes = texture->read(error); if (bytes.empty()) return fail();
    std::ofstream image(argv[1], std::ios::binary);
    image << "P6\n512 512\n255\n";
    for (size_t i = 0; i < bytes.size(); i += 4) image.write(reinterpret_cast<const char *>(bytes.data() + i), 3);
    if (!image) { std::cerr << "Could not write GPU readback image\n"; return 1; }
    std::cout << device->hardware().renderer << ": " << frames << " MSL-rendered frames, "
              << device->pipelineBuildCount() << " retained pipeline compilation; RGBA readback exported\n";
    return 0;
}
