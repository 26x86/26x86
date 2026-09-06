// SPDX-License-Identifier: MIT
// Actual LLVM C API lifetime/concurrency test. Positive bitcode is deliberately
// synthetic; this does not call an Apple compiler, lower shaders or run a GPU.
#include "AirDecoder.hpp"
#include <atomic>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    std::ifstream file(argv[1], std::ios::binary);
    if (!file) return 2;
    std::vector<uint8_t> valid(4 * 1024 * 1024 + 1);
    file.read(reinterpret_cast<char *>(valid.data()), static_cast<std::streamsize>(valid.size()));
    valid.resize(static_cast<size_t>(file.gcount()));
    if (file.bad() || valid.size() < 4 || valid.size() > 4 * 1024 * 1024) return 2;

    std::atomic<unsigned> checks {0}, failures {0};
    std::vector<std::thread> jobs;
    for (unsigned thread = 0; thread < 4; ++thread) {
        jobs.emplace_back([&] {
            for (unsigned iteration = 0; iteration < 32; ++iteration) {
                std::string ir = "stale IR", error = "stale error";
                bool ok = MellowRT::ShaderJit::decodeAirBitcode(valid, argv[2], ir, error);
                ++checks;
                if (!ok || ir.find("@air_affine") == std::string::npos || !error.empty()) ++failures;
                // Valid magic alone cannot pass. Reusing outputs also verifies
                // that failure clears previously decoded IR and records an error.
                const std::vector<uint8_t> malformed {'B', 'C', 0xc0, 0xde};
                ok = MellowRT::ShaderJit::decodeAirBitcode(malformed, argv[2], ir, error);
                ++checks;
                if (ok || !ir.empty() || error.empty()) ++failures;
            }
        });
    }
    for (auto &job : jobs) job.join();
    std::cout << "{\"status\":\"" << (failures ? "FAIL" : "PASS_LLVM_C_DECODER_LIFETIME")
              << "\",\"threads\":4,\"checks\":" << checks << ",\"failures\":" << failures
              << ",\"gpu_executed\":false,\"shader_lowered\":false"
              << ",\"apple_compiler_origin_authenticated\":false}\n";
    return failures ? 1 : 0;
}
