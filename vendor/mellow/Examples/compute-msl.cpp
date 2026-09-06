// SPDX-License-Identifier: MIT
// An application using the explicit portable Mellow object API. It needs an
// existing accelerated OpenCL driver, and does not install a macOS Metal device.
#include "../Runtime/MetalObjects.hpp"
#include <iostream>

int main() {
    MellowMTL::Error error;
    const auto fail = [&]() { std::cerr << error.message << '\n'; return 1; };
    auto device = MellowMTL::Device::createOpenCL(0, error);
    if (!device) return fail();
    auto library = device->newLibraryWithSource(R"(
        #include <metal_stdlib>
        using namespace metal;
        kernel void affine(device uint *x [[buffer(0)]],
                           uint i [[thread_position_in_grid]]) {
            x[i] = x[i] * 7u + 3u;
        }
    )", error);
    if (!library) return fail();
    auto function = library->newFunction("affine", error);
    if (!function) return fail();
    auto pipeline = device->newComputePipeline(function, error);
    if (!pipeline) return fail();
    auto buffer = device->newBuffer({1, 2, 3, 4}, error);
    if (!buffer) return fail();
    auto queue = device->newCommandQueue();
    auto command = queue->commandBuffer();
    auto encoder = command->computeCommandEncoder(error);
    if (!encoder || !encoder->setComputePipeline(pipeline, error) ||
        !encoder->setBuffer(buffer, 0, error) || !encoder->dispatchThreads(buffer->elementCount(), error) ||
        !encoder->endEncoding(error) || !command->commit(error) || !command->waitUntilCompleted(error)) return fail();
    std::cout << device->hardware().name << " via Mellow MSL/OpenCL compute subset\n";
    for (const auto value : buffer->read()) std::cout << value << ' ';
    std::cout << '\n';
    return 0;
}
