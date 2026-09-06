// Local 7D41 implementation, 2026. MIT; layout derived from Intel Linux Xe.
#include "XeContext.hpp"
namespace XeContext {
static bool alignedPage(uint64_t v) { return !(v & (PageBytes-1)); }
static bool ringSize(uint64_t v) { return v>=PageBytes && v<=2*1024*1024 && !(v&(v-1)); }
static bool intersects(uint64_t a,uint64_t n,uint64_t b,uint64_t m) {
    return a<b+m && b<a+n;
}
static void layout(uint32_t *r) {
    // xe_lrc.c: mtl_rcs_offsets, set_offsets. LRI CS_MMIO + FORCE_POSTED.
    const uint16_t group1[]={0x244,0x034,0x030,0x038,0x03c,0x168,0x140,
        0x110,0x1c0,0x1c4,0x1c8,0x180,0x2b4,0x120,0x124};
    const uint16_t group2[]={0x3a8,0x28c,0x288,0x284,0x280,0x27c,0x278,0x274,0x270};
    r[1]=0x1108101dU;
    for(size_t i=0;i<15;++i) r[2+2*i]=RenderMmioBase+group1[i];
    r[0x21]=0x11081011U;
    for(size_t i=0;i<9;++i) r[0x22+2*i]=RenderMmioBase+group2[i];
    r[0x36]=0x11081003U; r[0x37]=RenderMmioBase+0x5a8; r[0x39]=RenderMmioBase+0x5ac;
    r[0x41]=0x11080001U; r[0x42]=RenderMmioBase+0x0c8;
    r[0x44]=0x05000001U; // context-image terminator: MI_BATCH_BUFFER_END | BIT(0)
}
bool registerLayoutMatches(const uint32_t *image,size_t bytes) {
    if(!image || (reinterpret_cast<uintptr_t>(image)&3U) || bytes<ImageBytes) return false;
    uint32_t expected[RegisterDwords] {}; layout(expected);
    const uint32_t *r=image+PageBytes/4;
    // Every command/address/NOP location is checked; only register data varies.
    for(size_t i=0;i<RegisterDwords;++i) {
        bool data=(i>=3 && i<=31 && (i&1)) ||
            (i>=0x23 && i<=0x33 && (i&1)) || i==0x38 || i==0x3a || i==0x43;
        if(!data && r[i]!=expected[i]) return false;
    }
    return true;
}
Error buildBootstrap(const Spec &s,uint32_t *image,size_t bytes,Staged &out) {
    if(!image || (reinterpret_cast<uintptr_t>(image)&3U) || bytes<ImageBytes) return Error::Capacity;
    if(!s.ggttContext || !s.ggttRing || !alignedPage(s.ggttContext) ||
       !alignedPage(s.ggttRing) || !ringSize(s.ringBytes) ||
       uint64_t(s.ggttContext)+ImageBytes>(1ULL<<32) ||
       uint64_t(s.ggttRing)+s.ringBytes>(1ULL<<32) ||
       intersects(s.ggttContext,ImageBytes,s.ggttRing,s.ringBytes)) return Error::Invalid;
    uint64_t pdp=0;
    if(XeMemory::encodeSystemPde(s.rootDma,s.tablePat,pdp)!=XeMemory::Status::Ok || !s.rootDma)
        return Error::Invalid;
    for(size_t i=0;i<ImageBytes/4;++i) image[i]=0;
    uint32_t *r=image+PageBytes/4; layout(r);
    r[3]=0x00090009U; // masked INHIBIT_SYN_CTX_SWITCH | ENGINE_CTX_RESTORE_INHIBIT
    r[5]=0; r[7]=0; r[9]=s.ggttRing; r[11]=(s.ringBytes-PageBytes)|1U;
    r[0x31]=uint32_t(pdp>>32); r[0x33]=uint32_t(pdp);
    Staged result; result.descriptor=uint64_t(s.ggttContext)|0x119ULL;
    // >=12.50 does NOT encode engine class/instance in the LRC descriptor.
    result.rootDescriptor=pdp; result.ggttContext=s.ggttContext;
    result.ggttRing=s.ggttRing; result.ringBytes=s.ringBytes; out=result;
    return Error::None;
}
Error appendRing(uint32_t *ring,size_t bytes,uint32_t head,uint32_t tail,
                 const uint32_t *commands,size_t count,uint32_t &nextTail) {
    if(!ring || !commands || !ringSize(bytes) || !count || count>(bytes-8)/4 ||
       (reinterpret_cast<uintptr_t>(ring)&3U) || (reinterpret_cast<uintptr_t>(commands)&3U) ||
       head>=bytes || tail>=bytes || (head&7U) || (tail&7U)) return Error::Invalid;
    uintptr_t rp=reinterpret_cast<uintptr_t>(ring),cp=reinterpret_cast<uintptr_t>(commands);
    const size_t raw=count*4, padded=(raw+7)&~size_t(7);
    if(rp>UINTPTR_MAX-bytes || cp>UINTPTR_MAX-raw || intersects(rp,bytes,cp,raw)) return Error::Invalid;
    size_t skip=padded>bytes-tail ? bytes-tail : 0;
    size_t free=(head+bytes-tail-8)%bytes;
    if(padded+skip>free) return Error::Capacity;
    uint32_t start=skip ? 0 : tail;
    if(skip) for(size_t i=tail/4;i<bytes/4;++i) ring[i]=0;
    for(size_t i=0;i<count;++i) ring[start/4+i]=commands[i];
    if(padded!=raw) ring[start/4+count]=0;
    nextTail=uint32_t((start+padded)%bytes);
    return Error::None;
}
}
