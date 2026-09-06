# Platform implementation status

The runnable platform now includes portable Mellow objects, a typed MSL/AIR compute frontend,
actual LLVM bitcode decoding, reusable host OpenCL pipelines, bounded MSL render objects and
a native Windows OpenGL provider, plus source-derived Xe memory code.
The kext also contains an opt-in Tahoe diagnostic service. The current record is
[VERIFICATION-METAL-JIT-2026-09-06](VERIFICATION-METAL-JIT-2026-09-06.md).
The graphics contract is [RENDER-IMPLEMENTATION](RENDER-IMPLEMENTATION.md).
The source-bound [render integration record](../validation/render/integration.json) indexes the
actual frontend, provider, object, client and report-control evidence.
Full Apple Metal ABI compatibility, native Tahoe GPU execution and WindowServer remain incomplete.

## Implemented and exercised

- `Runtime/RenderShaderJit.*`: checked MSL vertex/fragment source lowers to GLSL330.
  Float/vector types, three-vertex arrays, a shared float4 parameter and fragment position are
  bounded and validated. Clip-depth, fragment-coordinate and readback-row transformations are
  explicit. Current [Windows](../validation/render/frontend-windows.json) and
  [Linux sanitizer](../validation/render/frontend-linux-sanitized.json) tests pass 969 frontend checks.
  Render AIR, sampled textures and user varyings are not implemented.
- `Runtime/RenderObjects.*`: explicit C++ render device, RGBA8 texture, library/functions,
  retained pipeline, command queue/buffer and encoder. Windows offscreen tests passed 1,000
  MSL frames, 16,050 native assertions and 27 negative API cases with one driver program build.
  The [offscreen pixel oracle](../validation/render/objects-offscreen.json) checked all
  3,072,000 pixels from 12,288,000 actual RGBA bytes.
  Each frame had at least 572 foreground pixels. Across the run, 1,016 subpixel-boundary pixels were checked
  against a restricted clear-or-valid-fragment rule, not skipped. A separate
  [120-frame visible run](../validation/render/objects-visible.json)
  checked all 368,640 pixels and swap API acceptance. Neither run passed an oracle to the
  runtime. Actual readback PNGs and complete raw streams accompany the runner reports.
- `Runtime/OpenGLProvider.*`: a private worker owns an isolated WGL context/window, verifies
  a non-generic accelerated pixel format and core3.3 profile, compiles GLSL programs and checks
  FBO rendering, real fences, context identity, readback and per-frame cleanup. Native GLSL
  provider tests separately passed 1,000 offscreen and 120 visible frames. Driver identity is
  Intel(R) Graphics / 32.0.101.6737; renderer strings do not establish a PCI device ID.
  Invalidated/failed contexts clear discovery claims, and retained pipelines cannot revive in
  a new epoch. Six provider-report and seven object-report control tests pass without a GPU.
  [Linux compilation](../validation/render/objects-linux-build.json) succeeds; native GL execution
  is explicitly Windows-only. [Report controls](../validation/render/report-controls.json) remain software-only.
- `Runtime/MetalObjects.*`: explicit portable C++ Device/Buffer/Library/Function/Pipeline/Queue/
  CommandBuffer/ComputeEncoder. One immutable-size uint buffer, exact 1D dispatch, retained
  pipeline compilation and synchronous completion. Ordinary workloads do not need an expected
  answer. Windows MSL and raw AIR paths each passed 10,000 GPU submissions and independent
  readbacks, each with one driver compilation and two additional ordered encoder dispatches.
- `Runtime/ShaderJit.*`: actual typed MSL AST and a separate AIR2.7 SSA/metadata frontend,
  emitting OpenCL C for the documented compute subset. Windows/Linux tests pass 2,269 parser
  checks and 72 independent CPU references; clang verifies nine generated CL1.2 fixtures.
- `Runtime/AirDecoder.*`: actual LLVM C API parse/module verification/assembly printing,
  using an explicitly selected LLVM18–20 library. Raw or wrapped bitcode is decoded; the
  compiler then validates AIR semantics. Positive AIR fixtures are synthetic, including the
  actual LLVM/GPU runs. Real SDL render metallibs are decoded and rejected as unsupported.
- `Mellow/TahoeDiagnostic*`: exact 8086:7D41 PCI service, bounded admin IOUserClient and
  existing IOKit prepared-DMA backend integration. Query-only if an attached device IOMapper
  cannot be admitted. Production protocol tests pass 6,328 checks on Windows and ASan/UBSan
  Linux; the IOKit path has been cross-linked but not executed on Tahoe.

- `Runtime/PlatformRuntime.hpp/.cpp`: bounded provider/route policy, resource transition admission,
  reset-generation completion checks and cache identity. 108 synthetic policy checks pass with
  ASan/UBSan. Direct OpenCL C is explicit and cannot satisfy the default Metal translation route.
- `Runtime/OpenCLProvider.*`: actual OpenCL context/queue/compiler/buffer/event ownership.
  It validates a bootstrap workload before advertising Compute/OrderedQueue, then uses MellowRT
  planning and completion correlation for real dispatches. Its input is OpenCL C 1.2 and one
  in-place uint buffer. The `executeOpenClC` acceptance adapter additionally requires an
  independent reference; ordinary retained `executePipeline` does not. MSL/AIR translation
  belongs to the separate ShaderJit layer above this provider.
  Windows Intel driver 32.0.101.6737 reports 8086:7D41 through its advertised Intel query extension.
  Its final Windows stress run verified 10,000 consecutive submissions (2,560,000 uint results),
  matching independent expected/readback stream hashes, on one queue/device/session epoch.
  Seventy injected lifecycle checks, including reusable pipeline ownership, pass under
  ASan/UBSan. Retained pipelines complete without oracle evidence flags; the earlier oracle
  adapter remains backward compatible. New object report controls also pass six tests.
- `Drivers/PortedXe/`: Linux Xe page-entry algorithms (six unchanged function bodies) and adapted
  scatter/gather GGTT mapping/clear loops with pin, write, invalidation and release contracts.
  Addresses/PAT/permissions are validated. Host and actual QEMU Linux guest tests each pass
  18,721 checks; their MMIO/DMA/invalidations are simulated boundaries.
- `Mellow/XeMemory.cpp` and `PortedXeBindings.cpp`: call the ported PTE/PDE encoding inside the
  existing kext source target while preserving its 46-bit, 4K, system-memory and read-only contract.
  The actual 33-unit cross build now produces Mellow.kext 0.4.3, including the diagnostic service.
  All 426 kernel/Lilu imports have declared and exported providers in the inspected Tahoe
  25G83 Recovery and Lilu artifacts. Native kernel-linker execution remains untested.
- `Tools/mellow-port.py` and `Tools/mellow_port/`: source intake, hashes, licensing facts,
  lexical inventory, gap reports and limited integer extraction. Eleven tests pass. The separate
  PortedXe subsystem is a reviewed manual port, not output demonstrating automatic driver conversion.

## What has not been implemented or validated

Apple Objective-C Metal protocol conformance, general MSL/AIR/metallib compatibility,
render AIR, general texture sampling/storage, a blit encoder, cross-API resource sharing, complete LinuxKPI/DRM and vendor
driver ports, NVIDIA/AMD binding, system Metal registration and WindowServer integration
remain work. The C++ compute and render objects implement separate narrow opt-in subsets.
RenderDevice chooses the GL provider explicitly; the shared route policy does not automatically
combine GL rendering and OpenCL compute or establish interop between their resources.
Windows SwapBuffers acceptance does not prove physical scanout, cursor-plane operation or macOS
compositor acceleration.

The diagnostic service can call the real IOKit DMA preparation APIs when a device mapper is
admitted, but no actual Darwin mapping has been observed on hardware. Physical GGTT publication,
GuC authentication, context submission, GPU interrupts/fences and reset recovery are not connected
into a working native GPU owner. Host protocol callbacks are explicitly simulated. The Windows
OpenCL and OpenGL providers use the installed Intel Windows driver and do not run the Darwin kernel code.

No physical Tahoe host was available for this verification. Actual kext loading, installation,
Recovery GUI, Metal compute/render/stress, WindowServer and sleep/wake have not passed.
The separate QEMU Recovery experiment reached boot.efi/kernel collection loading, not a verified
XNU boot or Recovery desktop. QEMU algorithm tests do not close that boot blocker.

## Reproduce the implemented paths

Python 3.9 or newer and a C++17 compiler are required for the portable source/tool tests.

```sh
python3 Tools/run-platform-tests.py --cxx g++ --out build/platform-tests --sanitize
python3 -m unittest discover -s tests -p test_mellow_port.py -v
python3 Tools/run-ported-xe-tests.py --cxx g++ --out ../ported-xe-tests
python3 Tools/run-opencl-runtime-regressions.py --cxx g++ --out build/opencl-regressions --sanitize
python3 Tools/run-shader-jit-tests.py --cxx g++ --sanitize --out ../shader-jit-test
python3 tests/air_decoder_tests.py
python3 tests/shader_cli_controls.py
python3 Tools/run-render-shader-tests.py --cxx g++ --sanitize --out ../new-render-shader-tests
python3 Tools/run-opengl-provider.py --cxx g++ --out build/opengl-provider-compile
python3 Tools/run-render-objects.py --cxx g++ --out build/render-objects-compile
python3 tests/opengl_provider_report_tests.py
python3 tests/render_objects_report_tests.py
```

On Windows with an installed Intel OpenCL driver and MinGW compiler:

```powershell
python Tools/run-opencl-runtime.py --cxx C:/msys64/mingw64/bin/g++.exe --out build/opencl-runtime --compute
python Tools/run-opencl-runtime.py --cxx C:/msys64/mingw64/bin/g++.exe --out build/opencl-stress --compute --iterations 10000 --timeout 180
python Tools/run-metal-objects.py --cxx C:/msys64/mingw64/bin/g++.exe --out build/msl-objects --compute --iterations 10000
python Tools/run-render-objects.py --cxx C:/msys64/mingw64/bin/g++.exe --out build/msl-render --render --frames 1000
python Tools/run-render-objects.py --cxx C:/msys64/mingw64/bin/g++.exe --out build/msl-render-visible --render --visible --frames 120
```

Omit `--compute` or `--render` for compile-only validation. Actual driver calls are supervised in a separate
process with a deadline. Driver failure, unexpected device identity, event ownership mismatch,
readback mismatch or cleanup failure cannot produce successful runtime completion.

The platform workflow includes render frontend sanitizers, compile-only provider/object builds
and Python report controls. It never requests GPU rendering on hosted CI. Local results above
are not a hosted Actions pass: the account billing restriction currently prevents a confirming
CI run, so hosted CI success is not claimed.

Use [run-ported-xe-emulator.py](../Tools/run-ported-xe-emulator.py) from Linux/WSL with QEMU and
an explicitly supplied Linux kernel. It boots an initramfs and runs the compiled tests as a child
of guest PID1. Success requires the exact guest protocol, nonzero checks, expected scope flags,
process/VM exits and stable input/source hashes. It is not a Xe GPU device model.

## Historical evidence

[platform-foundation.json](../validation/platform-foundation.json) describes the earlier 102-check
policy/intake snapshot. [opencl-windows-substrate.json](../validation/opencl-windows-substrate.json)
is the earlier independent probe, which bypassed MellowRT. Their recorded source hashes and scope
remain historical; use the current verification record for the integrated provider and port.
