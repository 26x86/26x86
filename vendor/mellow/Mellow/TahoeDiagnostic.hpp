// Local IOKit diagnostic owner, 2026. See repository LICENSE and NOTICE.
#pragma once
#include "TahoeDiagnosticProtocol.hpp"
#include "XeMemoryIOKit.hpp"
#include "XeMmioIOKit.hpp"
#include <IOKit/IOUserClient.h>
#include <IOKit/IOLocks.h>
class MellowTahoeDiagnosticClient;
class MellowTahoeDiagnostic : public IOService {
    OSDeclareDefaultStructors(MellowTahoeDiagnostic)
public:
    IOService *probe(IOService *, SInt32 *) override;
    bool start(IOService *) override;
    void stop(IOService *) override;
    void free() override;
    IOReturn newUserClient(task_t, void *, UInt32, OSDictionary *, IOUserClient **) override;
    bool openDiagnostic(MellowTahoeDiagnosticClient *, uint64_t &);
    IOReturn callDiagnostic(MellowTahoeDiagnosticClient *, uint64_t, uint32_t,
                           const MellowDiagRequest &, MellowDiagReply &);
    IOReturn closeDiagnostic(MellowTahoeDiagnosticClient *, uint64_t);
private:
    IOLock *lock_ {};
    IOPCIDevice *pci_ {};
    MellowXe::IOKitMmio mmio_ {};
    XeMemory::IOKitContext dma_ {};
    MellowDiagnostic::Session session_ {};
    MellowTahoeDiagnosticClient *client_ {};
    uint64_t nextOwner_ {1};
    bool attached_ {}, stopping_ {}, quarantineHold_ {}, superStarted_ {};
    void cleanup();
    void retainQuarantine();
    bool failStart(IOService *);
};
class MellowTahoeDiagnosticClient : public IOUserClient {
    OSDeclareDefaultStructors(MellowTahoeDiagnosticClient)
public:
    bool initWithTask(task_t, void *, UInt32, OSDictionary *) override;
    bool start(IOService *) override;
    void stop(IOService *) override;
    void free() override;
    IOReturn clientClose() override;
    IOReturn externalMethod(uint32_t, IOExternalMethodArguments *, IOExternalMethodDispatch * = nullptr,
                           OSObject * = nullptr, void * = nullptr) override;
private:
    MellowTahoeDiagnostic *owner_ {};
    uint64_t token_ {};
};
