#include "../Mellow/XeContext.hpp"
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <cstring>
static size_t checks;
#define CHECK(x) do{++checks;if(!(x)){std::fprintf(stderr,"FAIL %d: %s\n",__LINE__,#x);std::exit(1);}}while(0)
using namespace XeContext;
int main(){
    std::vector<uint32_t> image(ImageBytes/4+16,0xfefefefeU);
    Spec spec{0x100000,0x200000,4096,0x120003000ULL,3};Staged out;
    CHECK(buildBootstrap(spec,image.data(),ImageBytes,out)==Error::None);
    CHECK(registerLayoutMatches(image.data(),ImageBytes));CHECK(out.softwareOnly && out.bootstrapCaptureOnly);
    CHECK(out.descriptor==0x100119 && out.rootDescriptor==0x12000301bULL);
    uint32_t *r=image.data()+1024;
    CHECK(r[3]==0x90009 && r[9]==0x200000 && r[11]==1 && r[0x31]==1 && r[0x33]==0x2000301b);
    CHECK(r[0x36]==0x11081003 && r[0x37]==0x25a8 && r[0x39]==0x25ac && r[0x42]==0x20c8 && r[0x44]==0x05000001);
    for(size_t i=ImageBytes/4;i<image.size();++i)CHECK(image[i]==0xfefefefeU);
    for(size_t i=0;i<RegisterDwords;++i){uint32_t old=r[i];r[i]^=0x10;
        bool data=(i>=3&&i<=31&&(i&1))||(i>=0x23&&i<=0x33&&(i&1))||i==0x38||i==0x3a||i==0x43;
        CHECK(registerLayoutMatches(image.data(),ImageBytes)==data);r[i]=old;}
    auto bad=spec;bad.ggttRing=bad.ggttContext;CHECK(buildBootstrap(bad,image.data(),ImageBytes,out)==Error::Invalid);
    bad=spec;bad.ggttContext=0xfffff000U;CHECK(buildBootstrap(bad,image.data(),ImageBytes,out)==Error::Invalid);
    bad=spec;bad.rootDma=(1ULL<<46);CHECK(buildBootstrap(bad,image.data(),ImageBytes,out)==Error::Invalid);
    bad=spec;bad.tablePat=4;CHECK(buildBootstrap(bad,image.data(),ImageBytes,out)==Error::Invalid);
    bad=spec;bad.ringBytes=12288;CHECK(buildBootstrap(bad,image.data(),ImageBytes,out)==Error::Invalid);
    std::vector<uint32_t> ring(1024), commands(1024,0x11111111);uint32_t next=0;
    // Exhaust all aligned head/tail pairs and representative sequence sizes.
    for(uint32_t head=0;head<4096;head+=8)for(uint32_t tail=0;tail<4096;tail+=8)
    for(size_t words:{1U,2U,19U,20U,1020U}) {
        size_t padded=(words*4+7)&~size_t(7),skip=padded>4096-tail?4096-tail:0;
        size_t occupied=(tail+4096-head)%4096,required=padded+skip;
        bool fits=occupied+required+8<=4096;
        uint32_t before=next;
        auto ret=appendRing(ring.data(),4096,head,tail,commands.data(),words,next);
        CHECK((ret==Error::None)==fits);
        if(fits){CHECK(next==((skip?0:tail)+padded)%4096);CHECK((next&7)==0);}
        else CHECK(next==before);
    }
    CHECK(appendRing(ring.data(),4096,0,0,ring.data()+1,4,next)==Error::Invalid);
    CHECK(appendRing(ring.data(),4096,1,0,commands.data(),4,next)==Error::Invalid);
    CHECK(appendRing(ring.data(),4096,0,4096,commands.data(),4,next)==Error::Invalid);
    CHECK(appendRing(ring.data(),4096,0,0,commands.data(),1023,next)==Error::Invalid);
    std::printf("XeContext: PASS %zu checks; offline LRC/ring, GPU not executed\n",checks);
}
