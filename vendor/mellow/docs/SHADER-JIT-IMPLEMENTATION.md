# Shader frontend and AIR lowering

This is a **user-space shader compiler layer**. `Runtime/ShaderJit.cpp` implements a lexer, recursive-descent expression parser, typed AST, index proof, constant evaluation, and OpenCL C emission. The AIR path implements a separate SSA and metadata parser. A successful `CompileResult` means that a supported shader was translated. The OpenCL provider must then perform actual driver compilation and command execution. This code does not register a macOS Metal device, implement a Tahoe IOAccelerator user client, or install an XNU GPU driver.

## MSL contract

`compileMsl(source, entry)` accepts one compute entry with exactly these arguments, in either source order:

```metal
#include <metal_stdlib>
using namespace metal;
kernel void affine(device uint *data [[buffer(0)]],
                   uint gid [[thread_position_in_grid]]) {
    uint original = data[gid];
    data[gid] = original * 7u + 3u;
}
```

The include and namespace declaration are optional. The accepted body is a straight-line sequence of initialized `uint` or `const uint` locals and assignments. Operators are unary `+`, uint unary `-`/`~`, and binary `+ - * / % & | ^ << >>`, with C-family precedence and associativity. Division/remainder needs a nonzero constant expression; shifts need a constant in `0..31`. Decimal and hexadecimal uint32 literals are supported. Unsuffixed decimal literals must fit int32. Signed-only constant subexpressions must remain nonnegative and within int32; unsigned operations wrap to 32 bits. A typed AST determines these rules before emission.

Every buffer access must use the immutable thread index, optionally parenthesized, or a `const uint` alias proven to contain precisely that index. `data[gid+1]`, mutable index aliases, pointers, function calls, casts, conditions, loops, atomics, barriers, textures, vectors, additional kernels, arbitrary preprocessing, and unsupported attributes are rejected. A kernel must contain a buffer store. Comments are lexed; they cannot merge identifiers or disguise unsupported operators. Source names are checked and local identifiers are regenerated.

Reflection returns the generated entry and one writable `uint` buffer at binding zero. The generated signature has **one argument**:

```c
__kernel void affine(__global uint *mellow_buffer0)
```

The thread index comes from `get_global_id(0)`. The caller must bind one uint32 buffer and dispatch exactly its element count in one dimension, with no global offset and no more than `UINT32_MAX` work items. The current Mellow object/provider layer imposes a smaller allocation/dispatch limit. Reflection's `requiresExactDispatch` is mandatory; a rounded-up dispatch is outside this compiler contract.

The relevant language definitions are Apple's [Metal Shading Language specification](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf), sections 2.8, 4.1, and 5.2.1, and Khronos's [OpenCL C specification](https://registry.khronos.org/OpenCL/specs/unified/html/OpenCL_C.html), sections 6.4.6, 6.5, 6.7, 6.9, and 6.15.1. This implementation deliberately accepts a subset of those languages.

## AIR contract

`compileAir(bitcode, entry, absoluteLlvmLibrary)` calls the separate `AirDecoder` implementation, which loads an explicitly selected LLVM C API library, reads actual raw or wrapped bitcode, verifies the LLVM module, and prints LLVM assembly. `compileAirText(ir, entry)` then performs the lowering checks. The two-argument `compileAir` rejects input because no decoder library was explicitly selected. A magic number is never accepted as proof of a valid AIR module. Metallib container extraction belongs to `Tools/mellow_air.py` and is separate from raw bitcode decoding.

The accepted ABI is the **observed AIR 2.7 subset**: the exact recorded 64-bit data layout, an `air64_v27-apple-macosx...` target, AIR `2.7.0` and Metal `3.2.0` metadata, one void kernel, one `ptr addrspace(1)` read/write `uint` buffer at location zero with size/alignment four, and a scalar uint thread position or the x component of uint3 thread position. Kernel metadata must reference the selected function and both exact argument descriptions. Unknown, duplicate, unused, ambiguous, or mismatched metadata is rejected.

The observation is based on an author's [Apple metalfe AIR 2.7 output](https://gist.github.com/makslevental/8e115ba84489d32bf5c043662a1ba068). That real example operates on half values and multiple buffers, so it is **not a positive fixture for this implementation**. Metadata matching here does not establish general compatibility with Apple's private AIR dialect or runtime ABI.

Supported SSA operations are index `extractelement`/`zext`, `getelementptr` over uint, aligned uint load/store, wrapping integer add/subtract/multiply/bitwise operations, and checked constant shifts/unsigned division. Each SSA value has a tracked type and definition. GEP must use an i64 zero-extension of the exact thread index; LLVM sign-extends narrower GEP indices, so a direct i32 GEP is rejected. There is one block ending in `ret void`. Branches, intrinsics, external functions, `nsw`/`nuw`, atomics, volatile accesses, arbitrary pointer arithmetic, and instruction metadata are rejected. These decisions follow the public [LLVM instruction semantics](https://llvm.org/docs/LangRef.html#getelementptr-instruction).

## Limits and verification

The frontend bounds source to 65,536 bytes, 8,192 tokens, 4,096 AST or metadata nodes, 256 statements/instructions, and depth 64. Both parsing and emitted expression trees are bounded. Failure produces no OpenCL source or successful reflection. Arbitrary third-party LLVM decoding and vendor JIT compilation must run in supervised worker processes: parser limits do not impose time or memory limits inside those external compilers.

`Tools/run-shader-jit-tests.py` builds and executes the frontend tests, emits nine OpenCL fixtures, and compiles/runs generated code as **test-only CPU C++** against 72 independent expected values. Optional actual clang checks those fixtures as OpenCL C 1.2. `--sanitize` enables real ASan/UBSan. Optional `--llvm-as` and `--llvm-dis` assemble and decode the synthetic AIR fixture and require identical lowering after that real LLVM roundtrip. Reports pin source and artifact hashes and reject source changes during a run.

```sh
python3 Tools/run-shader-jit-tests.py --cxx /usr/bin/g++ \
  --sanitize --out ../shader-jit-linux
```

Tests cover arithmetic boundaries, precedence, load/store ordering, source/argument mismatches, unsafe indexing, malformed tokens, duplicate names, resource budgets, SSA type/lifetime errors, AIR ABI mismatches, poison-producing flags, unsupported bitcode, and 2,000 deterministic input mutations. The AIR positive fixture is hand-authored conformance input and remains labelled **synthetic**, including after real LLVM assembly/decoding or GPU execution. Real Apple-compiled render modules are useful negative cases; rejecting them is not evidence of render support.

No test in this runner uses a GPU. Native provider JIT/readback and macOS device registration are separate acceptance results. Passing the frontend, CPU references, LLVM roundtrip, or OpenCL syntax checks cannot establish Tahoe boot, WindowServer acceleration, arbitrary Metal application compatibility, or native 7D41 driver operation.
