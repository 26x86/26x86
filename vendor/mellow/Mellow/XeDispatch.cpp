// Local 7D41 implementation, 2026. MIT; command fields from Intel compute-runtime.
#include "XeDispatch.hpp"
namespace XeDispatch {
static bool span(uint64_t a,uint64_t n) { return a && n && a<XeMemory::VaLimit && n<=XeMemory::VaLimit-a; }
static bool overlap(uint64_t a,uint64_t n,uint64_t b,uint64_t m) { return a<b+m && b<a+n; }
static uint32_t le32(const uint8_t *p) { return uint32_t(p[0])|(uint32_t(p[1])<<8)|(uint32_t(p[2])<<16)|(uint32_t(p[3])<<24); }
static void clear(void *p,size_t n) { auto b=static_cast<uint8_t *>(p); for(size_t i=0;i<n;++i)b[i]=0; }
static void pair(uint32_t *p,uint64_t v) { p[0]=uint32_t(v);p[1]=uint32_t(v>>32); }
static bool validLayout(const Layout &l) {
    const uint64_t a[]={l.instruction,l.indirect,l.surface,l.batch};
    for(size_t i=0;i<4;++i) {
        if(!span(a[i],HeapBytes) || (a[i]&(HeapBytes-1))) return false;
        for(size_t j=0;j<i;++j) if(overlap(a[i],HeapBytes,a[j],HeapBytes))return false;
    }
    return true;
}
Error encodeBufferSurface(uint64_t address,uint64_t bytes,uint8_t mocs,uint32_t (&s)[16]) {
    if(!span(address,bytes) || (address&3U) || (bytes&3U) || bytes>0xfffffffcULL || mocs>63) return Error::Invalid;
    clear(s,sizeof(s));
    // RAW buffer length uses 7/14/11 bits (not the texture width field's 14).
    uint32_t n=uint32_t(bytes-1);
    s[0]=(4U<<29)|(0x1ffU<<18)|(1U<<16)|(3U<<14);
    s[1]=uint32_t(mocs)<<25;
    s[2]=(n&127U)|(((n>>7)&0x3fffU)<<16);
    s[3]=(n>>21)<<21;
    // XeHPG uses GPU_COHERENT even for CPU allocations. Choose uncached L1;
    // CPU/GPU synchronization is still mandatory and is not implied here.
    s[5]=1U<<16;
    pair(s+8,address);
    return Error::None;
}
static void pipe(uint32_t *p,uint32_t flags0,uint32_t flags1,uint32_t address=0,uint32_t value=0) {
    p[0]=0x7a000004U|flags0;p[1]=flags1;p[2]=address;p[3]=0;p[4]=value;p[5]=0;
}
static uint32_t flushFlags(bool depthStall) {
    return (1U<<28)|(1U<<20)|(1U<<12)|(1U<<7)|(1U<<5)|1U|(depthStall?(1U<<13):0U);
}
Error prepareEvidence(const XeZebin::Image &image,const Layout &l,const Policy &policy,
                      const XeZebin::EvidenceValues &values,Prepared &out) {
    const auto *m=image.metadata();
    if(!m || m->simd!=32 || m->grf!=128 || m->inlineBytes!=32 || m->crossThreadBytes!=64 ||
       m->perThreadBytes!=192 || m->skipPerThreadLoad!=192 || !m->disableMidThreadPreemption ||
       image.segmentCount()!=1 || !image.segment(0)->executable || image.segment(0)->bytes>HeapBytes)
        return Error::Unsupported;
    if(!validLayout(l) || !policy.maxFrontEndThreads || policy.mocsIndex>63 ||
       !values.count || values.localSize[0]!=32 || values.localSize[1]!=1 || values.localSize[2]!=1 ||
       values.globalOffset[0] || values.globalOffset[1] || values.globalOffset[2] ||
       uint64_t(values.count)*4>values.inputBytes || uint64_t(values.count)*4>values.outputBytes)
        return Error::Invalid;
    const uint64_t heaps[]={l.instruction,l.indirect,l.surface,l.batch};
    if(!span(values.inputAddress,values.inputBytes) || !span(values.outputAddress,values.outputBytes))return Error::Invalid;
    for(size_t i=0;i<4;++i) if(overlap(heaps[i],HeapBytes,values.inputAddress,values.inputBytes) ||
                              overlap(heaps[i],HeapBytes,values.outputAddress,values.outputBytes))return Error::Invalid;
    uint32_t surfaces[2][16] {};
    if(encodeBufferSurface(values.inputAddress,values.inputBytes,policy.mocsIndex,surfaces[0])!=Error::None ||
       encodeBufferSurface(values.outputAddress,values.outputBytes,policy.mocsIndex,surfaces[1])!=Error::None)return Error::Invalid;
    XeZebin::EvidenceValues args=values;
    // XeHPG extended descriptor preserves aligned byte offsets. Surface entries
    // occupy offsets 0 and 64 relative to SBA.BindlessSurfaceStateBaseAddress.
    args.inputSurface=0;args.outputSurface=64;
    XeZebin::Payload payload;
    if(image.payload(args,payload)!=XeZebin::Error::None)return Error::Zebin;
    XeZebin::Destination destination {out.isa,HeapBytes,l.instruction};
    XeZebin::StagedImage staged;
    if(image.stage(&destination,1,staged)!=XeZebin::Error::None)return Error::Zebin;
    // No further fallible operations. Preserve actual relocated ISA bytes.
    for(size_t i=staged.textBytes;i<HeapBytes;++i)out.isa[i]=0;
    clear(out.indirect,sizeof(out.indirect));clear(out.surface,sizeof(out.surface));clear(out.batch,sizeof(out.batch));
    for(size_t i=0;i<32;++i)out.indirect[i]=payload.bytes[32+i];
    // Runtime XYZ local-ID layout: 32 uint16 lanes per dimension. Y/Z zero.
    // The kernel prologue reads from R0 cross-thread pointer +32+threadID*192.
    for(size_t i=0;i<32;++i)out.indirect[32+i*2]=uint8_t(i);
    for(size_t i=0;i<16;++i){out.surface[i]=surfaces[0][i];out.surface[16+i]=surfaces[1][i];}
    uint32_t *b=out.batch;size_t n=0;
    // Baseline RCS cache flush before pipeline/non-pipelined state updates.
    // Stepping-specific extra barriers and AUX invalidation remain prerequisites.
    pipe(b+n,1U<<9,flushFlags(false));n+=6;
    b[n++]=0x69040302U; // PIPELINE_SELECT: GPGPU, modify selection bits only
    pipe(b+n,0,(1U<<20)|(1U<<2)|(1U<<3)|(1U<<11));n+=6;
    uint32_t *sba=b+n;sba[0]=0x61010014U;
    const uint64_t mocs=uint64_t(policy.mocsIndex)<<5;
    pair(sba+1,l.indirect|mocs|1U);pair(sba+4,l.surface|mocs|1U);
    pair(sba+10,l.instruction|mocs|1U);pair(sba+16,l.surface|mocs|1U);
    sba[3]=(uint32_t(policy.mocsIndex)<<17)|(1U<<23); // stateless MOCS, L1 UC
    sba[12]=(1U<<12)|1U;sba[15]=(1U<<12)|1U;sba[18]=HeapBytes/64-1;n+=22;
    b[n++]=0x61050000U;b[n++]=0x80000000U; // STATE_COMPUTE_MODE: 128 GRFs, masked
    uint32_t *cfe=b+n;cfe[0]=0x72000004U;
    cfe[3]=(uint32_t(policy.maxFrontEndThreads)<<16)|(2U<<14)|
        (policy.disableEuFusion?(1U<<6):0U)|(policy.disableOverdispatch?(1U<<11):0U);n+=6;
    out.walkerOffset=n;uint32_t *w=b+n;
    w[0]=0x72080025U;w[2]=224;w[3]=0; // indirect offset relative to General State base
    w[4]=(2U<<30)|(2U<<17)|(1U<<25); // SIMD32, inline, software local IDs
    w[5]=0xffffffffU;
    const uint32_t groups=uint32_t((uint64_t(values.count)+31)/32);
    w[7]=groups;w[8]=1;w[9]=1;
    w[18]=0; // ISA entry zero relative to Instruction base (software IDs)
    w[23]=1U|(policy.disableOverdispatch?(2U<<26):0U); // one HW thread, no SLM/barrier
    w[24]=8; // preferred SLM allocation 0KB; no scratch/SLM allocated
    for(size_t i=0;i<8;++i)w[31+i]=le32(payload.bytes+4*i);
    n+=WalkerDwords;b[n++]=0x05000000U;
    out.layout=l;out.batchDwords=n;out.isaBytes=staged.textBytes;out.indirectBytes=224;
    out.groups=groups;out.count=values.count;out.softwareOnly=true;
    return Error::None;
}
Error encodeRenderRingJob(uint64_t batchGpu,uint32_t fence,uint32_t seq,bool depthStall,RingJob &out) {
    if(!span(batchGpu,8) || (batchGpu&7U) || !fence || (fence&7U) ||
       uint64_t(fence)+8>(1ULL<<32) || !seq)return Error::Invalid;
    RingJob j;size_t n=0;
    j.words[n++]=0x04000001U;
    j.words[n++]=0x18800101U;pair(j.words+n,batchGpu);n+=2; // 3-DW PPGTT batch start
    j.words[n++]=0x04000000U; // non-preemptible fence signaling
    pipe(j.words+n,1U<<9,flushFlags(depthStall));n+=6;
    pipe(j.words+n,0,(1U<<24)|(1U<<20)|(1U<<14)|(1U<<7),fence,seq);n+=6;
    j.words[n++]=0x01000000U;j.words[n++]=0x04000001U;j.words[n++]=0x02800000U;
    if(n&1U)j.words[n++]=0;
    j.count=n;out=j;return Error::None;
}
bool boundHeaps(const XeMemory::VirtualMemory &vm,uint64_t owner,const Layout &l,
                const XeMemory::Handle (&handles)[4]) {
    if(!owner || !validLayout(l))return false;
    const uint64_t addresses[]={l.instruction,l.indirect,l.surface,l.batch};
    for(size_t i=0;i<4;++i) {
        const auto *a=vm.inspect(owner,handles[i]);
        if(!a || a->state!=XeMemory::State::Bound || a->address!=addresses[i] || a->bytes!=HeapBytes ||
           !a->pin.cookie || !a->pin.dmaPages || a->pin.pageCount!=1)return false;
    }
    return true;
}
Error prepareBoundEvidence(const XeZebin::Image &image,const XeMemory::VirtualMemory &vm,
    uint64_t owner,const XeMemory::Handle (&handles)[6],const Policy &policy,
    uint32_t nonce,uint32_t count,Prepared &out) {
    if(!owner)return Error::Invalid;
    const XeMemory::Allocation *a[6] {};
    for(size_t i=0;i<6;++i) {
        a[i]=vm.inspect(owner,handles[i]);
        if(!a[i] || a[i]->state!=XeMemory::State::Bound || !a[i]->pin.cookie ||
           !a[i]->pin.dmaPages || !a[i]->pin.pageCount)return Error::Unavailable;
    }
    Layout l{a[0]->address,a[1]->address,a[2]->address,a[3]->address};
    XeMemory::Handle heaps[]={handles[0],handles[1],handles[2],handles[3]};
    if(!boundHeaps(vm,owner,l,heaps))return Error::Unavailable;
    XeZebin::EvidenceValues values;values.nonce=nonce;values.count=count;
    values.inputAddress=a[4]->address;values.inputBytes=a[4]->bytes;
    values.outputAddress=a[5]->address;values.outputBytes=a[5]->bytes;
    return prepareEvidence(image,l,policy,values,out);
}
}
