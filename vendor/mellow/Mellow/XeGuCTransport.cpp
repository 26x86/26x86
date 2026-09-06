// Local implementation from pinned Intel MIT ABI; see docs/XE-GUC-TRANSPORT.md.
#include "XeGuCTransport.hpp"

namespace XeGuC {
bool statusAuthenticatedAndReady(uint32_t s) {
    return s != UINT32_MAX && (s & 0xc0000000U) == 0x80000000U &&
        (s & 0x0000ff00U) == 0x0000f000U && (s & 0x000000feU) == 0xec &&
        !(s & 0x00020001U);
}
static bool idValid(uint32_t id) { return id < 65535; }
Status encodeRegister(uint32_t id, uint32_t cls, uint32_t mask, uint64_t lrc, Action &a) {
    a = {};
    if (!idValid(id) || (cls != 0 && cls != 4) || !mask || !lrc) return Status::Invalid;
    a.count = 12; a.words[0] = 0x4502; a.words[1] = 1; a.words[2] = id;
    a.words[3] = cls; a.words[4] = mask;
    a.words[10] = uint32_t(lrc); a.words[11] = uint32_t(lrc >> 32);
    return Status::Ok;
}
Status encodeSchedule(uint32_t id, Action &a) {
    a = {}; if (!idValid(id)) return Status::Invalid;
    a.count = 2; a.words[0] = 0x1000; a.words[1] = id; return Status::Ok;
}
Status encodeMode(uint32_t id, bool enable, Action &a) {
    if (encodeSchedule(id, a) != Status::Ok) return Status::Invalid;
    a.count = 3; a.words[0] = 0x1001; a.words[2] = enable ? 1 : 0; return Status::Ok;
}
Status encodeDeregister(uint32_t id, Action &a) {
    if (encodeSchedule(id, a) != Status::Ok) return Status::Invalid;
    a.words[0] = 0x4503; return Status::Ok;
}
Status encodeAuthenticateHuC(uint32_t address, Action &a) {
    a = {}; if (!address || (address & 3)) return Status::Invalid;
    a.count = 2; a.words[0] = 0x4000; a.words[1] = address; return Status::Ok;
}
Status validateAction(const Action &a) {
    if (!a.count || a.count > 12) return Status::Invalid;
    switch (a.words[0]) {
    case 0x4502:
        if (a.count != 12 || a.words[1] != 1 || !idValid(a.words[2]) ||
            (a.words[3] != 0 && a.words[3] != 4) || !a.words[4] ||
            (!a.words[10] && !a.words[11])) return Status::Invalid;
        for (unsigned i = 5; i < 10; ++i) if (a.words[i]) return Status::Invalid;
        return Status::Ok;
    case 0x1000: case 0x4503:
        return a.count == 2 && idValid(a.words[1]) ? Status::Ok : Status::Invalid;
    case 0x1001:
        return a.count == 3 && idValid(a.words[1]) && a.words[2] <= 1 ? Status::Ok : Status::Invalid;
    case 0x4000:
        return a.count == 2 && a.words[1] && !(a.words[1] & 3) ? Status::Ok : Status::Invalid;
    default: return Status::Invalid;
    }
}
static bool ringValid(const Ring &r) {
    return r.descriptor && r.words && !(uintptr_t(r.descriptor) & 3) &&
        !(uintptr_t(r.words) & 3) && r.count >= 1024 && r.count <= (1U << 20) &&
        !(r.count & (r.count - 1));
}
static bool abiValid(const MellowXe::FirmwareInfo &f) {
    return f.release.packed() == MellowXe::gucRecommendedRelease &&
        f.submission.packed() == requiredSubmissionAbi;
}
Status Transport::fault(Status s) { broken_ = true; return s; }
Status Transport::clock(uint64_t now) {
    if (now < lastTime_) return Status::Invalid;
    lastTime_ = now; return Status::Ok;
}
Status Transport::attach(const Ring &h, const Ring &g, const Ops &ops, uint64_t epoch,
                         const MellowXe::FirmwareInfo &f) {
    if (attached_ || !epoch || !ringValid(h) || !ringValid(g) || !abiValid(f)) return Status::Invalid;
    if (!ops.admitted || !ops.authorizeAction || !ops.acquire || !ops.release || !ops.notify ||
        !ops.admitted(ops.opaque, epoch)) return Status::Unavailable;
    if (!ops.acquire(ops.opaque)) return Status::IoFailure;
    if (h.descriptor->head || h.descriptor->tail || h.descriptor->status ||
        g.descriptor->head || g.descriptor->tail >= g.count || g.descriptor->status) return Status::Corrupt;
    h2g_ = h; g2h_ = g; ops_ = ops; epoch_ = epoch;
    maxCredits_ = credits_ = g.count - 1 - g.count / 2;
    attached_ = true; return Status::Ok;
}
Status Transport::checkDescriptors() {
    if (!attached_) return Status::Unavailable;
    if (broken_) return Status::Corrupt;
    if (!ops_.admitted(ops_.opaque, epoch_)) return fault(Status::Unavailable);
    if (!ops_.acquire(ops_.opaque)) return fault(Status::IoFailure);
    if (h2g_.descriptor->status || g2h_.descriptor->status ||
        h2g_.descriptor->tail != hTail_ || g2h_.descriptor->head != gHead_ ||
        h2g_.descriptor->head >= h2g_.count || g2h_.descriptor->tail >= g2h_.count)
        return fault(Status::Corrupt);
    return Status::Ok;
}
Transport::Pending *Transport::find(Cookie c) {
    for (auto &p : pending_) if (p.used && p.reply.cookie.epoch == c.epoch &&
        p.reply.cookie.fence == c.fence) return &p;
    return nullptr;
}
const Transport::Pending *Transport::find(Cookie c) const {
    for (const auto &p : pending_) if (p.used && p.reply.cookie.epoch == c.epoch &&
        p.reply.cookie.fence == c.fence) return &p;
    return nullptr;
}
Status Transport::send(const Action &input, uint64_t now, uint64_t deadline, Cookie &cookie) {
    cookie = {};
    const Action a = input; // immutable wire snapshot before validation/admission
    if (validateAction(a) != Status::Ok || deadline <= now || clock(now) != Status::Ok)
        return Status::Invalid;
    Status s = checkDescriptors(); if (s != Status::Ok) return s;
    if (!ops_.authorizeAction(ops_.opaque, epoch_, a)) return Status::Unavailable;
    if (nextFence_ >= 0x8000) return Status::Exhausted; // no cookie reuse within epoch
    const bool request = a.words[0] == 0x4000;
    const uint32_t reserve = request ? 256 : a.words[0] == 0x1001 ? 4 : a.words[0] == 0x4503 ? 3 : 0;
    Pending *slot = nullptr;
    for (auto &p : pending_) {
        if (!p.used) slot = &p;
        // GuC event replies carry context, not a response-cookie guarantee.
        if (p.used && p.reply.creditsHeld && !request && p.context == a.words[1] &&
            (p.action == 0x1001 || p.action == 0x4503)) return Status::Busy;
    }
    if (!slot || (reserve && credits_ <= reserve)) return Status::Busy;
    uint32_t head = h2g_.descriptor->head;
    uint32_t space = (head - hTail_ - 1) & (h2g_.count - 1);
    const uint32_t length = a.count + 1;
    if (space < length) return Status::Busy;
    // H2G messages must be contiguous. Zero-length CT headers are padding NOPs.
    if (hTail_ + length > h2g_.count) {
        const uint32_t padding = h2g_.count - hTail_;
        for (uint32_t i = hTail_; i < h2g_.count; ++i) h2g_.words[i] = 0;
        if (!ops_.release(ops_.opaque)) return fault(Status::IoFailure);
        hTail_ = 0; h2g_.descriptor->tail = 0;
        if (!ops_.release(ops_.opaque) || !ops_.notify(ops_.opaque)) return fault(Status::IoFailure);
        space -= padding;
        if (space < length) return Status::Busy; // caller retries after peer consumes padding
    }
    *slot = {};
    slot->used = true; slot->deadline = deadline; slot->action = a.words[0];
    slot->context = a.words[1]; slot->mode = a.words[2]; slot->reservation = reserve;
    slot->reply.cookie = Cookie{epoch_, uint16_t(nextFence_++ | (request ? 0 : 0x8000))};
    slot->reply.creditsHeld = reserve != 0;
    slot->reply.state = reserve ? ReplyState::Pending : ReplyState::SentUnconfirmed;
    credits_ -= reserve;
    cookie = slot->reply.cookie;
    h2g_.words[hTail_] = (uint32_t(cookie.fence) << 16) | a.count;
    h2g_.words[hTail_ + 1] = a.words[0] | (request ? 0 : 0x20000000U);
    for (uint32_t i = 1; i < a.count; ++i) h2g_.words[hTail_ + 1 + i] = a.words[i];
    if (!ops_.release(ops_.opaque)) return fault(Status::PublishedUnknown);
    hTail_ = (hTail_ + length) & (h2g_.count - 1);
    h2g_.descriptor->tail = hTail_;
    if (!ops_.release(ops_.opaque) || !ops_.notify(ops_.opaque)) return fault(Status::PublishedUnknown);
    return Status::Ok; // enqueued, not GuC acknowledgment or GPU completion
}
Status Transport::expire(uint64_t now) {
    if (clock(now) != Status::Ok) return Status::Invalid;
    for (auto &p : pending_) if (p.used && p.reply.creditsHeld && now >= p.deadline &&
        p.reply.state != ReplyState::TimedOut) p.reply.state = ReplyState::TimedOut;
    return Status::Ok;
}
Status Transport::dispatch(const Message &m) {
    const uint32_t header = m.hxg[0], type = (header >> 28) & 7;
    if (!(header & 0x80000000U)) return fault(Status::Corrupt);
    Pending *p = nullptr;
    if (type == 1) {
        const uint32_t action = header & 0xffff;
        if (action != 0x1002 && action != 0x4600)
            return Status::Ok; // caller receives unsolicited event; no credit invented
        if ((header & 0x0fff0000U) || m.count != (action == 0x1002 ? 3U : 2U) || !idValid(m.hxg[1]))
            return fault(Status::Corrupt);
        for (auto &candidate : pending_) if (candidate.used && candidate.reply.creditsHeld &&
            candidate.context == m.hxg[1] &&
            candidate.action == (action == 0x1002 ? 0x1001U : 0x4503U)) p = &candidate;
        if (!p || (action == 0x1002 && m.hxg[2] != p->mode)) return fault(Status::Corrupt);
    } else {
        if (type != 3 && type != 5 && type != 6 && type != 7) return fault(Status::Corrupt);
        if (type != 7 && m.count != 1) return fault(Status::Corrupt);
        p = find(Cookie{epoch_, m.fence});
        if (!p) return fault(Status::UnknownCookie);
        if ((m.fence & 0x8000) && type != 6) return fault(Status::Corrupt);
        if (!(m.fence & 0x8000) && !p->reply.creditsHeld) return fault(Status::Corrupt);
    }
    p->reply.count = m.count;
    for (unsigned i = 0; i < m.count; ++i) p->reply.hxg[i] = m.hxg[i];
    const bool timedOut = p->reply.state == ReplyState::TimedOut;
    if (type == 3) {
        if (!timedOut) p->reply.state = ReplyState::Busy;
        return Status::Ok; // intermediate BUSY retains original absolute deadline
    }
    if (p->reply.creditsHeld) {
        if (p->reservation > maxCredits_ - credits_) return fault(Status::Corrupt);
        credits_ += p->reservation; p->reply.creditsHeld = false;
    }
    if (timedOut) p->reply.late = true;
    else p->reply.state = type == 6 ? ReplyState::Failure : type == 5 ? ReplyState::Retry : ReplyState::Success;
    return Status::Ok;
}
Status Transport::receive(uint64_t epoch, uint64_t now, Message &message) {
    message = {};
    if (epoch != epoch_) return Status::StaleEpoch;
    if (expire(now) != Status::Ok) return Status::Invalid;
    Status s = checkDescriptors(); if (s != Status::Ok) return s;
    const uint32_t tail = g2h_.descriptor->tail;
    // acquire AFTER observing peer's published tail, before reading its payload.
    if (!ops_.acquire(ops_.opaque)) return fault(Status::IoFailure);
    const uint32_t available = (tail - gHead_) & (g2h_.count - 1);
    if (!available) return Status::Empty;
    const uint32_t header = g2h_.words[gHead_];
    const uint32_t count = header & 255;
    if ((header & 0x0000ff00U) || !count || count + 1 > available) return fault(Status::Corrupt);
    message.fence = uint16_t(header >> 16); message.count = count;
    for (uint32_t i = 0; i < count; ++i)
        message.hxg[i] = g2h_.words[(gHead_ + 1 + i) & (g2h_.count - 1)];
    s = dispatch(message);
    if (s != Status::Ok) return s;
    // Peer may reuse consumed words only after the complete snapshot is read.
    if (!ops_.release(ops_.opaque)) return fault(Status::IoFailure);
    gHead_ = (gHead_ + 1 + count) & (g2h_.count - 1);
    g2h_.descriptor->head = gHead_;
    if (!ops_.release(ops_.opaque)) return fault(Status::IoFailure);
    return Status::Ok;
}
Status Transport::query(Cookie cookie, Reply &reply) const {
    if (cookie.epoch != epoch_) return Status::StaleEpoch;
    const Pending *p = find(cookie); if (!p) return Status::UnknownCookie;
    reply = p->reply; return Status::Ok;
}
Status Transport::retire(Cookie cookie) {
    if (cookie.epoch != epoch_) return Status::StaleEpoch;
    Pending *p = find(cookie); if (!p) return Status::UnknownCookie;
    if (p->reply.creditsHeld) return Status::Busy;
    *p = {}; return Status::Ok;
}

Status Mailbox::exchange(const uint32_t *input, uint32_t count, uint32_t &response) {
    response = 0;
    if (!input || !count || count > 4) return Status::Invalid;
    uint32_t request[4] {};
    for (unsigned i = 0; i < count; ++i) request[i] = input[i];
    const uint32_t key = request[1] >> 16;
    const uint32_t klvLength = key == 0x904 || key == 0x907 ? 1 : 2;
    if (!((count == 4 && request[0] == 0x508 &&
           key >= 0x902 && key <= 0x907 && uint16_t(request[1]) == klvLength &&
           (uint16_t(request[1]) == 2 || !request[3])) ||
          (count == 2 && request[0] == 0x4509 && request[1] <= 1))) return Status::Invalid;
    if (active_) return Status::Busy;
    if (poisoned_) return Status::Corrupt;
    if (!epoch_ || !ops_.admitted || !ops_.read32 || !ops_.write32 || !ops_.nowMicros ||
        !ops_.delayMicros || !ops_.admitted(ops_.opaque, epoch_)) return Status::Unavailable;
    active_ = true;
    auto finish = [&](Status s, bool uncertain) {
        active_ = false; if (uncertain) poisoned_ = true; return s;
    };
    auto read = [&](uint32_t offset, uint32_t &value) {
        return ops_.admitted(ops_.opaque, epoch_) && ops_.read32(ops_.opaque, offset, value);
    };
    auto write = [&](uint32_t offset, uint32_t value) {
        return ops_.admitted(ops_.opaque, epoch_) && ops_.write32(ops_.opaque, offset, value);
    };
    for (unsigned i = 0; i < count; ++i)
        if (!write(mainMailboxRegister + i * 4, request[i])) return finish(Status::IoFailure, true);
    uint32_t header = 0;
    if (!read(mainMailboxRegister + 12, header) || !write(mainNotifyRegister, 0))
        return finish(Status::IoFailure, true);
    const uint64_t start = ops_.nowMicros(ops_.opaque);
    uint64_t last = start, busyStart = 0;
    bool seenBusy = false;
    // Independent iteration bound also catches a stuck clock/delay callback.
    for (uint32_t poll = 0; poll < 2052; ++poll) {
        if (!read(mainMailboxRegister, header) || header == UINT32_MAX)
            return finish(Status::IoFailure, true);
        const uint64_t now = ops_.nowMicros(ops_.opaque);
        if (now < last) return finish(Status::IoFailure, true);
        last = now;
        if ((!seenBusy && now - start >= 50000) || (seenBusy && now - busyStart >= 2000000))
            return finish(Status::Timeout, true);
        if (header & 0x80000000U) {
            const uint32_t type = (header >> 28) & 7;
            if (type == 7) { response = header & 0x0fffffffU; return finish(Status::Ok, false); }
            if (type == 6) { response = header; return finish(Status::Rejected, false); }
            if (type == 5) { response = header; return finish(Status::Retry, false); }
            if (type != 3) return finish(Status::Corrupt, true);
            if (!seenBusy) { seenBusy = true; busyStart = now; }
        } else if (seenBusy) return finish(Status::Corrupt, true);
        ops_.delayMicros(ops_.opaque, 1000);
    }
    return finish(Status::Timeout, true);
}
static bool range(uint64_t base, uint64_t bytes, uint64_t minimum, uint64_t limit) {
    return base >= minimum && base < limit && bytes <= limit - base;
}
Status configureAndEnable(Mailbox &mailbox, const Configuration &c, const Ops &ops) {
    if (!c.epoch || c.epoch != mailbox.epoch() || !ringValid(c.h2g) || !ringValid(c.g2h) || !abiValid(c.firmware) ||
        c.minimumGgtt >= c.limitGgtt || c.limitGgtt > (1ULL << 32)) return Status::Invalid;
    const uint64_t base[] = {c.h2g.descriptorGgtt, c.h2g.bufferGgtt, c.g2h.descriptorGgtt, c.g2h.bufferGgtt};
    const uint64_t size[] = {64, uint64_t(c.h2g.count) * 4, 64, uint64_t(c.g2h.count) * 4};
    for (unsigned i = 0; i < 4; ++i) {
        if ((base[i] & ((i & 1) ? 4095 : 63)) ||
            !range(base[i], size[i], c.minimumGgtt, c.limitGgtt)) return Status::Invalid;
        for (unsigned j = 0; j < i; ++j)
            if (base[i] < base[j] + size[j] && base[j] < base[i] + size[i]) return Status::Invalid;
    }
    if (!ops.admitted || !ops.release || !ops.configurationAllowed ||
        !ops.admitted(ops.opaque, c.epoch) || !ops.configurationAllowed(ops.opaque, c)) return Status::Unavailable;
    const Ring *rings[] = {&c.h2g, &c.g2h};
    for (const Ring *r : rings) {
        r->descriptor->head = r->descriptor->tail = r->descriptor->status = 0;
        for (unsigned i = 0; i < 13; ++i) r->descriptor->reserved[i] = 0;
        for (uint32_t i = 0; i < r->count; ++i) r->words[i] = 0;
    }
    if (!ops.release(ops.opaque)) return Status::IoFailure;
    const uint16_t keys[] = {0x903, 0x902, 0x904, 0x906, 0x905, 0x907};
    const uint64_t values[] = {base[0], base[1], size[1], base[2], base[3], size[3]};
    for (unsigned i = 0; i < 6; ++i) {
        if (!ops.admitted(ops.opaque, c.epoch)) return Status::Unavailable;
        const uint32_t request[] = {0x508, (uint32_t(keys[i]) << 16) | (i % 3 == 2 ? 1U : 2U),
                                   uint32_t(values[i]), uint32_t(values[i] >> 32)};
        uint32_t response = 0;
        const Status s = mailbox.exchange(request, 4, response);
        if (s != Status::Ok) return s;
        if (response != 1) return Status::Rejected;
    }
    const uint32_t enable[] = {0x4509, 1}; uint32_t response = 0;
    const Status s = mailbox.exchange(enable, 2, response);
    return s == Status::Ok && response != 0 ? Status::Corrupt : s;
}
}
