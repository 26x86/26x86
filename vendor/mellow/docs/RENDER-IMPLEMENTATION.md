# Explicit Mellow rendering: implementation contract

This is the user-space graphics path. `RenderShaderJit` translates a checked MSL vertex/fragment
subset to GLSL, `RenderObjects` implements explicit C++ library/pipeline/texture/encoder objects,
and `OpenGLProvider` compiles and executes that GLSL on an existing accelerated Windows driver.
It extends the earlier compute path toward graphics workloads. It does not implement Apple's
Objective-C Metal ABI, native Tahoe GPU execution, WindowServer, hardware cursor planes or
GL/CL resource sharing. Those remain requirements of the full project.

## Shader semantics

The frontend performs lexical, type and symbol validation; it does not paste arbitrary MSL into
GLSL. Source is limited to 64 KiB, 8,192 tokens, 4,096 expression nodes, 256 statements and 48
levels of expression nesting. Unknown tokens, keywords used as names, duplicate symbols/entries,
unsupported parameters, control flow, function calls and unsafe array addressing are rejected.
All functions in an input must belong to the admitted subset, even when only one is selected.

- Entry result is `float4`. Stages are `vertex` and `fragment`; optional fragment output is
  `[[color(0)]]`. Vertex `float4` position has no return attribute.
- A vertex entry may take one `uint [[vertex_id]]`; it may use const local three-element
  float/vector arrays addressed only by that exact parameter. The API enforces one non-indexed
  triangle with vertexStart 0 and vertexCount 3.
- A fragment entry may take `float4 [[position]]`. Either stage may take one
  `constant float4& [[buffer(0)]]`. This API explicitly supplies one shared parameter vector
  to both stages. Independent stage bindings are not implemented.
- `float`, `float2`, `float3`, `float4`, constructors, checked swizzles, initialized local values
  and component-wise float arithmetic are supported. Uint is only a vertex index or a numeric
  constructor operand. Division requires a nonzero constant float scalar after float32 rounding.
  A uint-to-float conversion also rounds before validating a constant divisor. Unsupported
  integer arithmetic, octal/hex, invalid suffixes, overflow and nonfinite literals are rejected.
- No sampled textures, vertex buffers, user varyings, matrices, depth attachments, blending,
  raster-order groups, discard, derivatives, tessellation, mesh or AIR render lowering are claimed.

MSL entry/output contracts were checked against Apple's
[Metal Shading Language Specification](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf),
2026-06-04 edition, pages 144–146 and 172. The inspected PDF SHA256 is
`41538b30d2f1140a5b2a0c84ce0a9f7b67bf0c707e224cfea0bfe5a44aa26cf5`.
This is source-language reference evidence, not an invocation of Apple's compiler.

Metal clip depth uses 0 through w. The generated vertex stage applies `2*z-w` before OpenGL
rasterization. No Y inversion is applied to clip position. Fragment position Y is
`viewportHeight - gl_FragCoord.y`; `RenderTexture::read` flips the provider's bottom-up rows
to top-down RGBA8. These are separate depth, fragment-coordinate and readback transformations.
The end-to-end tests independently check triangle coverage and position-dependent colors.
Apple's [viewport and normalized-device-coordinate contract](https://developer.apple.com/library/archive/documentation/Miscellaneous/Conceptual/MetalProgrammingGuide/Render-Ctx/Render-Ctx.html)
defines these coordinate spaces. Khronos documents the default OpenGL negative-one-to-one
clip depth in [ARB_clip_control](https://github.com/KhronosGroup/OpenGL-Registry/blob/main/extensions/ARB/ARB_clip_control.txt).

## Objects, resources and completion

`RenderDevice::createOpenGL` creates a dedicated graphics device with an isolated provider.
It does not inherit the compute device's capabilities. Libraries own source; `newFunction`
performs translation, and `newRenderPipeline` performs actual driver compilation/linking.
Programs remain compiled across command buffers. The functions/libraries/device and provider
state remain alive while required by a pipeline or queued draw.

`RenderTexture` has immutable 1–2048 dimensions and RGBA8 format. Each pass currently renders
into a newly allocated native texture/FBO, reads its bytes and releases that native allocation.
The object retains the latest successful top-down CPU snapshot and sequence. Reading before a
successful pass fails; a failed later pass leaves the previous successful snapshot available.
This is explicit copying, not persistent VRAM, IOSurface or shared Metal storage semantics.

One draw is accepted per clearing pass, up to 16 passes in a command buffer. Pipelines and
textures must belong to the same RenderDevice. Nonfinite parameters, a mismatched stage,
unsupported vertex counts, an empty/abandoned encoder and repeated commit are rejected.
Command buffers and encoders require single-thread ownership. Texture snapshot access is locked;
device submission is serialized and actual GL calls run on the provider's private thread.

Commit is synchronous. Completion requires submission, a real signaled GL fence, readback,
correct context/epoch/sequence, exact dimensions/byte count and checked per-pass cleanup.
There is no application-provided expected pixel array in this runtime API. Test reference
images are computed independently by the supervisor after reading actual GPU output.

Optional `present` requests a blit and `SwapBuffers` on the owned visible window. Success proves
API acceptance only. It does not establish how many frames reached the monitor, frame pacing,
cursor smoothness or a working macOS compositor. The corresponding scope flags remain false.
Provider details and primary GL/WGL references are in [OpenGLProvider](../Runtime/OpenGLProvider.md).

## Reproduce

```powershell
python Tools/run-render-shader-tests.py --cxx C:/msys64/mingw64/bin/g++.exe --out build/new-render-frontend
python Tools/run-opengl-provider.py --cxx C:/msys64/mingw64/bin/g++.exe --out build/new-gl-render --render --frames 1000
python Tools/run-render-objects.py --cxx C:/msys64/mingw64/bin/g++.exe --out build/new-msl-render --render --frames 1000
python Tools/run-render-objects.py --cxx C:/msys64/mingw64/bin/g++.exe --out build/new-msl-visible --render --visible --frames 120
```

The full MSL object runner is `Tools/run-render-objects.py`; its GPU test binds the real MSL
fixture through `RenderLibrary` and `RenderPipeline`, rather than bypassing them with GLSL.
Run `--help` for its supervised execution and output arguments. Use a fresh output directory.
The ordinary application source [render-msl.cpp](../Examples/render-msl.cpp) is also runnable:

```powershell
g++ -std=c++17 -O2 Runtime/RenderShaderJit.cpp Runtime/RenderObjects.cpp Runtime/OpenGLProvider.cpp Examples/render-msl.cpp -lopengl32 -lgdi32 -luser32 -o render-msl.exe
./render-msl.exe gpu-readback.ppm --visible
```

It renders 180 paced client submissions using one compiled pipeline and exports the final
GPU readback. The wait between submissions is host pacing, not measured monitor refresh.
Native driver calls can block, so acceptance tools execute them in a process with a deadline.
Linux currently supports frontend/build checks; actual native GL execution explicitly fails
as unsupported. There is no silent CPU or virtual display fallback.

## Recorded verification

The [integration index](../validation/render/integration.json) pins eight reports, the tested
source hashes and the actual GPU snapshots. On the Windows Intel driver 32.0.101.6737:

- MSL object rendering passed 1,000 offscreen frames: 3,072,000 independently checked pixels,
  16,050 native assertions and 27 named negative API checks. One driver program was reused.
- The visible run passed 120 frames and 368,640 checked pixels with 120 successful swap API
  calls. Physical scanout and WindowServer verification remain false.
- The independent pixel oracle checks triangle coverage and position-dependent RGBA, with
  RGB tolerance one and exact alpha. At the bounded subpixel edge only valid gradient or clear
  is accepted. The offscreen run had 1,016 such boundary pixels, not arbitrary unchecked pixels.
- The provider-only GLSL path separately passed 1,000 offscreen and 120 visible frames. These
  runs test the substrate and do not add to the MSL-object frame count.
- Windows frontend and Linux ASan/UBSan each passed 969 checks. Linux object compilation
  passed without GPU execution. Thirteen synthetic report/pixel corruption controls passed.

The full top-down RGBA streams are in the release evidence archive. The PNGs in
`validation/render` are encodings of GPU readback, not photographs or screenshots of a monitor.
`python Tools/verify-render-evidence.py` checks the recorded report/source hashes without
executing graphics. Add `--raw-directory <extracted-evidence>` to check both full stream hashes.
The [ordinary client](../Examples/render-msl.cpp) separately executed one offscreen and 180
paced visible submissions. None of these results tests general application binary compatibility,
Apple-generated AIR, native macOS rendering, display/cursor ownership or complete Metal 2/3.
