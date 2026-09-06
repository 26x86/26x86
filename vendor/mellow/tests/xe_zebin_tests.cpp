// Actual compiler artifact + malformed/synthetic ELF tests. No GPU execution.
#include "../Mellow/XeZebin.hpp"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
using namespace XeZebin;
static unsigned checks;
static void check(bool ok){++checks;if(!ok){std::fprintf(stderr,"FAIL xe_zebin check %u\n",checks);std::exit(1);}}
static uint16_t r16(const uint8_t*p){return p[0]|uint16_t(p[1])<<8;}
static uint32_t r32(const uint8_t*p){return r16(p)|uint32_t(r16(p+2))<<16;}
static uint64_t r64(const uint8_t*p){return r32(p)|uint64_t(r32(p+4))<<32;}
static void put(std::vector<uint8_t>&v,size_t at,uint64_t n,unsigned width){check(at+width<=v.size());for(unsigned i=0;i<width;++i)v[at+i]=uint8_t(n>>(8*i));}
struct Elf {
    struct S {uint32_t name{},type{},link{},info{};uint64_t flags{},alignment{},entry{},size{};std::vector<uint8_t> data;};
    std::vector<uint8_t> header;std::vector<S> s;
    Elf(const std::vector<uint8_t>&bytes):header(bytes.begin(),bytes.begin()+64) {
        const uint64_t table=r64(bytes.data()+40);const unsigned count=r16(bytes.data()+60);
        for(unsigned i=0;i<count;++i){const auto*p=bytes.data()+table+i*64;S part;
            part.name=r32(p);part.type=r32(p+4);part.flags=r64(p+8);part.size=r64(p+32);
            part.link=r32(p+40);part.info=r32(p+44);part.alignment=r64(p+48);part.entry=r64(p+56);
            if(part.type!=8)part.data.assign(bytes.begin()+r64(p+24),bytes.begin()+r64(p+24)+part.size);
            s.push_back(part);}
    }
    unsigned add(const char*name,uint32_t type,uint64_t size) {
        S part;part.name=static_cast<uint32_t>(s[9].data.size());
        for(const char*p=name;;++p){s[9].data.push_back(uint8_t(*p));if(!*p)break;}
        s[9].size=s[9].data.size();part.type=type;part.size=size;part.alignment=8;
        if(type!=8)part.data.resize(size);
        s.push_back(part);return static_cast<unsigned>(s.size()-1);
    }
    unsigned symbol(unsigned section,uint64_t value,uint64_t size=0) {
        const unsigned result=static_cast<unsigned>(s[2].data.size()/24);s[2].data.resize(s[2].data.size()+24);
        put(s[2].data,result*24+6,section,2);put(s[2].data,result*24+8,value,8);put(s[2].data,result*24+16,size,8);s[2].size=s[2].data.size();return result;
    }
    std::vector<uint8_t> encode() const {
        std::vector<uint8_t> bytes=header;std::vector<uint64_t> offsets;
        for(const auto&part:s){while(bytes.size()%8)bytes.push_back(0);offsets.push_back(bytes.size());if(part.type!=8)bytes.insert(bytes.end(),part.data.begin(),part.data.end());}
        while(bytes.size()%8)bytes.push_back(0);
        const uint64_t table=bytes.size();bytes.resize(bytes.size()+s.size()*64);
        put(bytes,40,table,8);put(bytes,60,s.size(),2);
        for(size_t i=0;i<s.size();++i){const size_t at=table+i*64;const auto&part=s[i];
            put(bytes,at,part.name,4);put(bytes,at+4,part.type,4);put(bytes,at+8,part.flags,8);put(bytes,at+24,offsets[i],8);
            put(bytes,at+32,part.size,8);put(bytes,at+40,part.link,4);put(bytes,at+44,part.info,4);put(bytes,at+48,part.alignment,8);put(bytes,at+56,part.entry,8);}
        return bytes;
    }
};
static void actualArtifact(const std::vector<uint8_t>&bytes) {
    Image image;check(image.parse(bytes.data(),bytes.size())==Error::None);
    const auto&m=*image.metadata();check(m.crossThreadBytes==64 && m.inlineBytes==32 && m.perThreadBytes==192);
    check(m.simd==32 && m.grf==128 && m.skipPerThreadLoad==192 && m.argumentCount==8 && m.disableMidThreadPreemption);
    const auto&c=*image.compatibility();check(c.productFamily==1272 && c.gfxCore==3079 && c.productConfig==51478528);
    check(image.segmentCount()==1 && image.segment(0)->bytes==1216);
    std::vector<uint8_t> isa(4096,0xcc);Destination d{isa.data(),isa.size(),0x100000000ULL};StagedImage staged;
    check(image.stage(&d,1,staged)==Error::None && staged.softwareOnly && staged.relocationCount==2);
    check(staged.kernelGpuAddress==0x100000000ULL && staged.skipLocalIdLoadGpuAddress==0x1000000c0ULL);
    check(r32(isa.data()+76)==0 && r32(isa.data()+236)==0); // No implicit prefix in this exact non-debug profile.
    for(size_t i=0;i<1216;++i)check(isa[i]==bytes[64+i]);
    for(size_t i=1216;i<isa.size();++i)check(isa[i]==0xcc);
    EvidenceValues values;values.inputAddress=0x200000000ULL;values.outputAddress=0x300000000ULL;
    values.inputBytes=values.outputBytes=4096;values.inputSurface=0x123;values.outputSurface=0x456;
    values.nonce=0xaabbccdd;values.count=1024;values.globalOffset[0]=17;
    Payload payload;check(image.payload(values,payload)==Error::None && payload.softwareOnly && payload.size==64);
    check(r32(payload.bytes)==17 && r32(payload.bytes+12)==32 && r32(payload.bytes+16)==1 && r32(payload.bytes+20)==1);
    check(r64(payload.bytes+24)==values.inputAddress && r64(payload.bytes+32)==values.outputAddress);
    check(r32(payload.bytes+40)==values.nonce && r32(payload.bytes+44)==1024 && r32(payload.bytes+48)==0x123 && r32(payload.bytes+52)==0x456);
    for(unsigned i=56;i<64;++i)check(payload.bytes[i]==0);
    auto bad=values;bad.inputBytes=4095;check(image.payload(bad,payload)==Error::InvalidBinding);
    bad=values;bad.localSize[0]=0;check(image.payload(bad,payload)==Error::InvalidBinding);
    bad=values;bad.inputAddress=XeMemory::VaLimit-4;check(image.payload(bad,payload)==Error::InvalidBinding);
    bad=values;bad.count=UINT32_MAX;check(image.payload(bad,payload)==Error::InvalidBinding);
}
static void truncationAndMetadata(const std::vector<uint8_t>&bytes) {
    for(size_t i=0;i<bytes.size();++i){Image image;check(image.parse(bytes.data(),i)!=Error::None && !image.metadata());}
    for(unsigned offset:{0U,4U,5U,6U,16U,18U,20U,24U,32U,52U,56U,58U,60U,62U}){
        auto bad=bytes;bad[offset]=0xff;Image image;check(image.parse(bad.data(),bad.size())!=Error::None);}
    const uint64_t table=r64(bytes.data()+40);
    for(unsigned section=1;section<10;++section)for(unsigned field:{24U,32U,48U}){
        auto bad=bytes;put(bad,table+section*64+field,UINT64_MAX,8);Image image;check(image.parse(bad.data(),bad.size())!=Error::None);}
    const char* needles[]={"'1.73'","grf_count","simd_size","readonly","enqueued_local_size","local_id"};
    for(const char*needle:needles){Elf elf(bytes);auto&meta=elf.s[7].data;std::string text(meta.begin(),meta.end());
        const size_t at=text.find(needle);check(at!=std::string::npos);meta[at]='!';auto bad=elf.encode();Image image;check(image.parse(bad.data(),bad.size())!=Error::None);}
    {Elf elf(bytes);auto&meta=elf.s[7].data;std::string text(meta.begin(),meta.end());size_t at=text.find("offset:          32");check(at!=std::string::npos);meta[at+17]='2';meta[at+18]='4';auto bad=elf.encode();Image image;check(image.parse(bad.data(),bad.size())!=Error::None);}
    {Elf elf(bytes);put(elf.s[2].data,2*24+8,64,8);auto bad=elf.encode();Image image;check(image.parse(bad.data(),bad.size())==Error::Unsupported);}
}
static void relocations(const std::vector<uint8_t>&bytes) {
    {
        Elf elf(bytes);put(elf.s[6].data,8,(uint64_t(1)<<32)|2,8);put(elf.s[6].data,24,(uint64_t(1)<<32)|3,8);
        auto changed=elf.encode();Image image;check(image.parse(changed.data(),changed.size())==Error::None);
        std::vector<uint8_t> isa(1216);Destination d{isa.data(),isa.size(),0x1234500000ULL};StagedImage out;
        check(image.stage(&d,1,out)==Error::None);check(r32(isa.data()+76)==0x34500100 && r32(isa.data()+236)==0x12);
    }
    {
        Elf elf(bytes);put(elf.s[6].data,8,4,8);put(elf.s[6].data,24,4,8);auto changed=elf.encode();Image image;
        check(image.parse(changed.data(),changed.size())==Error::None);std::vector<uint8_t> isa(1216);Destination d{isa.data(),isa.size(),0x100000};StagedImage out;
        check(image.stage(&d,1,out)==Error::None && r32(isa.data()+76)==32 && r32(isa.data()+236)==32);
    }
    for(unsigned variant=0;variant<7;++variant) {
        Elf elf(bytes);
        if(variant==0)put(elf.s[6].data,0,1214,8);
        if(variant==1)put(elf.s[6].data,8,(uint64_t(99)<<32)|2,8);
        if(variant==2)put(elf.s[6].data,8,(uint64_t(3)<<32)|255,8);
        if(variant==3)put(elf.s[6].data,16,76,8);
        if(variant==4){uint32_t name=r32(elf.s[2].data.data()+3*24);elf.s[9].data[name]='!';}
        if(variant==5)put(elf.s[1].data,76,12,4); // Nonzero unsupported implicit prefix.
        if(variant==6)elf.s[6].link=9;
        auto changed=elf.encode();Image image;check(image.parse(changed.data(),changed.size())==Error::None);
        std::vector<uint8_t> isa(1216,0xab);Destination d{isa.data(),isa.size(),0x100000};StagedImage out;out.textBytes=999;
        check(image.stage(&d,1,out)!=Error::None && out.textBytes==999);
        for(auto b:isa)check(b==0xab);
    }
    {
        Elf elf(bytes);unsigned bss=elf.add(".bss.global",8,32),data=elf.add(".data.global",1,24),rel=elf.add(".rela.data.global",4,48);
        elf.s[rel].link=2;elf.s[rel].info=data;elf.s[rel].entry=24;
        unsigned symbol=elf.symbol(bss,16,4);
        put(elf.s[data].data,0,5,8);put(elf.s[data].data,8,7,4);
        put(elf.s[rel].data,0,0,8);put(elf.s[rel].data,8,(uint64_t(symbol)<<32)|1,8);put(elf.s[rel].data,16,uint64_t(-8),8);
        put(elf.s[rel].data,24,8,8);put(elf.s[rel].data,32,(uint64_t(1)<<32)|3,8);put(elf.s[rel].data,40,0,8);
        auto changed=elf.encode();Image image;check(image.parse(changed.data(),changed.size())==Error::None && image.segmentCount()==3);
        std::vector<uint8_t> isa(1216,0xaa),zero(32,0xaa),initialized(24,0xaa);
        Destination d[]={{isa.data(),isa.size(),0x1234500000ULL},{zero.data(),zero.size(),0x300000},{initialized.data(),initialized.size(),0x400000}};StagedImage out;
        check(image.stage(d,3,out)==Error::None && out.relocationCount==4);
        for(auto b:zero)check(!b);
        check(r64(initialized.data())==0x30000d && r32(initialized.data()+8)==0x19);
        d[1].gpuAddress=d[0].gpuAddress;check(image.stage(d,3,out)==Error::InvalidBinding);
        d[1].gpuAddress=0x300000;d[2].cpu=d[0].cpu;check(image.stage(d,3,out)==Error::InvalidBinding);
    }
}
static void vmConnection(const std::vector<uint8_t>&bytes) {
    XeMemory::Allocation slots[4];XeMemory::VirtualMemory vm;XeMemory::Handle input{},output{};
    uint64_t pages[2]={0x100000,0x200000};unsigned index=0;
    struct Mock {uint64_t*pages;unsigned*index;};Mock mock{pages,&index};XeMemory::Backend backend{};backend.context=&mock;
    backend.pin=[](void*p,uint64_t,uint64_t size,XeMemory::Pin&out){auto&m=*static_cast<Mock*>(p);check(size==4096 && *m.index<2);out={m.pages+*m.index,m.pages+*m.index,1};++*m.index;return XeMemory::Status::Ok;};
    backend.unpin=[](void*,XeMemory::Pin&p){p={};return XeMemory::Status::Ok;};
    check(vm.initialize(slots,4,4096,65536,backend)==XeMemory::Status::Ok);
    check(vm.reserve(42,4096,4096,input)==XeMemory::Status::Ok && vm.reserve(42,4096,4096,output)==XeMemory::Status::Ok);
    EvidenceValues values;values.count=1024;values.nonce=123;
    check(resolveEvidencePointers(vm,42,input,output,{},values)==Error::InvalidBinding);
    check(vm.pin(42,input)==XeMemory::Status::Ok && vm.pin(42,output)==XeMemory::Status::Ok);
    check(resolveEvidencePointers(vm,42,input,output,{},values)==Error::Unavailable);
    SurfaceBackend surfaces{};surfaces.resolve=[](void*,uint64_t owner,XeMemory::Handle,const XeMemory::Allocation&a,bool writable,uint32_t&surface){check(owner==42 && a.state==XeMemory::State::Pinned);surface=writable?0x456:0x123;return true;};
    check(resolveEvidencePointers(vm,43,input,output,surfaces,values)==Error::InvalidBinding);
    check(resolveEvidencePointers(vm,42,input,output,surfaces,values)==Error::None);
    check(values.inputAddress==4096 && values.outputAddress==8192 && values.inputSurface==0x123 && values.outputSurface==0x456);
    Image image;check(image.parse(bytes.data(),bytes.size())==Error::None);Payload payload;
    check(image.payload(values,payload)==Error::None && payload.softwareOnly);
    check(vm.inspect(42,input)->state==XeMemory::State::Pinned && !vm.inspect(42,input)->activeUses);
    check(vm.reclaim(42,input)==XeMemory::Status::Ok && vm.reclaim(42,output)==XeMemory::Status::Ok);
    check(resolveEvidencePointers(vm,42,input,output,surfaces,values)==Error::InvalidBinding);
}
int main(int argc,char**argv){check(argc==2);std::ifstream file(argv[1],std::ios::binary);std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(file)),{});check(file && bytes.size()==6944);
    actualArtifact(bytes);truncationAndMetadata(bytes);relocations(bytes);vmConnection(bytes);
    std::printf("PASS xe_zebin: %u checks; actual 6944-byte Intel Zebin, GPU NOT executed\n",checks);
}
