// SPDX-License-Identifier: MIT
#include "../Runtime/ShaderJit.hpp"

#include <array>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace MellowRT::ShaderJit;
namespace {
size_t checks = 0;
void check(bool condition, const char *description) { ++checks; if (!condition) throw std::runtime_error(description); }
std::string msl(const std::string &body, const std::string &entry = "affine") {
    return "#include <metal_stdlib>\nusing namespace metal;\nkernel void " + entry + "(device uint *data [[buffer(0)]], uint gid [[thread_position_in_grid]]) {" + body + "}";
}
std::string replace(std::string s, const std::string &before, const std::string &after) {
    auto offset = s.find(before); if (offset == std::string::npos) throw std::runtime_error("Invalid test mutation");
    s.replace(offset, before.size(), after); return s;
}
void rejectedMsl(const std::string &source, const std::string &entry = "affine") {
    const auto result = compileMsl(source, entry);
    check(!result.success, "Unsupported MSL unexpectedly accepted");
    check(result.openclSource.empty() && result.reflection.buffers.empty() && !result.diagnostics.empty(), "MSL failure leaked a successful payload");
}
void rejectedAir(const std::string &source) {
    const auto result = compileAirText(source, "air_affine");
    check(!result.success, "Unsupported AIR unexpectedly accepted");
    check(result.openclSource.empty() && result.reflection.buffers.empty() && !result.diagnostics.empty(), "AIR failure leaked a successful payload");
}

// Synthetic conformance fixture, NOT an Apple compiler output. Metadata syntax
// is constrained to the observed AIR 2.7 example cited in implementation docs.
const std::string airFixture = R"AIR(source_filename = "mellow-synthetic-affine.metal"
target datalayout = "e-p:64:64:64-i1:8:8-i8:8:8-i16:16:16-i32:32:32-i64:64:64-f32:32:32-f64:64:64-v16:16:16-v24:32:32-v32:32:32-v48:64:64-v64:64:64-v96:128:128-v128:128:128-v192:256:256-v256:256:256-v512:512:512-v1024:1024:1024-n8:16:32"
target triple = "air64_v27-apple-macosx15.6.0"
define weak_odr void @air_affine(ptr addrspace(1) noundef %data, i32 noundef %gid) {
entry:
  %index = zext i32 %gid to i64
  %element = getelementptr inbounds i32, ptr addrspace(1) %data, i64 %index
  %input = load i32, ptr addrspace(1) %element, align 4
  %scaled = mul i32 %input, 7
  %output = add i32 %scaled, 3
  store i32 %output, ptr addrspace(1) %element, align 4
  ret void
}
!air.kernel = !{!0}
!air.version = !{!5}
!air.language_version = !{!6}
!0 = !{ptr @air_affine, !1, !2}
!1 = !{}
!2 = !{!3, !4}
!3 = !{i32 0, !"air.buffer", !"air.location_index", i32 0, i32 1, !"air.read_write", !"air.address_space", i32 1, !"air.arg_type_size", i32 4, !"air.arg_type_align_size", i32 4, !"air.arg_type_name", !"uint", !"air.arg_name", !"data"}
!4 = !{i32 1, !"air.thread_position_in_grid", !"air.arg_type_name", !"uint", !"air.arg_name", !"gid"}
!5 = !{i32 2, i32 7, i32 0}
!6 = !{!"Metal", i32 3, i32 2, i32 0}
)AIR";

struct Fixture { std::string entry, source; std::array<uint32_t, 8> expected; };
const std::array<uint32_t, 8> inputs = {{0, 1, 2, 3, 4, 0xffffffffu, 0x80000000u, 0x55555555u}};
const std::vector<Fixture> positives = {
    {"affine", msl("data[gid] = data[gid] * 7u + 3u;"), {{3,10,17,24,31,0xfffffffcu,0x80000003u,0x55555556u}}},
    {"precedence", msl("data[gid] = data[gid] + 2 * 3;", "precedence"), {{6,7,8,9,10,5,0x80000006u,0x5555555bu}}},
    {"rotate_bits", msl("data[gid] = (data[gid] << 3u) | (data[gid] >> 29);", "rotate_bits"), {{0,8,16,24,32,0xffffffffu,4,0xaaaaaaaau}}},
    {"ordered", msl("data[gid] = data[gid] + 1u; uint original = data[gid]; data[gid] = original * 3;", "ordered"), {{3,6,9,12,15,0,0x80000003u,2}}},
    {"wrap", msl("const uint index = gid; uint value = data[index]; value = value + (4294967295u + 2u); data[index] = value;", "wrap"), {{1,2,3,4,5,0,0x80000001u,0x55555556u}}},
    {"division", msl("data[gid] = data[gid] / 7u + data[gid] % 7;", "division"), {{0,1,2,3,4,613566759u,306783380u,204522253u}}},
    {"complement", msl("data[gid] = ~data[gid];", "complement"), {{0xffffffffu,0xfffffffeu,0xfffffffdu,0xfffffffcu,0xfffffffbu,0,0x7fffffffu,0xaaaaaaaau}}},
    {"negate", msl("data[gid] = -data[gid];", "negate"), {{0,0xffffffffu,0xfffffffeu,0xfffffffdu,0xfffffffcu,1,0x80000000u,0xaaaaaaabu}}}
};

void tests() {
    for (const auto &fixture : positives) {
        auto result = compileMsl(fixture.source, fixture.entry);
        if (!result.success) throw std::runtime_error(fixture.entry + ": " + result.diagnostics[0]);
        check(result.diagnostics.empty(), "Successful MSL has diagnostics");
        check(result.reflection.entry == fixture.entry && result.reflection.buffers.size() == 1, "MSL entry/reflection mismatch");
        const auto &buffer = result.reflection.buffers[0];
        check(buffer.index == 0 && buffer.elementType == "uint" && buffer.writable && result.reflection.requiresExactDispatch, "MSL ABI contract mismatch");
        check(result.openclSource.find("(__global uint *mellow_buffer0)") != std::string::npos, "Generated OpenCL argument mismatch");
        check(result.openclSource == compileMsl(fixture.source, fixture.entry).openclSource, "Nondeterministic MSL lowering");
    }
    check(compileMsl(replace(positives[0].source, "* 7u + 3u", "* 7 + 3"), "affine").success, "Unsigned usual arithmetic conversion");
    check(compileMsl(replace(positives[0].source, "device uint *data [[buffer(0)]], uint gid [[thread_position_in_grid]]", "uint gid [[thread_position_in_grid]], device uint *data [[buffer(0)]]"), "affine").success, "Reordered source parameters");
    check(compileMsl(msl("/* no token merging */ data[gid] = 0xffffffff; // comment\n"), "affine").success, "Hex unsigned and comments");
    check(compileMsl(msl("data[(gid)] = +data[gid];"), "affine").success, "Parenthesized exact index");
    check(compileMsl(msl("data[gid] = 1 + 2 * 3;"), "affine").openclSource.find(" = 7;") != std::string::npos, "Precedence/constant fold incorrect");
    check(compileMsl(msl("data[gid] = 0xffffffffu + 2u;"), "affine").openclSource.find(" = 1u;") != std::string::npos, "Unsigned wrap constant fold incorrect");
    for (const std::string body : {
        "", "uint value = data[gid];", "data[gid+1] = 1u;", "data[0] = 1u;", "data[gid] = data[gid-1];", "data[data[gid]] = 1u;",
        "uint index = gid; data[index] = 1u;", "const uint index = gid; index = 1u; data[index] = 1u;", "gid = 0u; data[gid] = 1u;",
        "data[gid] = unknown;", "uint x = x; data[gid] = x;", "uint x = 1; uint x = 2; data[gid] = x;", "uint data = 2; data[gid] = 1u;",
        "data[gid] = 1.0;", "data[gid] = 4294967296u;", "data[gid] = 2147483648;", "data[gid] = 2147483647 + 1;", "data[gid] = 1 - 2;",
        "data[gid] = -1;", "data[gid] = ~1;", "data[gid] = 1 << 31;", "data[gid] = data[gid] << 32u;", "data[gid] = data[gid] >> gid;",
        "data[gid] = data[gid] / 0u;", "data[gid] = data[gid] / gid;", "data[gid] = data[gid] % (2u - 2u);", "data[gid] = 077u;", "data[gid] = 0x;",
        "data[gid] = data[gid]++1u;", "data[gid] = data[gid]--1u;", "data[gid] += 1u;", "data[gid] = gid && 1u;", "data[gid] = gid || 1u;",
        "data[gid] = gid == 1u;", "data[gid] = atomic_load(data);", "if (gid) data[gid] = 1u;", "for (;;) data[gid] = 1u;", "return;",
        "uint *p = data; data[gid] = 1u;", "data[gid] = sizeof(uint);", "data[gid] = (uint)1;", "data[gid] = 1u; barrier();", "data[gid] = 1u; /* unterminated"
    }) rejectedMsl(msl(body));
    for (const auto &mutation : std::vector<std::pair<std::string, std::string>>{
        {"buffer(0)", "buffer(1)"}, {"device uint", "device float"}, {"device uint", "constant uint"}, {"uint gid", "uint3 gid"},
        {"thread_position_in_grid", "thread_index_in_threadgroup"}, {"kernel void", "ke/**/rnel void"}, {"kernel void", "void"},
        {"metal_stdlib", "stdlib.h"}, {"*data", "*gid"}, {"*data", "**data"}
    }) rejectedMsl(replace(positives[0].source, mutation.first, mutation.second));
    rejectedMsl(positives[0].source + "kernel void extra() {}");
    rejectedMsl("#define SOMETHING 1\n" + positives[0].source);
    rejectedMsl(positives[0].source, "missing");
    rejectedMsl(msl("data[gid] = 1;", "__kernel"), "__kernel");
    rejectedMsl(msl("data[gid] = 1;", "union"), "union");
    rejectedMsl(msl("uint template = 1u; data[gid] = template;"));
    check(compileMsl(msl("data[gid] = 1u;", "mellow_objects"), "mellow_objects").success, "Harmless Mellow entry prefix rejected");
    rejectedMsl(std::string(1, '\0') + positives[0].source);
    rejectedMsl(std::string(1, static_cast<char>(0xff)) + positives[0].source);
    rejectedMsl(std::string(MaxSourceBytes + 1, ' '));
    rejectedMsl(msl("data[gid] = " + std::string(1000, '(') + "1u" + std::string(1000, ')') + ";"));
    std::string linear = "data[gid] = 1u";
    for (int i = 0; i < 100; ++i) linear += "+1u";
    rejectedMsl(msl(linear + ";"));
    std::string many;
    for (size_t i = 0; i <= MaxStatements; ++i) many += "data[gid] = 1u;";
    rejectedMsl(msl(many));

    auto air = compileAirText(airFixture, "air_affine");
    if (!air.success) throw std::runtime_error("AIR fixture: " + air.diagnostics[0]);
    check(air.diagnostics.empty() && air.reflection.entry == "air_affine", "AIR result mismatch");
    check(air.reflection.buffers.size() == 1 && air.reflection.buffers[0].elementType == "uint" && air.reflection.requiresExactDispatch, "AIR ABI mismatch");
    check(air.openclSource == compileAirText(airFixture, "air_affine").openclSource, "Nondeterministic AIR lowering");
    auto vectorAir = replace(airFixture, "i32 noundef %gid", "<3 x i32> noundef %thread");
    vectorAir = replace(vectorAir, "%index = zext", "%gid = extractelement <3 x i32> %thread, i64 0\n  %index = zext");
    vectorAir = replace(vectorAir, "!\"uint\", !\"air.arg_name\", !\"gid\"", "!\"uint3\", !\"air.arg_name\", !\"gid\"");
    check(compileAirText(vectorAir, "air_affine").success, "AIR vector index x extraction rejected");
    auto attributeAir = replace(airFixture, "%gid) {", "%gid) local_unnamed_addr #0 {");
    attributeAir = replace(attributeAir, "!air.kernel", "attributes #0 = { mustprogress nounwind \"frame-pointer\"=\"all\" }\n!air.kernel");
    check(compileAirText(attributeAir, "air_affine").success, "Known AIR attributes rejected");
    for (const auto &mutation : std::vector<std::pair<std::string, std::string>>{
        {"air64_v27-apple", "x86_64-apple"}, {"e-p:64:64:64", "E-p:64:64:64"}, {"i32 2, i32 7, i32 0", "i32 2, i32 6, i32 0"},
        {"!\"Metal\", i32 3, i32 2", "!\"Metal\", i32 3, i32 1"}, {"!\"air.location_index\", i32 0", "!\"air.location_index\", i32 1"},
        {"!\"air.address_space\", i32 1", "!\"air.address_space\", i32 2"}, {"!\"air.arg_type_size\", i32 4", "!\"air.arg_type_size\", i32 8"},
        {"!\"air.arg_type_align_size\", i32 4", "!\"air.arg_type_align_size\", i32 2"}, {"!\"air.read_write\"", "!\"air.read\""},
        {"!\"air.thread_position_in_grid\"", "!\"air.thread_index_in_threadgroup\""}, {"!0 = !{ptr @air_affine", "!0 = !{ptr @wrong"},
        {"!air.kernel = !{!0}", "!air.kernel = !{!0, !0}"}, {"!air.kernel = !{!0}", "!air.kernel = !{!99}"},
        {"!2 = !{!3, !4}", "!2 = !{!3}"}, {"!1 = !{}", "!1 = !{i32 0}"}, {"mul i32", "mul nsw i32"}, {"mul i32", "mul nuw i32"},
        {"load i32", "load volatile i32"}, {"load i32", "load atomic i32"}, {"align 4", "align 1"}, {"align 4", "align 8"},
        {"%data, i64 %index", "%data, i64 1"}, {"%data, i64 %index", "%element, i64 %index"}, {"%element, align 4", "%data, align 4"},
        {"%data, i64 %index", "%data, i32 %gid"},
        {"mul i32 %input, 7", "shl i32 %input, 32"}, {"mul i32 %input, 7", "udiv i32 %input, 0"}, {"mul i32 %input, 7", "udiv i32 %input, %gid"},
        {"mul i32 %input, 7", "call i32 @foreign()"}, {"%scaled = mul", "%input = mul"}, {"add i32 %scaled", "add i32 %undefined"},
        {"ret void", "br label %entry"}, {"ptr addrspace(1) noundef", "ptr addrspace(2) noundef"}, {"i32 noundef %gid", "i64 noundef %gid"},
        {"!\"uint\", !\"air.arg_name\", !\"data\"", "!\"float\", !\"air.arg_name\", !\"data\""},
        {"%index = zext i32 %gid", "%index = zext i32 %unknown"}
    }) rejectedAir(replace(airFixture, mutation.first, mutation.second));
    rejectedAir(airFixture + "!99 = !{}\n");
    rejectedAir(airFixture + "!air.version = !{!5}\n");
    rejectedAir(airFixture + "!5 = !{i32 2, i32 7, i32 0}\n");
    rejectedAir(replace(airFixture, "store i32 %output, ptr addrspace(1) %element, align 4", ""));
    rejectedAir(replace(vectorAir, "i64 0", "i64 1"));
    check(!compileAirText(airFixture, "wrong").success, "AIR selected-entry mismatch accepted");
    for (const std::vector<uint8_t> &blob : {std::vector<uint8_t>{}, std::vector<uint8_t>{'B','C',0xc0,0xde}, std::vector<uint8_t>{0xde,0xc0,0x17,0x0b}, std::vector<uint8_t>{'M','T','L','B'}}) {
        auto result = compileAir(blob, "air_affine");
        check(!result.success && result.openclSource.empty() && !result.diagnostics.empty(), "Bitcode magic falsely accepted as AIR");
    }
    // Deterministic adversarial mutation coverage. Success must still obey the
    // complete ABI contract; arbitrary mutated input is not expected to fail.
    uint32_t seed = 0x7d41u;
    for (size_t i = 0; i < 2000; ++i) {
        seed = seed * 1664525u + 1013904223u;
        auto source = i & 1 ? positives[0].source : airFixture;
        source[seed % source.size()] = static_cast<char>((seed >> 16) & 127);
        auto result = i & 1 ? compileMsl(source, "affine") : compileAirText(source, "air_affine");
        check(result.success ? (!result.openclSource.empty() && result.diagnostics.empty() && result.reflection.buffers.size() == 1 && result.reflection.requiresExactDispatch) : (result.openclSource.empty() && !result.diagnostics.empty()), "Mutation produced contradictory result");
    }
}

void write(const std::string &path, const std::string &data) {
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    stream << data; if (!stream) throw std::runtime_error("Cannot write fixture");
}
void emitFixtures(const std::string &directory) {
    std::string host = "// Test-only CPU execution of generated OpenCL-shaped C++. Not GPU execution.\n#include <cstdint>\n#include <cstddef>\n#include <iostream>\nusing uint = uint32_t;\n#define __kernel\n#define __global\nstatic size_t current_id = 0;\nstatic size_t get_global_id(unsigned) { return current_id; }\n";
    for (const auto &fixture : positives) {
        auto result = compileMsl(fixture.source, fixture.entry);
        write(directory + "/" + fixture.entry + ".metal", fixture.source);
        write(directory + "/" + fixture.entry + ".cl", result.openclSource);
        host += result.openclSource;
    }
    auto air = compileAirText(airFixture, "air_affine");
    write(directory + "/synthetic-air-affine.ll", airFixture);
    write(directory + "/air_affine.cl", air.openclSource);
    host += air.openclSource;
    host += "int main() { size_t checks = 0;\n";
    for (size_t f = 0; f <= positives.size(); ++f) {
        auto fixture = f < positives.size() ? positives[f] : Fixture{"air_affine", "", positives[0].expected};
        host += "{ uint values[] = {";
        for (auto v : inputs) host += std::to_string(v) + "u,";
        host += "}; const uint expected[] = {";
        for (auto v : fixture.expected) host += std::to_string(v) + "u,";
        host += "}; for(current_id=0; current_id<8; ++current_id) " + fixture.entry + "(values); for(size_t i=0;i<8;++i) { ++checks; if(values[i]!=expected[i]) { std::cerr << \"" + fixture.entry + " mismatch at \" << i << \" got \" << values[i] << \" expected \" << expected[i]; return 2; } } }\n";
    }
    host += "std::cout << \"{\\\"status\\\":\\\"PASS_GENERATED_SHADER_CPU_REFERENCE\\\",\\\"checks\\\":\" << checks << \"}\\n\"; }\n";
    write(directory + "/generated-host-tests.cpp", host);
}
}

int main(int argc, char **argv) {
    try {
        if (argc == 5 && (std::string(argv[1]) == "--lower-air" || std::string(argv[1]) == "--lower-msl")) {
            std::ifstream input(argv[2], std::ios::binary);
            if (!input) throw std::runtime_error("Cannot read shader input");
            std::string source;
            char c;
            while (input.get(c)) { source.push_back(c); if (source.size() > MaxSourceBytes) throw std::runtime_error("Input exceeds source byte limit"); }
            auto result = std::string(argv[1]) == "--lower-air" ? compileAirText(source, argv[3]) : compileMsl(source, argv[3]);
            if (!result.success) { for (const auto &error : result.diagnostics) std::cerr << error << '\n'; return 2; }
            write(argv[4], result.openclSource);
            std::cout << "{\"status\":\"PASS_SHADER_TRANSLATION_ONLY\",\"hardware_execution\":false}\n";
            return 0;
        }
        tests();
        if (argc == 3 && std::string(argv[1]) == "--emit-fixtures") emitFixtures(argv[2]);
        else if (argc != 1) throw std::runtime_error("Usage: shader-jit-tests [--emit-fixtures DIRECTORY]");
        std::cout << "{\"status\":\"PASS_SHADER_FRONTEND_SUBSET\",\"checks\":" << checks << ",\"hardware_execution\":false,\"air_fixture_origin\":\"synthetic\"}\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n'; return 2;
    }
}
