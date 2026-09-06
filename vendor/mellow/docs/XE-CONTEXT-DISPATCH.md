> **Historical record — preserved unedited.** Component documentation for the hand-written
> Intel Xe backend, which compiles into the kext but has no call path
> ([Mellow/RuntimeReadiness.hpp:84](../Mellow/RuntimeReadiness.hpp)). Scheduled to move to
> `docs/backends/xe/` in P1. For how these modules map onto the vendor-neutral abstraction
> see [MGAL.md](MGAL.md); for the current architecture see [ARCHITECTURE.md](ARCHITECTURE.md).

# MTL / 7D41 context and evidence-kernel dispatch construction

This component constructs native Xe-LPG GPU command bytes and the actual
compiler-produced evidence kernel's execution heaps. It does not report GPU
execution, native Metal acceleration, a published GGTT mapping, or an initialized
render engine. `Prepared`, `Staged`, and `RingJob` explicitly remain `softwareOnly`.
The packaged boot path does not run these commands on the Windows GPU.

The implementation is deliberately restricted to MTL graphics 12.70, RCS0,
four-level system-memory PPGTT, and the included `mellow_evidence` SIMD32 / 128-GRF
kernel. The physical 8086:7D41 identifier alone does not establish GT stepping,
engine topology, cache policy, or completion of hardware initialization.

## Implemented code

`Mellow/XeContext.cpp::buildBootstrap` emits the complete 96-DWORD register-command
prefix from Linux's `mtl_rcs_offsets`, followed by zeroed engine state inside a
14-page LRC allocation: one 4 KiB PPHWSP followed by 13 pages of RCS context state.
The first context's masked control value inhibits engine-state restore, as Linux
does while constructing the first submission used to capture a default context.
It sets ring head/tail/start/control and the PPGTT root **descriptor**, using
`XeMemory::encodeSystemPde`; the latter is not a raw CPU physical address.

The descriptor names the PPHWSP GGTT address and sets valid, legacy-64-bit
addressing, and PPGTT mode (`0x119`). Engine class/instance bits are not inserted:
Linux only inserts them for graphics versions below 12.50. The command prefix
uses the source-defined RCS register base `0x2000`. The API rejects overlapping
LRC/ring GGTT ranges, address overflow, invalid root/PAT values and invalid ring
sizes. `registerLayoutMatches` checks command, address, terminator and NOP slots;
it intentionally does not certify arbitrary register data as safe to restore.

This is the bootstrap capture image, **not a golden engine context**. Engine
initialization, priming/capturing the hardware's context image, register
workarounds, AUX invalidation, and required per-context/indirect workaround
batches still have to be established by the hardware integration. An all-zero
engine-state area must never be presented as a captured, working context.

`appendRing` handles arbitrary aligned head/tail positions, reserves an 8-byte
empty/full gap, pads odd DWORD counts to qword alignment and inserts MI_NOOPs at
the end instead of splitting a command sequence across the wrap. On insufficient
space, it changes neither the ring nor output tail. It performs no tail write to
an LRC or register. A live caller must obtain a current, acquire-ordered hardware
head while holding the context's ownership lock; a user-supplied head is not
acceptable evidence of free space.

`Mellow/XeDispatch.cpp::prepareEvidence` uses `XeZebin::Image::stage` and `payload`
to produce four separate 4 KiB CPU staging heaps:

- Instruction heap: actual 1,216-byte `.text.mellow_evidence`, including its
  resolved relocations, zero padded. ISA bytes are not interpreted as ring words.
- Indirect heap: the remaining 32 cross-thread bytes followed by 192 bytes of
  software XYZ local IDs. The X vector contains 32 little-endian uint16 lane IDs;
  Y and Z contain zeros. Remaining heap bytes are zero.
- Surface heap: two real 64-byte RAW, linear, uncompressed
  `RENDER_SURFACE_STATE` records, with full 48-bit input/output GPU addresses,
  source-defined 7/14/11-bit buffer-length encoding, caller-selected initialized
  MOCS index, and uncached L1 policy. The XeHPG coherency field remains
  GPU_COHERENT, as in the runtime's XeHPG specialization. CPU coherence still
  requires the DMA/coherency backend. This field does not grant it.
- Batch heap: 83 DWORDs comprising RCS PIPE_CONTROL barriers, GPGPU
  PIPELINE_SELECT, 22-DWORD STATE_BASE_ADDRESS, masked 128-GRF STATE_COMPUTE_MODE,
  6-DWORD CFE_STATE, 39-DWORD COMPUTE_WALKER, and MI_BATCH_BUFFER_END.

The local workgroup is 32x1x1, with one SIMD32 hardware thread per workgroup and
`ceil(count/32)` workgroups. Extra final-group lanes are masked by the actual
kernel's `i < count` branch. Global offsets other than zero are rejected by this
bounded bring-up profile. The first 32 cross-thread bytes live inside the walker.
Its indirect length is 224 bytes and its indirect pointer is offset zero relative
to SBA GeneralStateBaseAddress. Kernel entry is offset zero relative to SBA
InstructionBaseAddress, retaining the software-local-ID load prologue. The
hardware-local-ID skip entry at ISA+192 is **not** used. Surface offsets 0 and 64
are placed in the bindless payload fields, relative to the bindless surface SBA.

The compiler's `disable_mid_thread_preemption` requirement is not implemented by
setting the old interface-descriptor bit: Intel's XeHPG setter explicitly rejects
that operation. The hardware context must already have an independently verified
preemption configuration compatible with the kernel. CFE topology/dispatch
policy and MOCS table initialization are likewise external inputs, not inferred
from a CPU name or a successful source compile.

`prepareBoundEvidence` resolves six real VM handles in order: instruction,
indirect, surface, batch, input, output. It checks owner, generation, Bound state,
pin storage and exact heap ranges. Reserved, merely Pinned, foreign, stale or
retiring resources fail. The function stages bytes only; it neither acquires
submission holds nor drops them. Callers must serialize validation/retention with
retirement and retain all resources until an authoritative fence or confirmed
quiescence, using the existing VM / submission ownership bridge.

`encodeRenderRingJob` emits an RCS ring fragment with PPGTT
MI_BATCH_BUFFER_START, arbitration control, HDC/render/depth/DC/tile cache flush,
GGTT qword PIPE_CONTROL post-sync, and MI_USER_INTERRUPT followed by arbitration
enable/check. The qword is `{sequence32, 0}` and fits the independent `XeFence`
slot contract. Zero sequences and misaligned/out-of-range addresses fail.
`depthStallWorkaround` must be selected from actual stepping evidence. The fragment
does not perform pre-batch TLB/AUX invalidation or claim that stepping workarounds
were applied. Its GGTT completion address is not a PPGTT or DMA address.

## Publication boundary and stopping conditions

Before an actual context registration or schedule operation, integration must:

1. Admit the physical GPU and live GMD/stepping/topology; initialize the exact
   engine, MOCS/PAT state, forcewake and reset epoch.
2. Pin through the real DMA backend; publish and invalidate both GPU address
   spaces as appropriate. Verify the LRC/ring/fence GGTT PTEs against retained
   DMA pages. A PPGTT page-table tree and a numeric GGTT address are insufficient.
3. Capture the primed engine context and install all required MTL context/engine
   workarounds, preemption state, scratch/AUX state and GuC ADS policy.
4. Copy these staged heaps to their held DMA allocations and complete the
   required CPU-to-device synchronization. Publish PPGTT root and bind/TLB state
   through the authorized backend; then retain all job resources.
5. Install the live IRQ/fence route, publish the actual ring tail with required
   ordering, and register/schedule the prepared LRC via authenticated GuC CTB.
6. Observe the GPU-written qword through `XeFence`, check exact output bytes
   against the independent CPU reference, and correlate to the physical device.

Stop with Unavailable when any mapping, context-image, firmware, coherency,
preemption, IRQ, or private Metal-driver dependency is missing. Preserve pinned
resources after unknown acceptance or timeout until real completion/quiescence.
The existing `XeSubmission` MI_NOOP-only admission whitelist is intentionally not
widened to accept arbitrary user command streams. This evidence batch needs a
separate trusted dispatch admission path. No successful GPU result exists yet.

## Primary provenance and validation

- [Linux Xe LRC implementation](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_lrc.c):
  `mtl_rcs_offsets`, `set_offsets`, `empty_lrc_data`, `xe_lrc_ctx_init`,
  `xe_lrc_set_ppgtt`, `xe_lrc_descriptor`, and RCS context sizing.
- [Linux Xe LRC register layout](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/regs/xe_lrc_layout.h)
  and [ring operations](https://github.com/torvalds/linux/blob/4d7d9486c04d917265f64c55bd23b2cc4fe7749c/drivers/gpu/drm/xe/xe_ring_ops.c):
  `emit_bb_start`, `emit_render_cache_flush`, `emit_pipe_imm_ggtt`, `emit_user_interrupt`.
- [MTL hardware family](https://github.com/intel/compute-runtime/blob/26.27.39122.11/shared/source/xe_hpg_core/hw_cmds_mtl.h)
  inherits XeHpgCoreFamily. Intel tag 26.27.39122.11 resolves to commit
  `930b848261031928061f744020de30c104c0f207`.
- [Intel generated command fields](https://github.com/intel/compute-runtime/blob/26.27.39122.11/shared/source/generated/xe_hpg_core/hw_cmds_generated_xe_hpg_core.inl)
  provide the exact packet definitions. The unmodified source is preserved at
  `tests/xe_dispatch_intel_reference.inl` with its MIT license in
  `tests/xe_dispatch_intel_LICENSE.md`; it is a host-test oracle, not linked into
  the kernel plugin.
- [Intel dispatch encoder](https://github.com/intel/compute-runtime/blob/26.27.39122.11/shared/source/command_container/command_encoder_xehp_and_later.inl),
  [buffer encoder](https://github.com/intel/compute-runtime/blob/26.27.39122.11/shared/source/command_container/command_encoder.inl),
  [buffer-length definition](https://github.com/intel/compute-runtime/blob/26.27.39122.11/shared/source/command_container/encode_surface_state.h),
  and [XeHPG bindless descriptor](https://github.com/intel/compute-runtime/blob/26.27.39122.11/shared/source/xe_hpg_core/hw_cmds_xe_hpg_core_base.h)
  establish payload/entry offsets, software local-ID arrangement and surface handles.

Host validation passes 3,658,796 context/ring checks and 88,716 dispatch checks.
Tests exhaust all 512x512 aligned ring head/tail pairs for five sequence lengths;
compare full walker, SBA, CFE, SCM, pipeline, surface and fence command DWORDs
against Intel's original generated setters; load the actual 6,944-byte Zebin;
verify local-ID/payload bytes; and reject malformed address ranges, unbound VM
resources, stale owners/generations and retired output mappings. Both new C++
translation units also compile with Clang for x86_64 Apple kernel target and
`-Wall -Wextra -Werror`. These are source/host checks, not evidence of GPU execution.
