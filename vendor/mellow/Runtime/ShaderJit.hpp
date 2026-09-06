// SPDX-License-Identifier: MIT
#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace MellowRT { namespace ShaderJit {

enum class InputKind { MslSource, AirBitcode, AirLlvmText };

struct BufferBinding {
    std::string name;
    uint32_t index = 0;
    std::string elementType;
    bool writable = false;
};

struct Reflection {
    // This is the generated OpenCL entry. There is exactly one buffer argument;
    // the thread index is generated from get_global_id(0), not passed by host.
    std::string entry;
    std::vector<BufferBinding> buffers;
    std::string threadIndexName;
    bool requiresExactDispatch = true;
};

struct CompileResult {
    bool success = false;
    std::string openclSource;
    Reflection reflection;
    std::vector<std::string> diagnostics;
};

constexpr size_t MaxSourceBytes = 65536;
constexpr size_t MaxTokens = 8192;
constexpr size_t MaxAstNodes = 4096;
constexpr size_t MaxStatements = 256;
constexpr size_t MaxExpressionDepth = 64;

// Typed, bounded MSL compute subset, documented in SHADER-JIT-IMPLEMENTATION.md.
// Success means source translation only. The OpenCL driver must still compile
// it; the caller must bind exactly buffer(0) and dispatch one dimension with
// exactly buffer.size()/sizeof(uint32_t) work items (at most UINT32_MAX).
CompileResult compileMsl(const std::string &source, const std::string &entry);

// Raw bitcode cannot be accepted merely from its magic. It needs a real LLVM
// decoder and the AIR metadata validation performed by compileAirText.
CompileResult compileAir(const std::vector<uint8_t> &bitcode, const std::string &entry);
CompileResult compileAir(const std::vector<uint8_t> &bitcode, const std::string &entry,
                         const std::string &llvmLibrary);

// Narrow AIR LLVM assembly input after an external, actual LLVM decoder.
// This function does not treat arbitrary LLVM IR as a supported AIR shader.
CompileResult compileAirText(const std::string &ir, const std::string &entry);

} } // namespace MellowRT::ShaderJit
