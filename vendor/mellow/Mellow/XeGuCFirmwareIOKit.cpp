#include "XeGuCFirmwareIOKit.hpp"

namespace XeGuCFirmware {
bool IOKitBinding::admitted(void *opaque,uint64_t owner,uint64_t epoch) {
    auto &self=*static_cast<IOKitBinding *>(opaque);auto &device=self.device_;
    if(!owner || !epoch || !self.proofs_.ownsEpoch || !self.proofs_.ownsEpoch(self.proofs_.opaque,owner,epoch) ||
        device.getBusNumber()!=0 || device.getDeviceNumber()!=2 || device.getFunctionNumber()!=0 ||
        device.configRead16(0)!=0x8086 || device.configRead16(2)!=0x7d41)return false;
    const uint16_t command=device.configRead16(4);
    if(command==0xffff || (command&6)!=6)return false; // real MMIO decode and bus mastering
    if(!self.mmio_.forceWake().held(MellowXe::WakeDomain::Gt))return false;
    const auto &ip=self.mmio_.forceWake().ip();if(ip.architecture!=12 || ip.release!=70)return false;
    // PCI conventional capability walk: confirm actual PMCSR.D-state==D0.
    const uint16_t status=device.configRead16(6);if(status==0xffff || !(status&0x10))return false;
    uint8_t cap=device.configRead8(0x34);uint64_t seen=0;
    for(unsigned i=0;i<48 && cap;++i) {
        if((cap&3) || cap<0x40 || cap>0xfc)return false;
        const uint64_t bit=1ULL<<(cap/4);if(seen&bit)return false;seen|=bit;
        const uint8_t type=device.configRead8(cap);
        if(type==1) {if(cap>0xf8)return false;const uint16_t pm=device.configRead16(cap+4);return pm!=0xffff && !(pm&3);}
        cap=device.configRead8(cap+1);
    }
    return false;
}
bool IOKitBinding::quiesced(void *opaque,uint64_t owner,uint64_t epoch) {
    auto &s=*static_cast<IOKitBinding *>(opaque);
    return admitted(opaque,owner,epoch) && s.proofs_.quiesced && s.proofs_.quiesced(s.proofs_.opaque,owner,epoch);
}
bool IOKitBinding::retain(void *opaque,const Region &r,bool writable) {
    auto &s=*static_cast<IOKitBinding *>(opaque);
    const XeMemory::Pin pin{r.pinCookie,r.dmaPages,r.pageCount};
    // Actual IOBufferMemoryDescriptor identity, in addition to authoritative
    // GGTT ownership. The current owner must already hold the pin while checked.
    if(XeMemory::kernelBuffer(pin)!=r.cpu || !s.proofs_.retainGgtt)return false;
    return s.proofs_.retainGgtt(s.proofs_.opaque,r,writable);
}
bool IOKitBinding::release(void *opaque,const Region &r) {
    auto &s=*static_cast<IOKitBinding *>(opaque);
    return s.proofs_.releaseGgtt && s.proofs_.releaseGgtt(s.proofs_.opaque,r);
}
bool IOKitBinding::synchronize(void *,const Region &r) {
    const XeMemory::Pin pin{r.pinCookie,r.dmaPages,r.pageCount};
    if(XeMemory::kernelBuffer(pin)!=r.cpu)return false;
    if(XeMemory::synchronizeForDevice(pin)!=XeMemory::Status::Ok)return false;
    __sync_synchronize();return true;
}
bool IOKitBinding::readPat(void *opaque,uint32_t &value) {
    auto &s=*static_cast<IOKitBinding *>(opaque);
    return s.proofs_.readPat3 && s.proofs_.readPat3(s.proofs_.opaque,value);
}
bool IOKitBinding::published(void *opaque,const Region &r,uint64_t epoch) {
    auto &s=*static_cast<IOKitBinding *>(opaque);
    return admitted(opaque,r.owner,epoch) && s.proofs_.mappingPublished && s.proofs_.mappingPublished(s.proofs_.opaque,r,epoch);
}
bool IOKitBinding::ads(void *opaque,const Plan &p,const MellowXe::FirmwareInfo &f) {
    auto &s=*static_cast<IOKitBinding *>(opaque);
    return s.proofs_.fullAdsValid && s.proofs_.fullAdsValid(s.proofs_.opaque,p,f);
}
Backend IOKitBinding::backend() {
    Backend result {};result.io=mmio_.access();result.physicalRevision=device_.configRead8(8);result.opaque=this;
    result.admitted=admitted;result.quiesced=quiesced;result.retain=retain;result.release=release;
    result.synchronize=synchronize;result.readPat3=readPat;result.mappingPublished=published;result.fullAdsValid=ads;
    return result;
}
}
