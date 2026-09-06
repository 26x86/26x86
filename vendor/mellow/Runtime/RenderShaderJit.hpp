// SPDX-License-Identifier: MIT
#pragma once
#include <cstddef>
#include <string>
#include <vector>

namespace MellowRT { namespace RenderShaderJit {
enum class Stage { Vertex, Fragment };
struct CompileResult {
    bool success {};
    Stage stage {Stage::Vertex};
    std::string entry, glslSource;
    bool usesParameters {}, usesFragmentPosition {};
    // Every admitted vertex array is indexed only by vertex_id, and has 3 entries.
    // The draw contract is a non-indexed triangle, vertexStart=0, vertexCount=3.
    unsigned requiredVertexCount {3};
    std::vector<std::string> diagnostics;
};
constexpr size_t MaxSourceBytes = 65536;
// Original typed MSL vertex/fragment subset -> GLSL 330, not AIR/render support
// or an Apple compiler. Unknown semantics are rejected before driver compilation.
CompileResult compileMsl(const std::string &, const std::string &entry, Stage);
} }
