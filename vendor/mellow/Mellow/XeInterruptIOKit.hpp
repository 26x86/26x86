// Local IOKit delivery adapter. No runtime execution has been performed.
#pragma once
#include "XeInterrupt.hpp"
#include "XeMmioIOKit.hpp"
#include <IOKit/IOFilterInterruptEventSource.h>
#include <IOKit/IOWorkLoop.h>

class MellowXeInterrupt : public OSObject {
    OSDeclareDefaultStructors(MellowXeInterrupt);
public:
    // Call attach/start/detach on the supplied workloop gate. The mmio owner
    // and callback objects outlive successful detach. IRQ index is supplied by
    // actual provider enumeration; no assumed MSI vector or global IRQ number.
    XeInterrupt::Status attach(IOPCIDevice *, IOWorkLoop *, int index,
                              MellowXe::IOKitMmio *, const XeInterrupt::Configuration &,
                              const XeInterrupt::Ops &handlers);
    XeInterrupt::Status start();
    XeInterrupt::Status detach();
    XeInterrupt::Status lastStatus() const { return last_; }
    void free() override;
private:
    MellowXe::IOKitMmio *mmio_ {};
    IOPCIDevice *device_ {};
    IOFilterInterruptEventSource *source_ {};
    IOWorkLoop *loop_ {};
    XeInterrupt::Controller controller_ {};
    XeInterrupt::Ops handlers_ {};
    XeInterrupt::Status last_ {XeInterrupt::Status::Empty};
    bool selfRetained_ {};
    static bool admit(void *, uint64_t);
    static XeInterrupt::Handling identity(void *,uint64_t,const XeInterrupt::Identity &);
    static XeInterrupt::Handling other(void *,uint64_t,uint32_t);
    static bool filter(OSObject *,IOFilterInterruptEventSource *);
    static void action(OSObject *,IOInterruptEventSource *,int);
};
