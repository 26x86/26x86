// SPDX-License-Identifier: MIT
// Source translation CLI only. GPU machine compilation/execution is performed
// by MellowMTL/OpenCLProvider, not asserted from this program's successful exit.
#include "../Runtime/ShaderJit.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>

static std::string quote(const std::string &s) {
    std::string out = "\"";
    constexpr char hex[] = "0123456789abcdef";
    for (unsigned char c : s) {
        if (c == '\"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
        else if (c < 32) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
        else out += static_cast<char>(c);
    }
    return out + "\"";
}

int main(int argc, char **argv) {
    if (!((argc == 4 && (std::string(argv[1]) == "msl" || std::string(argv[1]) == "air-text")) ||
          (argc == 5 && std::string(argv[1]) == "air"))) {
        std::cerr << "Usage: shader-jit-cli msl|air-text INPUT ENTRY | air INPUT ENTRY ABSOLUTE_LLVM_LIBRARY\n";
        return 2;
    }
    std::ifstream file(argv[2], std::ios::binary);
    if (!file) { std::cerr << "Cannot read shader input\n"; return 2; }
    std::string source;
    const size_t limit = std::string(argv[1]) == "air" ? 4 * 1024 * 1024 : MellowRT::ShaderJit::MaxSourceBytes;
    source.resize(limit + 1);
    file.read(&source[0], static_cast<std::streamsize>(source.size()));
    source.resize(static_cast<size_t>(file.gcount()));
    if (source.size() > limit) {
        std::cerr << "Shader input exceeds byte limit\n"; return 2;
    }
    MellowRT::ShaderJit::CompileResult result;
    if (std::string(argv[1]) == "msl") result = MellowRT::ShaderJit::compileMsl(source, argv[3]);
    else if (std::string(argv[1]) == "air") result = MellowRT::ShaderJit::compileAir(
        std::vector<uint8_t>(source.begin(), source.end()), argv[3], argv[4]);
    else result = MellowRT::ShaderJit::compileAirText(source, argv[3]);
    std::cout << "{\"schema_version\":1,\"status\":"
              << quote(result.success ? "LOWERED_OPENCL_C_ONLY" : "REJECTED")
              << ",\"gpu_executed\":false,\"input\":" << quote(argv[1])
              << ",\"entry\":" << quote(result.reflection.entry)
              << ",\"opencl_source\":" << quote(result.openclSource)
              << ",\"diagnostics\":[";
    for (size_t i = 0; i < result.diagnostics.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << quote(result.diagnostics[i]);
    }
    std::cout << "]}\n";
    return result.success ? 0 : 2;
}
