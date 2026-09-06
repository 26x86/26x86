#include "XePageTableIOKit.hpp"
#include <cstdio>
#include <cstdlib>
using namespace XeMemory;
static unsigned checks=0;
#define CHECK(x) do { ++checks; if (!(x)) { std::fprintf(stderr,"line %d: %s\n",__LINE__,#x); std::exit(1); } } while (0)
namespace {
alignas(4096) uint8_t backing[4096*8];
uint64_t dmas[8];
unsigned live=0,syncs=0;
bool failPin=false,leakPin=false,failSync=false,failUnpin=false;
Status pin(void *,uint64_t owner,uint64_t bytes,Pin &out) {
    CHECK(owner==7 && bytes<=sizeof(backing) && bytes%PageSize==0 && !live);
    if (failPin && !leakPin) return Status::BackendFailure;
    for (size_t i=0;i<bytes/PageSize;++i) dmas[i]=0x100000+i*0x8000; // Noncontiguous device addresses.
    out={backing,dmas,static_cast<size_t>(bytes/PageSize)}; live=1;
    return failPin?Status::BackendFailure:Status::Ok;
}
Status unpin(void *,Pin &out) {
    CHECK(live && out.cookie==backing);
    if (failUnpin) return Status::BackendFailure;
    --live; out=Pin {}; return Status::Ok;
}
struct Proof { bool allow=false; uint64_t expected=0; unsigned calls=0;
  static bool complete(void *opaque,uint64_t owner,uint64_t root) {
    auto &p=*static_cast<Proof *>(opaque); ++p.calls;
    CHECK(owner==7 && root==p.expected); return p.allow;
  }
};
}
// Fake ONLY the OS pin/copy boundary. Actual production pool/tree implementation
// is compiled below; real IOKit allocation is kernel-cross-compiled separately.
namespace XeMemory {
Backend makeIOKitPinBackend(IOKitContext &c) { Backend b {}; b.context=&c; b.pin=::pin; b.unpin=::unpin; return b; }
void *kernelBuffer(const Pin &p) { return p.cookie; }
Status synchronizeForDevice(const Pin &p) {
    CHECK(p.cookie==backing && live); ++syncs;
    return failSync?Status::BackendFailure:Status::Ok;
}
}
int main() {
    IOMapper mapper; IOKitContext context; context.mapper=&mapper;
    { IOKitPageTable p;
      CHECK(p.initialize(context,7,8,0,0)==Status::Invalid);
      CHECK(p.initialize(context,7,8,0,1)==Status::Ok);
      CHECK(p.initialize(context,7,8,0,1)==Status::Busy);
      CHECK(p.pinnedPages()==8 && live==1);
      CHECK(p.map4K(8,0x2000,0x400000,0,true)==Status::WrongOwner);
      CHECK(p.map4K(7,0x2000,0x400000,1,true)==Status::Unavailable);
      CHECK(p.map4K(7,0x2000,0x400000,0,true)==Status::Ok);
      uint64_t pte=0; CHECK(p.lookup(7,0x2000,pte)==Status::Ok && (pte&~4095ULL)==0x400000);
      uint64_t root=0; CHECK(p.sealForDevice(8,root)==Status::WrongOwner && root==0);
      CHECK(p.sealForDevice(7,root)==Status::Ok && root==dmas[0] && syncs==1);
      CHECK(p.rootExposed());
      CHECK(p.map4K(7,0x3000,0x401000,0,true)==Status::Busy);
      CHECK(p.unmap4K(7,0x2000)==Status::Busy);
      CHECK(p.release(8)==Status::WrongOwner);
      CHECK(p.release(7)==Status::Busy && live==1);
      Proof proof; proof.expected=root;
      CHECK(p.release(7,{&proof,Proof::complete})==Status::Busy && proof.calls==1);
      proof.allow=true; failUnpin=true;
      CHECK(p.release(7,{&proof,Proof::complete})==Status::Quarantined && live==1 && p.rootExposed());
      failUnpin=false;
      CHECK(p.release(7,{&proof,Proof::complete})==Status::Ok && !live && !p.rootExposed());
      CHECK(p.release(7)==Status::Invalid);
      CHECK(p.initialize(context,7,8,0,1)==Status::Busy);
      CHECK(p.lookup(7,0x2000,pte)==Status::Unavailable);
    }
    { IOKitPageTable p;
      CHECK(p.initialize(context,7,8,0,1)==Status::Ok);
      failSync=true; uint64_t root=0xdead;
      CHECK(p.sealForDevice(7,root)==Status::BackendFailure && root==0xdead && !p.rootExposed());
      CHECK(p.release(7)==Status::Ok && !live); failSync=false;
    }
    for (unsigned leak=0;leak<2;++leak) {
      IOKitPageTable p; failPin=true; leakPin=leak!=0;
      CHECK(p.initialize(context,7,8,0,1)==(leak?Status::Quarantined:Status::BackendFailure));
      CHECK(p.release(7)==Status::Ok && !live);
    }
    std::printf("PASS %u assertions; actual pinned-table lifecycle/tree, simulated IOKit boundary\n",checks);
}
