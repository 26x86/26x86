# Optional Reims graphics candidate

This directory is deliberately outside the default `patches/series`. Its
separate series is applied only by `tools/build_graphics_backend.py`, after the
exact core patches listed in `lock.json`. The builder uses a fresh work
directory and never changes an active native backend.

The current core-0001/0002/0003/0004 candidate has been built and exercised end
to end. [`evidence-core4.json`](evidence-core4.json) records its 67,005,136-byte
executable, source audit, exact input hashes and measured results. It passes
the complete graphics acceptance suite, five virtio BARRIER cases and 22 BDIF
COW checks, including restart readback and injected flush failure. The graphics
CPU probes use `cntfrq=24000000`; this build contains no subsequent timer core
patch. Graphics remains explicitly opt-in.

The earlier core-0001/0002/0003 candidate remains unchanged;
[`evidence-core3.json`](evidence-core3.json) records its executable SHA-256,
source pins and measured results. Its 67,002,152-byte release executable passes
the complete graphics acceptance suite and five additional storage BARRIER
cases. The later BDIF-write patch 0004 is not included in that frozen result.

The source layers are QEMU's VMApple/MMIO device interfaces, the Reims host Rust
engine, and the host Vulkan loader/ICD. The import consists of exactly six named
GPU host files and their trace declarations from the pinned Reims QEMU tree.
Each imported file is checked against its reviewed SHA-256 before it is added.
No accelerator code, guest kernel patch, signature/PAC bypass, Apple image, or
Reims guest boot script is imported.

The three optional patches provide:

1. Meson dependency options and explicit `research-graphics=on` machine selection.
   The default remains off. `research-headless=on` is also required; the
   experimental Reims device is never represented as Apple's host framework.
2. The synchronous current ARM vCPU register callback for the IOSurface handoff.
3. Bounded firmware RAM-framebuffer copying through the existing Reims ABI,
   with staging so unsuccessful copies preserve the prior valid frame.

The Meson options `reims_vgpu_library` and `reims_vgpu_include` receive absolute
dependency paths from the builder invocation. No patch embeds a machine's home
directory or build location. Source pins, Cargo.lock, feature selection, patch
hashes, named-file import hashes and authored probe hashes are in `lock.json`.
This pins source inputs; toolchain and host library versions are also recorded,
but byte-for-byte builds across different toolchains are not claimed.

Run from a source checkout on Intel x86_64 Linux with OS-visible AVX2. Windows
development can invoke the same command inside WSL:

```sh
python3 tools/build_graphics_backend.py \
  --work /absolute/path/to/new-graphics-build --jobs 8
```

Required build tools include Rust/Cargo (upstream minimum Rust 1.87), a C
toolchain, Git, Ninja, Python's venv support and the GLib/Pixman development
dependencies required by QEMU. Acceptance additionally requires AArch64 GNU
binutils, `glslc`, `spirv-as`, `spirv-val`, `llvm-dis`, `vulkaninfo`, a Vulkan
loader and Mesa's software Vulkan ICD. `--tool-bin` and `--library-dir` can be
repeated for locally extracted tools and shared libraries. `--vulkan-icd`
selects its JSON; the acceptance suite explicitly requires a CPU Vulkan device.
`--linker lld` uses `ld.lld` found in that tool path. Nothing is installed
globally by this builder.

The Rust release profile is the default and retains upstream's optimized
settings and unwind behavior. `--rust-profile debug` supports investigation.
The QEMU executable keeps TCG and QARMA5 support, disables KVM/HVF, and does not
include C debug information. It supports headless/QMP/VNC display inspection;
this candidate builder does not establish SDL/KMS physical USB presentation.

Optional `--qemu-reference`, `--reims-reference`, and
`--reims-qemu-reference` reuse an existing repository's Git objects read-only;
uncommitted working files are never copied. Those repositories must remain
available while the shared clones are in use. Omit them for independent network
fetches. `--cargo-cache` explicitly selects a reusable, writable Cargo cache.
The fresh source trees, Rust target directory, QEMU build, generated patch and
test evidence always belong to the new work directory.

The builder runs fixed-input acceptance by default: an AIR known-answer
translation/dispatch, three upstream compute tests with skip detection, the
12-case bundled CPU guest with graphics both on and off, the actual IOSFC
mapper-register handoff, and 11 qtest/QMP framebuffer checks. The latter keep
the CPUs stopped and compare all 1920x1080 pixels. There is no guest-image
option. A completed candidate can be checked again with `--verify-only`, the
same work path, and its required tool/library paths. A changed executable or
different lockfile is rejected.

QEMU drive filenames escape commas. The frozen core3 candidate was rechecked with
the corrected harness in an output directory containing both spaces and a
comma; all graphics checks passed again. The original build report remains
unchanged, and the compact evidence records both harness versions. A changed
lockfile requires a new build for the strict `--verify-only` route.

Every generated candidate is marked `NONREDISTRIBUTABLE DEVELOPMENT ARTIFACT`
under Venfire's project distribution policy. This does not change upstream
licenses, add restrictions to GPL/LGPL rights, or claim to prevent modified
forks. It includes no runtime host-guard bypass. Deployment of an Apple guest
still uses Venfire's host authorization and immutable-input/trust checks.

Upstream license metadata is recorded without resolving it by assumption:
Reims README/LICENSE identify LGPL-3.0-or-later while its Cargo crate manifests
identify GPL-2.0-or-later; the imported QEMU files carry GPL-2.0-or-later SPDX
headers, and metal2vulkan identifies LGPL-3.0-or-later. The original checkouts
retain their license files. See `docs/graphics.md` for exact pins, source links,
measured acceptance and the remaining macOS/physical-display boundaries.
