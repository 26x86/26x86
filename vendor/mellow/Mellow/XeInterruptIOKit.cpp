#include "XeInterruptIOKit.hpp"
OSDefineMetaClassAndStructors(MellowXeInterrupt,OSObject);

bool MellowXeInterrupt::admit(void *opaque,uint64_t epoch) {
    auto &s=*static_cast<MellowXeInterrupt *>(opaque);
    if (!s.mmio_ || !s.handlers_.admitted || !s.handlers_.admitted(s.handlers_.opaque,epoch)) return false;
    const auto &wake=s.mmio_->forceWake(); const auto &ip=wake.ip();
    return ip.architecture==12 && ip.release==70 && wake.held(MellowXe::WakeDomain::Gt);
}
XeInterrupt::Handling MellowXeInterrupt::identity(void *p,uint64_t epoch,const XeInterrupt::Identity &id) {
    auto &s=*static_cast<MellowXeInterrupt *>(p);
    return s.handlers_.identity(s.handlers_.opaque,epoch,id);
}
XeInterrupt::Handling MellowXeInterrupt::other(void *p,uint64_t epoch,uint32_t bits) {
    auto &s=*static_cast<MellowXeInterrupt *>(p);
    return s.handlers_.otherMaster(s.handlers_.opaque,epoch,bits);
}
bool MellowXeInterrupt::filter(OSObject *p,IOFilterInterruptEventSource *) {
    // Owner type was fixed by factory construction; no RTTI/allocations here.
    return static_cast<MellowXeInterrupt *>(p)->controller_.filter();
}
void MellowXeInterrupt::action(OSObject *p,IOInterruptEventSource *,int) {
    auto &s=*static_cast<MellowXeInterrupt *>(p);
    s.last_=s.controller_.service();
    if (s.last_==XeInterrupt::Status::Pending) s.source_->signalInterrupt();
    else if (s.last_!=XeInterrupt::Status::Ok && s.last_!=XeInterrupt::Status::Empty)
        s.source_->disable(); // fail closed; caller observes error and resets
}
XeInterrupt::Status MellowXeInterrupt::attach(IOPCIDevice *device,IOWorkLoop *loop,int index,
        MellowXe::IOKitMmio *mmio,const XeInterrupt::Configuration &config,const XeInterrupt::Ops &handlers) {
    using XeInterrupt::Status;
    if (source_ || loop_ || !device || !loop || !mmio || index<0 || !handlers.admitted ||
        !handlers.identity || !handlers.otherMaster || !loop->inGate()) return Status::Invalid;
    int type=0;
    if (device->getInterruptType(index,&type)!=kIOReturnSuccess) return Status::Unavailable;
    if (device->getBusNumber()!=0 || device->getDeviceNumber()!=2 || device->getFunctionNumber()!=0 ||
        device->configRead16(kIOPCIConfigVendorID)!=0x8086 ||
        device->configRead16(kIOPCIConfigDeviceID)!=0x7d41) return Status::Invalid;
    mmio_=mmio; handlers_=handlers; device_=device; device_->retain();
    source_=IOFilterInterruptEventSource::filterInterruptEventSource(this,action,filter,device,index);
    if (!source_) { mmio_=nullptr; device_->release(); device_=nullptr; return Status::Unavailable; }
    source_->disable();
    if (loop->addEventSource(source_)!=kIOReturnSuccess) {
        source_->release(); source_=nullptr; mmio_=nullptr;
        device_->release(); device_=nullptr; return Status::IoFailure;
    }
    loop_=loop; loop_->retain(); retain(); selfRetained_=true;
    XeInterrupt::Ops ops {mmio_->access(),this,admit,identity,other};
    last_=controller_.configure(config,ops);
    if (last_!=Status::Ok) {
        const Status saved=last_; detach(); last_=saved;
    }
    return last_;
}
XeInterrupt::Status MellowXeInterrupt::start() {
    if (!loop_ || !source_ || !loop_->inGate()) return XeInterrupt::Status::Invalid;
    source_->enable(); last_=controller_.start();
    if (last_!=XeInterrupt::Status::Ok) source_->disable();
    return last_;
}
XeInterrupt::Status MellowXeInterrupt::detach() {
    if (loop_ && !loop_->inGate()) return XeInterrupt::Status::Invalid;
    if (source_) source_->disable();
    last_=controller_.stop();
    // A failed/uncertain mask write cannot revoke the MMIO/owner lifetime.
    // Keep the disabled source registered and every reference for a gated retry.
    if (last_!=XeInterrupt::Status::Ok) return last_;
    if (source_) {
        if (loop_) loop_->removeEventSource(source_);
        source_->release(); source_=nullptr;
    }
    if (loop_) { loop_->release(); loop_=nullptr; }
    if (device_) { device_->release(); device_=nullptr; }
    mmio_=nullptr;
    const auto status=last_;
    if (selfRetained_) { selfRetained_=false; release(); }
    return status; // no member access after dropping the internal reference
}
void MellowXeInterrupt::free() {
    // attach holds an internal owner reference until successful gated detach,
    // so a caller dropping its reference cannot free a live interrupt owner.
    OSObject::free();
}
