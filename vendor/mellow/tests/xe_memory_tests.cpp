#include "../Mellow/XeMemory.hpp"
#include <stdio.h>
#include <stdlib.h>

using namespace XeMemory;
static unsigned checks;
static void expect(bool condition, const char *message) {
    ++checks;
    if (!condition) { fprintf(stderr, "FAIL %s (check %u)\n", message, checks); exit(1); }
}
static void encoding() {
    // Expected literal flags, independently listed from Intel's PTE definitions.
    const uint64_t flags[] = {0,8,16,24,128,136,144,152,
        0x4000000000000000ULL,0x4000000000000008ULL,0x4000000000000010ULL,
        0x4000000000000018ULL,0x4000000000000080ULL,0x4000000000000088ULL,
        0x4000000000000090ULL,0x4000000000000098ULL};
    const uint64_t addresses[] = {0,4096,0x123456000ULL,DmaLimit-PageSize};
    const bool permissions[] = {false,true};
    for (auto address : addresses) for (unsigned pat=0; pat<256; ++pat) {
        for (bool writable : permissions) {
            uint64_t out=0xDEADBEEF;
            const Status result=encodeSystemPte4K(address,pat,writable,out);
            expect(result==(pat<16?Status::Ok:Status::Invalid),"PAT representability");
            expect(out==(pat<16?address|flags[pat]|(writable?3:1):0xDEADBEEF),"literal PTE encoding/no mutation");
        }
        uint64_t out=0xDEADBEEF;
        expect(encodeSystemPde(address,pat,out)==(pat<4?Status::Ok:Status::Invalid),"nonleaf only two PAT bits");
        expect(out==(pat<4?address|flags[pat]|3:0xDEADBEEF),"literal PDE encoding");
    }
    const uint64_t invalidAddresses[] = {1,4095,4097,DmaLimit,DmaLimit+4096,UINT64_MAX};
    for (auto address : invalidAddresses) {
        uint64_t out=0xDEADBEEF;
        expect(encodeSystemPte4K(address,0,true,out)==Status::Invalid && out==0xDEADBEEF,"unaligned/too large DMA rejected");
    }
    for (unsigned level=0; level<4; ++level) for (uint64_t i=0; i<512; ++i) {
        uint16_t indices[4] {};
        const uint64_t address=i<<(12+9*level);
        expect(pageTableIndices(address,indices)==Status::Ok,"index range");
        for (unsigned j=0;j<4;++j) expect(indices[j]==(j==level?i:0),"level boundary decomposition");
    }
    uint16_t indices[4] {7,7,7,7};
    expect(pageTableIndices(VaLimit,indices)==Status::Invalid && indices[0]==7,"48 bit VA restriction");
}
static void intervalOracle() {
    // All 256 occupancy patterns of an eight-page address space, every request
    // length and four alignments. Oracle walks individual pages, not intervals.
    for (unsigned mask=0;mask<256;++mask) for (unsigned length=1;length<=8;++length)
        for (unsigned alignPages=1;alignPages<=8;alignPages*=2) {
            Allocation slots[16]; VirtualMemory vm;
            expect(vm.initialize(slots,16,0,8*PageSize,Backend{})==Status::Ok,"initialize oracle VM");
            for (unsigned page=0;page<8;++page) if (mask&(1U<<page))
                expect(vm.exclude(page*PageSize,PageSize)==Status::Ok,"reserve permanent hole");
            int expected=-1;
            for (unsigned page=0;page+length<=8;++page) {
                if (page%alignPages) continue;
                bool free=true;
                for (unsigned k=page;k<page+length;++k) if(mask&(1U<<k)) free=false;
                if(free) {expected=static_cast<int>(page);break;}
            }
            Handle handle {999,999};
            Status result=vm.reserve(1,length*PageSize,alignPages*PageSize,handle);
            expect(result==(expected<0?Status::NoSpace:Status::Ok),"first fit vs independent occupancy oracle");
            if(expected<0) expect(handle.slot==999 && handle.generation==999,"failed allocation does not mutate handle");
            else {
                const Allocation *a=vm.inspect(1,handle);
                expect(a && a->address==static_cast<uint64_t>(expected)*PageSize,"first fit exact VA");
                expect(vm.reclaim(2,handle)==Status::WrongOwner,"ownership before reclaim");
                expect(vm.reclaim(1,handle)==Status::Ok,"free unpinned reservation");
                expect(!vm.inspect(1,handle),"stale handle invalid after free");
            }
        }
}
struct Fake {
    uint64_t pages[8] {0x1000,0x2000,0x4000,0x9000,0x12000,0x20000,0xA0000,0x100000};
    unsigned pins{},unpins{},binds{},unbinds{},polls{};
    Status pinResult{Status::Ok},bindResult{Status::Ok},unbindResult{Status::Ok},unpinResult{Status::Ok};
    bool incomplete{true},invalidPage{},partialPin{};
    static Status pin(void *p,uint64_t owner,uint64_t bytes,Pin &out) {
        auto &f=*static_cast<Fake*>(p);++f.pins;
        expect(owner==42 && bytes<=8*PageSize,"pin receives exact owner and bytes");
        if(f.pinResult!=Status::Ok && !f.partialPin) return f.pinResult;
        if(f.invalidPage) f.pages[0]=1;
        out=Pin{&f,f.pages,static_cast<size_t>(bytes/PageSize)};
        return f.pinResult;
    }
    static Status unpin(void *p,Pin &out) {
        auto &f=*static_cast<Fake*>(p);++f.unpins;
        expect(out.cookie==&f,"unpin retains original pin cookie");
        if(f.unpinResult==Status::Ok) out=Pin{};
        return f.unpinResult;
    }
    static Status bind(void *p,uint64_t va,const Pin &pin,uint8_t pat,bool writable) {
        auto &f=*static_cast<Fake*>(p);++f.binds;
        expect(va==PageSize && pin.cookie==&f && pat==0 && writable,"bind arguments preserve allocation");
        return f.bindResult;
    }
    static Status unbind(void *p,uint64_t va,uint64_t bytes) {
        auto &f=*static_cast<Fake*>(p);++f.unbinds;
        expect(va==PageSize && bytes==2*PageSize,"unbind retains full allocation");
        return f.unbindResult;
    }
    static bool complete(void *p,Fence fence) {
        auto &f=*static_cast<Fake*>(p);++f.polls;
        expect(fence.timeline==7 && fence.value==3,"poll exact last fence");
        return !f.incomplete;
    }
    Backend ops() { Backend b{}; b.context=this;b.pin=pin;b.unpin=unpin;b.bind=bind;b.unbind=unbind;b.fenceComplete=complete;b.verifiedPatIndices=1;return b; }
};
struct Fixture {
    Fake fake; Allocation slots[8]; VirtualMemory vm; Handle handle{};
    Fixture() {
        expect(vm.initialize(slots,8,PageSize,64*PageSize,fake.ops())==Status::Ok,"lifecycle VM init");
        expect(vm.reserve(42,2*PageSize,PageSize,handle)==Status::Ok,"lifecycle reserve");
    }
    void pinned() {expect(vm.pin(42,handle)==Status::Ok,"pin succeeds with real backend receipt");}
    void bound() {pinned();expect(vm.bind(42,handle,0,true)==Status::Ok,"backend bind acknowledged");}
};
static void lifecycle() {
    Fixture x;
    expect(x.vm.bind(42,x.handle,0,true)==Status::Busy && x.fake.binds==0,"cannot bind without pin");
    expect(x.vm.pin(1,x.handle)==Status::WrongOwner && x.fake.pins==0,"cross owner cannot pin");
    x.bound();
    expect(x.vm.pin(42,x.handle)==Status::Busy && x.fake.pins==1,"no double pin");
    expect(x.vm.reclaim(42,x.handle)==Status::Busy,"bound memory cannot be freed");
    expect(x.vm.recordUse(42,x.handle,Fence{7,1})==Status::Ok,"first job fence");
    expect(x.vm.recordUse(42,x.handle,Fence{8,2})==Status::Invalid,"cross queue needs real dependency join");
    expect(x.vm.recordUse(42,x.handle,Fence{7,1})==Status::Invalid,"duplicate or old fence refused");
    expect(x.vm.recordUse(42,x.handle,Fence{7,3})==Status::Ok,"last ordered fence replaces older");
    expect(x.vm.retire(42,x.handle)==Status::Ok,"retire closes new use");
    expect(x.vm.recordUse(42,x.handle,Fence{7,4})==Status::Busy,"cannot submit after retirement");
    expect(x.vm.reclaim(42,x.handle)==Status::Busy && x.fake.unbinds==0 && x.fake.unpins==0,"incomplete fence preserves VA and pin");
    x.fake.incomplete=false;
    expect(x.vm.reclaim(42,x.handle)==Status::Ok && x.fake.unbinds==1 && x.fake.unpins==1,"fence then unbind then unpin");
    Handle newer{};
    expect(x.vm.reserve(42,2*PageSize,PageSize,newer)==Status::Ok,"reuse only after completion and invalidation");
    expect(newer.generation!=x.handle.generation,"generation protects reused VA slot");
    expect(x.vm.pin(42,x.handle)==Status::NotFound,"stale handle cannot pin new allocation");
    Fixture unavailable;unavailable.pinned();unavailable.fake.bindResult=Status::Unavailable;
    expect(unavailable.vm.bind(42,unavailable.handle,0,true)==Status::Unavailable,"missing backend not fake bound");
    expect(unavailable.vm.inspect(42,unavailable.handle)->state==State::Pinned,"unavailable leaves honest pin state");
    expect(unavailable.vm.reclaim(42,unavailable.handle)==Status::Ok && unavailable.fake.unbinds==0,"unpublished pin can release");
    Fixture failed;failed.pinned();failed.fake.bindResult=Status::BackendFailure;
    expect(failed.vm.bind(42,failed.handle,0,true)==Status::Quarantined,"partial bind quarantines");
    expect(failed.vm.reclaim(42,failed.handle)==Status::Quarantined && failed.fake.unpins==0,"uncertain GPU exposure retains pages");
    Fixture invalid;invalid.fake.invalidPage=true;
    expect(invalid.vm.pin(42,invalid.handle)==Status::BackendFailure && invalid.fake.unpins==1,"invalid DMA rejected and unwound");
    expect(invalid.vm.inspect(42,invalid.handle)->state==State::Reserved,"invalid pin not published");
    Fixture noPin;noPin.fake.pinResult=Status::NoSpace;
    expect(noPin.vm.pin(42,noPin.handle)==Status::NoSpace && noPin.fake.unpins==0,"atomic pin failure no invented resources");
    Fixture partial;partial.fake.pinResult=Status::BackendFailure;partial.fake.partialPin=true;
    expect(partial.vm.pin(42,partial.handle)==Status::Quarantined,"broken partial pin contract quarantines receipt");
    Fixture badUnbind;badUnbind.bound();expect(badUnbind.vm.retire(42,badUnbind.handle)==Status::Ok,"retire idle allocation");
    badUnbind.fake.unbindResult=Status::BackendFailure;
    expect(badUnbind.vm.reclaim(42,badUnbind.handle)==Status::Quarantined && badUnbind.fake.unpins==0,"partial invalidation cannot free");
    Fixture deferred;deferred.bound();expect(deferred.vm.retire(42,deferred.handle)==Status::Ok,"retire deferred unbind");
    deferred.fake.unbindResult=Status::Unavailable;
    expect(deferred.vm.reclaim(42,deferred.handle)==Status::Unavailable && deferred.fake.unpins==0,"no unbind retains retirement");
    deferred.fake.unbindResult=Status::Ok;
    expect(deferred.vm.reclaim(42,deferred.handle)==Status::Ok,"retry completed unbind releases");
    Fixture badUnpin;badUnpin.pinned();badUnpin.fake.unpinResult=Status::BackendFailure;
    expect(badUnpin.vm.reclaim(42,badUnpin.handle)==Status::Quarantined,"failed DMA teardown quarantines");
}
static void missingBackend() {
    Allocation slots[2];VirtualMemory vm;Handle h{};
    expect(vm.initialize(slots,2,PageSize,VaLimit,Backend{})==Status::Ok,"empty backend allowed for reservation only");
    expect(vm.reserve(42,PageSize,PageSize,h)==Status::Ok,"software reserve succeeds");
    expect(vm.pin(42,h)==Status::Unavailable && vm.inspect(42,h)->state==State::Reserved,"no pin implementation no pinned claim");
    expect(vm.bind(42,h,0,true)==Status::Busy,"no GPU binding from reservation");
    expect(vm.reserve(42,UINT64_MAX,PageSize,h)==Status::Invalid,"size overflow guard");
    expect(vm.reserve(42,PageSize,UINT64_MAX,h)==Status::Invalid,"alignment overflow guard");
    expect(vm.reserveAt(42,VaLimit,PageSize,h)==Status::Invalid,"VA upper bound");
    expect(vm.reserve(0,PageSize,PageSize,h)==Status::Invalid,"owner zero reserved for exclusions");
    expect(vm.initialize(slots,2,PageSize,VaLimit,Backend{})==Status::Busy,"reinit cannot destroy live allocations");
}
static void submissionHolds() {
    Fixture x;
    expect(x.vm.retainUse(42,x.handle)==Status::Busy,"unbound memory cannot enter queue");
    x.bound();
    expect(x.vm.releaseUse(42,x.handle)==Status::Invalid,"hold underflow refused");
    expect(x.vm.retainUse(99,x.handle)==Status::WrongOwner,"cross owner queue cannot retain");
    expect(x.vm.retainUse(42,x.handle)==Status::Ok,"first queue hold");
    expect(x.vm.retainUse(42,x.handle)==Status::Ok,"second queue hold");
    expect(x.vm.inspect(42,x.handle)->activeUses==2,"separate accepted or pending jobs counted");
    expect(x.vm.retire(42,x.handle)==Status::Ok,"retire with jobs outstanding");
    expect(x.vm.retainUse(42,x.handle)==Status::Busy,"retired memory rejects new queue hold");
    expect(x.vm.releaseUse(99,x.handle)==Status::WrongOwner,"cross owner cannot release hold");
    expect(x.vm.reclaim(42,x.handle)==Status::Busy && x.fake.unbinds==0,"active jobs forbid unbind");
    expect(x.vm.releaseUse(42,x.handle)==Status::Ok,"confirmed rejected job releases its hold");
    expect(x.vm.reclaim(42,x.handle)==Status::Busy && x.fake.unpins==0,"one completed job does not release remaining job");
    expect(x.vm.releaseUse(42,x.handle)==Status::Ok,"authoritative last completion releases hold");
    expect(x.vm.reclaim(42,x.handle)==Status::Ok && x.fake.unbinds==1 && x.fake.unpins==1,"all holds then GPU unbind then unpin");
    expect(x.vm.releaseUse(42,x.handle)==Status::NotFound,"late completion cannot affect reused allocation");
    Fixture saturated;saturated.bound();
    saturated.slots[saturated.handle.slot].activeUses=UINT32_MAX;
    expect(saturated.vm.retainUse(42,saturated.handle)==Status::NoSpace &&
           saturated.vm.inspect(42,saturated.handle)->activeUses==UINT32_MAX,"hold counter cannot wrap");
}
int main(){encoding();intervalOracle();lifecycle();missingBackend();submissionHolds();printf("PASS xe_memory: %u checks; hardware backend NOT executed\n",checks);}
