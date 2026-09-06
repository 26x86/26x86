// Local implementation from the Intel MIT GuC ABI. See docs/XE-GUC-TRANSPORT.md.
#pragma once
#include "XeFirmware.hpp"

namespace XeGuC {
enum class Status : uint8_t {
    Ok, Invalid, Unavailable, Busy, Empty, Corrupt, IoFailure, Timeout,
    Retry, Rejected, UnknownCookie, Exhausted, PublishedUnknown, StaleEpoch
};
constexpr uint32_t maxHxgWords = 255, maxPending = 32;
constexpr uint32_t mainNotifyRegister = 0x1901f0, mainMailboxRegister = 0x190240;
constexpr uint32_t requiredSubmissionAbi = 0x011a00; // 1.26.0, inspected MTL 70.53.0
// Conservative hardware status check: GS_AUTH_STATUS_GOOD, ukernel READY,
// bootrom JUMP_PASSED and not in reset/halt. Does not identify the loaded image.
bool statusAuthenticatedAndReady(uint32_t gucStatus);
struct Descriptor { volatile uint32_t head, tail, status, reserved[13]; };
static_assert(sizeof(Descriptor) == 64, "GuC CT descriptor wire size");
struct Ring {
    Descriptor *descriptor {};
    volatile uint32_t *words {};
    uint32_t count {};
    uint64_t descriptorGgtt {}, bufferGgtt {};
};
struct Action { uint32_t words[12] {}; uint32_t count {}; };
// Single normal KMD context only. lrcDescriptor is the prepared 64-bit hardware
// descriptor, NOT an unadorned address. The backend must validate its ownership,
// engine topology, initialized LRC/ring and published page-table root.
Status encodeRegister(uint32_t id, uint32_t gucClass, uint32_t submitMask,
                      uint64_t lrcDescriptor, Action &out);
Status encodeSchedule(uint32_t id, Action &out);
Status encodeMode(uint32_t id, bool enable, Action &out);
Status encodeDeregister(uint32_t id, Action &out);
// Wire helper only: does not itself authenticate HuC or replace MTL GSC flow.
Status encodeAuthenticateHuC(uint32_t rsaGgtt, Action &out);
Status validateAction(const Action &action);

// All callbacks and methods are serialized, non-reentrant. Ring pages and MMIO
// mapping outlive the transport through confirmed GuC stop. Coherent shared
// memory must NOT use whole-buffer bounce copies (host and GuC own different
// fields). acquire/release implement platform DMA ordering, not GPU completion.
struct Configuration;
struct Ops {
    void *opaque {};
    bool (*admitted)(void *, uint64_t epoch) {};
    bool (*authorizeAction)(void *, uint64_t epoch, const Action &) {};
    bool (*acquire)(void *) {};
    bool (*release)(void *) {};
    bool (*notify)(void *) {};
    // Prove CTB stopped and exact CPU/GGTT ranges, allocation ownership and
    // direct DMA coherency for this configuration before its first memory write.
    bool (*configurationAllowed)(void *, const Configuration &) {};
};
struct Cookie { uint64_t epoch {}; uint16_t fence {}; };
enum class ReplyState : uint8_t { Pending, Busy, Success, Failure, Retry, TimedOut, SentUnconfirmed };
struct Reply {
    Cookie cookie {};
    ReplyState state {ReplyState::Pending};
    uint32_t hxg[maxHxgWords] {}, count {};
    bool late {}, creditsHeld {};
};
struct Message { uint16_t fence {}; uint32_t hxg[maxHxgWords] {}, count {}; };

// Does not mark an engine job/fence complete. A successful control reply only
// means GuC processed that control request. FAST_REQUEST publication has no
// success acknowledgment. Use hardware seqno evidence for execution completion.
class Transport {
public:
    Transport() = default;
    Transport(const Transport &) = delete;
    Transport &operator=(const Transport &) = delete;
    // Descriptors must already be reset and CTB enabled by the actual mailbox
    // configuration. G2H may already hold unsolicited events after enable;
    // no writes occur when admission fails. One bind per object.
    Status attach(const Ring &h2g, const Ring &g2h, const Ops &, uint64_t epoch,
                  const MellowXe::FirmwareInfo &firmware);
    Status send(const Action &, uint64_t now, uint64_t deadline, Cookie &);
    Status receive(uint64_t epoch, uint64_t now, Message &);
    Status expire(uint64_t now);
    Status query(Cookie, Reply &) const;
    Status retire(Cookie); // cannot forget pending/timed-out response ownership
    uint32_t responseCredits() const { return credits_; }
    bool broken() const { return broken_; }
private:
    struct Pending {
        Reply reply {};
        uint64_t deadline {};
        uint32_t action {}, context {}, mode {}, reservation {};
        bool used {};
    };
    Ring h2g_ {}, g2h_ {};
    Ops ops_ {};
    Pending pending_[maxPending] {};
    uint64_t epoch_ {}, lastTime_ {};
    uint32_t hTail_ {}, gHead_ {}, credits_ {}, maxCredits_ {}, nextFence_ {};
    bool attached_ {}, broken_ {};
    Status fault(Status);
    Status clock(uint64_t);
    Status checkDescriptors();
    Pending *find(Cookie);
    const Pending *find(Cookie) const;
    Status dispatch(const Message &);
};

// This is a bounded, actual MMIO protocol engine. Wire it to checked BAR0 I/O;
// no register write is attempted without admission on every access. Admission
// must establish main GT/GMD, forcewake/runtime power, GuC hardware-authenticated
// and running, PF ownership and exact epoch. CSS metadata is insufficient.
struct MmioOps {
    void *opaque {};
    bool (*admitted)(void *, uint64_t epoch) {};
    bool (*read32)(void *, uint32_t offset, uint32_t &) {};
    bool (*write32)(void *, uint32_t offset, uint32_t) {};
    uint64_t (*nowMicros)(void *) {};
    void (*delayMicros)(void *, uint32_t) {};
};
class Mailbox {
public:
    explicit Mailbox(MmioOps ops, uint64_t epoch) : ops_(ops), epoch_(epoch) {}
    // SELF_CFG and CONTROL_CTB only. Busy/retry/timeouts never become success.
    Status exchange(const uint32_t *request, uint32_t count, uint32_t &response);
    bool poisoned() const { return poisoned_; }
    uint64_t epoch() const { return epoch_; }
private:
    MmioOps ops_ {};
    uint64_t epoch_ {};
    bool active_ {}, poisoned_ {};
};
struct Configuration {
    Ring h2g {}, g2h {};
    uint64_t epoch {}, minimumGgtt {}, limitGgtt {};
    MellowXe::FirmwareInfo firmware {};
};
// Caller must prove CTB stopped before invoking and keep backing memory pinned
// on ANY failure until confirmed stop/reset. Each six KLV acknowledgments and
// the final CONTROL_CTB acknowledgment is checked. No upload/auth is fabricated.
Status configureAndEnable(Mailbox &, const Configuration &, const Ops &);
}
