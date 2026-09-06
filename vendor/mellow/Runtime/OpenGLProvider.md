# Native OpenGL render provider

OpenGLProvider is an actual Windows WGL user-space render substrate. It owns an
isolated window, device context and OpenGL 3.3 core context on a private worker
thread. Public calls synchronously marshal to that thread; it also pumps the
owned window's messages. It does not adopt, change or destroy an application's
ambient GL context. Other operating systems fail explicitly.

Initialization selects a double-buffered RGBA pixel format and rejects generic
software/MCD pixel-format flags and known software renderer strings. It verifies
the actual core version and profile, and records driver vendor/renderer/version.
These are driver-reported hardware ICD facts, not physical PCI attestation.
See Microsoft's [pixel-format query API](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-describepixelformat)
and Khronos's [WGL core-context contract](https://registry.khronos.org/OpenGL/extensions/ARB/WGL_ARB_create_context.txt).

Compile accepts bounded vertex/fragment GLSL source and actually compiles and
links the native program. The resulting pipeline retains the original provider
state and worker/context even after the public provider facade is destroyed.
Its program is reused across render calls. Programs from another provider or a
stale context epoch are rejected; reinitialization never revives old programs.

Render currently draws three vertices using gl_VertexID, with no vertex buffers
or sampled textures. Optional uniforms are vec4 mellow_params and vec2
mellow_viewport. Each call creates an RGBA8 texture/FBO and a core VAO, clears,
draws, waits for its GL fence, and reads tightly packed RGBA8 bytes. Readback row
zero is the bottom row. Width/height are bounded to 1..2048. Blending, depth,
stencil, scissor, culling, dithering, multisampling and framebuffer sRGB conversion
are disabled for this deterministic render contract.

The fence is waited in 10 ms intervals with a two-second host deadline. Readback,
current-context identity, GL errors and per-frame deletion are checked before
success is returned. A submitted frame failure invalidates the context epoch.
Persistent programs remain live until their pipeline is released; per-frame
resourcesReleased describes the texture/FBO/VAO/fence, not persistent programs.
Native driver calls can still block, so the application must use an externally
timed worker; the internal fence deadline cannot preempt a hung driver API.

Explicit visible initialization permits a render call with present=true. The
provider blits the offscreen FBO to the owned window's backbuffer and calls
SwapBuffers. swapCompleted records API success; displayScanoutVerified remains
false. This does not prove physical scanout, macOS WindowServer acceleration,
Metal ABI registration, a display kernel driver, cursor planes, or GL/CL sharing.

Run Tools/run-opengl-provider.py with --render --out build/opengl-provider to
execute real driver acceptance, or add --visible --frames 120 for an owned
animated window. The tests independently compare every RGBA byte of varying
quadrant patterns and reuse one program. Invalid GLSL, bounds, NaN uniforms,
hidden presentation, null/foreign/stale pipelines and retained context lifetime
have explicit negative checks. Reports pin sources, native binary, OS and the
actual hardware-driver observations. Synthetic report mutations are separate
software tests; none counts as a GPU frame.
