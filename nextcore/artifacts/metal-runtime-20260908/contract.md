# Metal runtime continuation contract (2026-09-08)

Current state: the recorded GPU command executor logs DispatchCompute and increments
its execution counter without executing a shader. The explicit Vulkan compute
manager does implement validated submission, completion, and buffer readback, but
there is no connection from the recorded command list to that manager. The portable
Mellow objects are a separate OpenCL API and neither path supplies the guest Metal
framework/driver connection. No guest image is available in this new WSL checkout.

Desired state: recorded compute commands can execute through an explicitly supplied
ComputePipelineManager, in command order, using its registered pipeline and storage
buffers. A command is counted only after the manager completes GPU readback. A
missing backend or failed dispatch returns the original typed error and stops the
list. No shader translation, guest ABI or Metal capability is invented.

Decisions:
- Add execute_with_compute and execute_with_backends entry points; preserve existing
  render entry points. Compute inside an active render pass is rejected.
- Each synchronous compute dispatch uses an internal fence manager whose lifetime
  ends on return, avoiding fence accumulation. The Vulkan manager still owns actual
  in-flight objects on timeout and retains its existing poison behavior.
- No rollback of earlier completed commands is promised. A later command consumes
  the previous successful dispatch's readback.
- Extend the actual-GPU acceptance example with two ordered recorded dispatches,
  all 256 independent output comparisons, offset guards, and propagated failures.
- Native host tests must cover absent backend, invalid pipeline/dimensions, no
  count on error, render-pass rejection and failure stopping later commands.
- Physical GPU execution uses exact device IDs; software Vulkan is never reported
  as GPU hardware. WSL driver installation is an execution prerequisite if needed.

Public contract: Vulkan 1.1 command ordering, buffer barriers and fence completion:
https://docs.vulkan.org/spec/latest/chapters/synchronization.html
The existing Vulkan manager uploads coherent buffers and uses a compute-to-host
barrier before readback. The new adapter changes no Vulkan memory semantics.

Scope: nextcore-gpu, its owned tests/example/documentation and this artifact folder.
Delegation from root permits Runtime/Userspace investigation; no unrelated source
changes are currently proposed. ARM64 and x86 callers share the same host Rust API;
actual guest Metal and macOS 27 ARM64E boot remain separate unverified objectives.

OPEN_QUESTION: Guest driver: neither this crate nor the portable Mellow object API
registers a system MTLDevice or implements the guest accelerator transport.


Additional agreed implementation: retain one native Vulkan compute pipeline per
backend session. Reuse requires byte-identical SPIR-V words, identical entry name
and ordered binding numbers. A different key destroys the old pipeline only after
its last dispatch completed; failed preparation is never cached. The cache is
bounded to one pipeline, and teardown/uncertain-submission lifetime rules apply to
both cached pipeline objects and per-dispatch resources. Expose a compilation
counter incremented only after successful vkCreateComputePipelines; the physical
acceptance must observe one compilation across repeated same-key submissions.
Shader reflection and spirv-val validation remain required before every dispatch.


Product target clarification from user via root (2026-09-08): x86 UEFI hosts the VM;
macOS 27 ARM64E is the guest. WSL is the development environment only. The Vulkan
adapter/cache changes above are host reference tests, not a product UEFI GPU driver.
Mesa source work is stopped in favor of the EFI transport boundary.

EFI source audit:
- sandbox/efi/preos is an allocation-free no_std static library with a C JIT bridge.
- Its M1Framebuffer::present changes bookkeeping and its logical display interrupt;
  it does not submit host GPU commands or copy scanout pixels to a physical display.
- sandbox/efi/preos_abi.h exports execution request/result data, without GPU submission
  or scanout callbacks. The current minimal uefi.h has no GOP/PCI I/O GPU binding.
- There is no physical PCI GPU command processor, DMA mapping, shader compiler,
  interrupt/fence driver or macOS guest accelerator transport in this EFI path.
- A GOP pixel-copy bridge can provide boot scanout. GOP is not a Metal execution
  interface and cannot supply GPU compute/shader submission by itself.

OPEN_QUESTION: EFI ownership: add a standalone checked scanout adapter to preOS and
connect the C-owned GOP destination without overlapping active CPU/M1 edits.


Development test-only Vulkan selection: root approved an ignored Linux integration
test selecting the explicitly identified Mesa CPU Vulkan device. Public production
construction still requires an integrated/discrete GPU with exact nonzero IDs.
The ignored test exercises real Vulkan shader compilation, submission, readback,
cache reuse and cache replacement. Its output explicitly identifies software Vulkan
and keeps hardware/Metal verification false; it is not a product GPU backend.


Runtime relocation: root moved the freestanding EFI/JIT sources, including
gop_scanout.c, gop_scanout.h and test_gop_scanout.c, into
nextcore/crates/nextcore-ise/runtime/. Prior sandbox/efi paths above record the
implementation location before that move. Source hashes were rechecked unchanged.
