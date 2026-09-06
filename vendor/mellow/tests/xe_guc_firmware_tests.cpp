// Tests execute the production loader against an explicitly emulated device.
// The firmware input is the unmodified pinned Intel image, never a fake CSS.
#include "XeGuCFirmware.hpp"
#include <array>
#include <vector>
#include <fstream>
#include <iterator>
#include <map>
#include <iostream>
#include <cstdlib>
#include <algorithm>
using namespace XeGuCFirmware;
static unsigned assertions;
#define CHECK(x) do { ++assertions; if(!(x)) { std::cerr << "line " << __LINE__ << ": " << #x << '\n'; std::exit(1); } } while(0)
static uint32_t word(const uint8_t *p) { return p[0]|(uint32_t(p[1])<<8)|(uint32_t(p[2])<<16)|(uint32_t(p[3])<<24); }
static std::vector<uint8_t> original;
struct Device {
    std::array<std::vector<uint8_t>,3> memory;
    std::array<std::vector<uint64_t>,3> pages;
    Plan plan {};
    std::map<uint32_t,uint32_t> regs;
    std::vector<std::pair<uint32_t,uint32_t>> writes;
    std::vector<unsigned> releases;
    unsigned retains {}, syncs {}, patReads {}, mappingReads {}, fullAdsReads {};
    unsigned retainFailAt {99}, releaseFailAt {99}, syncFailAt {99}, writeFailAt {999};
    uint32_t readFailReg {0xffffffff}, allOnesReg {0xffffffff}, pat {2};
    uint32_t finalStatus {0x8000f0ec};
    uint64_t now {100}, readyAfter {}, pteXor {};
    unsigned clockCalls {}, pteReads {};
    bool admitted {true}, quiet {true}, published {true}, fullAds {false};
    bool resetCompletes {true}, resetClearsDma {true}, dmaCompletes {true}, dmaStarted {}, locksAppear {true};
    bool regressingClock {}, frozenClock {}, unstablePte {}, adsUntouchedAtReset {true};
    Device() {
        const uint64_t sizes[]={ (firmwareFileBytes+4095U)&~4095U, 8417280, logBytes };
        plan.owner=7;plan.epoch=11;plan.pciRevision=8;
        Region *r[]={&plan.firmware,&plan.ads,&plan.log};
        for(unsigned n=0;n<3;++n) {
            memory[n].assign(size_t(sizes[n]),0xa5);pages[n].resize(size_t(sizes[n]/4096));
            for(size_t i=0;i<pages[n].size();++i)pages[n][i]=0x100000000ULL+n*0x10000000ULL+i*4096;
            *r[n]={7,20+n,0x01000000ULL*(n+1),sizes[n],memory[n].data(),pages[n].data(),pages[n].size(),&memory[n]};
        }
        std::copy(original.begin(),original.end(),memory[0].begin());
        regs[0xc000]=1;regs[0xd08]=15<<16;regs[0xa168]=0xffff;
    }
    static Device &self(void *p) { return *static_cast<Device *>(p); }
    static bool read(void *p,uint32_t reg,uint32_t &v) {
        auto &s=self(p);
        if(reg==s.readFailReg)return false;
        if(reg==s.allOnesReg){v=0xffffffff;return true;}
        if(reg>=0x800000) {
            const Region *regions[]={&s.plan.firmware,&s.plan.ads,&s.plan.log};
            for(const auto *r:regions) {
                const uint64_t base=0x800000+r->ggtt/4096*8;
                if(reg>=base && reg<base+r->pageCount*8) {
                    const uint64_t offset=reg-base;
                    uint64_t pte=(r->dmaPages[offset/8]|1ULL|(3ULL<<52))^s.pteXor;
                    ++s.pteReads;
                    if(s.unstablePte && s.pteReads%3==0)pte^=1ULL<<32;
                    v=uint32_t(pte>>(offset%8*8));return true;
                }
            }
            return false;
        }
        if(reg==0xc314 && s.dmaStarted && s.dmaCompletes)s.regs[reg]&=~1U;
        if(reg==0xc000 && s.dmaStarted)s.regs[reg]=s.now>=s.readyAfter?s.finalStatus:0;
        v=s.regs[reg];return true;
    }
    static bool write(void *p,uint32_t reg,uint32_t value) {
        auto &s=self(p);s.writes.emplace_back(reg,value);
        if(s.writes.size()==s.writeFailAt)return false;
        if(reg==0x941c && value==8) {
            if(s.writes.size()==1)s.adsUntouchedAtReset=s.memory[1][0]==0xa5 && s.memory[2][0]==0xa5;
            s.regs[reg]=s.resetCompletes?0:8;
            if(s.resetCompletes){s.regs[0xc000]=1;if(s.resetClearsDma)s.regs[0xc314]=0;s.dmaStarted=false;}
        } else if(reg==0xc050 || reg==0xc340)s.regs[reg]=value|(s.locksAppear?1:0);
        else if(reg==0xc314) {
            s.regs[reg]=(s.regs[reg]&~(value>>16))|(value&(value>>16));
            if(value&1)s.dmaStarted=true;
        } else s.regs[reg]=value;
        return true;
    }
    static uint64_t clock(void *p) { auto &s=self(p);++s.clockCalls;return s.regressingClock && s.clockCalls>1?0:s.now; }
    static void delay(void *p,uint32_t us) { auto &s=self(p);if(!s.frozenClock)s.now+=us; }
    static bool admission(void *p,uint64_t owner,uint64_t epoch) { auto &s=self(p);return s.admitted && owner==s.plan.owner && epoch==s.plan.epoch; }
    static bool quiescence(void *p,uint64_t,uint64_t) { return self(p).quiet; }
    static bool retain(void *p,const Region &r,bool writable) {
        auto &s=self(p);++s.retains;
        CHECK(writable==(r.generation!=20));return s.retains!=s.retainFailAt;
    }
    static bool release(void *p,const Region &r) {
        auto &s=self(p);if(s.releases.size()+1==s.releaseFailAt)return false;
        s.releases.push_back(unsigned(r.generation));return true;
    }
    static bool sync(void *p,const Region &) { auto &s=self(p);++s.syncs;return s.syncs!=s.syncFailAt; }
    static bool readPat(void *p,uint32_t &v) { auto &s=self(p);++s.patReads;v=s.pat;return true; }
    static bool mapping(void *p,const Region &,uint64_t) { auto &s=self(p);++s.mappingReads;return s.published; }
    static bool ads(void *p,const Plan &,const MellowXe::FirmwareInfo &) { auto &s=self(p);++s.fullAdsReads;return s.fullAds; }
    Backend backend() {
        Backend b {};b.io={this,read,write,clock,delay};b.opaque=this;b.physicalRevision=8;
        b.admitted=admission;b.quiesced=quiescence;b.retain=retain;b.release=release;
        b.synchronize=sync;b.readPat3=readPat;b.mappingPublished=mapping;b.fullAdsValid=ads;return b;
    }
};
static void checkRelease(Device &d,Loader &l) {
    CHECK(l.resetAndRelease()==Error::None);CHECK(l.heldRegions()==0);
    CHECK(d.releases==std::vector<unsigned>({22,21,20}));
    CHECK(!l.running(7,11));CHECK(l.start(d.plan)==Error::Busy);
}
static void validBoot() {
    Device d;Loader l(d.backend());CHECK(l.start(d.plan)==Error::None);
    CHECK(l.state()==State::Running);CHECK(l.running(7,11));CHECK(!l.running(8,11));CHECK(!l.running(7,12));
    CHECK(!l.submissionProfile());CHECK(l.heldRegions()==3);CHECK(d.releases.empty());
    CHECK(d.syncs==3 && d.fullAdsReads==0 && d.mappingReads==3 && d.patReads==1);
    CHECK(d.adsUntouchedAtReset);CHECK(l.lastStatus()==0x8000f0ec);
    const std::vector<std::pair<uint32_t,uint32_t>> prefix={{0x941c,8},{0xc050,0x3f3000},{0xc340,0x4000},{0xc180,0}};
    CHECK(std::equal(prefix.begin(),prefix.end(),d.writes.begin()));
    CHECK(d.writes.size()==29);
    CHECK(d.regs[0xc184]==(uint32_t(d.plan.log.ggtt)|0x3f7));
    CHECK(d.regs[0xc188]==0 && d.regs[0xc18c]==0 && d.regs[0xc190]==64);
    CHECK(d.regs[0xc194]==uint32_t((d.plan.ads.ggtt>>12)<<1));CHECK(d.regs[0xc198]==0x7d410008);
    for(uint32_t r=0xc19c;r<=0xc1b8;r+=4)CHECK(d.regs[r]==0);
    CHECK(d.regs[0xc064]==0x8602 && d.regs[0x13816c]==1 && d.regs[0xa168]==0xfdff);
    CHECK(d.regs[0xc200]==d.plan.firmware.ggtt+319936);
    CHECK(d.regs[0xc300]==d.plan.firmware.ggtt && d.regs[0xc304]==0x80000);
    CHECK(d.regs[0xc308]==0x2000 && d.regs[0xc30c]==0x70000 && d.regs[0xc310]==319936);
    CHECK(d.writes[d.writes.size()-2]==std::make_pair(0xc314U,0x00110011U));
    CHECK(d.writes.back()==std::make_pair(0xc314U,0x00100000U));
    const uint8_t *a=d.plan.ads.cpu;
    CHECK(word(a+4100)==d.plan.ads.ggtt+4572);CHECK(word(a+4104)==d.plan.ads.ggtt+4668);
    CHECK(word(a+4244)==d.plan.ads.ggtt+24576);
    CHECK(word(a+4572+64)==500000 && word(a+4572+68)==1 && word(a+4572+72)==15);
    for(unsigned i=0;i<512;++i)CHECK(a[4668+i]==32);
    for(unsigned i=0;i<16;++i)CHECK(word(a+4668+512+4*i)==0);
    CHECK(word(a+4668+512+64+8)==16);
    CHECK(a[8417279]==0);CHECK(std::all_of(d.memory[2].begin(),d.memory[2].end(),[](uint8_t x){return x==0;}));
    d.admitted=false;CHECK(!l.running(7,11));CHECK(l.resetAndRelease()==Error::Unavailable);CHECK(l.heldRegions()==3);
    d.admitted=true;checkRelease(d,l);
}
static void firmwareAndMappings() {
    MellowXe::FirmwareInfo f {};CHECK(inspectPinnedFirmware(original.data(),original.size(),f)==Error::None);
    CHECK(f.rsaOffset==319936 && f.rsaBytes==384 && f.ucodeBytes==319808);
    CHECK(minimalAdsBytes(f)==8417280);CHECK(inspectPinnedFirmware(original.data(),original.size()-1,f)==Error::FirmwareMismatch);
    for(size_t offset: {size_t(0),size_t(127),size_t(128),size_t(319935),size_t(319936),size_t(320319)}) {
        auto altered=original;altered[offset]^=1;
        CHECK(inspectPinnedFirmware(altered.data(),altered.size(),f)==Error::FirmwareMismatch);
    }
    for(uint64_t mask: {1ULL,2ULL,4ULL,1ULL<<12,1ULL<<52,1ULL<<53,1ULL<<63}) {
        Device d;d.pteXor=mask;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Mapping);
        CHECK(d.writes.empty());CHECK(l.heldRegions()==0);CHECK(d.releases.size()==3);
    }
    {Device d;d.unstablePte=true;CHECK(verifyGgtt(d.backend().io,d.plan.firmware)==Error::Mapping);}
    {Device d;d.pages[0][0]|=1;CHECK(verifyGgtt(d.backend().io,d.plan.firmware)==Error::Mapping);}
    {Device d;d.pages[0][0]=1ULL<<46;CHECK(verifyGgtt(d.backend().io,d.plan.firmware)==Error::Mapping);}
    {Device d;d.plan.firmware.ggtt=gucGgttTop;CHECK(verifyGgtt(d.backend().io,d.plan.firmware)==Error::Invalid);}
    {Device d;d.readFailReg=0x800000+uint32_t(d.plan.firmware.ggtt/4096*8)+4;CHECK(verifyGgtt(d.backend().io,d.plan.firmware)==Error::Io);}
    {Device d;d.pat=3;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Mapping);CHECK(d.writes.empty());}
    {Device d;d.published=false;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Mapping);CHECK(d.writes.empty());}
    {Device d;d.memory[0][100]^=1;Loader l(d.backend());CHECK(l.start(d.plan)==Error::FirmwareMismatch);CHECK(d.writes.empty());CHECK(l.heldRegions()==0);}
}
static void validationAndOwnership() {
    {Device d;d.plan.pciRevision=9;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Invalid);CHECK(d.retains==0);}
    {Device d;d.plan.ads.ggtt=d.plan.firmware.ggtt;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Invalid);}
    {Device d;d.plan.ads.cpu=d.plan.firmware.cpu;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Invalid);}
    {Device d;d.plan.log.bytes-=4096;d.plan.log.pageCount--;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Invalid);}
    {Device d;d.plan.ads.bytes-=4096;d.plan.ads.pageCount--;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Invalid);CHECK(l.heldRegions()==0);}
    {Device d;d.admitted=false;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Unavailable);CHECK(d.writes.empty());CHECK(d.retains==0);}
    {Device d;d.quiet=false;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Busy);CHECK(d.retains==0);}
    {Device d;auto b=d.backend();b.mappingPublished=nullptr;Loader l(b);CHECK(l.start(d.plan)==Error::Unavailable);}
    for(unsigned n=1;n<=3;++n) {
        Device d;d.retainFailAt=n;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Mapping);
        CHECK(l.heldRegions()==0);CHECK(d.releases.size()==n-1);CHECK(d.writes.empty());
    }
    {Device d;d.pat=0;d.releaseFailAt=1;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Quarantined);
        CHECK(l.heldRegions()==3);CHECK(d.writes.empty());d.releaseFailAt=99;CHECK(l.resetAndRelease()==Error::None);CHECK(d.writes.empty());}
    for(unsigned n=1;n<=3;++n) {
        Device d;d.syncFailAt=n;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Mapping);
        CHECK(l.heldRegions()==3 && d.releases.empty());CHECK(!d.dmaStarted);checkRelease(d,l);
    }
    for(unsigned n=1;n<=29;++n) {
        Device d;d.writeFailAt=n;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Io);
        CHECK(l.state()==State::Failed);CHECK(l.heldRegions()==3);CHECK(d.releases.empty());
        d.writeFailAt=999;checkRelease(d,l);
    }
    {Device d;Loader l(d.backend());CHECK(l.start(d.plan)==Error::None);d.releaseFailAt=2;
        CHECK(l.resetAndRelease()==Error::Quarantined);CHECK(l.heldRegions()==2);CHECK(!l.running(7,11));
        CHECK(d.releases==std::vector<unsigned>({22}));d.releaseFailAt=99;checkRelease(d,l);}
}
static void wopcmAndProfiles() {
    {Device d;d.regs[0xc050]=0x3f3001;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Wopcm);CHECK(l.heldRegions()==3);checkRelease(d,l);}
    {Device d;d.locksAppear=false;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Wopcm);CHECK(d.writes.size()==2);checkRelease(d,l);}
    {Device d;d.regs[0xc050]=0x7f3001;d.regs[0xc340]=0x4001;Loader l(d.backend());CHECK(l.start(d.plan)==Error::None);
        CHECK(std::none_of(d.writes.begin(),d.writes.end(),[](auto p){return p.first==0xc050 || p.first==0xc340;}));checkRelease(d,l);}
    {Device d;d.regs[0xc050]=0x7f3001;d.regs[0xc340]=0x4003;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Wopcm);checkRelease(d,l);}
    {Device d;d.plan.hucUploadBytes=100000;Loader l(d.backend());CHECK(l.start(d.plan)==Error::None);CHECK(d.regs[0xc340]==0x20003);checkRelease(d,l);}
    {Device d;d.plan.hucUploadBytes=0xffffffff;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Wopcm);checkRelease(d,l);}
    {Device d;d.plan.profile=Profile::Submission;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Unavailable);CHECK(d.writes.empty());CHECK(l.heldRegions()==0);}
    for(bool ccs:{false,true}) {Device d;d.plan.profile=Profile::Submission;d.plan.ccsPresent=ccs;d.fullAds=true;
        Loader l(d.backend());CHECK(l.start(d.plan)==Error::None);CHECK(l.submissionProfile());
        CHECK(d.regs[0xc188]==((1U<<22)|(ccs?(1U<<11):0)));CHECK(d.regs[0xc18c]==0x01000010);
        CHECK(d.memory[1][0]==0xa5);CHECK(d.fullAdsReads==1);checkRelease(d,l);}
}
static void timeoutsAndErrors() {
    {Device d;d.resetCompletes=false;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Timeout);CHECK(d.now==5100);CHECK(l.heldRegions()==3);
        CHECK(d.memory[1][0]==0xa5);d.resetCompletes=true;checkRelease(d,l);}
    {Device d;d.dmaCompletes=false;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Timeout);CHECK(d.now==100100);
        CHECK(d.writes.back()==std::make_pair(0xc314U,0x00100000U));CHECK(l.heldRegions()==3);checkRelease(d,l);}
    {Device d;Loader l(d.backend());CHECK(l.start(d.plan)==Error::None);d.regs[0xc314]=1;d.resetClearsDma=false;
        CHECK(l.resetAndRelease()==Error::Timeout);CHECK(l.heldRegions()==3);CHECK(d.releases.empty());
        d.resetClearsDma=true;checkRelease(d,l);}
    {Device d;d.readyAfter=3000101;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Timeout);CHECK(d.now==3000100);
        d.now+=10000;CHECK(!l.running(7,11));CHECK(l.state()==State::Failed);CHECK(l.heldRegions()==3);checkRelease(d,l);}
    {Device d;d.readyAfter=3000100;Loader l(d.backend());CHECK(l.start(d.plan)==Error::None);checkRelease(d,l);}
    {Device d;d.frozenClock=true;d.resetCompletes=false;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Timeout);CHECK(d.now==100);}
    {Device d;d.regressingClock=true;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Clock);CHECK(l.heldRegions()==3);}
    for(uint32_t boot:{0x13U,0x2bU,0x50U,0x73U,0x74U,0x75U,0x77U,0x79U,0x7aU,0x7eU}) {
        Device d;d.finalStatus=boot<<1;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Authentication);CHECK(l.heldRegions()==3);checkRelease(d,l);
    }
    for(uint32_t uk:{2U,3U,4U,7U,8U,0x60U,0x70U,0x71U,0x73U,0x74U,0x75U,0x76U}) {
        Device d;d.finalStatus=uk<<8;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Boot);checkRelease(d,l);
    }
    {Device d;d.finalStatus=0x40000000;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Authentication);checkRelease(d,l);}
    {Device d;d.allOnesReg=0xc000;Loader l(d.backend());CHECK(l.start(d.plan)==Error::Boot);CHECK(l.heldRegions()==3);}
    {Device d;Loader l(d.backend());CHECK(l.start(d.plan)==Error::None);d.finalStatus|=0x20000;CHECK(!l.running(7,11));
        d.quiet=false;CHECK(l.resetAndRelease()==Error::Busy);CHECK(l.heldRegions()==3);d.quiet=true;checkRelease(d,l);}
}
int main(int argc,char **argv) {
    CHECK(argc==2);std::ifstream f(argv[1],std::ios::binary);CHECK(bool(f));
    original.assign(std::istreambuf_iterator<char>(f),{});CHECK(original.size()==firmwareFileBytes);
    firmwareAndMappings();validBoot();validationAndOwnership();wopcmAndProfiles();timeoutsAndErrors();
    std::cout << "{\"assertions\":" << assertions << ",\"passed\":true,\"firmware_bytes\":" << original.size() << "}\n";
}
