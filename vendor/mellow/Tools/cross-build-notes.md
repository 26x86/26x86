# Reproducible cross build

This builds the **actual Mellow Xcode target** as a thin x86_64 research kext.
It does not establish that Tahoe can resolve its imported KPI/Lilu symbols,
load it, attach a GPU accelerator, or execute Metal. No load or installation
commands are included.

Windows prerequisites: Python 3, 7-Zip, and an **existing** WSL Ubuntu 24.04
installation. `cross-build-toolchain.ps1` downloads about 375 MiB into the
specified directory and verifies pinned SHA256 digests. The LLVM installer is
only opened as an archive. There is no global installation or distro creation.
The extracted cctools-port linker uses the existing WSL C++/UUID runtime and a
local TAPI library. Its optional LLVM LTO library is unnecessary because no LTO
objects are produced.

From the workspace directory in PowerShell:

```powershell
& './outputs/Mellow-7D41-integration/Tools/cross-build-toolchain.ps1' -ToolchainDirectory './work/mellow-build'
python './outputs/Mellow-7D41-integration/Tools/cross-build.py' --llvm-bin './work/mellow-build/llvm-20.1.8/bin' --output './work/mellow-build/Integration-Release' --configuration Release --darwin-linker './work/mellow-build/ld64-prefix/bin/x86_64-apple-darwin13.4.0-ld' --wsl-distro Ubuntu-24.04
python './outputs/Mellow-7D41-integration/Tools/validate-macho.py' './work/mellow-build/Integration-Release/Mellow.kext' --output './work/mellow-build/Integration-Release/macho-validation.json'
python './outputs/Mellow-7D41-integration/tests/build_macho_validation.py' './work/mellow-build/Integration-Release/Mellow.kext/Contents/MacOS/Mellow'
```

The compiler source list is extracted from `PBXSourcesBuildPhase`, rather than
building a substitute probe. All listed C++ units, real Lilu plugin startup,
standard generated KMOD metadata, and the vendored `libkmod.a` are linked.
The metadata preserves the real start/stop functions and gets its identifier
and version from the source Info.plist. All source/object hashes and complete
commands are recorded in the JSON build report.

Cross compilation uses C++17, `-mkernel`, `-fapple-kext`, no C++ exceptions/RTTI,
no red zone through kernel code generation, and Release `-O3`. It preserves
both `__mod_init_func` and `__mod_term_func`. LLVM 20 requires
`-mllvm -disable-atexit-based-global-dtor-lowering` to preserve the kernel
destructor convention; no destructors or driver functionality are replaced
with stubs. The original upstream Xcode project's SIMD/vectorization options
are intentionally not copied into this cross configuration, to retain kernel
code generation defaults. Native Xcode parity has not been tested.

`ld64.lld` is **not** a substitute for Apple's linker here. It accepts the
command but warns that `-kext` and `-static` are unimplemented, and can return
exit code zero while emitting an ordinary MH_EXECUTE binary. The validator
rejects it. The real Darwin linker used here is cctools-port ld64 609, packaged
by conda-forge, and emits MH_KEXT_BUNDLE with retained relocations for kernel
linking. Undefined imports are inventoried, not assumed to resolve on Tahoe.

Debug `-O0` compilation is useful for source checks but currently imports
`___memcpy_chk` from the SDK's fortified inline copy routines. This has not
been validated as a Tahoe KPI; the structural validator rejects it. Release
optimization folds those calls without disabling the SDK's bounds checks.
Only the Release artifact is a candidate for subsequent native validation.

`cross-build-native.sh Release` performs a native Xcode build on macOS and
uses the same structural validator. This native path has not been run here.
It produces an unsigned artifact and does not load it or rebuild a kernel
collection. A structural pass is a necessary format check, not a claim of
loadability, compatibility, display output, or GPU acceleration.

Primary references:

- [LLVM 20.1.8 official release](https://github.com/llvm/llvm-project/releases/tag/llvmorg-20.1.8)
- [Clang cross compilation](https://clang.llvm.org/docs/CrossCompilation.html)
- [LLVM Mach-O linker output kinds](https://github.com/llvm/llvm-project/blob/llvmorg-20.1.8/lld/MachO/Driver.cpp)
- [LLVM kernel static-destructor convention](https://github.com/llvm/llvm-project/blob/llvmorg-20.1.8/llvm/lib/CodeGen/TargetLoweringObjectFileImpl.cpp)
- [cctools-port source pinned by this ld64 package](https://github.com/tpoechtrager/cctools-port/tree/04663295d0425abfac90a42440a7ec02d7155fea)
- [conda-forge recipe commit for this exact ld64 package](https://github.com/conda-forge/cctools-and-ld64-feedstock/tree/7e3eea1272320f22d55523e63902f9a4696121be)
- [Apple KMOD wrapper example](https://github.com/apple-oss-distributions/xnu/blob/main/security/mac_policy.h)
