# Tahoe Metal Shader Compiler & Pre-AVX CPU Gate

Technical notes regarding the Metal compiler daemon (`metal-plugin-host` and `MTLCompilerService`) crashing on CPUs lacking AVX instructions.

## Mitigation

Injecting RestrictEvents hooks ensures that compiler workers fall back to SSE-compatible code paths when compiling shading language bytecode on MacPro5,1 systems.
