// Local research implementation, 2026. See LICENSE and NOTICE.
#pragma once
#include "XePageTable.hpp"
#include "XeMemoryIOKit.hpp"

namespace XeMemory {
// Trusted backend must prove every context stopped referencing this exact root
// and required invalidate/reset completion, not merely elapsed time.
struct RootRetirement {
    void *opaque {};
    bool (*complete)(void *, uint64_t owner, uint64_t rootDma) {};
};
// Actual IOKit/IOMMU-pinned page-table backing. Context/mapper must outlive this
// object. Keep alive until release succeeds; no destructor frees possibly live
// DMA. Serialized sleepable operations. Single-use: after release create anew.
class IOKitPageTable {
public:
    IOKitPageTable() = default;
    IOKitPageTable(const IOKitPageTable &) = delete;
    IOKitPageTable &operator=(const IOKitPageTable &) = delete;
    Status initialize(IOKitContext &context, uint64_t owner, size_t pages,
                      uint8_t tablePat, uint16_t verifiedPatIndices);
    // dataDma must be independently retained and owned in this device's mapper.
    // This private kernel API does not authorize user-controlled DMA addresses.
    Status map4K(uint64_t owner, uint64_t va, uint64_t dataDma, uint8_t pat, bool writable);
    Status unmap4K(uint64_t owner, uint64_t va);
    Status lookup(uint64_t owner, uint64_t va, uint64_t &pte) const;
    // Seal + IODMACommand synchronize. Publication/PAT/TLB belong to context
    // backend. Returned device root address is not evidence of a GPU bind.
    Status sealForDevice(uint64_t owner, uint64_t &rootDma);
    Status release(uint64_t owner, RootRetirement retirement = {});
    size_t pinnedPages() const { return pin_.pageCount; }
    bool rootExposed() const { return exposed_; }
private:
    Backend pins_ {};
    Pin pin_ {};
    TablePage pool_[PageTable::MaxPages] {};
    PageTable tree_ {};
    uint64_t owner_ {}, root_ {};
    uint16_t patMask_ {};
    bool started_ {}, ready_ {}, exposed_ {}, ended_ {};
};
}
