#include "XeGuCFirmware.hpp"
#include "XeGuCTransport.hpp"

namespace XeGuCFirmware {
namespace {
constexpr uint32_t statusReg=0xc000, dmaControl=0xc314;
void put32(uint8_t *p,uint32_t value) { for(unsigned i=0;i<4;++i)p[i]=uint8_t(value>>(8*i)); }
bool span(uint64_t base,uint64_t bytes,uint64_t limit) { return base<limit && bytes && bytes<=limit-base; }
bool overlap(uint64_t a,uint64_t n,uint64_t b,uint64_t m) { return a<b+m && b<a+n; }
bool regionValid(const Region &r) {
    return r.owner && r.generation && r.cpu && r.pinCookie && r.dmaPages &&
        r.bytes && r.bytes<=64*1024*1024 && !(r.bytes&4095) && !(r.ggtt&4095) &&
        r.ggtt>=4*1024*1024 && span(r.ggtt,r.bytes,gucGgttTop) &&
        r.pageCount==r.bytes/4096 && uintptr_t(r.cpu)<=UINTPTR_MAX-r.bytes;
}
uint32_t rotate(uint32_t x,unsigned n) { return (x>>n)|(x<<(32-n)); }
// SHA-256 identifies the exact pinned image; authentication remains in BootROM.
bool exactHash(const uint8_t *data,size_t length) {
    static const uint32_t k[64]={
        0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
    uint32_t h[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    const size_t total=(length+9+63)&~size_t(63);
    for(size_t offset=0;offset<total;offset+=64) {
        uint32_t w[64] {};
        for(unsigned i=0;i<64;++i) {
            const size_t at=offset+i;uint8_t byte=0;
            if(at<length)byte=data[at];else if(at==length)byte=0x80;
            else if(at>=total-8)byte=uint8_t((uint64_t(length)*8)>>(8*(total-1-at)));
            w[i/4]|=uint32_t(byte)<<(24-8*(i%4));
        }
        for(unsigned i=16;i<64;++i) {
            const uint32_t x=w[i-15],y=w[i-2];
            w[i]=w[i-16]+(rotate(x,7)^rotate(x,18)^(x>>3))+w[i-7]+(rotate(y,17)^rotate(y,19)^(y>>10));
        }
        uint32_t a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],v=h[7];
        for(unsigned i=0;i<64;++i) {
            const uint32_t t1=v+(rotate(e,6)^rotate(e,11)^rotate(e,25))+((e&f)^(~e&g))+k[i]+w[i];
            const uint32_t t2=(rotate(a,2)^rotate(a,13)^rotate(a,22))+((a&b)^(a&c)^(b&c));
            v=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
        }
        h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=v;
    }
    static const uint32_t expected[]={0x7794f0b6,0xabe5fcd9,0xc6f47035,0xdafe2199,0xf30a6e7d,0x230bd5a5,0x3fbf8005,0xa60e5911};
    uint32_t difference=0;for(unsigned i=0;i<8;++i)difference|=h[i]^expected[i];
    return difference==0;
}
const Region &at(const Plan &p,unsigned i) { return i==0?p.firmware:i==1?p.ads:p.log; }
}
Error inspectPinnedFirmware(const uint8_t *data,size_t count,MellowXe::FirmwareInfo &info) {
    info={};
    if(!data || count!=firmwareFileBytes || !exactHash(data,count))return Error::FirmwareMismatch;
    if(MellowXe::parseGuCCss(data,count,info)!=MellowXe::FirmwareError::None ||
        info.release.packed()!=0x463500 || info.submission.packed()!=0x011a00 ||
        info.rsaBytes!=384 || info.ucodeOffset!=128 || info.minimumBytes!=count ||
        info.privateDataBytes!=8392704)return Error::FirmwareMismatch;
    return Error::None;
}
Error verifyGgtt(const MellowXe::MmioAccess &io,const Region &r) {
    if(!regionValid(r) || !io.read32)return Error::Invalid;
    for(size_t i=0;i<r.pageCount;++i) {
        const uint64_t dma=r.dmaPages[i];
        if((dma&4095) || dma>=(1ULL<<46))return Error::Mapping;
        const uint32_t reg=0x800000+uint32_t(((r.ggtt/4096)+i)*8);
        uint32_t hi=0,lo=0,again=0;
        // Split stable read is safe only while the owning driver locks GGTT writers.
        if(!io.read32(io.opaque,reg+4,hi) || !io.read32(io.opaque,reg,lo) ||
            !io.read32(io.opaque,reg+4,again))return Error::Io;
        const uint64_t pte=(uint64_t(hi)<<32)|lo;
        if(hi!=again || pte!=(dma|1ULL|(3ULL<<52)))return Error::Mapping;
    }
    return Error::None;
}
uint32_t minimalAdsBytes(const MellowXe::FirmwareInfo &f) {
    if(!f.privateDataBytes || f.privateDataBytes>32*1024*1024)return 0;
    return minimalAdsPrefix+((f.privateDataBytes+4095)&~4095U);
}
Error populateMinimalAds(const Region &ads,const MellowXe::FirmwareInfo &f,uint32_t doorbell) {
    const uint32_t bytes=minimalAdsBytes(f);
    if(!regionValid(ads) || !bytes || ads.bytes<bytes || doorbell==UINT32_MAX)return Error::Invalid;
    // guc_ads=4572, guc_policies=96, system_info=640; all fields below are
    // byte offsets derived from the packed Intel structures, not private Apple offsets.
    constexpr unsigned policies=4572,systemInfo=4668;
    for(uint64_t i=0;i<ads.bytes;++i)ads.cpu[i]=0;
    put32(ads.cpu+4100,uint32_t(ads.ggtt+policies));
    put32(ads.cpu+4104,uint32_t(ads.ggtt+systemInfo));
    put32(ads.cpu+4244,uint32_t(ads.ggtt+minimalAdsPrefix));
    put32(ads.cpu+policies+64,500000);put32(ads.cpu+policies+68,1);
    put32(ads.cpu+policies+72,15);
    for(unsigned i=0;i<16*32;++i)ads.cpu[systemInfo+i]=32;
    put32(ads.cpu+systemInfo+512+64+2*4,((doorbell>>16)&255)+1);
    return Error::None;
}
bool Loader::allowed() const {
    return backend_.admitted && backend_.admitted(backend_.opaque,plan_.owner,plan_.epoch);
}
bool Loader::read(uint32_t reg,uint32_t &value) const {
    return allowed() && backend_.io.read32 && backend_.io.read32(backend_.io.opaque,reg,value) && value!=UINT32_MAX;
}
bool Loader::write(uint32_t reg,uint32_t value) {
    if(!allowed() || !backend_.io.write32)return false;
    touchedHardware_=true;return backend_.io.write32(backend_.io.opaque,reg,value);
}
Error Loader::wait(uint32_t reg,uint32_t mask,uint32_t expected,uint32_t timeout,uint32_t interval) {
    const uint64_t start=backend_.io.nowMicros(backend_.io.opaque);uint64_t previous=start;
    for(uint32_t tries=0;tries<=timeout/interval;++tries) {
        uint32_t value=0;if(!read(reg,value))return Error::Io;
        const uint64_t now=backend_.io.nowMicros(backend_.io.opaque);
        if(now<previous)return Error::Clock;
        previous=now;
        if((value&mask)==expected)return Error::None;
        if(now-start>=timeout || tries==timeout/interval)return Error::Timeout;
        backend_.io.delayMicros(backend_.io.opaque,interval);
    }
    return Error::Timeout;
}
Error Loader::reset() {
    if(!backend_.quiesced || !backend_.quiesced(backend_.opaque,plan_.owner,plan_.epoch))return Error::Busy;
    // Main GT12.70 is outside Wa_14025883347's graphics>=20.04 range.
    if(!write(0x941c,8))return Error::Io;
    Error error=wait(0x941c,8,0,5000,50);if(error!=Error::None)return error;
    if(!read(statusReg,lastStatus_) || !(lastStatus_&1))return Error::Boot;
    return wait(dmaControl,1,0,100000,1000);
}
Error Loader::wopcm() {
    uint32_t baseReg=0,sizeReg=0;
    if(!read(0xc340,baseReg) || !read(0xc050,sizeReg))return Error::Io;
    const bool baseLocked=baseReg&1,sizeLocked=sizeReg&1;
    if(baseLocked!=sizeLocked)return Error::Wopcm; // partial write-once layout is not repaired by guess
    const uint32_t total=baseLocked?8*1024*1024:4*1024*1024;
    const uint32_t usable=total-36864;
    const uint64_t minimumBase=uint64_t(plan_.hucUploadBytes)+16384;
    if(minimumBase>=usable)return Error::Wopcm;
    uint32_t base=baseLocked?(baseReg&0xffffc000U):uint32_t((minimumBase+16383)&~16383ULL);
    uint32_t size=baseLocked?(sizeReg&0xfffff000U):(usable-base)&0xfffff000U;
    if(base<minimumBase || base>=usable || size>usable-base ||
        uint64_t(size)<info_.rsaOffset+24576)return Error::Wopcm;
    // Regions must sit above the actual (possibly firmware-prelocked 8MiB) WOPCM.
    for(unsigned i=0;i<3;++i)if(at(plan_,i).ggtt<total)return Error::Mapping;
    const uint32_t agent=plan_.hucUploadBytes?2:0;
    if(baseLocked) {
        if((baseReg&2)!=agent)return Error::Wopcm;
        return Error::None;
    }
    // Hardware supplies LOCKED/VALID on successful write; do not fake those bits.
    if(!write(0xc050,size) || !read(0xc050,sizeReg))return Error::Io;
    if((sizeReg&0xfffff001U)!=(size|1))return Error::Wopcm;
    if(!write(0xc340,base|agent) || !read(0xc340,baseReg))return Error::Io;
    if((baseReg&0xffffc003U)!=(base|agent|1))return Error::Wopcm;
    return Error::None;
}
Error Loader::authenticate() {
    const uint64_t start=backend_.io.nowMicros(backend_.io.opaque);uint64_t previous=start;
    for(unsigned tries=0;tries<=300;++tries) {
        if(!read(statusReg,lastStatus_))return Error::Io;
        const uint64_t now=backend_.io.nowMicros(backend_.io.opaque);
        if(now<previous)return Error::Clock;
        previous=now;
        if(XeGuC::statusAuthenticatedAndReady(lastStatus_))return Error::None;
        const uint32_t boot=(lastStatus_>>1)&127,uk=(lastStatus_>>8)&255;
        if((lastStatus_&0xc0000000U)==0x40000000U || boot==0x13 || boot==0x2b || boot==0x50 ||
            boot==0x73 || boot==0x74 || boot==0x75 || boot==0x77 || boot==0x79 || boot==0x7a || boot==0x7e)
            return Error::Authentication;
        if(uk==2 || uk==3 || uk==4 || uk==7 || uk==8 || uk==0x60 || uk==0x70 || uk==0x71 ||
            uk==0x73 || uk==0x74 || uk==0x75 || uk==0x76)return Error::Boot;
        if(now-start>=3000000 || tries==300)return Error::Timeout;
        backend_.io.delayMicros(backend_.io.opaque,10000);
    }
    return Error::Timeout;
}
Error Loader::releaseRegions() {
    while(held_) {
        if(!backend_.release(backend_.opaque,at(plan_,held_-1)))return Error::Quarantined;
        --held_;
    }
    return Error::None;
}
Error Loader::fail(Error error) {
    state_=State::Failed;
    // Any issued register write can leave live device ownership. Only an actual
    // later resetAndRelease may drop these references, including after timeout.
    if(!touchedHardware_ && releaseRegions()!=Error::None)return Error::Quarantined;
    return error;
}
Error Loader::start(const Plan &input) {
    if(attempted_)return Error::Busy;
    plan_=input;
    if(!plan_.owner || !plan_.epoch || plan_.pciRevision!=backend_.physicalRevision ||
        (plan_.profile!=Profile::HardwareConfig && plan_.profile!=Profile::Submission))return Error::Invalid;
    for(unsigned i=0;i<3;++i) {
        const Region &r=at(plan_,i);
        if(!regionValid(r) || r.owner!=plan_.owner)return Error::Invalid;
        for(unsigned j=0;j<i;++j)if(overlap(r.ggtt,r.bytes,at(plan_,j).ggtt,at(plan_,j).bytes) ||
            overlap(uintptr_t(r.cpu),r.bytes,uintptr_t(at(plan_,j).cpu),at(plan_,j).bytes))return Error::Invalid;
    }
    if(plan_.firmware.bytes<firmwareFileBytes || plan_.log.bytes<logBytes)return Error::Invalid;
    if(!backend_.io.read32 || !backend_.io.write32 || !backend_.io.nowMicros || !backend_.io.delayMicros ||
        !backend_.retain || !backend_.release || !backend_.synchronize || !backend_.readPat3 ||
        !backend_.mappingPublished || !allowed())return Error::Unavailable;
    if(!backend_.quiesced || !backend_.quiesced(backend_.opaque,plan_.owner,plan_.epoch))return Error::Busy;
    attempted_=true;
    for(unsigned i=0;i<3;++i) {
        if(!backend_.retain(backend_.opaque,at(plan_,i),i!=0))return fail(Error::Mapping);
        ++held_;
    }
    state_=State::Retained;
    Error error=inspectPinnedFirmware(plan_.firmware.cpu,firmwareFileBytes,info_);
    if(error!=Error::None)return fail(error);
    if(plan_.ads.bytes<minimalAdsBytes(info_))return fail(Error::Invalid);
    uint32_t pat=0;
    if(!backend_.readPat3(backend_.opaque,pat) || pat!=2)return fail(Error::Mapping);
    for(unsigned i=0;i<3;++i) {
        if(!backend_.mappingPublished(backend_.opaque,at(plan_,i),plan_.epoch))return fail(Error::Mapping);
        error=verifyGgtt(backend_.io,at(plan_,i));if(error!=Error::None)return fail(error);
    }
    if(plan_.profile==Profile::Submission && (!backend_.fullAdsValid ||
        !backend_.fullAdsValid(backend_.opaque,plan_,info_)))return fail(Error::Unavailable);
    state_=State::Starting;
    error=reset();if(error!=Error::None)return fail(error);
    error=wopcm();if(error!=Error::None)return fail(error);
    // No CPU overwrite of shared ADS/log while a previous GuC could access it.
    uint32_t doorbells=0;if(!read(0xd08,doorbells))return fail(Error::Io);
    if(plan_.profile==Profile::HardwareConfig) {
        error=populateMinimalAds(plan_.ads,info_,doorbells);if(error!=Error::None)return fail(error);
    }
    for(uint64_t i=0;i<plan_.log.bytes;++i)plan_.log.cpu[i]=0;
    for(unsigned i=0;i<3;++i)if(!backend_.synchronize(backend_.opaque,at(plan_,i)))return fail(Error::Mapping);
    uint32_t params[14] {};
    params[0]=uint32_t(plan_.log.ggtt)|0x3f7; // 16KiB crash,64KiB event,1MiB capture
    if(plan_.profile==Profile::Submission) {params[1]=(1U<<22)|(plan_.ccsPresent?(1U<<11):0);params[2]=(1U<<4)|(1U<<24);}
    params[3]=1U<<6; // no verbose logging; valid backing still allocated
    params[4]=uint32_t((plan_.ads.ggtt>>12)<<1);params[5]=(0x7d41U<<16)|plan_.pciRevision;
    if(!write(0xc180,0))return fail(Error::Io);
    for(unsigned i=0;i<14;++i)if(!write(0xc184+i*4,params[i]))return fail(Error::Io);
    if(!write(0xc064,0x8602) || !write(0x13816c,1))return fail(Error::Io);
    uint32_t interrupts=0;if(!read(0xa168,interrupts) || !write(0xa168,interrupts&~(1U<<9)))return fail(Error::Io);
    // MTL384-byte RSA is read by BootROM via GGTT, not copied into64 scratch slots.
    if(!write(0xc200,uint32_t(plan_.firmware.ggtt+info_.rsaOffset)))return fail(Error::Io);
    if(!write(0xc300,uint32_t(plan_.firmware.ggtt)) || !write(0xc304,8U<<16) ||
        !write(0xc308,0x2000) || !write(0xc30c,7U<<16) || !write(0xc310,uint32_t(info_.rsaOffset)))return fail(Error::Io);
    state_=State::Dma;
    if(!write(dmaControl,0x00110011))return fail(Error::Io); // masked enable UOS_MOVE|START_DMA
    error=wait(dmaControl,1,0,100000,1000);
    // Disable UOS_MOVE as in Xe, even after timeout; this does not prove DMA stopped.
    if(!write(dmaControl,0x00100000))return fail(Error::Io);
    if(error!=Error::None)return fail(error);
    state_=State::Authenticating;error=authenticate();if(error!=Error::None)return fail(error);
    state_=State::Running;return Error::None;
}
Error Loader::resetAndRelease() {
    if(!attempted_)return Error::Invalid;
    if(!held_)return Error::None;
    if(!allowed())return Error::Unavailable;
    if(touchedHardware_) {const Error error=reset();if(error!=Error::None)return fail(error);}
    state_=State::Failed;return releaseRegions();
}
bool Loader::running(uint64_t owner,uint64_t epoch) const {
    if(state_!=State::Running || owner!=plan_.owner || epoch!=plan_.epoch)return false;
    uint32_t value=0;return read(statusReg,value) && XeGuC::statusAuthenticatedAndReady(value);
}
}
