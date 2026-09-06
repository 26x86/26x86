# Graphics backend investigation and build evidence

The **host Vulkan engine and its QEMU VMApple MMIO device build and run on
x86_64 Linux/TCG, including Mesa's CPU renderer**. Two missing host paths were
implemented and exercised in an independent checkout: the current ARM vCPU's
IOSurface handoff registers and the guest-programmed firmware RAM framebuffer.
This establishes tested components of the graphics path; a working ARM64
macOS desktop, WindowServer, and complete Metal compatibility remain unverified.

A separate **portable release-profile candidate is now built and verified**
with 26x86's exact core patches 0001 through 0004, followed by the optional
graphics series. The executable is 67,005,136 bytes with SHA-256
`2cad40bfa6d9e50c596697577b3ccaec8d78db4537e7f605e200df25e09ba3b6`.
The checked-in [builder](../tools/build_graphics_backend.py),
[optional patch instructions](../patches/graphics/README.md),
[source lock](../patches/graphics/lock.json), and
[measured candidate evidence](../patches/graphics/evidence-core4.json) make this
integration separate from the initial investigation described below. The
earlier [core3 candidate evidence](../patches/graphics/evidence-core3.json) and
its executable remain unchanged. Neither candidate includes a timer core fix.

The layers in this investigation are Apple's existing guest GPU protocol,
QEMU's device and guest-memory interfaces, the Reims host Rust engine, and the
host Vulkan driver. No macOS kernel, kext, system image, signature, PAC check,
or guest boot instruction was changed or disabled.

The reviewed reference is
[steelbrain-bot/reims-vgpu at 2844274c34baa1043d37995f5b1a9f1d265eae03](https://github.com/steelbrain-bot/reims-vgpu/tree/2844274c34baa1043d37995f5b1a9f1d265eae03).
Its upstream is [steelbrain/reims-vgpu](https://github.com/steelbrain/reims-vgpu),
whose HEAD was `69a57dd69a6958e946c03b73e02db331f330f435` when checked. The
investigation retained the requested reference pin instead of silently
substituting that newer revision.

The other exact inputs are:

- Reims QEMU submodule:
  [e17ddb98f71df5697daf2f830587f672a8f4f5a7](https://github.com/steelbrain/qemu-reims-vgpu/tree/e17ddb98f71df5697daf2f830587f672a8f4f5a7).
- Shader translator:
  [steelbrain/metal2vulkan at 8b78eaca3be72b4e596aa1c790a4cd114ac1e9ec](https://github.com/steelbrain/metal2vulkan/tree/8b78eaca3be72b4e596aa1c790a4cd114ac1e9ec),
  as pinned in the reference Cargo manifest and lockfile. Its upstream HEAD
  was `9e0e99a41dc3cb8bb7e288b531f1698a79fd4b1c` when checked.
- Independent QEMU integration base:
  `ff1d2d19d7e24893e2012d879f8e73077e17b9bd`, matching 26x86's backend base.
  The Reims fork and this base share ancestor
  `b83371668192a705b878e909c5ae9c1233cbd5fb`; they are not interchangeable trees.

The source layout supports Linux/x86 guest PCI plus Vulkan, and macOS/ARM64
guest MMIO plus Metal or Vulkan/MoltenVK. The supplied shell builder explicitly
rejects an aarch64 target on Linux. This is a launcher restriction, but removing
that check alone would not supply the missing MMIO host callbacks.
[Pinned build script](https://github.com/steelbrain-bot/reims-vgpu/blob/2844274c34baa1043d37995f5b1a9f1d265eae03/scripts/qemu-build/qemu-build.sh).

The upstream `backend-metal` default is unavailable on Linux. A real build
with only `backend-vulkan` failed with Rust E0425: `queue_owner.rs` references
`PresentTransaction` while `context.rs` declares it only with `host-window`.
The combination used by the QEMU integration,
`--no-default-features --features backend-vulkan,host-window`, built successfully
without changing the Reims Rust source. Thus the result is specific to that
feature combination; a bare Vulkan-feature build is not reported as working.
[Pinned engine callback](https://github.com/steelbrain-bot/reims-vgpu/blob/2844274c34baa1043d37995f5b1a9f1d265eae03/crates/reims-vgpu/src/backend/vulkan/engine/queue_owner.rs),
[pinned context](https://github.com/steelbrain-bot/reims-vgpu/blob/2844274c34baa1043d37995f5b1a9f1d265eae03/crates/reims-vgpu/src/backend/vulkan/engine/context.rs).

The initial investigation used Rust/Cargo 1.97.1, the pinned Cargo.lock, and an isolated
Cargo cache and target directory. The resulting debug-profile
`libreims_vgpu.a` was 714,405,458 bytes with SHA-256
`7c538aaa8a9e42b57d739862be20a4c6df3814342eb216a8ac9ffada9a5b3ae3`.
This is a build and correctness artifact; it is not an optimized performance
measurement.

Vulkan was forced to `/usr/share/vulkan/icd.d/lvp_icd.json`. `vulkaninfo`
identified `llvmpipe (LLVM 20.1.2, 256 bits)`, Mesa 25.2.8, CPU device type,
Vulkan API 1.4.318. Three upstream known-answer tests then passed serially,
with no ignored tests or skip messages:

- `compute_inc_ssbo_known_result`: compute writes and buffer readback.
- `compute_2d_grid_tiles_global_invocation_xy`: two-dimensional dispatch coordinates.
- `compute_storage_image_rgba8unorm_known_result`: storage-image writes and pixel readback.

The shader compiler and SPIR-V tools were present during these tests. A test
suite returning success after skipping initialization would not be accepted as
software-renderer evidence. The tested inputs were synthetic shader fixtures,
not material taken from a macOS installation.
[Pinned compute tests](https://github.com/steelbrain-bot/reims-vgpu/blob/2844274c34baa1043d37995f5b1a9f1d265eae03/crates/reims-vgpu/tests/vk_engine_compute.rs).

A separate strict experiment also exercised the shader translator rather than
starting with SPIR-V. The pinned, self-authored `float_mul4_add3.air` fixture
was disassembled with the extracted Ubuntu LLVM 18.1.3 `llvm-dis`, translated
by the pinned metal2vulkan library, validated with `spirv-val`, and dispatched
through the Reims Vulkan engine on llvmpipe. Input floats `[1,2,3,4,5,6,7,8]`
produced exactly `[7,11,15,19,23,27,31,35]`; the emitted SPIR-V was 632 bytes.
The process returned zero, emitted no stderr, and could not skip a missing
compiler, Vulkan initialization, translation, validation, or dispatch failure.
The AIR fixture SHA-256 before and after execution was
`92fc46a2f22f55a2fc3f492d6bd4528c045408ab399c9f8558e551dfa9b87374`.
This proves one AIR compute pathway; it does not prove the full Metal API or
the translation of a macOS application's shaders.
[Pinned AIR fixture](https://github.com/steelbrain-bot/reims-vgpu/blob/2844274c34baa1043d37995f5b1a9f1d265eae03/crates/reims-vgpu/tests/fixtures/air/float_mul4_add3.air).

Host dependencies for this path are a Rust toolchain, C toolchain/linker,
Vulkan loader and ICD, and the window-system libraries used by winit at
runtime. Shader translation additionally needs `spirv-val`, and AIR bitcode
needs `llvm-dis`; the translator is a native Rust emitter, not a requirement
to link a host Metal framework. The synthetic compute tests also use `glslc`
or `spirv-as`. These dependencies were downloaded as Ubuntu packages and
extracted under the investigation directory instead of replacing system
packages. The pinned translator declares Rust 1.87 as its minimum.
[Pinned translator manifest](https://github.com/steelbrain/metal2vulkan/blob/8b78eaca3be72b4e596aa1c790a4cd114ac1e9ec/Cargo.toml),
[pinned translator requirements](https://github.com/steelbrain/metal2vulkan/blob/8b78eaca3be72b4e596aa1c790a4cd114ac1e9ec/README.md).

The independently staged QEMU tree imports only these six GPU host files:
`reims-vgpu-mmio.c`, `reims-vgpu-pci.c`, `reims-vgpu-dirty.c/.h`, and
`reims-vgpu-shim.c/.h`, plus their named trace events. Local glue adds the
static-library link, device configuration, and an explicit research-only
VMApple graphics selection. It starts from clean upstream QEMU and applies
26x86's TCG/headless enablement in that separate checkout. It does not build
the complete Reims QEMU fork or use its guest boot scripts, and it imports no
accelerator or x86 kernel-modification code. 26x86's existing native QEMU
checkout, patch series, USB builder, and boot inputs remain separate.

The initial investigation's final QEMU build has TCG enabled and KVM/HVF disabled. Its
debug ELF is 440,925,608 bytes, SHA-256
`b2e9e2bec7ae538a572f6dfe4768ee6d6d71ec8db98b24f5cec1c42035cd5eb8`.
GCC 13 compiled the C code; the final link used extracted Ubuntu LLD 18.1.3.
With `vmapple,research-headless=on,research-graphics=on`, the actual device
realize trace names `backend=vulkan`, and 26x86's self-authored VMApple
CPU/MMU/PAC/IRQ guest passes 12/12 cases. The same final binary with
`research-graphics=off` also passes 12/12 and does not realize the GPU. QARMA5
PAC remains enabled in both executions. These runs use only the fixed authored
guest and blank read-only synthetic flash files, whose hashes remain unchanged.

The pinned MMIO shim starts its Rust host window from device realize,
independently of QEMU's `-display` choice. The advertised `REIMS_VGPU_WINDOW`
environment name is present only in comments at this pin, so it must not be
treated as an implemented off switch. Synthetic startup tests remove
`DISPLAY`, `WAYLAND_DISPLAY`, and `XDG_RUNTIME_DIR` from the child process
environment. A future integration should expose an explicit device property
for host window creation and keep guest scanout processing independent of that
choice; actual USB display presentation still needs its SDL/KMS integration.

The original ARM64 MMIO omission was specific. The pinned callback
`reims_vgpu_mmio_read_xreg()` reads the current publishing vCPU's registers on
Darwin, but returns `-1` on Linux. The local patch uses the currently publishing
ARM CPU's `CPUClass.gdb_read_register` callback and decodes the exact eight-byte
result in the target's byte order. It requires an AArch64 target and an ARM CPU
object, bounds the register index, and rejects missing or short results. It
starts no debugger server, writes no CPU register, and never samples another
CPU or falls back to `first_cpu`.
[Pinned MMIO shim](https://github.com/steelbrain/qemu-reims-vgpu/blob/e17ddb98f71df5697daf2f830587f672a8f4f5a7/hw/display/reims-vgpu-mmio.c).
[QEMU AArch64 core register implementation](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/target/arm/gdbstub64.c).

A self-authored AArch64 guest publishes a synthetic MAP entry through the
actual IOSFC ring producer register. The real Rust `capture_at_producer` path
then calls the host callback. Its trace reports CPU 0 with
`x19=0xfffffe0011223344`, `x21=1`, and `x22=0x5566778899aabbcc`, exactly matching
the fixture; the guest returns from MMIO and exits successfully. The fake
internal address is intentionally unsuitable for a real mapping. This test
proves the synchronous handoff, not IOSurface identity validation, guest KVA
translation, or a complete page mapping. The original page-view callback still
uses Darwin-specific aliasing; Linux's documented GPA-copy fallback needs
further guest-protocol coverage.

The pinned MMIO firmware-console branch returned without copying pixels. The
local display patch calls the existing
`reims_vgpu_qemu_efi_console_copy` ABI when firmware owns the console. It checks
the advertised 1920x1080 geometry, a little-endian 32-bit BGRA-compatible host
surface, source stride and address arithmetic, and explicit depth/length
constraints. Zero depth and length retain the pin's unspecified defaults;
nonzero depth must be 32. The source stride ranges from a tight row to the
backend's existing maximum pixel-row width times four; that padding bound is
local implementation policy, not a claimed Apple ABI limit. Rust validates
every source page as guest RAM. A persistent staging buffer means a refused
or incomplete copy cannot overwrite the last valid display surface.

An actual qtest/QMP experiment passes **11/11 checks** on both the initial
investigation's final binary and the portable combined candidate.
It leaves CPUs stopped, programs synthetic BGRA guest RAM with 64 padding bytes
per row and writes the real MMIO registers. QMP's PPM output matches all
2,073,600 expected RGB pixels, SHA-256
`e0938b00e94ab70d45911ab98c1ec8699a3995d8d3d64514327b50be300fa0de`.
Zero address, short or excessive stride, 16-bit depth, short declared length,
address overflow, a framebuffer aimed at the device's own MMIO, and a span
crossing the end of RAM all preserve the previous valid frame. A subsequent
valid update succeeds. No guest code, Apple firmware, physical display, or
hardware GPU executes in this pixel test. The copy is a firmware-console
memory path, not a Vulkan draw or a Metal acceleration result.

There is also a guest-version limitation in the reference history. Its author
reports that x86_64 macOS 26's PCI-matched Metal plugin lacks an architecture
property used by several icon services, producing an assertion and restart
loop. That is the author's observed x86 pathway result, not a result reproduced
here and not a conclusion about the ARM64 MMIO personality.
[Upstream observation at 260ea24915](https://github.com/steelbrain/qemu-reims-vgpu/commit/260ea24915).

Licensing metadata is inconsistent in the requested Reims pin: its repository
README and LICENSE identify LGPL-3.0-or-later, while `reims-vgpu`,
`reims-vgpu-wire`, and `reims-vgpu-paging` Cargo manifests each identify
GPL-2.0-or-later. The imported QEMU C shims have GPL-2.0-or-later SPDX headers;
metal2vulkan identifies LGPL-3.0-or-later. The investigation preserves those
declarations and records the discrepancy rather than presenting one as an
unambiguous license grant for the whole combined artifact. No combined binary
is published by this work. 26x86's private developer-artifact policy does
not change any upstream license.
[Reims LICENSE](https://github.com/steelbrain-bot/reims-vgpu/blob/2844274c34baa1043d37995f5b1a9f1d265eae03/LICENSE),
[Reims crate manifest](https://github.com/steelbrain-bot/reims-vgpu/blob/2844274c34baa1043d37995f5b1a9f1d265eae03/crates/reims-vgpu/Cargo.toml).

The reference checkout, isolated caches/build trees, imported-file SHA-256
manifest, build logs, exact test commands, and result JSON files are retained
under `work/reims-reference`. The key results are `host-validation.json`,
`air-compute-result.json`, `qemu-firmware-console-build-result.json`,
`qemu-startup-result-final-graphics.json`,
`qemu-startup-result-final-headless.json`, `mapper-handoff-result-final.json`,
and `firmware-console-result.json`.

The bounded host fixes are `qemu-linux-mmio-xreg.patch` and
`qemu-mmio-firmware-console.patch`, applied after the selected-file integration
in that order. The full `qemu-host-integration.patch` is a research-tree diff
against the pinned QEMU base and includes 26x86's TCG/headless prerequisite.
Its static-library/include paths describe this isolated build layout; it is
not a replacement for 26x86's native backend patch series. Reims Rust sources
and Cargo.lock retain their original bytes. ARM64 macOS graphics, WindowServer,
a Metal application, hardware GPU acceleration, physical display/window
presentation, and update compatibility require separate runtime evidence and
are not marked complete by this investigation.

The portable candidate builds in a new directory, leaving the active native
recovery binary and source unchanged. It reads only the six reviewed files
from the pinned Reims QEMU repository; each file, imported trace declaration,
patch, authored probe, Cargo lockfile and source revision is checked against
the optional lock. Every patch passes `git apply --check` before application,
and the resulting changed-path set must exactly equal the expected scope.
The combined diff is retained for review. Core patch 0003 is specifically
`29faaa21e284e82fb3e7848574730627c9c7d55f60a5a2e8bdb3310bad4acd0c`.
The default `patches/series` does not acquire any GPU patches.

The Meson glue accepts `reims_vgpu_library` and `reims_vgpu_include` options
instead of embedding this machine's paths. Reims Rust sources and Cargo.lock
remain unmodified. The observed release static library is 145,703,066 bytes,
SHA-256 `f28b77dfe805c0b41d61f5c526e847687e43cac1e3831fb1d0fabbfca8a98451`.
The candidate uses GCC 13.3, Rust 1.97.1 and LLD 18.1.3, with QEMU C debug
information disabled. Pins make the source inputs reproducible; identical
executable bytes across different toolchain or system-library versions are
not asserted.

On this same combined executable, acceptance passed the authored AIR
translation and eight-value Vulkan result, three upstream compute tests,
CPU conformance **12/12 with graphics on and 12/12 with graphics off**, the
actual three-register mapper handoff, and the firmware console's **11/11**
full-pixel and invalid-input checks. An additional actual virtio-blk BARRIER
test passed **5/5**, including delayed completion and injected EIO propagation.
Seven input/path regression tests passed on Linux with no skipped tests.
These are host device, CPU translation, memory-copy and software-Vulkan
results; they do not establish an Apple guest desktop or storage power-loss
persistence.

After the original complete build run, probe filename escaping was corrected
for QEMU's comma-separated drive options. The entire graphics acceptance suite
was rerun successfully on the unchanged executable with both a space and a
comma in the output directory. The original build and acceptance reports
remain unchanged; `evidence-core3.json` records the revised probe hashes and
both sets of report hashes. A lock change intentionally makes the builder's
strict `--verify-only` reject older candidates; this additional fixed-input
check was invoked directly through the pinned probe entry point.

The first frozen core3 candidate and its detailed reports live in the Linux work
directory `/home/developer/work/venfire-graphics-20260906`; they are marked
`NONREDISTRIBUTABLE DEVELOPMENT ARTIFACT` under project policy. There is no
host-guard bypass compiled or packaged by this builder. The builder snapshots
inputs before building, so another development task cannot silently substitute
a changed core patch mid-build.

The second frozen candidate lives in
`/home/developer/work/venfire-graphics-core4-20260906`. Its lock additionally
includes BDIF patch 0004 with SHA-256
`1d4639c0e845ad0d5a8d9f542c6ed104897f5a69eba95998373770e691a3e541`.
It repeated the complete AIR/software-Vulkan, three upstream compute, CPU
12/12 on and off, mapper-register and 11-case framebuffer acceptance. On this
same executable, BARRIER passed 5/5 and the BDIF COW suite passed 22/22:
disabled/readonly write refusal, AUX and root writes, readback after process
restart, invalid descriptors and injected flush EIO. Original base files
remained unchanged. The full source scope, source hashes, static library and
executable were rechecked after verification; the first candidate's binary
hash was also rechecked unchanged. Seven builder input/path checks passed
again on Linux with the new lock.

The core4 graphics probes use `max,pauth-qarma5=on,cntfrq=24000000` to match the
original Apple DeviceTree frequency identified in the separate
[XNU watchdog investigation](kernel-watchdog.md). This is a runtime CPU option,
not a timer source patch, and it retains the pinned QEMU's integer-period
precision limitation. Future core patches require a reviewed lock update and
another fresh build; these measured candidates remain frozen. Hardware display
integration and actual guest graphics remain separate acceptance steps.
