#include "XeInterruptIOKit.hpp"
#include "XeFenceIOKit.hpp"
#include <cstdio>
#include <cstdlib>
static unsigned checks=0;
#define CHECK(x) do{++checks;if(!(x)){std::fprintf(stderr,"line %d: %s\n",__LINE__,#x);std::exit(1);}}while(0)
struct Owner {
    bool valid=true,stopped=true;unsigned pins=0;
    static bool admit(void *p,uint64_t e){return static_cast<Owner*>(p)->valid && e==7;}
    static XeInterrupt::Handling identity(void *,uint64_t,const XeInterrupt::Identity &){return XeInterrupt::Handling::Drained;}
    static XeInterrupt::Handling other(void *,uint64_t,uint32_t){return XeInterrupt::Handling::Failed;}
    XeInterrupt::Ops ops(){return {{},this,admit,identity,other};}
    static bool mapValid(void *p,IOMemoryDescriptor *,uint64_t,const XeFence::Slot &s){return static_cast<Owner*>(p)->valid && s.epoch==7;}
    static bool quiescent(void *p,const XeFence::Slot &){return static_cast<Owner*>(p)->stopped;}
    static bool retain(void *p,const XeFence::Slot &){++static_cast<Owner*>(p)->pins;return true;}
    static void release(void *p,const XeFence::Slot &){--static_cast<Owner*>(p)->pins;}
    XeFence::MappingProofs proofs(){return {this,mapValid,quiescent,retain,release};}
};
static void irq(){using S=XeInterrupt::Status;IOPCIDevice pci;IOWorkLoop loop;MellowXe::IOKitMmio mmio;Owner owner;
    auto *obj=new MellowXeInterrupt;XeInterrupt::Configuration c{7,0x8086,0x7d41,1,true,true};
    CHECK(obj->attach(&pci,&loop,0,&mmio,c,owner.ops())==S::Ok);CHECK(obj->refs==2 && loop.refs==2 && IOFilterInterruptEventSource::alive==1);
    CHECK(obj->start()==S::Ok);mmio.ignoreStop=true;CHECK(obj->detach()==S::IoFailure && obj->refs==2);
    mmio.ignoreStop=false;mmio.failStop=true;
    CHECK(obj->detach()==S::IoFailure);CHECK(obj->refs==2 && loop.refs==2 && loop.removes==0 && IOFilterInterruptEventSource::alive==1);
    owner.valid=false;auto n=mmio.accesses;CHECK(obj->detach()==S::Unavailable);CHECK(mmio.accesses==n && obj->refs==2);
    owner.valid=true;mmio.failStop=false;CHECK(obj->detach()==S::Ok);CHECK(loop.removes==1 && loop.refs==1 && obj->refs==1 && IOFilterInterruptEventSource::alive==0);obj->release();
    // Partial attach failure also pins the disabled source until stop retry.
    obj=new MellowXeInterrupt;mmio.failStop=true;CHECK(obj->attach(&pci,&loop,0,&mmio,c,owner.ops())==S::IoFailure);
    CHECK(obj->refs==2 && IOFilterInterruptEventSource::alive==1);mmio.failStop=false;CHECK(obj->detach()==S::Ok);obj->release();
    // An attached object holds itself even after external reference is dropped.
    obj=new MellowXeInterrupt;CHECK(obj->attach(&pci,&loop,0,&mmio,c,owner.ops())==S::Ok);obj->release();CHECK(obj->refs==1);
    CHECK(obj->detach()==S::Ok);CHECK(IOFilterInterruptEventSource::alive==0 && loop.refs==1);
    obj=new MellowXeInterrupt;loop.gate=false;CHECK(obj->attach(&pci,&loop,0,&mmio,c,owner.ops())==S::Invalid);loop.gate=true;
    IOFilterInterruptEventSource::failFactory=true;CHECK(obj->attach(&pci,&loop,0,&mmio,c,owner.ops())==S::Unavailable);
    IOFilterInterruptEventSource::failFactory=false;loop.failAdd=true;CHECK(obj->attach(&pci,&loop,0,&mmio,c,owner.ops())==S::IoFailure);
    CHECK(IOFilterInterruptEventSource::alive==0 && obj->refs==1);obj->release();
}
static void memory(){using S=XeFence::Status;Owner owner;IOMemoryDescriptor d;XeFence::IOKitSlot slot;
    XeFence::Slot id{nullptr,0x200000,5,6,8,7,0,0};
    CHECK(slot.attach(&d,8,id,owner.proofs())==S::Ok);CHECK(d.refs==2 && d.prepares==1 && owner.pins==1);
    CHECK(slot.timeline().published(7,1)==S::Ok);d.words[1]=1;XeFence::Observation o;CHECK(slot.timeline().observe(7,o)==S::Ok && o.sequence==1);
    owner.stopped=false;CHECK(slot.detach()==S::Busy);CHECK(d.refs==2 && !d.completes && owner.pins==1);
    owner.stopped=true;CHECK(slot.detach()==S::Ok);CHECK(d.refs==1 && d.completes==1 && !owner.pins);
    for(unsigned failure=0;failure<3;++failure){XeFence::IOKitSlot s;IOMemoryDescriptor bad;bad.failPrepare=failure==0;bad.failMap=failure==1;
        CHECK(s.attach(&bad,failure==2?64:0,id,owner.proofs())!=S::Ok);CHECK(bad.refs==1 && !owner.pins);}
    XeFence::IOKitSlot s;IOMemoryDescriptor retry;CHECK(s.attach(&retry,0,id,owner.proofs())==S::Ok);retry.failComplete=true;
    CHECK(s.detach()==S::Unavailable && retry.refs==2);retry.failComplete=false;CHECK(s.detach()==S::Ok && retry.refs==1);
}
int main(){irq();memory();std::printf("{\"passed\":true,\"assertions\":%u,\"iokit_runtime_tested\":false}\n",checks);}
