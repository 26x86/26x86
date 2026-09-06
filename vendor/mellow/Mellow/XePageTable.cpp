// Local 7D41 research implementation, 2026. See LICENSE and NOTICE.
#include "XePageTable.hpp"

namespace XeMemory {
static constexpr uint64_t AddressMask = (DmaLimit - 1) & ~(PageSize - 1);
void PageTable::clear(TablePage &page) {
    for (size_t i = 0; i < 512; ++i) page.words[i] = 0;
}
size_t PageTable::findDma(uint64_t dma) const {
    for (size_t i = 0; i < count_; ++i) if (pool_[i].dma == dma) return i;
    return MaxPages;
}
size_t PageTable::allocate(uint8_t level) {
    for (size_t i = 0; i < count_; ++i) {
        if (nodes_[i].used) continue;
        clear(pool_[i]);
        nodes_[i].used = true;
        nodes_[i].level = level;
        return i;
    }
    return MaxPages;
}
Status PageTable::initialize(uint64_t owner, TablePage *pool, size_t count, uint8_t pat) {
    if (pool_) return Status::Busy;
    if (!owner || !pool || !count || count > MaxPages || pat > 3) return Status::Invalid;
    // Validate the complete pool before zeroing or consuming any page. Both DMA
    // and CPU ranges must be distinct; aliasing would corrupt a parent table.
    for (size_t i = 0; i < count; ++i) {
        uint64_t encoded = 0;
        const uintptr_t cpu = reinterpret_cast<uintptr_t>(pool[i].words);
        if (!cpu || (cpu & 7U) || cpu > UINTPTR_MAX - (PageSize - 1) ||
            encodeSystemPde(pool[i].dma, pat, encoded) != Status::Ok) return Status::Invalid;
        for (size_t j = 0; j < i; ++j) {
            const uintptr_t other = reinterpret_cast<uintptr_t>(pool[j].words);
            if (pool[i].dma == pool[j].dma ||
                (cpu <= other ? other - cpu < PageSize : cpu - other < PageSize)) return Status::Invalid;
        }
    }
    pool_ = pool; count_ = count; owner_ = owner; tablePat_ = pat;
    allocate(3); // Slot zero is the private root; no hardware write occurs.
    return Status::Ok;
}
Status PageTable::child(size_t parent, uint16_t index, size_t &out) const {
    const uint64_t entry = pool_[parent].words[index];
    if (!entry) return Status::NotFound;
    const size_t candidate = findDma(entry & AddressMask);
    uint64_t expected = 0;
    if (candidate == MaxPages || !nodes_[candidate].used ||
        nodes_[parent].level == 0 || nodes_[candidate].level + 1 != nodes_[parent].level ||
        encodeSystemPde(pool_[candidate].dma, tablePat_, expected) != Status::Ok || expected != entry)
        return Status::Invalid;
    out = candidate;
    return Status::Ok;
}
void PageTable::rollback(const Edge *edges, size_t count) {
    while (count) {
        const Edge &edge = edges[--count];
        pool_[edge.parent].words[edge.index] = 0;
        clear(pool_[edge.child]);
        nodes_[edge.child] = Node {};
    }
}
Status PageTable::map4K(uint64_t owner, uint64_t va, uint64_t dma, uint8_t pat, bool writable) {
    if (!pool_ || (va & (PageSize - 1))) return Status::Invalid;
    if (owner != owner_) return Status::WrongOwner;
    if (sealed_) return Status::Busy;
    uint16_t indices[4] {};
    uint64_t pte = 0;
    if (pageTableIndices(va, indices) != Status::Ok ||
        encodeSystemPte4K(dma, pat, writable, pte) != Status::Ok || findDma(dma) != MaxPages)
        return Status::Invalid; // Do not expose the page-table pool as writable data.
    Edge edits[3] {}; size_t editCount = 0; size_t node = 0;
    for (unsigned level = 3; level > 0; --level) {
        size_t next = 0;
        Status status = child(node, indices[level], next);
        if (status == Status::NotFound) {
            next = allocate(static_cast<uint8_t>(level - 1));
            if (next == MaxPages) { rollback(edits, editCount); return Status::NoSpace; }
            uint64_t entry = 0;
            // Pool/PAT were validated at initialize; caller must not mutate them.
            status = encodeSystemPde(pool_[next].dma, tablePat_, entry);
            if (status != Status::Ok) {
                nodes_[next] = Node {}; rollback(edits, editCount); return status;
            }
            pool_[node].words[indices[level]] = entry;
            edits[editCount++] = Edge {node, next, indices[level]};
        } else if (status != Status::Ok) {
            rollback(edits, editCount); return status;
        }
        node = next;
    }
    if (pool_[node].words[indices[0]]) { rollback(edits, editCount); return Status::Busy; }
    pool_[node].words[indices[0]] = pte;
    ++mappings_;
    return Status::Ok;
}
Status PageTable::lookup(uint64_t owner, uint64_t va, uint64_t &pte) const {
    if (!pool_ || (va & (PageSize - 1))) return Status::Invalid;
    if (owner != owner_) return Status::WrongOwner;
    uint16_t indices[4] {};
    if (pageTableIndices(va, indices) != Status::Ok) return Status::Invalid;
    size_t node = 0;
    for (unsigned level = 3; level > 0; --level) {
        size_t next = 0;
        Status status = child(node, indices[level], next);
        if (status != Status::Ok) return status;
        node = next;
    }
    const uint64_t entry = pool_[node].words[indices[0]];
    if (!entry) return Status::NotFound;
    if (!(entry & 1U)) return Status::Invalid;
    pte = entry;
    return Status::Ok;
}
Status PageTable::unmap4K(uint64_t owner, uint64_t va) {
    if (sealed_) return Status::Busy;
    uint64_t ignored = 0;
    Status status = lookup(owner, va, ignored);
    if (status != Status::Ok) return status;
    uint16_t indices[4] {}; pageTableIndices(va, indices);
    size_t path[4] {}; path[3] = 0;
    for (unsigned level = 3; level > 0; --level) {
        status = child(path[level], indices[level], path[level - 1]);
        if (status != Status::Ok) return status;
    }
    pool_[path[0]].words[indices[0]] = 0;
    --mappings_;
    for (unsigned level = 0; level < 3; ++level) {
        bool empty = true;
        for (size_t i = 0; i < 512; ++i) if (pool_[path[level]].words[i]) { empty = false; break; }
        if (!empty) break;
        pool_[path[level + 1]].words[indices[level + 1]] = 0;
        nodes_[path[level]] = Node {};
    }
    return Status::Ok;
}
Status PageTable::seal(uint64_t owner, uint64_t &root) {
    if (!pool_) return Status::Invalid;
    if (owner != owner_) return Status::WrongOwner;
    sealed_ = true;
    root = pool_[0].dma;
    return Status::Ok;
}
size_t PageTable::usedPages() const {
    size_t count = 0;
    for (size_t i = 0; i < count_; ++i) if (nodes_[i].used) ++count;
    return count;
}
}
