// Exercises the real Queue -> bridge -> VM path. Only hardware callbacks are
// deterministic mocks. No macOS pinning or GPU execution occurs in this test.
#include "../Mellow/XeMemorySubmission.hpp"
#include <stdio.h>
#include <stdlib.h>
using namespace XeMemory;
using namespace MellowXe;
static unsigned checks;
static void check(bool ok) { ++checks; if (!ok) { fprintf(stderr,"FAIL xe_bridge check %u\n",checks); exit(1); } }
struct Hardware {
    uint64_t dma = 0x200000;
    unsigned pins {}, unpins {}, binds {}, unbinds {}, submissions {}, reads {}, resets {};
    uint32_t completed {}, flags {requiredReadyBits};
    bool stopped {}, acquired {true}, wrongContext {};
    BackendAcceptance acceptance {BackendAcceptance::Accepted};
    Backend memory() {
        Backend b {}; b.context=this; b.verifiedPatIndices=1;
        b.pin=[](void *p,uint64_t owner,uint64_t bytes,Pin &out) {
            auto &h=*static_cast<Hardware*>(p);check(owner==42 && bytes==PageSize);++h.pins;
            out={&h,&h.dma,1};return Status::Ok;
        };
        b.unpin=[](void *p,Pin &out) {auto &h=*static_cast<Hardware*>(p);check(out.cookie==&h);++h.unpins;out={};return Status::Ok;};
        b.bind=[](void *p,uint64_t va,const Pin &pin,uint8_t pat,bool writable) {
            auto &h=*static_cast<Hardware*>(p);check(va==PageSize && pin.cookie==&h && !pat && writable);++h.binds;return Status::Ok;};
        b.unbind=[](void *p,uint64_t va,uint64_t bytes) {auto &h=*static_cast<Hardware*>(p);check(va==PageSize && bytes==PageSize);++h.unbinds;return Status::Ok;};
        return b;
    }
    SubmissionBackend transport() {
        SubmissionBackend b {};b.opaque=this;
        b.readiness=[](void *p,const FirmwareInfo &,uint64_t g,uint64_t o,uint64_t c,uint32_t e,Readiness &out) {
            auto &h=*static_cast<Hardware*>(p);check(o==42 && c==7 && e==3);out={g,o,c,e,h.flags};return SubmitError::None;};
        b.submit=[](void *p,const BatchSnapshot &batch) {auto &h=*static_cast<Hardware*>(p);check(batch.owner==42 && batch.context==7 && batch.engine==3);++h.submissions;return h.acceptance;};
        b.readFence=[](void *p,uint64_t g,uint64_t o,uint64_t c,uint32_t e,FenceObservation &out) {
            auto &h=*static_cast<Hardware*>(p);++h.reads;out={g,o,c+(h.wrongContext?1:0),e,h.completed,true,h.acquired};return SubmitError::None;};
        b.quiesce=[](void *p,uint64_t g,uint64_t o,uint64_t c,uint32_t e) {
            auto &h=*static_cast<Hardware*>(p);check(g && o==42 && c==7 && e==3);++h.resets;return h.stopped;};
        return b;
    }
};
struct Fixture {
    Hardware hw;Allocation slots[4];VirtualMemory vm;Handle handle {};
    SubmissionMemoryBridge bridge;SubmissionQueue queue;Resource r {};FirmwareInfo fw {};
    Fixture():bridge(vm,hw.transport()),queue(42,7,bridge.backend(),3) {
        check(vm.initialize(slots,4,PageSize,16*PageSize,hw.memory())==Status::Ok);
        check(vm.reserveAt(42,PageSize,PageSize,handle)==Status::Ok);
        check(!bridge.resource(42,handle,r));
        check(vm.pin(42,handle)==Status::Ok);check(!bridge.resource(42,handle,r));
        check(vm.bind(42,handle,0,true)==Status::Ok);check(bridge.resource(42,handle,r));
        fw.release={70,53,0};fw.ucodeBytes=64;fw.rsaBytes=256;
        check(queue.activate(fw)==SubmitError::None);
    }
    SubmitError submit(FenceToken &t,uint64_t now=0) {
        const uint32_t words[]={miNoop,miBatchBufferEnd};return queue.submit(words,2,&r,1,now,10,t);
    }
    uint32_t holds() {return vm.inspect(42,handle)->activeUses;}
};
int main() {
    {
        Fixture f;FenceToken t;
        check(f.submit(t)==SubmitError::None && f.holds()==1);
        check(f.vm.retire(42,f.handle)==Status::Ok);
        check(f.queue.expire(10)==SubmitError::None);
        check(f.vm.reclaim(42,f.handle)==Status::Busy && !f.hw.unbinds && !f.hw.unpins);
        check(f.queue.reset(11)==SubmitError::QuiesceFailed && f.holds()==1);
        check(f.vm.reclaim(42,f.handle)==Status::Busy && !f.hw.unpins);
        f.hw.stopped=true;check(f.queue.reset(12)==SubmitError::None && f.holds()==0);
        check(f.vm.reclaim(42,f.handle)==Status::Ok && f.hw.unpins==1 && f.hw.unbinds==1);
        check(!f.bridge.faulted() && f.bridge.lastReleaseStatus()==Status::Ok);
    }
    {
        Fixture f;FenceToken a,b;
        check(f.submit(a)==SubmitError::None);check(f.submit(b,1)==SubmitError::None && f.holds()==2);
        check(f.vm.retire(42,f.handle)==Status::Ok);
        f.hw.completed=1;f.hw.acquired=false;
        check(f.queue.onInterrupt(1,2)==SubmitError::InvalidObservation && f.holds()==2);
        f.hw.acquired=true;f.hw.wrongContext=true;
        check(f.queue.onInterrupt(1,3)==SubmitError::InvalidObservation && f.holds()==2);
        f.hw.wrongContext=false;
        check(f.queue.onInterrupt(1,4)==SubmitError::None && f.holds()==1);
        check(f.vm.reclaim(42,f.handle)==Status::Busy && !f.hw.unpins);
        f.hw.completed=2;check(f.queue.onInterrupt(1,5)==SubmitError::None && f.holds()==0);
        check(f.queue.onInterrupt(1,6)==SubmitError::None && f.holds()==0 && !f.bridge.faulted());
        check(f.vm.reclaim(42,f.handle)==Status::Ok && f.hw.unpins==1);
    }
    {
        Fixture f;FenceToken t;
        f.hw.acceptance=BackendAcceptance::Rejected;
        check(f.submit(t)==SubmitError::Rejected && !f.holds());
        f.hw.acceptance=BackendAcceptance::Unknown;
        check(f.submit(t,1)==SubmitError::AcceptanceUnknown && f.holds()==1);
        check(f.vm.retire(42,f.handle)==Status::Ok);
        check(f.vm.reclaim(42,f.handle)==Status::Busy);
        f.hw.completed=t.sequence;check(f.queue.onInterrupt(1,2)==SubmitError::None && !f.holds());
        JobResult result;check(f.queue.query(t,result)==SubmitError::None && result.state==JobState::AcceptanceUnknown);
        check(f.vm.reclaim(42,f.handle)==Status::Ok);
    }
    {
        Fixture f;FenceToken t;
        const Resource original=f.r;
        for(unsigned variant=0;variant<7;++variant) {
            f.r=original;
            if(variant==0)++f.r.id;
            if(variant==1)++f.r.mappingGeneration;
            if(variant==2)f.r.gpuAddress+=PageSize;
            if(variant==3)f.r.bytes+=PageSize;
            if(variant==4)++f.r.owner;
            if(variant==5)f.r.pinned=false;
            if(variant==6)f.r.gpuReadable=false;
            check(f.submit(t)!=SubmitError::None && !f.holds() && !f.hw.submissions);
        }
        f.r=original;check(f.vm.retire(42,f.handle)==Status::Ok);
        check(f.submit(t)==SubmitError::ResourceBusy && !f.holds());
        check(f.vm.reclaim(42,f.handle)==Status::Ok);
        check(f.vm.reserveAt(42,PageSize,PageSize,f.handle)==Status::Ok);
        check(f.vm.pin(42,f.handle)==Status::Ok && f.vm.bind(42,f.handle,0,true)==Status::Ok);
        check(f.handle.generation!=original.mappingGeneration);
        check(f.submit(t)==SubmitError::ResourceBusy && !f.holds());
        check(f.bridge.resource(42,f.handle,f.r));check(f.submit(t)==SubmitError::None && f.holds()==1);
        f.hw.stopped=true;check(f.queue.reset(1)==SubmitError::None);
        check(f.vm.retire(42,f.handle)==Status::Ok && f.vm.reclaim(42,f.handle)==Status::Ok);
    }
    {
        Fixture f;auto backend=f.bridge.backend();
        backend.release(backend.opaque,f.r); // Deliberately violate trusted queue contract.
        check(f.bridge.faulted() && f.bridge.lastReleaseStatus()==Status::Invalid);
        check(!backend.retain(backend.opaque,f.r) && !f.holds());
    }
    {
        VirtualMemory vm;SubmissionMemoryBridge bridge(vm,{});SubmissionQueue q(42,7,bridge.backend(),3);
        FirmwareInfo info {};check(q.activate(info)==SubmitError::UnsupportedBackend);
    }
    printf("PASS xe_bridge: %u checks; real VM/queue bridge, hardware callbacks are test mocks\n",checks);
}
