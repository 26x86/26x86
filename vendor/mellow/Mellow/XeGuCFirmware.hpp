// Local MTL GuC loader; Intel MIT protocol attribution in docs/XE-GUC-FIRMWARE.md.
#pragma once
#include "XeFirmware.hpp"
#include "XeMmioAccess.hpp"

namespace XeGuCFirmware {
enum class Error : uint8_t { None, Invalid, FirmwareMismatch, Unavailable, Mapping,
    Wopcm, Busy, Io, Timeout, Clock, Authentication, Boot, Quarantined };
enum class State : uint8_t { Idle, Retained, Starting, Dma, Authenticating, Running, Failed };
enum class Profile : uint8_t { HardwareConfig, Submission };
constexpr uint64_t gucGgttTop = 0xfee00000ULL;
constexpr uint32_t firmwareFileBytes = 320320;
constexpr uint32_t minimalAdsPrefix = 24576;
constexpr uint32_t logBytes = 4096 + 65536 + 16384 + 1048576;
struct Region {
    uint64_t owner {}, generation {}, ggtt {}, bytes {};
    uint8_t *cpu {};
    const uint64_t *dmaPages {};
    size_t pageCount {};
    void *pinCookie {};
};
struct Plan {
    uint64_t owner {}, epoch {};
    Region firmware {}, ads {}, log {};
    uint32_t hucUploadBytes {}; // zero means HuC unavailable for this boot
    uint8_t pciRevision {};
    Profile profile {Profile::HardwareConfig};
    bool ccsPresent {};
};
// In addition to exact PTE readback, ownership must hold the real DMA mapping,
// GGTT reservation and CPU view stable in one serialized domain. This cannot be
// supplied by PPGTT Bound alone. Failed retain must acquire no ownership.
// All handles/pointers are trusted kernel objects, never user-client arguments.
// Until release, retain must prevent aliasing and mutation of DMA pages, GGTT
// mappings and firmware/full-ADS bytes by anyone except the loader/device.
struct Backend {
    MellowXe::MmioAccess io {};
    uint8_t physicalRevision {}; // read from the admitted PCI device, before spoofing
    void *opaque {};
    bool (*admitted)(void *, uint64_t owner, uint64_t epoch) {};
    bool (*quiesced)(void *, uint64_t owner, uint64_t epoch) {};
    bool (*retain)(void *, const Region &, bool gpuWritable) {};
    bool (*release)(void *, const Region &) {};
    bool (*synchronize)(void *, const Region &) {};
    // Actual MCR-aware PAT3 readback and completed GGTT publication/TLB barrier.
    // Expected Xe-LPG PAT3=2 (WB, 1-way coherent); never infer a programmed PAT.
    bool (*readPat3)(void *, uint32_t &) {};
    bool (*mappingPublished)(void *, const Region &, uint64_t epoch) {};
    // Submission profile only: authoritative inspection of full ADS engine
    // masks/mapping/regsets/golden contexts and platform WA KLV contents.
    bool (*fullAdsValid)(void *, const Plan &, const MellowXe::FirmwareInfo &) {};
};
// Read-only hardware GGTT verifier: BAR0 + 8MiB GSM window, 8-byte PTE per4K,
// exact 46-bit DMA address + PRESENT + PAT3(bits52/53), no DM/VFID/extra bits.
// Caller holds mapping ownership and serializes all GGTT writers while reading.
Error verifyGgtt(const MellowXe::MmioAccess &, const Region &);
Error inspectPinnedFirmware(const uint8_t *bytes, size_t count, MellowXe::FirmwareInfo &);
uint32_t minimalAdsBytes(const MellowXe::FirmwareInfo &);
// Builds actual minimal ADS described by xe_guc_ads_populate_minimal: invalid
// mapping table, no engines, policies, doorbell count, private data pointer.
// This profile supports firmware/hwconfig boot, not command submission.
Error populateMinimalAds(const Region &, const MellowXe::FirmwareInfo &, uint32_t doorbellRegister);

class Loader {
public:
    explicit Loader(Backend backend) : backend_(backend) {}
    Loader(const Loader &) = delete;
    Loader &operator=(const Loader &) = delete;
    Error start(const Plan &);
    // Real reset + idle readback precedes release. Failure retains backing.
    // Single-use object; a new attempt needs a new owner-authorized epoch.
    Error resetAndRelease();
    bool running(uint64_t owner, uint64_t epoch) const;
    // Profile information is not a fresh hardware-health or CTB-ready proof;
    // admission must also use running(owner, epoch) and the live transport.
    bool submissionProfile() const { return state_ == State::Running && plan_.profile == Profile::Submission; }
    State state() const { return state_; }
    uint32_t lastStatus() const { return lastStatus_; }
    unsigned heldRegions() const { return held_; }
    const MellowXe::FirmwareInfo &firmware() const { return info_; }
private:
    Backend backend_ {};
    Plan plan_ {};
    MellowXe::FirmwareInfo info_ {};
    State state_ {State::Idle};
    uint32_t lastStatus_ {};
    unsigned held_ {};
    bool touchedHardware_ {}, attempted_ {};
    bool allowed() const;
    bool read(uint32_t, uint32_t &) const;
    bool write(uint32_t, uint32_t);
    Error wait(uint32_t, uint32_t mask, uint32_t expected, uint32_t timeoutUs, uint32_t intervalUs);
    Error reset();
    Error wopcm();
    Error authenticate();
    Error fail(Error);
    Error releaseRegions();
};
}
