# 26x86 abstraction binaries

An abstraction binary is a native adapter with an explicit OS build, CPU
architecture, runtime ABI identifier, source revision, license, and SHA-256.
It is separate from OpenCore firmware and from the EFI Apple Silicon Sandbox.
A native x86_64 adapter does not provide an ARM64 kernel execution engine.

The current implementation validates packages read-only. No native adapter has
been registered for macOS 27. The root patch preflight therefore stops macOS 27
before entering the legacy patch detector. macOS 26 keeps its existing hardware
patch detection path. Passing an explicit abstraction manifest requires an
implemented adapter; a valid hash alone never authorizes root writes.

Use `x86.patch.abstraction.validate_manifest(path, target_major=27,
os_build="26A5425a", architecture="x86_64", expected_abi="adapter-owned-abi")`
for inspection. `root.preflight(..., abstraction_manifest=path)` and
`root.apply(..., abstraction_manifest=path)` enforce the integration gate.
The build above is an example of exact binding, not a support claim.

The UTF-8 JSON manifest schema is `26x86.abstraction/1` and requires:

- `adapter`: a bounded lowercase identifier registered in project code.
- `target`: `macos_major` (26 or 27), exact `os_build`, `architecture`
  (`x86_64` or `arm64`), and a nonempty `runtime_abi`.
- `files`: 1–64 entries containing relative POSIX `path`, `kind` (`kext` or
  `dylib`), lowercase `sha256`, `license`, and `source` with HTTPS `url` and
  immutable hexadecimal `revision`.

Each file must be a thin little-endian Mach-O 64 for the declared architecture
and file type. Load-command bounds are checked. Paths outside the package,
symlinks, duplicate paths, duplicate JSON fields, invalid hashes, and target
mismatches are rejected. An OS update requires a new matching package and ABI
validation. The validator never loads code, mounts an APFS volume, copies Apple
binaries, or treats self-declared manifest evidence as hardware verification.

[Mellow source](https://github.com/NiSeullent/Mellow) is available separately.
Its current kernel path is an opt-in Tahoe PCI/IOUserClient/DMA diagnostic path
for Intel Xe-LPG bring-up. Its explicit C++ Metal objects and MSL/AIR subset
translation use accelerated OpenGL/OpenCL providers. These are separate from
Apple Objective-C Metal ABI, system MTLDevice registration and WindowServer.
Those latter integrations are not claimed as completed by upstream.

The reusable integration pattern is hardware-family selection, an explicit
provider capability set, reset/queue/completion identity, and shader cache keys
that bind frontend, lowering, backend, driver and resource ABI. A future native
adapter must also bind the installed OS build and actual Mach-O CPU. Mellow's
x86_64 kext cannot be relabeled as a macOS 27 ARM64 driver.

Mellow's root LICENSE and NOTICE specify TSNPL 1.0, with separate licenses for
Lilu, MacKernelSDK and expressly identified original MIT files. No Mellow code
or binary is copied or relicensed into 26x86 by this change.

PatcherSupportPkg and MetallibSupportPkg offer an optional `--artifact-receipt`
entry point that hashes an existing payload without executing their patching
pipeline. `26x86.support-artifact/1` receipts bind exact OS build, declared host
architecture, runtime ABI, artifact, source revision and license text identity.
The `gpu-compiler-abi` role additionally binds the actual compiler binary; it is
not a native kext/dylib abstraction. Use `x86.patch.artifact_receipt.verify_receipt`
to compare the receipt with independently selected target values and local
files. A receipt is identity evidence, never installation authorization or
proof that an ARM kernel runs on an x86 CPU.

Validation: `python -m unittest x86.patch.test_abstraction` checks OS update
invalidation, actual Mach-O architecture, tampering, load-command bounds, path
traversal, duplicate keys, and the macOS 27 preflight gate. Its synthetic Mach-O
fixture is deliberately not executable compatibility evidence.
