# Guest Metal compute probe

Layer: actual macOS user-space Metal API. This independently authored probe
compiles a small MSL function, submits two command buffers, and checks 512 GPU
results, unchanged inputs and prefix/suffix guards after status `Completed`.
There is no CPU fallback. A 90-second process alarm bounds blocking calls;
each command also has a 20-second polling budget. Failure returns nonzero.

The x86_64 and arm64 ABI declarations are a small public FFI surface, not extracted SDK
headers. The probe dynamically loads the installed Foundation, Objective-C and
Metal libraries. Its link stub declares only the public libSystem calls used.
It does not alter guest policy, inject a kext, or install a framework.

Sources checked before implementation:

- [Apple GPU compute sequence](https://developer.apple.com/documentation/metal/performing-calculations-on-a-gpu).
- [Shared resource synchronization](https://developer.apple.com/documentation/metal/mtlstoragemode/shared).
- [Public Metal-cpp headers, fixed revision](https://github.com/apple/metal-cpp/tree/27c4382b7151d55a51692cdcb27aaa98752240de):
  `MTLCommandBuffer.hpp` enum values, `MTLResource.hpp` shared options,
  `MTLTypes.hpp` three UInteger dimensions and `MTLComputeCommandEncoder.hpp`
  by-value dispatch arguments. Only their API declarations inform this code.
- [Apple ARM64 ABI](https://developer.apple.com/documentation/xcode/writing-arm64-code-for-apple-platforms):
  fixed typed Objective-C calls must use the target's aggregate argument rules;
  treating the encoder call as a C variadic call is incorrect on this target.

Build with `python3 tools/build_metal_probe.py --output <fresh-directory>`.
The default `--target tahoe-x86_64` retains macOS 26 x86_64 output. Select
`--target golden-gate-arm64` for macOS 27 arm64 output. This is ordinary arm64,
not an arm64e/PAC profile or evidence of running AMD64 code on Apple Silicon.
The host needs Clang, LLVM's Darwin linker and llvm-objdump. This builds a
Mach-O executable with an ad-hoc code signature. CPU type, PIE and the exact
minimum OS/SDK load command must match the requested target. Compilation and Mach-O
inspection do not prove that macOS loaded or ran it. The build receipt retains
that distinction. Run `./nxmetal` inside the macOS guest and preserve the entire
NDJSON output and exit status. The final success line must follow two actual
completed command statuses and two readback passes.

This proves only this guest's compute workload. Host Vulkan adapter/submission
evidence is separate, and native HAL, full Metal conformance, rendering and
physical Mac acceptance are not implied.
