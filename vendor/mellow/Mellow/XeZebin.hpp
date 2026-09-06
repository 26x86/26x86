// Local 7D41 research implementation, 2026. See LICENSE and NOTICE.
#pragma once
#include "XeMemory.hpp"

namespace XeZebin {
enum class Error { None, InvalidElf, Bounds, Capacity, Unsupported, Metadata,
                   Duplicate, Relocation, UnresolvedSymbol, InvalidBinding, Unavailable };
constexpr size_t MaxSections=32, MaxSegments=8, MaxRelocations=64, MaxPayload=256;
enum class ArgType { GlobalOffset, LocalSize, Pointer, Value };
enum class AddressMode { None, Stateless, Bindless };
struct Argument {
    ArgType type {}; AddressMode mode {}; uint32_t offset {}, size {}, index {};
    bool writable {};
};
struct Metadata {
    char name[64] {};
    uint32_t versionMajor {}, versionMinor {}, simd {}, grf {}, inlineBytes {},
        crossThreadBytes {}, perThreadBytes {}, skipPerThreadLoad {}, euThreads {};
    bool disableMidThreadPreemption {}, noStatelessWrites {}, independentProgress {};
    Argument args[8] {}; size_t argumentCount {};
};
struct Compatibility {
    uint32_t productFamily {}, gfxCore {}, targetFlags {}, productConfig {};
};
struct Segment {
    uint16_t section {}; uint64_t fileOffset {}, bytes {}, alignment {};
    bool executable {}, zeroInit {};
};
struct Destination { uint8_t *cpu {}; size_t capacity {}; uint64_t gpuAddress {}; };
struct StagedImage {
    // CPU construction only. No GPU root publication, dispatch or completion.
    uint64_t kernelGpuAddress {}, skipLocalIdLoadGpuAddress {};
    size_t textBytes {}, relocationCount {};
    bool softwareOnly {true};
};
struct EvidenceValues {
    uint64_t inputAddress {}, outputAddress {}, inputBytes {}, outputBytes {};
    uint32_t inputSurface {}, outputSurface {}, nonce {}, count {};
    uint32_t globalOffset[3] {}, localSize[3] {32,1,1};
};
struct Payload {
    uint8_t bytes[MaxPayload] {};
    uint32_t size {}, inlineBytes {}, indirectCrossThreadBytes {}, perThreadBytes {};
    bool softwareOnly {true};
};
// Bounded ELF64/IntelGT loader for the emitted mellow_evidence .ze_info 1.73
// profile. It borrows an immutable input image. All source/destination memory
// must remain stable and serialized. Unknown metadata/relocations fail closed.
// Allocate this object off a small kernel stack; no allocation or GPU I/O occurs.
class Image {
public:
    Error parse(const uint8_t *data, size_t bytes);
    const Metadata *metadata() const { return valid_ ? &metadata_ : nullptr; }
    const Compatibility *compatibility() const { return valid_ ? &compatibility_ : nullptr; }
    size_t segmentCount() const { return valid_ ? segmentCount_ : 0; }
    const Segment *segment(size_t index) const { return valid_ && index<segmentCount_ ? &segments_[index] : nullptr; }
    // All checks, symbol resolution and patch planning precede any output write.
    Error stage(const Destination *destinations, size_t count, StagedImage &out) const;
    Error payload(const EvidenceValues &values, Payload &out) const;
private:
    struct Section { uint32_t name {},type {},link {},info {}; uint64_t flags {},offset {},bytes {},align {},entry {}; };
    const uint8_t *data_ {}; size_t bytes_ {}; bool valid_ {};
    Section sections_[MaxSections] {}; size_t sectionCount_ {}, stringSection_ {}, symbolSection_ {};
    Segment segments_[MaxSegments] {}; size_t segmentCount_ {}, textSegment_ {};
    Metadata metadata_ {}; Compatibility compatibility_ {};
    bool name(size_t section, const char *wanted) const;
    const char *string(size_t section,uint64_t offset) const;
    Error readMetadata(size_t section);
    Error readCompatibility(size_t section);
    size_t segmentForSection(uint32_t section) const;
};

// Optional connection to the authoritative VM. Surface resolution must validate
// the real bindless heap allocation and requested access by read-only lookup
// (it must not allocate or acquire ownership); there is no default
// zero-handle success. Pinned mappings may be used for offline staging, but only
// a later GPU bind/publication can make those virtual addresses executable.
struct SurfaceBackend {
    void *context {};
    bool (*resolve)(void *, uint64_t owner, XeMemory::Handle, const XeMemory::Allocation &,
                    bool writable, uint32_t &surfaceHandle) {};
};
Error resolveEvidencePointers(const XeMemory::VirtualMemory &vm, uint64_t owner,
    XeMemory::Handle input, XeMemory::Handle output, SurfaceBackend surfaces, EvidenceValues &values);
}
