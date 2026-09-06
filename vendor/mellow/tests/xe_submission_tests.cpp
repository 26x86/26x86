// Host tests of real source. Every hardware callback below is an explicit mock.
#include "XeSubmission.hpp"
#include <array>
#include <cassert>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <map>
#include <vector>
using namespace MellowXe;
namespace MellowXe {
struct SubmissionQueueTestAccess {
    static void setSequence(SubmissionQueue &q,uint32_t next) {q.nextSequence_=next;}
};
}
static unsigned checks;
static void check(bool yes) { ++checks; assert(yes); }
static void dw(std::vector<uint8_t> &v, unsigned at, uint32_t n) {
    for (unsigned i=0;i<4;++i) v[at+i]=uint8_t(n>>(8*i));
}
static std::vector<uint8_t> syntheticFirmware() {
    std::vector<uint8_t> v(128+64+256);
    dw(v,4,32+64+64+1); dw(v,24,32+64+64+1+16); dw(v,28,64); dw(v,32,64); dw(v,36,1);
    dw(v,64,gucRecommendedRelease); dw(v,68,0x010E00); dw(v,16,0x8086); return v;
}
struct Mock {
    uint32_t readinessFlags=requiredReadyBits;
    BackendAcceptance acceptance=BackendAcceptance::Accepted;
    bool canQuiesce=true, valid=true, acquired=true, wrongOwner=false, wrongEngine=false, wrongContext=false;
    uint64_t failResource=0; uint32_t completed=0;
    uint64_t mappingGeneration=1;
    unsigned retains=0,releases=0,submits=0,reads=0;
    std::map<uint64_t,unsigned> refs;
    BatchSnapshot snapshot {};
    SubmissionBackend backend() {
        return {this,
            [](void *p,const FirmwareInfo&,uint64_t g,uint64_t o,uint64_t c,uint32_t e,Readiness&r){
                auto&m=*static_cast<Mock*>(p); r={g,o,c,e,m.readinessFlags}; return SubmitError::None;},
            [](void*p,const Resource&r){auto&m=*static_cast<Mock*>(p);++m.retains;
                if(r.id==m.failResource || r.mappingGeneration!=m.mappingGeneration)return false;
                ++m.refs[r.id]; return true;},
            [](void*p,const Resource&r){auto&m=*static_cast<Mock*>(p); assert(m.refs[r.id]);--m.refs[r.id];++m.releases;},
            [](void*p,const BatchSnapshot&b){auto&m=*static_cast<Mock*>(p);++m.submits;m.snapshot=b;return m.acceptance;},
            [](void*p,uint64_t g,uint64_t o,uint64_t c,uint32_t e,FenceObservation&r){
                auto&m=*static_cast<Mock*>(p);++m.reads;
                r={g,o+(m.wrongOwner?1:0),c+(m.wrongContext?1:0),e+(m.wrongEngine?1U:0U),m.completed,m.valid,m.acquired};
                return SubmitError::None;},
            [](void*p,uint64_t,uint64_t,uint64_t,uint32_t){return static_cast<Mock*>(p)->canQuiesce;}};
    }
};
static Resource resource(uint64_t id=1,uint64_t generation=1) {return {id,99,generation,0x10000+id*4096,4096,true,true};}
static JobResult result(SubmissionQueue&q,FenceToken t){JobResult r;check(q.query(t,r)==SubmitError::None);return r;}
int main(int argc,char**argv) {
    FirmwareInfo info;
    auto fw=syntheticFirmware();
    check(parseGuCCss(fw.data(),fw.size(),info)==FirmwareError::None);
    check(info.ucodeBytes==64 && info.rsaBytes==256 && info.rsaOffset==192 && !info.belowRecommended);
    for(unsigned n=0;n<128;++n) check(parseGuCCss(fw.data(),n,info)==FirmwareError::TruncatedHeader);
    check(parseGuCCss(nullptr,0,info)==FirmwareError::NullInput);
    for(unsigned field:{4U,24U,28U,32U,36U}) {
        for(uint32_t n:{0U,0xFFFFFFFFU,0x80000000U}) {auto bad=fw;dw(bad,field,n);
            check(parseGuCCss(bad.data(),bad.size(),info)!=FirmwareError::None && !info.ucodeBytes);}
    }
    check(parseGuCCss(fw.data(),fw.size()-1,info)==FirmwareError::TruncatedPayload);
    auto old=fw; dw(old,64,gucMinimumRelease-1);
    check(parseGuCCss(old.data(),old.size(),info)==FirmwareError::UnsupportedRelease);
    dw(old,64,gucMinimumRelease);
    check(parseGuCCss(old.data(),old.size(),info)==FirmwareError::None && info.belowRecommended);
    dw(old,64,0x473500);check(parseGuCCss(old.data(),old.size(),info)==FirmwareError::UnsupportedRelease);
    check(parseGuCCss(fw.data(),fw.size(),info)==FirmwareError::None);
    uint32_t words[]={miNoop,miBatchBufferEnd};
    check(validateBootstrapBatch(words,2)==SubmitError::None);
    for(uint32_t bad:{0x464C457FU,0x07230203U,0x11000001U,0x05000001U,0x0A000000U}) {
        uint32_t code[]={bad,miBatchBufferEnd};check(validateBootstrapBatch(code,2)==SubmitError::InvalidCommand);}
    uint32_t early[]={miBatchBufferEnd,miNoop};check(validateBootstrapBatch(early,2)==SubmitError::InvalidCommand);
    check(validateBootstrapBatch(words,1)==SubmitError::InvalidCommand);
    SubmissionQueue unavailable(99,7,unavailableSubmissionBackend()); FenceToken t;
    Resource r=resource();
    check(unavailable.activate(info)==SubmitError::UnsupportedBackend);
    check(unavailable.submit(words,2,&r,1,0,20,t)==SubmitError::UnsupportedBackend && !t.sequence);
    {
        Mock m;SubmissionQueue q(99,7,m.backend(),3);
        for(unsigned bit=0;bit<8;++bit){m.readinessFlags=requiredReadyBits&~(1U<<bit);check(q.activate(info)==SubmitError::NotReady);}
        m.readinessFlags=requiredReadyBits;check(q.activate(info)==SubmitError::None);
        check(q.activate(info)==SubmitError::NotReady);
        Resource rs[]={resource(1),resource(2)};m.failResource=2;
        check(q.submit(words,2,rs,2,0,20,t)==SubmitError::ResourceBusy && m.refs[1]==0 && m.releases==1 && !t.sequence);
        m.failResource=0;m.acceptance=BackendAcceptance::Rejected;
        check(q.submit(words,2,&r,1,1,20,t)==SubmitError::Rejected && m.refs[1]==0 && !t.sequence);
        m.acceptance=BackendAcceptance::Unknown;
        check(q.submit(words,2,&r,1,2,20,t)==SubmitError::AcceptanceUnknown);
        check(result(q,t).resourcesHeld && q.state()==QueueState::NeedsReset);
        check(q.retire(t)==SubmitError::ResourceBusy);
        m.canQuiesce=false;check(q.reset(3)==SubmitError::QuiesceFailed && m.refs[1]==1 && q.generation()==1);
        m.canQuiesce=true;check(q.reset(4)==SubmitError::None && m.refs[1]==0 && q.generation()==2);
        check(result(q,t).state==JobState::Reset);check(q.retire(t)==SubmitError::None);
        check(q.onInterrupt(1,5)==SubmitError::StaleGeneration && m.reads==0);
    }
    {
        Mock m;SubmissionQueue q(99,7,m.backend(),3);check(q.activate(info)==SubmitError::None);
        FenceToken tokens[3];
        for(unsigned i=0;i<3;++i)check(q.submit(words,2,&r,1,i,10,tokens[i])==SubmitError::None);
        check(m.refs[1]==3 && tokens[0].sequence==1 && tokens[2].sequence==3);
        words[0]=0xFFFFFFFF;check(m.snapshot.words[0]==miNoop);words[0]=miNoop;
        m.completed=2;m.wrongOwner=true;check(q.onInterrupt(1,3)==SubmitError::InvalidObservation && m.refs[1]==3);m.wrongOwner=false;
        m.wrongEngine=true;check(q.onInterrupt(1,3)==SubmitError::InvalidObservation && m.refs[1]==3);m.wrongEngine=false;
        m.wrongContext=true;check(q.onInterrupt(1,3)==SubmitError::InvalidObservation && m.refs[1]==3);m.wrongContext=false;
        m.acquired=false;check(q.onInterrupt(1,3)==SubmitError::InvalidObservation && m.refs[1]==3);m.acquired=true;
        m.valid=false;check(q.onInterrupt(1,3)==SubmitError::InvalidObservation && m.refs[1]==3);m.valid=true;
        check(q.onInterrupt(1,4)==SubmitError::None && m.refs[1]==1);
        check(result(q,tokens[0]).state==JobState::Completed && result(q,tokens[1]).state==JobState::Completed);
        check(result(q,tokens[2]).state==JobState::Submitted);
        check(q.onInterrupt(1,4)==SubmitError::None && m.refs[1]==1); // duplicate IRQ
        m.completed=1;check(q.onInterrupt(1,5)==SubmitError::InvalidObservation && m.refs[1]==1);
        m.completed=4;check(q.onInterrupt(1,6)==SubmitError::InvalidObservation && m.refs[1]==1);
        check(q.expire(10)==SubmitError::None && result(q,tokens[2]).state==JobState::TimedOut && m.refs[1]==1);
        check(q.expire(9)==SubmitError::ClockRegression);
        m.completed=3;check(q.onInterrupt(1,11)==SubmitError::None && m.refs[1]==0);
        check(result(q,tokens[2]).state==JobState::TimedOut); // late fence cannot invent success
        check(q.reset(12)==SubmitError::None && q.generation()==2);
        check(q.activate(info)==SubmitError::None);
        m.mappingGeneration=2; // VM rebind/reallocation generation is independent.
        check(q.submit(words,2,&r,1,13,30,t)==SubmitError::ResourceBusy);
        r.mappingGeneration=2;check(q.submit(words,2,&r,1,13,30,t)==SubmitError::None && t.sequence==1);
        check(q.onInterrupt(1,14)==SubmitError::StaleGeneration && m.refs[1]==1);
        check(q.reset(15)==SubmitError::None && m.refs[1]==0);
    }
    r=resource();
    {
        Mock m;SubmissionQueue q(99,7,m.backend());check(q.activate(info)==SubmitError::None);
        for(unsigned variant=0;variant<7;++variant) {auto bad=r;
            if(variant==0)bad.owner=98;
            if(variant==1)bad.id=0;
            if(variant==2)bad.mappingGeneration=0;
            if(variant==3)bad.gpuAddress=UINT64_MAX-2;
            if(variant==4)bad.bytes=0;
            if(variant==5)bad.pinned=false;
            if(variant==6)bad.gpuReadable=false;
            check(q.submit(words,2,&bad,1,0,10,t)!=SubmitError::None && m.retains==0);}
        Resource duplicate[]={r,r};check(q.submit(words,2,duplicate,2,0,10,t)==SubmitError::InvalidArgument);
        check(q.submit(words,2,&r,1,0,0,t)==SubmitError::InvalidArgument);
        for(unsigned i=0;i<maxJobs;++i)check(q.submit(words,2,&r,1,0,10,t)==SubmitError::None);
        check(q.submit(words,2,&r,1,0,10,t)==SubmitError::Capacity && m.refs[1]==maxJobs);
        check(q.reset(1)==SubmitError::None && m.refs[1]==0);
    }
    {
        Mock m;SubmissionQueue q(99,7,m.backend());check(q.activate(info)==SubmitError::None);
        SubmissionQueueTestAccess::setSequence(q,0xFFFFFFFEU);
        FenceToken beforeWrap,last;
        check(q.submit(words,2,&r,1,0,10,beforeWrap)==SubmitError::None && beforeWrap.sequence==0xFFFFFFFEU);
        check(q.submit(words,2,&r,1,0,10,last)==SubmitError::None && last.sequence==0xFFFFFFFFU);
        check(q.submit(words,2,&r,1,0,10,t)==SubmitError::SequenceExhausted && m.refs[1]==2);
        m.completed=0xFFFFFFFFU;check(q.onInterrupt(1,1)==SubmitError::None && m.refs[1]==0);
        check(q.reset(2)==SubmitError::None && q.generation()==2);
        check(q.activate(info)==SubmitError::None);
        check(q.submit(words,2,&r,1,3,10,t)==SubmitError::None && t.sequence==1);
        check(q.onInterrupt(1,4)==SubmitError::StaleGeneration && m.refs[1]==1);
        check(q.reset(5)==SubmitError::None && m.refs[1]==0);
    }
    std::printf("{\"assertion_groups\":%u,\"hardware_backend\":\"explicit-test-mocks-only\"",checks);
    if(argc==2){std::ifstream stream(argv[1],std::ios::binary);
        std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(stream)),{});
        assert(stream && !bytes.empty());FirmwareInfo real;
        const auto status=parseGuCCss(bytes.data(),bytes.size(),real);assert(status==FirmwareError::None);
        std::printf(",\"firmware\":{\"bytes\":%zu,\"parse_status\":\"%s\",\"release\":\"%u.%u.%u\","
            "\"submission\":\"%u.%u.%u\",\"ucode_bytes\":%llu,\"rsa_bytes\":%llu,\"private_data_bytes\":%u,"
            "\"hardware_authenticated\":false}",bytes.size(),firmwareErrorName(status),
            real.release.major,real.release.minor,real.release.patch,real.submission.major,real.submission.minor,real.submission.patch,
            (unsigned long long)real.ucodeBytes,(unsigned long long)real.rsaBytes,real.privateDataBytes);}
    std::printf("}\n");
}
