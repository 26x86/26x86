# AIR input decoding and evidence

This is the **user-space compiler input layer**. There are two real decoding paths:

- `Runtime/AirDecoder.cpp` loads an explicitly selected LLVM C API library, parses raw/wrapped
  bitcode in a fresh LLVM context, calls the LLVM verifier, prints bounded assembly, then releases
  the module, input buffer and context. `ShaderJit::compileAir(..., absoluteLlvmLibrary)` validates
  and lowers the resulting AIR SSA. `MellowMTL::Device::newLibraryWithAir` uses this path.
- `Tools/mellow_air.py` validates known executable metallib containers, function offsets and
  SHA256, or raw/wrapped bitcode, then runs an actual `llvm-dis` child with a deadline and output
  size supervision. `Tools/mellow-shader.py` connects the decoded assembly to the compiled
  `Tools/shader-jit-cli.cpp` translator. This CLI path emits OpenCL C; it never claims GPU execution.

The C API declarations follow LLVM's public [Core.h](https://github.com/llvm/llvm-project/blob/llvmorg-20.1.8/llvm/include/llvm-c/Core.h),
[BitReader.h](https://github.com/llvm/llvm-project/blob/llvmorg-20.1.8/llvm/include/llvm-c/BitReader.h)
and [Analysis.h](https://github.com/llvm/llvm-project/blob/llvmorg-20.1.8/llvm/include/llvm-c/Analysis.h).
`LLVMParseBitcodeInContext2` performs eager parsing without transferring ownership of the input
buffer. `LLVMVerifyModule` uses public `LLVMReturnStatusAction` and its message is disposed.
No Apple compiler binary or private compiler function is invoked.

## Supported inputs

Raw LLVM magic and version-zero wrappers follow the documented
[LLVM bitcode wrapper](https://llvm.org/docs/BitCodeFormat.html#bitcode-wrapper-format).
Input is at most 4 MiB; wrapper offset/size and zero padding are checked before any LLVM call.
The native decoder admits LLVM C API major versions 18–20 and limits printed frontend input to
64 KiB. Reading valid LLVM IR is distinct from accepting an AIR shader: the separate
[MSL/AIR contract](SHADER-JIT-IMPLEMENTATION.md) requires a very narrow uint compute ABI.

The Python metallib reader supports the observed executable container versions 2.2 and 2.4,
with fixed MDSZ entries and known tags. Section order, boundaries, inter-section gaps, tag counts,
duplicate names/tags, metadata boundaries, per-function bitcode SHA256 and wrapper contents are
checked. Unknown layouts/extensions are rejected. It does not silently scan for a magic number.
Layout evidence comes from the primary implementation
[MetalLibraryArchive](https://github.com/YuAo/MetalLibraryArchive/tree/de573ba4a7b986bbecb3e4ce2464945d266a28e9)
and actual SDL fixtures with [pinned provenance](../tests/fixtures/air/provenance.json).
Container decoding does not grant semantics to unknown shaders.

## Actual verification and fixture origin

The included `synthetic-uint-affine.ll` is hand-authored test input. Its `.bc` was generated with
actual Ubuntu LLVM18.1.3 `llvm-as`, then decoded by LLVM and executed through the Mellow pipeline
on the Windows Intel GPU. It computes `x * 7 + 3`. This is useful execution evidence, but is not
an Apple-compiler-produced positive fixture or general metallib compatibility proof.

The two SDL fixtures are extracted unchanged from the macOS arrays in the pinned upstream
`Metal_Blit.h`; their zlib license is included. The actual vertex and fragment modules decode
through LLVM but fail the compute frontend. We have not run their render workloads.

`tests/air_decoder_tests.py` covers 17 container/process tests, including all truncations of a
synthetic container, HASH errors, undocumented section gaps, output write failure and path alias.
`tests/shader_cli_controls.py` covers nine report/process tests, including strict field allowlists,
entry/format binding, unknown evidence claims, duplicate keys, nonfinite JSON, exit mismatch,
source changes, timeout and running output overflow. Synthetic compiler stubs are used only in
those failure tests. `Tools/run-air-decoder-native-tests.py` separately tests the actual LLVM DLL.

## Windows LLVM lifetime correction

Actual LLVM-C 20.1.8 testing exposed exit `0xC0000005` after the DLL was unloaded, both for accepted
and rejected shaders. An independent load/unload test reproduced the crash without parsing.
Keeping the DLL mapped removed it. The native decoder now pins its selected DLL for process
lifetime with `GetModuleHandleExW`; normal load references remain balanced. This keeps LLVM's
code available during process termination and avoids calling process-global `LLVMShutdown` on
another client's live LLVM state. The precise internal crashing callback was not identified.
Windows documents the pin behavior in [GetModuleHandleExW](https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-getmodulehandleexw).

The tested DLL is the unmodified `bin/LLVM-C.dll` from LLVM20.1.8, SHA256
`b84e81d2ffa8fb030b58f1d9ad75ef3ab37f63cd094993c302d9efb34242eaf1`.
It remains a separately supplied dependency; the release does not bundle it.

LLVM's in-process parser/verification/printing can allocate memory before Mellow checks the
printed text length. It is not a sandbox or a hard memory limiter. Shader compilation and vendor
GPU calls belong in a supervised worker, as used by the actual GPU runner. A timeout or crash
cannot be converted into successful GPU or Metal evidence.

## Reproduce

```powershell
python Tools/run-metal-objects.py --cxx C:/msys64/mingw64/bin/g++.exe --out build/raw-air-test --compute --iterations 10000 --air-bitcode tests/fixtures/air/synthetic-uint-affine.bc --entry air_affine --llvm-library C:/path/to/LLVM-C.dll
python Tools/run-air-decoder-native-tests.py --compiler C:/msys64/mingw64/bin/g++.exe --llvm-library C:/path/to/LLVM-C.dll --output-dir build/air-native-test
```

For the separate toolchain decoder, compile the CLI with a native C++17 compiler:

```sh
g++ -std=c++17 -O2 Runtime/ShaderJit.cpp Runtime/AirDecoder.cpp Tools/shader-jit-cli.cpp -ldl -o build/shader-jit-cli
python3 Tools/mellow-shader.py tests/fixtures/air/synthetic-uint-affine.bc --format air --entry air_affine --llvm-dis /absolute/path/llvm-dis --translator "$PWD/build/shader-jit-cli" --report build/new-lowering-report.json
```

Use a new report path. A successful result is `LOWERED_OPENCL_C_ONLY`; the actual GPU evidence
comes from the object runner, not from a compiler or container parser exit code.
