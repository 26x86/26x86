// Local research implementation. Register definitions: Intel Linux Xe (MIT).
#pragma once
#include <stdint.h>

namespace MellowXe {
struct MmioAccess {
    void *opaque {};
    bool (*read32)(void *, uint32_t, uint32_t &) {};
    bool (*write32)(void *, uint32_t, uint32_t) {};
    uint64_t (*nowMicros)(void *) {};
    void (*delayMicros)(void *, uint32_t) {};
};
enum class MmioStatus { Ok, Invalid, UnsupportedIp, Unavailable, IoFailure, Timeout, Busy, Faulted, ClockRegression };
enum class WakeDomain : uint8_t { Gt, Render };
struct GraphicsIp { uint16_t architecture {}; uint8_t release {}, subIp {}, revision {}; };

// PF/main GT only. Caller must own the device, serialize access with every other
// MMIO/forcewake user, and run outside interrupt context. No SR-IOV or media GT.
class ForceWake {
public:
    ForceWake() = default;
    ForceWake(const ForceWake &) = delete;
    ForceWake &operator=(const ForceWake &) = delete;
    MmioStatus initialize(MmioAccess access);
    MmioStatus shutdown();
    MmioStatus acquire(WakeDomain domain);
    MmioStatus release(WakeDomain domain);
    bool held(WakeDomain domain) const;
    bool canDetach() const { return !refs_[0] && !refs_[1] && !faulted_; }
    const GraphicsIp &ip() const { return ip_; }
private:
    MmioAccess io_ {};
    GraphicsIp ip_ {};
    uint32_t refs_[2] {};
    bool initialized_ {}, faulted_ {};
    MmioStatus wait(uint32_t ack, bool awake);
};
}
