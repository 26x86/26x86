// Intel Xe interrupt register ABI (MIT); local bounded implementation.
#pragma once
#include "XeMmioAccess.hpp"

namespace XeInterrupt {
enum class Status : uint8_t { Ok, Empty, Pending, Invalid, Unavailable, IoFailure, Timeout, Unsupported, Faulted };
enum class Handling : uint8_t { Drained, More, Failed };
struct Identity { uint32_t raw {}; uint8_t bank {}, bit {}, engineClass {}, instance {}; uint16_t vector {}; };
constexpr uint32_t tileMaster = 0x190008, gfxMaster = 0x190010;
constexpr uint32_t bankStatus = 0x190018, identityRegister = 0x190060, selectorRegister = 0x190070;
constexpr uint32_t masterEnable = 0x80000000U, identityValid = 0x80000000U;
constexpr uint16_t gucToHost = 0x8000, engineUser = 1, engineFlush = 16;
// The tile IRQ router exclusively owns master enable/ack. Every other tile-0
// source (display/media/errors) must be dispatched by this router's handler.
// Proofs must come from the actual PF owner, not a user-set capability bit.
struct Ops {
    MellowXe::MmioAccess mmio {};
    void *opaque {};
    bool (*admitted)(void *, uint64_t epoch) {}; // hard-IRQ safe, no sleeping
    Handling (*identity)(void *, uint64_t epoch, const Identity &) {}; // workloop
    Handling (*otherMaster)(void *, uint64_t epoch, uint32_t bits) {}; // workloop
};
struct Configuration { uint64_t epoch {}; uint16_t vendor {}, device {}; uint8_t ccsMask {}; bool render {}, copy {}; };
// filter() performs only bounded MMIO and atomics in hard IRQ context. All
// other methods run on one serialized workloop; no forcewake acquisition here.
// The owner holds D0/MMIO lifetime and epoch until stop and IRQ synchronization.
class Controller {
public:
    Controller() = default;
    Controller(const Controller &) = delete;
    Controller &operator=(const Controller &) = delete;
    Status configure(const Configuration &, const Ops &);
    Status start();
    bool filter();
    Status service(); // More preserves pending handler; caller reschedules
    Status stop();
    bool faulted() const { return __atomic_load_n(&state_, __ATOMIC_ACQUIRE) == 4; }
    uint64_t epoch() const { return config_.epoch; }
private:
    Configuration config_ {}; Ops ops_ {};
    Identity events_[64] {}; uint32_t eventCount_ {}, nextEvent_ {}, other_ {};
    uint32_t state_ {}; // 0 stopped, 1 armed, 2 masked, 3 workloop, 4 fault
    bool configured_ {}, batchReady_ {};
    bool admitted() const;
    bool read(uint32_t reg, uint32_t &value);
    bool write(uint32_t reg, uint32_t value);
    bool update(uint32_t reg, uint32_t mask, uint32_t bits);
    Status fail(Status);
    Status rearm();
    Status collect();
};
}
