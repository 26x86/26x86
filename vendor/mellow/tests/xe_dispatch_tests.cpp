#include "../Mellow/XeDispatch.hpp"
#include "../Mellow/XeContext.hpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <vector>
#include <type_traits>
#define BITFIELD_RANGE(a,b) ((b)-(a)+1)
#define STATIC_ASSERT(...) static_assert(__VA_ARGS__, "Intel command size")
#define UNRECOVERABLE_IF(x) do { if(x) std::abort(); } while(0)
#define DEBUG_BREAK_IF(x) UNRECOVERABLE_IF(x)
namespace NEO { namespace TypeTraits {template<typename T> constexpr bool isPodV=std::is_standard_layout<T>::value;} }
struct IntelReference {
#include "xe_dispatch_intel_reference.inl"
};
#undef BITFIELD_RANGE
#undef STATIC_ASSERT
#undef UNRECOVERABLE_IF
#undef DEBUG_BREAK_IF
static size_t checks=0;
#define CHECK(x) do{++checks;if(!(x)){std::fprintf(stderr,"FAIL %d: %s\n",__LINE__,#x);std::exit(1);}}while(0)
static void equal(const uint32_t *a,const uint32_t *b,size_t n){for(size_t i=0;i<n;++i){if(a[i]!=b[i])std::fprintf(stderr,"word%zu %08x != %08x\n",i,a[i],b[i]);CHECK(a[i]==b[i]);}}
using namespace XeDispatch;
using RENDER_SURFACE_STATE=IntelReference::RENDER_SURFACE_STATE;
using COMPUTE_WALKER=IntelReference::COMPUTE_WALKER;
using INTERFACE_DESCRIPTOR_DATA=IntelReference::INTERFACE_DESCRIPTOR_DATA;
using STATE_BASE_ADDRESS=IntelReference::STATE_BASE_ADDRESS;
using CFE_STATE=IntelReference::CFE_STATE;
using STATE_COMPUTE_MODE=IntelReference::STATE_COMPUTE_MODE;
using PIPELINE_SELECT=IntelReference::PIPELINE_SELECT;
using PIPE_CONTROL=IntelReference::PIPE_CONTROL;
static void surfaceTests() {
    uint32_t actual[16];
    for(unsigned mocs=0;mocs<64;++mocs)for(uint64_t bytes: {4ULL,128ULL,132ULL,2097152ULL,0xfffffffcULL}) {
        CHECK(encodeBufferSurface(0x123450000ULL,bytes,uint8_t(mocs),actual)==Error::None);
        auto ref=RENDER_SURFACE_STATE::sInit();uint32_t length=uint32_t(bytes-1);
        ref.setWidth((length&127U)+1);ref.setHeight(((length>>7)&0x3fffU)+1);ref.setDepth((length>>21)+1);
        ref.setSurfaceType(RENDER_SURFACE_STATE::SURFACE_TYPE_SURFTYPE_BUFFER);
        ref.setSurfaceFormat(RENDER_SURFACE_STATE::SURFACE_FORMAT_RAW);
        ref.setSurfaceHorizontalAlignment(RENDER_SURFACE_STATE::SURFACE_HORIZONTAL_ALIGNMENT_HALIGN_DEFAULT);
        ref.setMemoryObjectControlState(mocs<<1);ref.setSurfaceBaseAddress(0x123450000ULL);
        ref.setL1CacheControlCachePolicy(RENDER_SURFACE_STATE::L1_CACHE_CONTROL_UC);
        equal(actual,ref.TheStructure.RawData,16);
        CHECK(((actual[2]&127U)|(((actual[2]>>16)&0x3fffU)<<7)|(actual[3]&0xffe00000U))==length);
    }
    for(uint64_t address: {0ULL,1ULL,0xffffffffffffffffULL,(1ULL<<48)-4})
        CHECK(encodeBufferSurface(address,8,3,actual)==Error::Invalid);
    for(uint64_t bytes: {0ULL,1ULL,3ULL,0x100000000ULL,UINT64_MAX})
        CHECK(encodeBufferSurface(0x10000,bytes,3,actual)==Error::Invalid);
    CHECK(encodeBufferSurface(0x10000,4,64,actual)==Error::Invalid);
}
static void commandTests(const XeZebin::Image &image) {
    auto out=new Prepared;
    Layout l{0x100000000ULL,0x200000000ULL,0x300000000ULL,0x400000000ULL};
    XeZebin::EvidenceValues v;v.inputAddress=0x800000000ULL;v.outputAddress=0x900000000ULL;
    v.inputBytes=v.outputBytes=4096;v.nonce=0x12345678;
    for(unsigned fusion=0;fusion<2;++fusion)for(unsigned over=0;over<2;++over)
    for(unsigned count: {1U,31U,32U,33U,1024U}) {
        v.count=count;Policy p{112,3,fusion!=0,over!=0};
        CHECK(prepareEvidence(image,l,p,v,*out)==Error::None);
        CHECK(out->softwareOnly && out->isaBytes==1216 && out->indirectBytes==224 && out->batchDwords==83);
        CHECK(out->groups==(count+31)/32 && out->walkerOffset==43);
        COMPUTE_WALKER w=COMPUTE_WALKER::sInit();
        w.setIndirectDataLength(224);w.setIndirectDataStartAddress(0);
        w.setSimdSize(COMPUTE_WALKER::SIMD_SIZE_SIMD32);w.setMessageSimd(COMPUTE_WALKER::MESSAGE_SIMD_SIMD32);
        w.setEmitInlineParameter(true);w.setExecutionMask(0xffffffffU);
        w.setThreadGroupIdXDimension((count+31)/32);w.setThreadGroupIdYDimension(1);w.setThreadGroupIdZDimension(1);
        auto &idd=w.getInterfaceDescriptor();idd.setKernelStartPointer(0);idd.setNumberOfThreadsInGpgpuThreadGroup(1);
        if(over)idd.setThreadGroupDispatchSize(INTERFACE_DESCRIPTOR_DATA::THREAD_GROUP_DISPATCH_SIZE_TG_SIZE_2);
        idd.setPreferredSlmAllocationSize(INTERFACE_DESCRIPTOR_DATA::PREFERRED_SLM_ALLOCATION_SIZE_0KB);
        XeZebin::Payload cross;v.inputSurface=0;v.outputSurface=64;CHECK(image.payload(v,cross)==XeZebin::Error::None);
        std::memcpy(w.getInlineDataPointer(),cross.bytes,32);
        equal(out->batch+out->walkerOffset,w.TheStructure.RawData,39);
        CHECK(std::memcmp(out->indirect,cross.bytes+32,32)==0);
        for(size_t i=0;i<192;++i)CHECK(out->indirect[32+i]==(i<64 && !(i&1)?i/2:0));
        for(size_t i=224;i<HeapBytes;++i)CHECK(out->indirect[i]==0);
        auto s=STATE_BASE_ADDRESS::sInit();
        s.setGeneralStateBaseAddress(l.indirect);s.setGeneralStateBaseAddressModifyEnable(true);s.setGeneralStateMemoryObjectControlState(6);
        s.setSurfaceStateBaseAddress(l.surface);s.setSurfaceStateBaseAddressModifyEnable(true);s.setSurfaceStateMemoryObjectControlState(6);
        s.setInstructionBaseAddress(l.instruction);s.setInstructionBaseAddressModifyEnable(true);s.setInstructionMemoryObjectControlState(6);
        s.setBindlessSurfaceStateBaseAddress(l.surface);s.setBindlessSurfaceStateBaseAddressModifyEnable(true);s.setBindlessSurfaceStateMemoryObjectControlState(6);
        s.setGeneralStateBufferSize(1);s.setGeneralStateBufferSizeModifyEnable(true);s.setInstructionBufferSize(1);s.setInstructionBufferSizeModifyEnable(true);
        s.setBindlessSurfaceStateSize(63);s.setStatelessDataPortAccessMemoryObjectControlState(6);s.setL1CacheControlCachePolicy(STATE_BASE_ADDRESS::L1_CACHE_CONTROL_UC);
        equal(out->batch+13,s.TheStructure.RawData,22);
        auto c=CFE_STATE::sInit();c.setMaximumNumberOfThreads(112);c.setNumberOfWalkers(1);c.setFusedEuDispatch(fusion);c.setComputeOverdispatchDisable(over);
        equal(out->batch+37,c.TheStructure.RawData,6);
        auto scm=STATE_COMPUTE_MODE::sInit();scm.setLargeGrfMode(false);scm.setMaskBits(0x8000);equal(out->batch+35,scm.TheStructure.RawData,2);
        auto ps=PIPELINE_SELECT::sInit();ps.setPipelineSelection(PIPELINE_SELECT::PIPELINE_SELECTION_GPGPU);ps.setMaskBits(3);CHECK(out->batch[6]==ps.TheStructure.RawData[0]);
        CHECK(out->batch[82]==0x05000000U);
    }
    Policy p{112,3,false,false};v.count=32;
    for(unsigned i=0;i<4;++i){Layout bad=l;uint64_t *fields[]={&bad.instruction,&bad.indirect,&bad.surface,&bad.batch};*fields[i]+=1;CHECK(prepareEvidence(image,bad,p,v,*out)==Error::Invalid);}
    auto bad=l;bad.batch=l.surface;CHECK(prepareEvidence(image,bad,p,v,*out)==Error::Invalid);
    bad=l;bad.surface=v.outputAddress;CHECK(prepareEvidence(image,bad,p,v,*out)==Error::Invalid);
    v.count=1025;CHECK(prepareEvidence(image,l,p,v,*out)==Error::Invalid);v.count=32;
    v.globalOffset[0]=1;CHECK(prepareEvidence(image,l,p,v,*out)==Error::Invalid);v.globalOffset[0]=0;
    v.localSize[0]=16;CHECK(prepareEvidence(image,l,p,v,*out)==Error::Invalid);v.localSize[0]=32;
    p.maxFrontEndThreads=0;CHECK(prepareEvidence(image,l,p,v,*out)==Error::Invalid);
    delete out;
}
static void fenceTests() {
    for(bool wa:{false,true})for(uint32_t seq:{1U,0xffffU,0xffffffffU}) {
        RingJob job;CHECK(encodeRenderRingJob(0x123456000ULL,0xfffffff8U,seq,wa,job)==Error::None);
        CHECK(job.count==20 && job.softwareOnly);
        auto pc=PIPE_CONTROL::sInit();pc.setHdcPipelineFlush(true);pc.setTileCacheFlushEnable(true);pc.setRenderTargetCacheFlushEnable(true);
        pc.setDepthCacheFlushEnable(true);pc.setDcFlushEnable(true);pc.setPipeControlFlushEnable(true);pc.setCommandStreamerStallEnable(true);pc.setDepthStallEnable(wa);
        equal(job.words+5,pc.TheStructure.RawData,6);
        pc=PIPE_CONTROL::sInit();pc.setDestinationAddressType(PIPE_CONTROL::DESTINATION_ADDRESS_TYPE_GGTT);
        pc.setPostSyncOperation(PIPE_CONTROL::POST_SYNC_OPERATION_WRITE_IMMEDIATE_DATA);pc.setCommandStreamerStallEnable(true);pc.setPipeControlFlushEnable(true);
        pc.setAddress(0xfffffff8U);pc.setImmediateData(seq);equal(job.words+11,pc.TheStructure.RawData,6);
        CHECK(job.words[17]==0x01000000U && job.words[19]==0x02800000U);
        CHECK(job.words[1]==0x18800101U && job.words[2]==0x23456000U && job.words[3]==1);
    }
    RingJob j;CHECK(encodeRenderRingJob(0x10000,0x1000,0,false,j)==Error::Invalid);
    CHECK(encodeRenderRingJob(0x10001,0x1000,1,false,j)==Error::Invalid);
    CHECK(encodeRenderRingJob(0x10000,0x1004,1,false,j)==Error::Invalid);
}
static void vmTests(const XeZebin::Image &image) {
    using S=XeMemory::Status;
    struct Mock {uint64_t pages[6]={0x800000,0x801000,0x802000,0x803000,0x804000,0x805000};unsigned pins=0,binds=0;} mock;
    XeMemory::Backend backend;backend.context=&mock;
    backend.pin=[](void *p,uint64_t,uint64_t bytes,XeMemory::Pin &pin){auto m=static_cast<Mock *>(p);if(bytes!=4096 || m->pins>=6)return S::Invalid;auto page=&m->pages[m->pins++];pin={page,page,1};return S::Ok;};
    backend.unpin=[](void *,XeMemory::Pin &pin){pin={};return S::Ok;};
    backend.bind=[](void *p,uint64_t,const XeMemory::Pin &,uint8_t,bool){++static_cast<Mock *>(p)->binds;return S::Ok;};
    backend.unbind=[](void *,uint64_t,uint64_t){return S::Ok;};backend.verifiedPatIndices=1U<<3;
    XeMemory::VirtualMemory vm;XeMemory::Allocation slots[8];XeMemory::Handle handles[6];
    CHECK(vm.initialize(slots,8,0x10000,0x1000000,backend)==S::Ok);
    for(auto &h:handles){CHECK(vm.reserve(51,4096,4096,h)==S::Ok);CHECK(vm.pin(51,h)==S::Ok);}
    auto out=new Prepared;Policy p{112,3,false,false};
    CHECK(prepareBoundEvidence(image,vm,51,handles,p,123,32,*out)==Error::Unavailable);
    for(auto h:handles)CHECK(vm.bind(51,h,3,true)==S::Ok);
    CHECK(prepareBoundEvidence(image,vm,51,handles,p,123,32,*out)==Error::None);
    CHECK(mock.pins==6 && mock.binds==6);
    CHECK(out->layout.instruction==0x10000 && out->layout.batch==0x13000);
    CHECK(prepareBoundEvidence(image,vm,52,handles,p,123,32,*out)==Error::Unavailable);
    ++handles[5].generation;CHECK(prepareBoundEvidence(image,vm,51,handles,p,123,32,*out)==Error::Unavailable);--handles[5].generation;
    CHECK(vm.retire(51,handles[5])==S::Ok);
    CHECK(prepareBoundEvidence(image,vm,51,handles,p,123,32,*out)==Error::Unavailable);
    // Mock-only mappings are not GPU evidence; staging never acquires/reclaims.
    for(const auto &a:slots)CHECK(a.activeUses==0);
    delete out;
}
int main(int argc,char **argv){
    const char *path=argc>1?argv[1]:"compiler-evidence/mellow_evidence_mtl.bin";
    std::ifstream f(path,std::ios::binary);CHECK(bool(f));std::vector<uint8_t> elf((std::istreambuf_iterator<char>(f)),{});
    XeZebin::Image image;CHECK(image.parse(elf.data(),elf.size())==XeZebin::Error::None);
    surfaceTests();commandTests(image);fenceTests();vmTests(image);std::printf("XeDispatch: PASS %zu checks; Intel original encoder oracle; GPU not executed\n",checks);
}
