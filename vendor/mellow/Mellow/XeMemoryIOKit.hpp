// Local 7D41 research implementation, 2026. See LICENSE and NOTICE.
#pragma once
#include "XeMemory.hpp"
#include <IOKit/IOMapper.h>

namespace XeMemory {
// Obtain the mapper for the admitted PCI device with
// IOMapper::copyMapperForDevice. Null is refused, never silently replaced with
// identity mapping or a mapper from another device. Caller owns/retains mapper.
struct IOKitContext {
    IOKitContext() = default;
    IOKitContext(const IOKitContext &) = delete;
    IOKitContext &operator=(const IOKitContext &) = delete;
    IOMapper *mapper {};
    uint64_t maxAllocationBytes {64ULL * 1024 * 1024};
    uint64_t maxPinnedBytes {256ULL * 1024 * 1024};
    uint64_t pinnedBytes {};
};
Backend makeIOKitPinBackend(IOKitContext &context);
// All adapter calls and quota access must be serialized in sleepable client
// context, never interrupt context or a gated work-loop action: DMA prepare can
// block. The context and its retained mapper must outlive every returned pin.
// Synchronize covers IODMACommand bounce-buffer copies; it is NOT a GPU engine
// cache flush, an MMIO ordering barrier, or evidence of GPU job completion.
Status synchronizeForDevice(const Pin &pin);
Status synchronizeForCpu(const Pin &pin);
void *kernelBuffer(const Pin &pin);
// This adapter allocates and pins real IOKit-owned system-memory pages. It does
// NOT create GPU page tables, publish a context root, invalidate GPU TLBs, handle
// GPU interrupts or provide bind/unbind/fenceComplete callbacks.
}
