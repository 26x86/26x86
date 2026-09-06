> **Historical record — preserved unedited.** Component documentation for the hand-written
> Intel Xe backend, which compiles into the kext but has no call path
> ([Mellow/RuntimeReadiness.hpp:84](../Mellow/RuntimeReadiness.hpp)). Scheduled to move to
> `docs/backends/xe/` in P1. For how these modules map onto the vendor-neutral abstraction
> see [MGAL.md](MGAL.md); for the current architecture see [ARCHITECTURE.md](ARCHITECTURE.md).

# Intel Zebin loader and kernel staging

`Mellow/XeZebin.hpp` and `.cpp` implement a bounded native C++ loader for the
actual `compiler-evidence/mellow_evidence_mtl.bin` produced by Intel ocloc
26.27.39122.11 / IGC 2.38.2. The file is a 6,944-byte ELF64 IntelGT relocatable
object. Its sole executable section contains 1,216 bytes of EU instructions;
the `mellow_evidence` function symbol describes 1,040 bytes. The remaining text
bytes are preserved rather than trimmed by guessing an instruction boundary.

This code prepares **CPU staging buffers**. It does not emit a compute walker,
submit ELF contents to a command ring, program a GPU context, publish a page-table
root or report GPU execution. Successful staging cannot satisfy the existing
submission backend's hardware readiness requirements.

## What the implementation does

`Image::parse` validates ELF class, byte order, IntelGT machine, relocatable type,
section-table bounds, file-backed section overlap, names, symbols, alignment and
record sizes. Fixed limits bound sections, symbols, segments, relocation patches
and metadata text. Extended ELF numbering, program headers, unknown allocated
sections and unsupported execution metadata are rejected. The input is borrowed
and must remain immutable for the entire parse/stage lifetime. The class does not
accept ownership of mutable user memory.

The metadata reader implements the specific `.ze_info` 1.73 `mellow_evidence`
profile. It parses every execution field and argument offset used by that
kernel, checks duplicates and overlapping payload ranges, and requires the
expected global pointer/scalar arguments, workgroup walk order, SIMD32, 128 GRFs,
32-byte inline payload, 192-byte per-thread local-ID data and disabled mid-thread
preemption. It rejects unimplemented features such as implicit-argument buffers,
stack calls, scratch descriptors, alternate addressing modes or additional
kernels. Reflection-only `kernels_misc_info` is bounded but does not control
dispatch. This is a deliberately limited metadata parser, not a general YAML
implementation. Intel's decoder is the reference for argument semantics and
rounding cross-thread storage up to 32 bytes.
([Intel ze_info decoder, pinned release](https://github.com/intel/compute-runtime/blob/26.27.39122.11/shared/source/device_binary_format/zebin/zeinfo_decoder.cpp))

`Image::stage` takes explicit CPU destinations and prospective GPU virtual
addresses for each loaded section. It checks their sizes, alignment and overlap,
resolves all supported symbols and plans all patches before writing any output.
It then copies initialized data and ISA, zeros `.bss.global` / `.bss.const`, and
applies the planned relocations. A failure leaves destination bytes and the
output descriptor unchanged. It supports full 64-bit, low-32, high-32 and the
documented per-thread-offset relocation forms, plus signed RELA addends. An
unresolved external, overlapping patch or out-of-range destination fails.
Section names and relocation numbers follow Intel's published Zebin definitions.
([Intel Zebin ELF definitions, pinned release](https://github.com/intel/compute-runtime/blob/26.27.39122.11/shared/source/device_binary_format/zebin/zebin_elf.h))

For instruction relocations the implementation replaces the immediate. Data
relocations add the resolved value to the initial field, with the field's
specified width; zero-initialized data starts at zero. Defined section symbols
are resolved against the explicit destination addresses, and absolute symbols
retain their declared values. Undefined symbols require a supported built-in
meaning. ELF bytes themselves are never interpreted as MI ring commands.
([Intel linker implementation, pinned release](https://github.com/intel/compute-runtime/blob/26.27.39122.11/shared/source/compiler_interface/linker.cpp))

## The two real relocations and their exact meaning

The actual artifact has two `R_ZE_SYM_ADDR_32` relocations at offsets **76** and
**236**, both referring to `__INTEL_PATCH_CROSS_THREAD_OFFSET_OFF_R0`.
Intel identifies that name as the **implicit-argument-prefix** relocation. It is
different from `__INTEL_PER_THREAD_OFF`. For this supported profile, stack calls,
debugger mode and `require_implicit_arg_buffer` are absent; no implicit prefix is
inserted. Both compiler-emitted immediates are zero and the loader resolves them
to zero. A nonzero initial prefix is rejected. The resulting ISA bytes are
therefore unchanged for this exact artifact, although its external relocation
requirements have been checked and resolved for the stated execution mode.
([Intel relocation names](https://github.com/intel/compute-runtime/blob/26.27.39122.11/shared/source/compiler_interface/linker.h))

The separately supported `R_PER_THREAD_PAYLOAD_OFFSET` /
`__INTEL_PER_THREAD_OFF` form uses cross-thread bytes minus the inline portion.
For this metadata that is `64 - 32 = 32`. Those are exercised by synthetic
relocation tests; they are **not** the two relocations present in the actual
artifact. Unsupported built-in addends and implicit-prefix configurations fail
rather than sharing an assumed value.
([Intel kernel descriptor offset calculation](https://github.com/intel/compute-runtime/blob/26.27.39122.11/shared/source/kernel/kernel_descriptor.h))

## Argument preparation and the VM connection

`Image::payload` produces the 64-byte cross-thread payload from explicit CPU
staging values. It verifies element count, required buffer byte lengths, address
ranges, pointer alignment and bounded nonzero workgroup dimensions. It writes:

- Global work-item offsets at byte 0, then enqueued local sizes at byte 12.
- Input and output stateless GPU addresses at bytes 24 and 32.
- The 32-bit nonce and element count at bytes 40 and 44.
- Input and output bindless surface handles at bytes 48 and 52.

All payload padding is zeroed. The returned descriptor records 32 inline bytes,
32 remaining indirect cross-thread bytes and 192 per-thread bytes. These lengths
do not generate local IDs or program hardware's local-ID generation. The caller
still has to select and implement the correct dispatch path.

`resolveEvidencePointers` connects argument preparation to `XeMemory::VirtualMemory`.
It resolves owner and generation-bearing handles, checks that the mappings are
`Pinned` or `Bound` with valid pin receipts, and derives addresses and sizes from
those authoritative allocations. `Reserved`, retired, quarantined, stale and
foreign allocations are refused. A required `SurfaceBackend::resolve` callback
must look up the existing bindless surface allocation and validate its requested
read/write access. It must not allocate or acquire new ownership. No callback
means `Unavailable`; there is no default fake zero surface handle.

The lower-level `EvidenceValues` API deliberately permits prospective addresses
for offline tests. Its successful return only means the CPU payload was formed.
Neither it nor the VM resolver acquires submission holds or changes mappings to
`Bound`. Future submission must retain all ISA, indirect-data, surface-state,
input and output allocations using the existing VM/queue lifetime rules.

Example staging values used by the actual-artifact test are input VA
`0x200000000`, output VA `0x300000000`, 4,096 bytes each, nonce `0xAABBCCDD`, count
1,024 and local size `(32,1,1)`. The handles `0x123` and `0x456` are explicitly
test values, not measured hardware surface handles. The VM integration test
separately derives its addresses from real VM records and mocks only pin/surface
backends. No test changes an allocation to `Bound` through this loader.

## Target and dispatch prerequisites

The compatibility-note parser exposes product family `1272`, graphics core
`3079`, target flags and product configuration `51478528` from the actual binary.
These are compiler metadata. They are not proof that the active GPU's GMD_ID or
stepping matches. Intel's runtime performs device compatibility checking after
decoding these notes; an actual hardware integration must do the equivalent
before dispatch. The loader does not override the captured physical device ID.
([Intel device compatibility validation](https://github.com/intel/compute-runtime/blob/26.27.39122.11/shared/source/device_binary_format/zebin/zebin_decoder.cpp))

The current kernel explicitly uses bindless accesses. Filling only stateless
pointer fields cannot supply its missing render-surface-state descriptors or
bindless heap configuration. Its `has_no_stateless_write` metadata means the
output write path must not be inferred from the presence of a stateless address.
The loader preserves both argument forms and the preemption requirement.

Still required are GPU-visible pinned storage for ISA, data and heaps; matching
cache/PAT setup and synchronization; bound page tables; valid surface descriptors;
indirect-data placement and local-ID generation; the correct Xe-LPG interface
descriptor/compute walker, pipeline and preemption state; an initialized logical
ring context; command validation; and actual completion with protected resource
lifetimes. GuC CTB scheduling selects a previously initialized context. It does
not replace these compute dispatch requirements. No walker offsets or commands
were guessed in this implementation.

This OpenCL C / Intel EU executable also does not implement Apple's Metal
compiler interface, IOAccel user-client ABI or Metal command-buffer translation.
Those integration points remain separate from successful native Zebin loading.

## Validation

Run from the source root:

```sh
g++ -std=c++17 -Wall -Wextra -Werror -O2 tests/xe_zebin_tests.cpp Mellow/XeZebin.cpp Mellow/XeMemory.cpp -o xe_zebin_tests
./xe_zebin_tests compiler-evidence/mellow_evidence_mtl.bin
```

The native test passed **21,438 checks**. It covers the actual compiler artifact,
every shorter truncation of that file, malformed ELF fields, invalid section
bounds and alignment, unsupported/overlapping metadata, kernel symbol identity,
real zero-prefix relocation resolution, distinct per-thread-offset semantics,
low/high address splitting above 4 GiB, BSS zeroing, initialized-data relocation,
signed addends, unknown symbols, duplicate patches, failure atomicity, destination
alias refusal, payload contents and the VM/surface lookup connection.

The implementation also compiled for the Darwin kernel target with LLVM 20.1.8,
the bundled MacKernelSDK and `-Wall -Wextra -Werror`. This is compile-time and CPU
staging evidence. The loader, generated ISA and payload have **not run on the
Galaxy Book GPU or on macOS**. A final acceptance result still needs a real
submission and output comparison on the identified GPU; this document does not
promote staging success into that result.
