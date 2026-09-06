// Local diagnostic lifecycle tests. See repository LICENSE and NOTICE.
#include "../Mellow/TahoeDiagnosticProtocol.hpp"
#include "../Mellow/RuntimeReadiness.hpp"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
#define CHECK(x) do { ++checks; if (!(x)) { fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x); exit(1); } } while (0)
using namespace MellowDiagnostic;
struct Memory {
    uint64_t pages[256] {};
    unsigned pins {}, unpins {}, live {};
    bool failPin {}, partialPin {}, failUnpin {}, invalidPages {}, wrongCount {}, forgetClear {};
    static XeMemory::Status pin(void *opaque, uint64_t owner, uint64_t bytes, XeMemory::Pin &out) {
        auto &m = *static_cast<Memory *>(opaque); ++m.pins;
        CHECK(owner && bytes && bytes <= MELLOW_DIAG_MAX_BYTES && !m.live);
        if (m.failPin && !m.partialPin) return XeMemory::Status::BackendFailure;
        ++m.live;
        for (unsigned i = 0; i < bytes / 4096; ++i) m.pages[i] = 0x120000 + i * 4096;
        if (m.invalidPages) m.pages[0] = XeMemory::DmaLimit;
        out = {&m, m.pages, static_cast<size_t>(bytes / 4096 + (m.wrongCount ? 1 : 0))};
        return m.failPin ? XeMemory::Status::BackendFailure : XeMemory::Status::Ok;
    }
    static XeMemory::Status unpin(void *opaque, XeMemory::Pin &pin) {
        auto &m = *static_cast<Memory *>(opaque); ++m.unpins;
        CHECK(pin.cookie == &m && m.live == 1);
        if (m.failUnpin) return XeMemory::Status::BackendFailure;
        if (m.forgetClear) return XeMemory::Status::Ok;
        --m.live; pin = {}; return XeMemory::Status::Ok;
    }
    XeMemory::Backend backend() { XeMemory::Backend b {}; b.context=this;b.pin=pin;b.unpin=unpin;return b; }
};
static MellowDiagRequest request(uint64_t handle=0,uint64_t bytes=0) {
    return {MELLOW_DIAG_ABI_VERSION,sizeof(MellowDiagRequest),handle,bytes,0};
}
static MellowDiagReply call(Session &s,uint64_t owner,uint32_t selector,MellowDiagRequest in) {
    MellowDiagReply reply; memset(&reply,0xa5,sizeof(reply)); s.call(owner,selector,in,reply);
    CHECK(reply.version==1 && reply.size==88 && !reply.reserved);
    CHECK(!reply.gpuSubmissionSupported && !reply.metalSupported);
    CHECK(!(reply.readinessEvidence & (MellowRuntime::AllEvidenceMask & ~(MellowRuntime::BootOptIn |
        MellowRuntime::PhysicalIdentity7D41 | MellowRuntime::Bar0Mapped | MellowRuntime::GmdArchitecture1270))));
    return reply;
}
static void admissionAndValidation() {
    Memory m; Session s;
    CHECK(!s.open(1));
    CHECK(!s.initialize({0x10de,0x7d41,12,70},true,m.backend(),0));
    CHECK(!s.initialize({0x8086,0x9a49,12,70},true,m.backend(),0));
    CHECK(!s.initialize({0x8086,0x7d41,12,71},true,m.backend(),0));
    CHECK(!s.initialize({0x8086,0x7d41,12,70},false,m.backend(),0));
    CHECK(s.initialize({0x8086,0x7d41,12,70},true,m.backend(),UINT64_MAX));
    CHECK(!s.initialize({0x8086,0x7d41,12,70},true,m.backend(),0));
    CHECK(!s.open(0));CHECK(s.open(11));CHECK(!s.open(12));
    CHECK(call(s,12,MellowDiagQuery,request()).status==MellowDiagUnavailable);
    for(unsigned selector=3;selector<128;++selector)
        CHECK(call(s,11,selector,request()).status==MellowDiagInvalid);
    const uint64_t invalidBytes[] = {0,1,4095,4097,MELLOW_DIAG_MAX_BYTES+4096,UINT64_MAX};
    for(uint64_t bytes : invalidBytes)
        CHECK(call(s,11,MellowDiagAllocate,request(0,bytes)).status==MellowDiagInvalid);
    for(unsigned field=0;field<3;++field) {
        auto bad=request(); if(field==0)bad.version=2; if(field==1)bad.size=31; if(field==2)bad.reserved=1;
        CHECK(call(s,11,MellowDiagQuery,bad).status==MellowDiagInvalid);
    }
    CHECK(call(s,11,MellowDiagQuery,request(1)).status==MellowDiagInvalid);
    CHECK(call(s,11,MellowDiagQuery,request(0,4096)).status==MellowDiagInvalid);
    CHECK(call(s,11,MellowDiagAllocate,request(1,4096)).status==MellowDiagInvalid);
    CHECK(call(s,11,MellowDiagRelease,request()).status==MellowDiagInvalid);
    CHECK(m.pins==0 && m.unpins==0);
    CHECK(s.close(12)==MellowDiagInvalid);CHECK(s.close(11)==MellowDiagOk);
    CHECK(s.stop()==MellowDiagOk && !s.open(13));
}
static void lifetime() {
    Memory m;Session s;CHECK(s.initialize({0x8086,0x7d41,12,70},true,m.backend(),0));CHECK(s.open(1));
    auto q=call(s,1,MellowDiagQuery,request());CHECK(q.diagnosticCapabilities==3 && !q.pageCount);
    uint64_t previous=0;
    for(unsigned i=1;i<=256;++i) {
        auto a=call(s,1,MellowDiagAllocate,request(0,uint64_t(i)*4096));
        CHECK(a.status==MellowDiagOk && a.allocationHandle>previous && a.pageCount==i && m.live==1);
        CHECK(call(s,1,MellowDiagAllocate,request(0,4096)).status==MellowDiagBusy);
        CHECK(call(s,1,MellowDiagRelease,request(a.allocationHandle+1)).status==MellowDiagInvalid);
        CHECK(call(s,1,MellowDiagRelease,request(a.allocationHandle)).status==MellowDiagOk && !m.live);
        CHECK(call(s,1,MellowDiagRelease,request(a.allocationHandle)).status==MellowDiagInvalid);
        previous=a.allocationHandle;
    }
    auto a=call(s,1,MellowDiagAllocate,request(0,4096));CHECK(a.status==MellowDiagOk);
    CHECK(s.close(1)==MellowDiagOk && !m.live);CHECK(s.open(2));
    CHECK(call(s,2,MellowDiagRelease,request(a.allocationHandle)).status==MellowDiagInvalid);
    CHECK(call(s,2,MellowDiagAllocate,request(0,4096)).allocationHandle>a.allocationHandle);
    CHECK(s.stop()==MellowDiagOk && !m.live && !s.hasResources());
    CHECK(call(s,2,MellowDiagQuery,request()).status==MellowDiagUnavailable);
    CHECK(s.stop()==MellowDiagOk);
}
static void failures() {
    for(unsigned mode=0;mode<6;++mode) {
        Memory m;Session s;CHECK(s.initialize({0x8086,0x7d41,12,70},true,m.backend(),0));CHECK(s.open(1));
        m.failPin=mode<2; m.partialPin=mode==1; m.invalidPages=mode==2; m.wrongCount=mode==3;
        m.failUnpin=mode==4; m.forgetClear=mode==5;
        const auto a=call(s,1,MellowDiagAllocate,request(0,4096));
        if(mode==0)CHECK(a.status==MellowDiagBackendFailure && !m.live);
        if(mode==1)CHECK(a.status==MellowDiagQuarantined && m.live && s.quarantined());
        if(mode==2 || mode==3)CHECK(a.status==MellowDiagBackendFailure && !m.live);
        if(mode>=4) {
            CHECK(a.status==MellowDiagOk);
            CHECK(call(s,1,MellowDiagRelease,request(a.allocationHandle)).status==MellowDiagQuarantined);
            CHECK(s.quarantined() && s.hasResources() && m.live);
            CHECK(call(s,1,MellowDiagAllocate,request(0,4096)).status==MellowDiagBusy);
            CHECK((call(s,1,MellowDiagQuery,request()).diagnosticCapabilities & MellowDiagPreparedDma)==0);
            CHECK(s.close(1)==MellowDiagQuarantined && !s.open(2));
        }
        m.failUnpin=m.forgetClear=false;
        CHECK(s.stop()==MellowDiagOk && !m.live && !s.hasResources());
    }
    Session noMapper;CHECK(noMapper.initialize({0x8086,0x7d41,12,70},true,{},0));CHECK(noMapper.open(1));
    CHECK(call(noMapper,1,MellowDiagQuery,request()).diagnosticCapabilities==MellowDiagBar0Read);
    CHECK(call(noMapper,1,MellowDiagAllocate,request(0,4096)).status==MellowDiagUnavailable);
    CHECK(noMapper.close(1)==MellowDiagOk);
}
int main() {
    admissionAndValidation();lifetime();failures();
    printf("{\"status\":\"PASS_TAHOE_DIAGNOSTIC_PROTOCOL_HOST\",\"checks\":%u,\"iokit_runtime_tested\":false,\"physical_gpu_tested\":false,\"metal_tested\":false}\n",checks);
}
