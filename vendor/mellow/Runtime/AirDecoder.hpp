// SPDX-License-Identifier: MIT
#pragma once
#include <cstdint>
#include <string>
#include <vector>

namespace MellowRT { namespace ShaderJit {
// Actual LLVM C API reader/verifier. Explicit absolute LLVM library path;
// nothing is downloaded or installed. Raw/wrapped bitcode only; container
// extraction is provided separately by Tools/mellow_air.py.
// Run compiler/GPU calls in a supervised worker for untrusted shader input.
bool decodeAirBitcode(const std::vector<uint8_t> &bitcode, const std::string &llvmLibrary,
                     std::string &ir, std::string &error);
} }
