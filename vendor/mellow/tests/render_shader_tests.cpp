// SPDX-License-Identifier: MIT
#include "../Runtime/RenderShaderJit.hpp"
#include "render_fixture.hpp"
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
using namespace MellowRT::RenderShaderJit;
static unsigned checks = 0, failures = 0;
static void check(bool b, const char *label) { ++checks; if (!b) { ++failures; std::cerr << label << '\n'; } }
static std::string fragment(const std::string &body) { return "fragment float4 f() { " + body + " }"; }
int main(int argc, char **argv) {
    auto v = compileMsl(MellowRenderFixture, "triangleVertex", Stage::Vertex);
    auto f = compileMsl(MellowRenderFixture, "gradientFragment", Stage::Fragment);
    check(v.success && v.usesParameters && !v.usesFragmentPosition, "vertex fixture");
    check(f.success && f.usesParameters && f.usesFragmentPosition, "fragment fixture");
    check(v.glslSource.find("2.0 * mellow_value.z - mellow_value.w") != std::string::npos, "depth conversion");
    check(f.glslSource.find("mellow_viewport.y - gl_FragCoord.y") != std::string::npos, "top-left position");
    for (const auto &expr : {"float4(1.0)", "float4(float2(1.0, 0.0), 0.5, 1.0)", "float4(1, 0, 1, 1)", "float4(-1.0, +0.5, 1e-2, 1.0)", "float4(float(2u) / 4.0)", "float4((float2(1.0, 0.0)).yx, 0.5, 1.0)"})
        check(compileMsl(fragment("return " + std::string(expr) + ";"), "f", Stage::Fragment).success, "positive constructors");
    std::vector<std::string> bad {
        "return float4(1.0u);", "return float4(1f);", "return float4(010);", "return float4(0x10);", "return float4(1e999);",
        "return float4(1.0 / 0.0);", "return float4(1.0 / 1e-100);", "return float4(1.0 / (1.0 - 1.0));",
        "return float4(1.0 / (16777216.0 + 1.0 - 16777216.0));",
        "return float4(1.0 / (float(16777217u) - 16777216.0));",
        "return float4(1.0, 0.0);", "return float4(float3(1.0), float2(0.0));",
        "return float4(float(float2(1.0)));", "return float4(sin(1.0));", "return float4(1u + 2u);",
        "return float4((float2(1.0)).z, 0.0, 0.0, 1.0);", "return float4((float4(1.0)).xr, 0.0, 1.0);",
        "float4 x = float4(0.0); x = float4(1.0); return x;",
        "float4 x; return x;", "float x = 1u; return float4(x);", "return float4(1.0); return float4(0.0);",
        "if (1) return float4(1.0);", "while (1) {} return float4(1.0);", "return gl_FragColor;",
        "float return = 1.0; return float4(return);", "float x = 1.0; float x = 2.0; return float4(x);",
        "return float4(1.0 / float4(2.0));", "return float4(-1);", "return float4(1e+);"
    };
    for (auto &body : bad) check(!compileMsl(fragment(body), "f", Stage::Fragment).success, body.c_str());
    for (const std::string source : {
        "vertex float4 v(uint id [[vertex_id]]) [[position]] { return float4(1.0); }",
        "fragment float4 f(uint id [[vertex_id]]) { return float4(1.0); }",
        "fragment float4 f(constant float4& p [[buffer(1)]]) { return p; }",
        "fragment float4 f(constant float4& p [[buffer(0)]],constant float4& q [[buffer(0)]]) { return p; }",
        "fragment float4 f() [[color(1)]] { return float4(1.0); }",
        "fragment float4 f() { return float4(1.0); } fragment float4 f() { return float4(1.0); }",
        "kernel void f() {}", "#define X 1\nfragment float4 f() {return float4(1.0);}",
        "fragment float4 f() {return float4(1.0);} /* unterminated"})
        check(!compileMsl(source, "f", Stage::Fragment).success, "rejected entry/source contract");
    const std::string fixture = MellowRenderFixture;
    for (const std::string word : {"if", "for", "kernel", "device", "true", "constexpr", "reinterpret_cast", "a__b"}) {
        check(!compileMsl("fragment float4 " + word + "(){return float4(1.0);}", word, Stage::Fragment).success, "reserved entry");
        check(!compileMsl(fragment("float " + word + "=1.0; return float4(" + word + ");"), "f", Stage::Fragment).success, "reserved local");
        check(!compileMsl("fragment float4 f(constant float4& " + word + " [[buffer(0)]]) {return " + word + ";}", "f", Stage::Fragment).success, "reserved argument");
    }
    for (const auto &needle : {"positions[vertexIndex + 1u]", "positions[float(vertexIndex)]", "positions[0]"}) {
        std::string mutated = fixture; auto p = mutated.find("positions[vertexIndex]"); mutated.replace(p, std::string("positions[vertexIndex]").size(), needle);
        check(!compileMsl(mutated, "triangleVertex", Stage::Vertex).success, "unsafe array addressing");
    }
    check(!compileMsl(fixture, "missing", Stage::Vertex).success, "missing entry");
    check(!compileMsl(fixture, "triangleVertex", Stage::Fragment).success, "stage mismatch");
    check(!compileMsl(std::string(MaxSourceBytes + 1, ' '), "f", Stage::Fragment).success, "source bound");
    check(!compileMsl(fragment("return " + std::string(80, '(') + "float4(1.0)" + std::string(80, ')') + ";"), "f", Stage::Fragment).success, "depth bound");
    for (size_t i = 0; i < fixture.size(); ++i) {
        // Truncated input that already contains the complete vertex function can
        // legitimately select it; fragment selection requires the entire body.
        auto result = compileMsl(fixture.substr(0, i), "gradientFragment", Stage::Fragment);
        check(!result.success || fixture.substr(i).find_first_not_of(" \n\r\t") == std::string::npos, "truncation admission");
    }
    for (unsigned i = 0; i < 256; ++i) {
        auto source = fragment("return float4(" + std::to_string(i) + ".0 / 255.0);");
        check(compileMsl(source, "f", Stage::Fragment).success, "varied finite literal");
    }
    if (argc == 3) {
        std::ofstream vs(argv[1]), fs(argv[2]); vs << v.glslSource; fs << f.glslSource;
        check(static_cast<bool>(vs) && static_cast<bool>(fs), "generated shader output");
    }
    std::cout << "{\"checks\":" << checks << ",\"failures\":" << failures << ",\"hardware_execution\":false,\"apple_compiler_used\":false}\n";
    return failures ? 1 : 0;
}
