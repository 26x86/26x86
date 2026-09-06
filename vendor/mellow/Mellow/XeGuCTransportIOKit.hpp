// Actual GuC protocol callbacks for the checked IOKit BAR0 adapter.
#pragma once
#include "XeGuCTransport.hpp"
#include "XeMmioIOKit.hpp"

namespace XeGuC {
// These are authoritative driver-side proofs, never user-supplied flags.
// No implementation currently supplies the missing GuC upload/GGTT/LRC proofs.
struct DriverProofs {
    void *opaque {};
    // Exclusive PF/main-GT ownership, D0 and known loaded firmware70.53.0/ABI1.26
    // in this reset epoch. It must become false before reset/power transition.
    bool (*ownsEpochAndLoadedImage)(void *, uint64_t) {};
    // CTB stopped; configuration ranges equal retained, coherent, direct
    // IOBufferMemoryDescriptor backing bound in GGTT above WOPCM/below APIC.
    // A PPGTT-bound allocation does not satisfy the GuC GGTT requirement.
    bool (*configurationAllowed)(void *, const Configuration &) {};
    // Current CTB enabled, LRC/context ownership and action-specific state:
    // register valid LRC; schedule published ring tail; mode expected transition;
    // deregister disabled/quiescent context; HuC correct mapped RSA/GSC policy.
    bool (*authorizeAction)(void *, uint64_t, const Action &) {};
};
// Non-owning binding: retain MMIO device, forcewake and CTB resources until
// confirmed stop/reset. Single serialized sleepable owner, no IRQ-context calls.
// No DMA bounce copies: this adapter uses real CPU fences for coherent SMEM.
class IOKitBinding {
public:
    IOKitBinding(MellowXe::IOKitMmio &mmio, DriverProofs proofs, uint64_t epoch)
        : mmio_(mmio), proofs_(proofs), epoch_(epoch) {}
    IOKitBinding(const IOKitBinding &) = delete;
    IOKitBinding &operator=(const IOKitBinding &) = delete;
    MmioOps mailboxOps();
    Ops transportOps();
    // Preferred production entry: configure and attach only after all seven
    // actual mailbox acknowledgments. A failed attempt requires confirmed
    // reset/stop before destroying this binding and trying a new epoch.
    Status startTransport(const Configuration &, Transport &);
    bool ctEnabled() const { return enabled_; }
private:
    MellowXe::IOKitMmio &mmio_;
    DriverProofs proofs_ {};
    uint64_t epoch_ {};
    bool attempted_ {}, configuring_ {}, enabled_ {};
    static bool admitted(void *, uint64_t);
    static bool read(void *, uint32_t, uint32_t &);
    static bool write(void *, uint32_t, uint32_t);
    static uint64_t now(void *);
    static void delay(void *, uint32_t);
    static bool barrier(void *);
    static bool notify(void *);
    static bool authorize(void *, uint64_t, const Action &);
    static bool configuration(void *, const Configuration &);
};
}
