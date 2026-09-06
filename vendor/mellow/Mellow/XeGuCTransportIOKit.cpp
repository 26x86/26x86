#include "XeGuCTransportIOKit.hpp"

namespace XeGuC {
bool IOKitBinding::admitted(void *opaque, uint64_t epoch) {
    auto &self = *static_cast<IOKitBinding *>(opaque);
    if (!epoch || epoch != self.epoch_ || !self.proofs_.ownsEpochAndLoadedImage ||
        !self.proofs_.ownsEpochAndLoadedImage(self.proofs_.opaque, epoch) ||
        !self.mmio_.forceWake().held(MellowXe::WakeDomain::Gt)) return false;
    const auto &ip = self.mmio_.forceWake().ip();
    if (ip.architecture != 12 || ip.release != 70) return false;
    const auto io = self.mmio_.access(); uint32_t status = 0;
    return io.read32 && io.read32(io.opaque, 0xc000, status) && statusAuthenticatedAndReady(status);
}
bool IOKitBinding::read(void *opaque, uint32_t reg, uint32_t &value) {
    auto &self = *static_cast<IOKitBinding *>(opaque);
    if (!admitted(opaque, self.epoch_) || reg < mainMailboxRegister ||
        reg > mainMailboxRegister + 12 || (reg & 3)) return false;
    const auto io = self.mmio_.access();
    return io.read32 && io.read32(io.opaque, reg, value);
}
bool IOKitBinding::write(void *opaque, uint32_t reg, uint32_t value) {
    auto &self = *static_cast<IOKitBinding *>(opaque);
    if (!admitted(opaque, self.epoch_) ||
        (reg != mainNotifyRegister && (reg < mainMailboxRegister || reg > mainMailboxRegister + 12 || (reg & 3)))) return false;
    if (reg == mainNotifyRegister && value != 0) return false;
    const auto io = self.mmio_.access();
    return io.write32 && io.write32(io.opaque, reg, value);
}
uint64_t IOKitBinding::now(void *opaque) {
    const auto io = static_cast<IOKitBinding *>(opaque)->mmio_.access();
    return io.nowMicros ? io.nowMicros(io.opaque) : 0;
}
void IOKitBinding::delay(void *opaque, uint32_t micros) {
    const auto io = static_cast<IOKitBinding *>(opaque)->mmio_.access();
    if (io.delayMicros) io.delayMicros(io.opaque, micros);
}
bool IOKitBinding::barrier(void *opaque) {
    auto &self = *static_cast<IOKitBinding *>(opaque);
    if (!admitted(opaque, self.epoch_)) return false;
    __sync_synchronize(); return true;
}
bool IOKitBinding::notify(void *opaque) { return write(opaque, mainNotifyRegister, 0); }
bool IOKitBinding::authorize(void *opaque, uint64_t epoch, const Action &action) {
    auto &self = *static_cast<IOKitBinding *>(opaque);
    return self.enabled_ && admitted(opaque, epoch) && self.proofs_.authorizeAction &&
        self.proofs_.authorizeAction(self.proofs_.opaque, epoch, action);
}
bool IOKitBinding::configuration(void *opaque, const Configuration &config) {
    auto &self = *static_cast<IOKitBinding *>(opaque);
    return self.configuring_ && admitted(opaque, config.epoch) && self.proofs_.configurationAllowed &&
        self.proofs_.configurationAllowed(self.proofs_.opaque, config);
}
MmioOps IOKitBinding::mailboxOps() { return {this, admitted, read, write, now, delay}; }
Ops IOKitBinding::transportOps() { return {this, admitted, authorize, barrier, barrier, notify, configuration}; }
Status IOKitBinding::startTransport(const Configuration &config, Transport &transport) {
    if (attempted_) return Status::Busy;
    if (config.epoch != epoch_) return Status::StaleEpoch;
    if (!admitted(this, epoch_)) return Status::Unavailable;
    attempted_ = configuring_ = true;
    Mailbox mailbox(mailboxOps(), epoch_);
    const Status status = configureAndEnable(mailbox, config, transportOps());
    configuring_ = false;
    if (status != Status::Ok) return status;
    enabled_ = true; // CONTROL_CTB acknowledged; still no context/job readiness
    return transport.attach(config.h2g, config.g2h, transportOps(), epoch_, config.firmware);
}
}
