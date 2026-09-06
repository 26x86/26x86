// Local 7D41 research implementation, 2026. See LICENSE and NOTICE.
#pragma once
#include "XeMemory.hpp"

namespace XeMemory {
struct TablePage { uint64_t dma {}; uint64_t *words {}; };

// Builds four-level system-memory page tables in private CPU buffers. The pool
// must be pinned/mapped DMA memory owned by the caller, not raw CPU physical
// addresses. This class neither publishes a root nor invalidates GPU TLBs.
// All calls and pool access must be serialized. Never modify a published tree
// with this interface: seal() permanently makes this instance read-only.
class PageTable {
public:
    static constexpr size_t MaxPages = 128;
    PageTable() = default;
    PageTable(const PageTable &) = delete;
    PageTable &operator=(const PageTable &) = delete;
    Status initialize(uint64_t owner, TablePage *pool, size_t count, uint8_t tablePat);
    Status map4K(uint64_t owner, uint64_t va, uint64_t dataDma, uint8_t leafPat, bool writable);
    Status unmap4K(uint64_t owner, uint64_t va);
    Status lookup(uint64_t owner, uint64_t va, uint64_t &rawPte) const;
    Status seal(uint64_t owner, uint64_t &rootDma);
    size_t usedPages() const;
    size_t mappedPages() const { return mappings_; }
    bool sealed() const { return sealed_; }
private:
    struct Node { bool used {}; uint8_t level {}; };
    struct Edge { size_t parent {}, child {}; uint16_t index {}; };
    TablePage *pool_ {};
    Node nodes_[MaxPages] {};
    size_t count_ {}, mappings_ {};
    uint64_t owner_ {};
    uint8_t tablePat_ {};
    bool sealed_ {};
    size_t findDma(uint64_t dma) const;
    size_t allocate(uint8_t level);
    Status child(size_t parent, uint16_t index, size_t &out) const;
    void rollback(const Edge *edges, size_t count);
    static void clear(TablePage &page);
};
}
