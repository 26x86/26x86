// Local 7D41 implementation, 2026. MIT. See docs/XE-CONTEXT-DISPATCH.md.
#pragma once
#include "XeZebin.hpp"
namespace XeDispatch {
enum class Error { None, Invalid, Unsupported, Capacity, Zebin, Unavailable };
constexpr size_t HeapBytes=4096, WalkerDwords=39, BatchDwords=128;
// Four separate PPGTT heaps. Staging does not allocate or bind these addresses.
struct Layout { uint64_t instruction {},indirect {},surface {},batch {}; };
struct Policy {
    // Values must come from the admitted device's topology and initialized MOCS
    // table. Numeric range checking alone does not establish hardware validity.
    uint16_t maxFrontEndThreads {}; uint8_t mocsIndex {};
    bool disableEuFusion {},disableOverdispatch {};
};
struct Prepared {
    alignas(64) uint8_t isa[HeapBytes] {};
    alignas(64) uint8_t indirect[HeapBytes] {};
    alignas(64) uint32_t surface[HeapBytes/4] {};
    alignas(64) uint32_t batch[HeapBytes/4] {};
    Layout layout {}; size_t batchDwords {},isaBytes {},indirectBytes {};
    size_t walkerOffset {}; uint32_t groups {},count {};
    bool softwareOnly {true};
};
// Exact supported program: parsed mellow_evidence SIMD32/GRF128, no scratch,
// no SLM/barriers, software XYZ local IDs, workgroup 32x1x1, one EU thread/group.
// Writes real ISA, bindless surfaces, argument/local-ID heap and native commands
// in caller-owned CPU memory. Prepared must not reside on a small kernel stack.
// Image bytes must be immutable and must not overlap Prepared.
Error prepareEvidence(const XeZebin::Image &, const Layout &,const Policy &,
                      const XeZebin::EvidenceValues &,Prepared &);
Error encodeBufferSurface(uint64_t gpuAddress,uint64_t bytes,uint8_t mocsIndex,
                          uint32_t (&surface)[16]);
// Exact RCS0 ring fragment: batch -> cache flush -> GGTT qword fence -> IRQ.
// Required pre-batch TLB/cache/aux invalidation and stepping workarounds are
// external prerequisites. This function does not claim they happened.
struct RingJob { uint32_t words[32] {}; size_t count {}; bool softwareOnly {true}; };
Error encodeRenderRingJob(uint64_t batchGpu,uint32_t fenceGgtt,uint32_t sequence,
                          bool depthStallWorkaround,RingJob &);
// Read-only link to real VM ownership. This checks Bound, exact heap addresses,
// lengths and pin storage. Caller must retain every handle for the whole job;
// validation itself does not acquire uses and cannot authorize a GPU publish.
bool boundHeaps(const XeMemory::VirtualMemory &,uint64_t owner,const Layout &,
                const XeMemory::Handle (&handles)[4]);
// Resolve six authoritative VM handles in order: instruction, indirect, surface,
// batch, input, output. Reserved/Pinned/Retiring and stale/foreign handles fail.
// Like prepareEvidence this only stages CPU bytes; the scheduler must retain
// all six handles and serialize publication with VM retirement.
Error prepareBoundEvidence(const XeZebin::Image &,const XeMemory::VirtualMemory &,
    uint64_t owner,const XeMemory::Handle (&handles)[6],const Policy &,
    uint32_t nonce,uint32_t count,Prepared &);
}
