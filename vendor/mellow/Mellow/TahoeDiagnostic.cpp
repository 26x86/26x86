// Local diagnostic IOService/IOUserClient, 2026. See LICENSE and NOTICE.
// Public SDK/source contracts and retained header hashes: docs/TAHOE-DRIVER-IMPLEMENTATION.md.
#include "TahoeDiagnostic.hpp"
#include "RuntimeReadiness.hpp"
#include <Headers/kern_util.hpp>
#include <IOKit/IOLib.h>
#include <libkern/libkern.h>

OSDefineMetaClassAndStructors(MellowTahoeDiagnostic, IOService)
OSDefineMetaClassAndStructors(MellowTahoeDiagnosticClient, IOUserClient)

static bool admitted(IOPCIDevice *pci) {
    return pci && static_cast<unsigned>(getKernelVersion()) == 25 && checkKernelArgument("-mellowdiag") &&
        pci->getBusNumber() == 0 && pci->getDeviceNumber() == 2 && pci->getFunctionNumber() == 0 &&
        pci->configRead16(kIOPCIConfigVendorID) == 0x8086 && pci->configRead16(kIOPCIConfigDeviceID) == 0x7d41;
}
IOService *MellowTahoeDiagnostic::probe(IOService *provider, SInt32 *score) {
    if (!admitted(OSDynamicCast(IOPCIDevice, provider))) return nullptr;
    return IOService::probe(provider, score);
}
bool MellowTahoeDiagnostic::start(IOService *provider) {
    auto *pci = OSDynamicCast(IOPCIDevice, provider);
    if (!admitted(pci) || !IOService::start(provider)) return false;
    superStarted_ = true;
    lock_ = IOLockAlloc();
    if (!lock_) return failStart(provider);
    // No seize, bus-master enable, PCI config write or takeover of another owner.
    if (!pci->open(this)) return failStart(provider);
    pci_ = pci; pci_->retain();
    UInt8 pmOffset = 0;
    const UInt32 pm = pci_->findPCICapability(kIOPCIPowerManagementCapability, &pmOffset);
    // IOPCIDevice's own PM implementation uses capability+4 for PMCSR.
    // Refuse unavailable/non-D0 state; do not negotiate or alter power here.
    if (!pm || pm == UINT32_MAX || pmOffset < 0x40 || pmOffset > 0xf8 || (pmOffset & 3)) return failStart(provider);
    const UInt16 pmcsr = pci_->configRead16(static_cast<UInt8>(pmOffset + 4));
    if (pmcsr == UINT16_MAX || (pmcsr & kPCIPMCSPowerStateMask) != kPCIPMCSPowerStateD0) return failStart(provider);
    if (mmio_.attach(pci_) != MellowXe::MmioStatus::Ok) return failStart(provider);
    attached_ = true;
    // Apple's copyMapperForDevice waits indefinitely for indirect iommu-parent
    // identifiers. This diagnostic only admits an already attached mapper object.
    // No global/identity mapper fallback and no boot-time wait for a missing one.
    auto *mapperProperty = pci_->copyProperty("iommu-parent");
    if (OSDynamicCast(IOMapper, mapperProperty)) dma_.mapper = IOMapper::copyMapperForDevice(pci_);
    if (mapperProperty) mapperProperty->release();
    dma_.maxAllocationBytes = dma_.maxPinnedBytes = MELLOW_DIAG_MAX_BYTES;
    const auto ip = mmio_.forceWake().ip();
    XeMemory::Backend backend {};
    if (dma_.mapper) backend = XeMemory::makeIOKitPinBackend(dma_);
    const uint64_t evidence = MellowRuntime::BootOptIn | MellowRuntime::PhysicalIdentity7D41 |
        MellowRuntime::Bar0Mapped | MellowRuntime::GmdArchitecture1270;
    if (!session_.initialize({0x8086, 0x7d41, ip.architecture, ip.release}, true, backend, evidence)) {
        return failStart(provider);
    }
    setProperty("MellowDiagnosticOnly", true);
    setProperty("MellowDiagnosticABI", static_cast<uint64_t>(MELLOW_DIAG_ABI_VERSION), 32);
    setProperty("MellowPreparedDmaAvailable", dma_.mapper != nullptr);
    setProperty("MellowGpuSubmissionSupported", false);
    setProperty("MellowMetalSupported", false);
    IOLog("MellowDiag: physical 8086:7d41 BAR0/GMD 12.70 read; prepared-DMA available=%d; GPU/Metal unverified\n", dma_.mapper != nullptr);
    registerService();
    return true;
}
bool MellowTahoeDiagnostic::failStart(IOService *provider) {
    // No user clients can exist before registerService; the unwind is serialized
    // here and balances every successful superclass start even on early failure.
    cleanup();
    if (superStarted_) { superStarted_ = false; IOService::stop(provider); }
    return false;
}
void MellowTahoeDiagnostic::retainQuarantine() {
    if (session_.quarantined() && !quarantineHold_) { quarantineHold_ = true; retain(); }
}
void MellowTahoeDiagnostic::cleanup() {
    // Called under the sleepable mutex or before service publication.
    stopping_ = true; client_ = nullptr;
    session_.stop();
    if (session_.hasResources()) {
        // Uncertain IODMACommand/descriptor teardown must not dangle its context.
        // Keep this diagnostic owner and mapper alive. Nothing was GPU-published.
        retainQuarantine();
        IOLog("MellowDiag: DMA cleanup quarantined; retained owner, no success claimed\n");
        return;
    }
    if (dma_.mapper) { dma_.mapper->release(); dma_.mapper = nullptr; }
    if (attached_) { mmio_.detach(); attached_ = false; }
    if (pci_) { pci_->close(this); pci_->release(); pci_ = nullptr; }
}
void MellowTahoeDiagnostic::stop(IOService *provider) {
    if (lock_) { IOLockLock(lock_); cleanup(); IOLockUnlock(lock_); }
    if (superStarted_) { superStarted_ = false; IOService::stop(provider); }
}
void MellowTahoeDiagnostic::free() {
    // A quarantine self-retain prevents this path while prepared memory remains.
    if (lock_) { IOLockLock(lock_); cleanup(); IOLockUnlock(lock_); IOLockFree(lock_); lock_ = nullptr; }
    IOService::free();
}
bool MellowTahoeDiagnostic::openDiagnostic(MellowTahoeDiagnosticClient *client, uint64_t &token) {
    if (!lock_) return false;
    IOLockLock(lock_);
    const bool ok = !stopping_ && !client_ && nextOwner_ && nextOwner_ != UINT64_MAX && session_.open(nextOwner_);
    if (ok) { token = nextOwner_++; client_ = client; }
    IOLockUnlock(lock_); return ok;
}
IOReturn MellowTahoeDiagnostic::closeDiagnostic(MellowTahoeDiagnosticClient *client, uint64_t token) {
    if (!lock_) return kIOReturnNotReady;
    IOLockLock(lock_);
    IOReturn result = kIOReturnSuccess;
    if (client_ == client && session_.owns(token)) {
        if (session_.close(token) != MellowDiagOk) { result = kIOReturnError; retainQuarantine(); }
        client_ = nullptr;
    }
    IOLockUnlock(lock_); return result;
}
IOReturn MellowTahoeDiagnostic::callDiagnostic(MellowTahoeDiagnosticClient *client, uint64_t token,
        uint32_t selector, const MellowDiagRequest &request, MellowDiagReply &reply) {
    if (!lock_) return kIOReturnNotReady;
    IOLockLock(lock_);
    const bool active = !stopping_ && client_ == client && session_.owns(token);
    if (active) { session_.call(token, selector, request, reply); retainQuarantine(); }
    IOLockUnlock(lock_);
    return active ? kIOReturnSuccess : kIOReturnNotReady;
}
IOReturn MellowTahoeDiagnostic::newUserClient(task_t task, void *security, UInt32 type,
        OSDictionary *properties, IOUserClient **handler) {
    if (!handler) return kIOReturnBadArgument;
    *handler = nullptr;
    if (type != MELLOW_DIAG_CONNECT_TYPE ||
        IOUserClient::clientHasPrivilege(task, kIOClientPrivilegeAdministrator) != kIOReturnSuccess)
        return kIOReturnNotPrivileged;
    auto *client = new MellowTahoeDiagnosticClient;
    if (!client) return kIOReturnNoMemory;
    if (!client->initWithTask(task, security, type, properties)) { client->release(); return kIOReturnError; }
    if (!client->attach(this)) { client->release(); return kIOReturnError; }
    if (!client->start(this)) { client->detach(this); client->release(); return kIOReturnExclusiveAccess; }
    *handler = client; return kIOReturnSuccess;
}
bool MellowTahoeDiagnosticClient::initWithTask(task_t task, void *security, UInt32 type, OSDictionary *properties) {
    return task && type == MELLOW_DIAG_CONNECT_TYPE &&
        clientHasPrivilege(task, kIOClientPrivilegeAdministrator) == kIOReturnSuccess &&
        IOUserClient::initWithTask(task, security, type, properties);
}
bool MellowTahoeDiagnosticClient::start(IOService *provider) {
    auto *owner = OSDynamicCast(MellowTahoeDiagnostic, provider);
    if (!owner || !IOUserClient::start(provider)) return false;
    if (!owner->openDiagnostic(this, token_)) { IOUserClient::stop(provider); return false; }
    owner_ = owner; owner_->retain(); return true;
}
IOReturn MellowTahoeDiagnosticClient::clientClose() {
    const IOReturn result = owner_ ? owner_->closeDiagnostic(this, token_) : kIOReturnSuccess;
    terminate(); return result;
}
void MellowTahoeDiagnosticClient::stop(IOService *provider) {
    if (owner_) owner_->closeDiagnostic(this, token_);
    IOUserClient::stop(provider);
}
void MellowTahoeDiagnosticClient::free() {
    if (owner_) { owner_->closeDiagnostic(this, token_); owner_->release(); owner_ = nullptr; }
    IOUserClient::free();
}
IOReturn MellowTahoeDiagnosticClient::externalMethod(uint32_t selector, IOExternalMethodArguments *args,
        IOExternalMethodDispatch *, OSObject *, void *) {
    if (clientHasPrivilege(current_task(), kIOClientPrivilegeAdministrator) != kIOReturnSuccess)
        return kIOReturnNotPrivileged;
    if (!args || selector > MellowDiagRelease || args->scalarInputCount || args->scalarOutputCount ||
        args->asyncWakePort || args->asyncReferenceCount || args->structureInputDescriptor ||
        args->structureOutputDescriptor || args->structureVariableOutputData ||
        args->structureInputSize != sizeof(MellowDiagRequest) || args->structureOutputSize != sizeof(MellowDiagReply) ||
        !args->structureInput || !args->structureOutput) return kIOReturnBadArgument;
    if (!owner_) return kIOReturnNotReady;
    MellowDiagRequest request {}; MellowDiagReply reply {};
    memcpy(&request, args->structureInput, sizeof(request));
    const IOReturn result = owner_->callDiagnostic(this, token_, selector, request, reply);
    if (result == kIOReturnSuccess) { memcpy(args->structureOutput, &reply, sizeof(reply)); args->structureOutputSize = sizeof(reply); }
    return result;
}
