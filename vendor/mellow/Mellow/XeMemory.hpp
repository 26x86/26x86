// Local 7D41 research implementation, 2026. See LICENSE and NOTICE.
#pragma once
#include <stdint.h>
#include <stddef.h>

namespace XeMemory {
constexpr uint64_t PageSize = 4096;
constexpr uint64_t VaLimit = 1ULL << 48;
constexpr uint64_t DmaLimit = 1ULL << 46;

enum class Status { Ok, Invalid, NoSpace, NotFound, WrongOwner, Busy,
                    Unavailable, BackendFailure, Quarantined };
enum class State { Free, Excluded, Reserved, Pinned, Bound, Retiring, Quarantined };
struct Handle { size_t slot; uint64_t generation; };
struct Fence { uint64_t timeline; uint64_t value; };
struct Pin { void *cookie; const uint64_t *dmaPages; size_t pageCount; };

// These helpers encode entries in CPU memory only. PAT index selection and its
// hardware programming are the backend's responsibility. System memory only:
// DSM/device-memory, huge pages, scratch/null PTEs and GGTT are not inferred.
Status encodeSystemPte4K(uint64_t dmaAddress, uint8_t patIndex, bool writable,
                         uint64_t &entry);
Status encodeSystemPde(uint64_t nextTableDma, uint8_t patIndex, uint64_t &entry);
Status pageTableIndices(uint64_t gpuVa, uint16_t (&indices)[4]);

struct Backend {
    void *context {};
    // A successful pin owns stable DMA-address storage until unpin. On failure,
    // no resources may escape; a violation is retained/quarantined by the VM.
    Status (*pin)(void *, uint64_t owner, uint64_t bytes, Pin &) {};
    Status (*unpin)(void *, Pin &) {};
    // Ok means the GPU PTE update AND required TLB invalidation have completed.
    // Unavailable guarantees no hardware change. Any other failure may be
    // partial: quarantine, retaining both VA and backing pages.
    Status (*bind)(void *, uint64_t gpuVa, const Pin &, uint8_t pat, bool writable) {};
    Status (*unbind)(void *, uint64_t gpuVa, uint64_t bytes) {};
    // Must query real completion from the backend, never manufacture a fence.
    bool (*fenceComplete)(void *, Fence) {};
    // Zero is the default: PAT programming has not been validated.
    uint16_t verifiedPatIndices {};
};

struct Allocation {
    State state {State::Free};
    uint64_t owner {}, generation {}, address {}, bytes {};
    uint32_t activeUses {};
    Pin pin {};
    Fence lastUse {};
};

// Allocation-free bookkeeping; caller owns slots and serializes ALL calls and
// backend callbacks. The caller must never drop this object while pins remain.
// No interrupt-context allocation, implicit lock or arbitrary GPU write occurs.
class VirtualMemory {
public:
    VirtualMemory() = default;
    VirtualMemory(const VirtualMemory &) = delete;
    VirtualMemory &operator=(const VirtualMemory &) = delete;
    Status initialize(Allocation *slots, size_t capacity, uint64_t firstVa,
                      uint64_t limitVa, Backend backend);
    Status exclude(uint64_t address, uint64_t bytes);
    Status reserve(uint64_t owner, uint64_t bytes, uint64_t alignment, Handle &out);
    Status reserveAt(uint64_t owner, uint64_t address, uint64_t bytes, Handle &out);
    Status pin(uint64_t owner, Handle handle);
    Status bind(uint64_t owner, Handle handle, uint8_t patIndex, bool writable);
    // Queue resource holds prevent reuse before its authoritative completion or
    // confirmed rejection/quiescence. These are trusted scheduler operations,
    // never exposed as user-client release calls. Serialize with submission.
    Status retainUse(uint64_t owner, Handle handle);
    Status releaseUse(uint64_t owner, Handle handle);
    // One ordered fence timeline per allocation; combine cross-queue fences in
    // the scheduler before using this interface. Record before publishing work.
    Status recordUse(uint64_t owner, Handle handle, Fence fence);
    Status retire(uint64_t owner, Handle handle);
    Status reclaim(uint64_t owner, Handle handle);
    const Allocation *inspect(uint64_t owner, Handle handle) const;
    size_t occupied() const;
private:
    Allocation *slots_ {};
    size_t capacity_ {};
    uint64_t first_ {}, limit_ {}, nextGeneration_ {1};
    Backend backend_ {};
    Status lookup(uint64_t owner, Handle handle, Allocation *&allocation);
    bool available(uint64_t address, uint64_t bytes) const;
    Status insert(uint64_t owner, uint64_t address, uint64_t bytes, State state, Handle *out);
};
}
