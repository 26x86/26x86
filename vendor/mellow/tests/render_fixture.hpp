// SPDX-License-Identifier: MIT
#pragma once
// Original MSL fixture. It is not Apple-compiler-produced AIR or metallib.
inline constexpr const char *MellowRenderFixture = R"MSL(
#include <metal_stdlib>
using namespace metal;
vertex float4 triangleVertex(uint vertexIndex [[vertex_id]],
                             constant float4& parameters [[buffer(0)]]) {
    const float2 positions[3] = {
        float2(-0.72, -0.52), float2(0.58, -0.32), float2(-0.18, 0.72)
    };
    float2 position = positions[vertexIndex] + parameters.xy;
    return float4(position, 0.5, 1.0);
}
fragment float4 gradientFragment(float4 location [[position]],
                                 constant float4& parameters [[buffer(0)]]) {
    return float4(location.x * parameters.w, location.y * parameters.w, parameters.z, 1.0);
}
)MSL";
