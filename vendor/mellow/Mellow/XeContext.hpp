// Local 7D41 implementation, 2026. MIT. See docs/XE-CONTEXT-DISPATCH.md.
#pragma once
#include "XeMemory.hpp"

namespace XeContext {
enum class Error { None, Invalid, Capacity, Unsupported, Unavailable };
constexpr size_t PageBytes=4096, RegisterDwords=96, ImageBytes=14*PageBytes;
constexpr uint32_t RenderMmioBase=0x2000;
// GGTT context address names the PPHWSP, followed by 13 pages of RCS state.
// These are construction inputs, NOT proof that a mapping exists.
struct Spec {
    uint32_t ggttContext {}, ggttRing {}, ringBytes {};
    uint64_t rootDma {}; uint8_t tablePat {};
};
struct Staged {
    uint64_t descriptor {}, rootDescriptor {};
    uint32_t ggttContext {}, ggttRing {}, ringBytes {};
    bool bootstrapCaptureOnly {true};
    bool softwareOnly {true};
};
// Construct Linux Xe's empty MTL RCS0 LRC register image for the first capture
// submission. It deliberately inhibits engine-context restore. This is not a
// captured golden context and is never automatically scheduled.
Error buildBootstrap(const Spec &, uint32_t *image, size_t bytes, Staged &);
// Validate exactly the MTL RCS register-command prefix without accepting an
// arbitrary stream of MMIO writes. Values are inspected separately by caller.
bool registerLayoutMatches(const uint32_t *image, size_t bytes);

// Offline ring construction. Caller must supply an authoritative, acquire-
// ordered head under its context ownership lock before using this on a live
// ring. No tail publication, GPU progress, or memory reclamation occurs here.
// Command sequences never straddle the ring end. The mandatory 8-byte gap is
// retained so equal head/tail can only mean empty. Input must not alias ring.
Error appendRing(uint32_t *ring, size_t bytes, uint32_t head, uint32_t tail,
                 const uint32_t *commands, size_t count, uint32_t &nextTail);
}
