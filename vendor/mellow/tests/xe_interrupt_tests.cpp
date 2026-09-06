#include "XeInterrupt.hpp"
#include "XeFence.hpp"
#include "XeInterruptDispatch.hpp"
#include <cstdio>
#include <cstdlib>
#include <map>
#include <vector>
#include <tuple>
static unsigned checks=0;
#define CHECK(x) do { ++checks; if(!(x)) {std::fprintf(stderr,"line %d: %s\n",__LINE__,#x);std::exit(1);} } while(0)
using namespace XeInterrupt;
struct Peer {
    std::map<uint32_t,uint32_t> reg;
    std::vector<std::pair<uint32_t,uint32_t>> writes;
    std::vector<Identity> events;
    uint32_t ids[2][32] {}, selected[2] {}, dw[2] {};
    bool alive=true, invalid=false, stalledClock=false, reenter=false;
    unsigned call=0,failAt=0,more=0,otherCalls=0;
    uint64_t tick=0;
    Controller *controller=nullptr;
    static bool admitted(void *p,uint64_t epoch){return static_cast<Peer*>(p)->alive && epoch==7;}
    bool allowed(){return !failAt || ++call!=failAt;}
    static bool read(void *p,uint32_t r,uint32_t &v){
        auto &s=*static_cast<Peer*>(p);if(!s.allowed())return false;
        if(r==bankStatus || r==bankStatus+4){v=s.dw[(r-bankStatus)/4];return true;}
        if(r==identityRegister || r==identityRegister+4){unsigned b=(r-identityRegister)/4;v=s.invalid?0:s.ids[b][s.selected[b]];return true;}
        v=s.reg[r];return true;
    }
    static bool write(void *p,uint32_t r,uint32_t v){
        auto &s=*static_cast<Peer*>(p);if(!s.allowed())return false;
        s.writes.push_back({r,v});
        if(r==tileMaster){
            if(v==masterEnable && s.reenter){s.reenter=false;s.reg[r]|=1;CHECK(s.controller->filter());}
            if(v==0) s.reg[r]&=~masterEnable;
            else if(v==masterEnable)s.reg[r]|=masterEnable;
            else s.reg[r]&=~v;
        }else if(r==gfxMaster)s.reg[r]&=~v;
        else if(r==bankStatus || r==bankStatus+4)s.dw[(r-bankStatus)/4]&=~v;
        else if(r==selectorRegister || r==selectorRegister+4){
            unsigned bit=0;while(bit<32 && !(v&(1U<<bit)))++bit;
            CHECK(bit<32 && v==(1U<<bit));s.selected[(r-selectorRegister)/4]=bit;
        }else if(r==identityRegister || r==identityRegister+4){unsigned b=(r-identityRegister)/4;CHECK(v==s.ids[b][s.selected[b]]);s.ids[b][s.selected[b]]=0;}
        else s.reg[r]=v;
        return true;
    }
    static uint64_t now(void *p){auto &s=*static_cast<Peer*>(p);return s.stalledClock?0:++s.tick;}
    static Handling identity(void *p,uint64_t epoch,const Identity &id){
        auto &s=*static_cast<Peer*>(p);CHECK(epoch==7);CHECK(!(s.reg[tileMaster]&masterEnable));
        if(s.more){--s.more;return Handling::More;}s.events.push_back(id);return Handling::Drained;
    }
    static Handling other(void *p,uint64_t epoch,uint32_t bits){auto &s=*static_cast<Peer*>(p);CHECK(epoch==7 && bits);++s.otherCalls;return Handling::Drained;}
    Ops ops(){return {{this,read,write,now,nullptr},this,admitted,identity,other};}
    Configuration config(){return {7,0x8086,0x7d41,1,true,true};}
    void raise(unsigned bank,unsigned bit,unsigned cls,unsigned instance,uint16_t vector){
        reg[tileMaster]|=1;reg[gfxMaster]|=1U<<bank;dw[bank]|=1U<<bit;
        ids[bank][bit]=identityValid|(instance<<20)|(cls<<16)|vector;
    }
    void setup(Controller &c){controller=&c;reg[0x1900e8]=0xffffffff;reg[0x190090]=0xffffffff;reg[0x1900a0]=0xffffffff;reg[0x190100]=0xffffffff;
        CHECK(c.configure(config(),ops())==Status::Ok);CHECK(c.start()==Status::Ok);}
};
static void irqTests(){
    {Peer p;Controller c;p.setup(c);CHECK(p.reg[0x190030]==0x00110011);CHECK(p.reg[0x190048]==0x00110000);
     CHECK(p.reg[0x190100]==0xffeeffee);CHECK(p.reg[0x1900e8]==0x7fffffff);CHECK(!c.filter());
     p.raise(0,0,0,0,1);p.raise(1,25,4,0,0x8000);p.reg[gfxMaster]|=1U<<16;
     auto n=p.writes.size();CHECK(c.filter());CHECK(p.writes.size()==n+1);CHECK(p.writes.back()==std::make_pair(tileMaster,0U));
     CHECK(!c.filter());CHECK(c.service()==Status::Ok);CHECK(p.events.size()==2 && p.otherCalls==1);
     CHECK(p.events[0].engineClass==0 && p.events[1].engineClass==4 && p.events[1].vector==0x8000);
     CHECK(p.dw[0]==0 && p.dw[1]==0);CHECK(p.reg[tileMaster]&masterEnable);
     CHECK(c.stop()==Status::Ok);CHECK(!c.filter());}
    // Every bank and selector position, including bit31 and instance63.
    for(unsigned bank=0;bank<2;++bank)for(unsigned bit=0;bit<32;++bit){Peer p;Controller c;p.setup(c);
        p.raise(bank,bit,5,63,0x11);CHECK(c.filter());CHECK(c.service()==Status::Ok);
        CHECK(p.events.size()==1 && p.events[0].bit==bit && p.events[0].bank==bank && p.events[0].instance==63);}
    {Peer p;Controller c;p.setup(c);p.raise(0,0,0,0,1);p.more=2;CHECK(c.filter());
     CHECK(c.service()==Status::Pending);auto n=p.writes.size();CHECK(c.service()==Status::Pending);CHECK(p.writes.size()==n);
     CHECK(c.service()==Status::Ok);CHECK(p.events.size()==1);}
    for(bool stuck:{false,true}){Peer p;Controller c;p.setup(c);p.raise(0,0,0,0,1);p.invalid=true;p.stalledClock=stuck;CHECK(c.filter());
     CHECK(c.service()==Status::Timeout && c.faulted());CHECK(p.dw[0]==1);CHECK(p.events.empty());CHECK(!(p.reg[tileMaster]&masterEnable));}
    {Peer p;Controller c;p.setup(c);p.reg[tileMaster]=0xffffffff;CHECK(c.filter());CHECK(c.faulted());CHECK(c.service()==Status::Faulted);}
    {Peer p;Controller c;p.setup(c);p.raise(0,0,0,0,1);CHECK(c.filter());p.alive=false;auto n=p.writes.size();
     CHECK(c.service()==Status::Unavailable);CHECK(p.writes.size()==n);CHECK(c.stop()==Status::Unavailable);}
    {Peer p;Controller c;p.setup(c);p.raise(0,0,0,0,1);CHECK(c.filter());p.reenter=true;
     CHECK(c.service()==Status::Ok);CHECK(!(p.reg[tileMaster]&masterEnable));CHECK(c.service()==Status::Ok);}
    // Fault at each real register operation in configuration or IRQ collection.
    for(unsigned fail=1;fail<45;++fail){Peer p;Controller c;p.controller=&c;p.failAt=fail;
        Status s=c.configure(p.config(),p.ops());
        if(s==Status::Ok){s=c.start();if(s==Status::Ok){p.raise(0,0,0,0,1);if(c.filter())s=c.service();}}
        if(c.faulted())CHECK(!(p.reg[tileMaster]&masterEnable));
        CHECK(s==Status::Ok || s==Status::IoFailure || s==Status::Faulted);}
    {Peer p;Controller c;auto cfg=p.config();cfg.device=0x1234;CHECK(c.configure(cfg,p.ops())==Status::Invalid);CHECK(p.writes.empty());}
}
struct Memory {
    alignas(8) uint64_t word=123;
    bool valid=true,stopped=true,retainOK=true;
    unsigned holds=0,releases=0,validCalls=0,revokeAt=0;
    XeFence::Slot slot(){return {&word,0x200000,5,6,8,7,0,0};}
    static bool validSlot(void *p,const XeFence::Slot &s){auto &m=*static_cast<Memory*>(p);++m.validCalls;return m.valid && s.allocation==5 && s.owner==6 && s.context==8 && s.epoch==7 && s.cpu==&m.word && (!m.revokeAt || m.validCalls!=m.revokeAt);}
    static bool retain(void *p,const XeFence::Slot &){auto &m=*static_cast<Memory*>(p);if(!m.retainOK)return false;++m.holds;return true;}
    static void release(void *p,const XeFence::Slot &){auto &m=*static_cast<Memory*>(p);CHECK(m.holds==1);--m.holds;++m.releases;}
    static bool quiesced(void *p,const XeFence::Slot &){return static_cast<Memory*>(p)->stopped;}
    XeFence::Ops ops(){return {this,validSlot,retain,release,quiesced};}
};
static void fenceTests(){using F=XeFence::Status;
    {Memory m;XeFence::Timeline t;XeFence::Observation o;CHECK(t.bind(m.slot(),m.ops())==F::Ok);CHECK(m.word==0 && m.holds==1);
     m.stopped=false;CHECK(t.observe(7,o)==F::Ok && !o.sequence && o.acquireOrdered);
     CHECK(t.published(6,1)==F::StaleEpoch);CHECK(t.published(7,2)==F::Invalid);CHECK(t.published(7,1)==F::Ok);
     CHECK(t.observe(7,o)==F::Ok && o.sequence==0);m.word=1;CHECK(t.observe(7,o)==F::Ok && o.sequence==1);
     CHECK(o.context==8 && o.owner==6 && o.epoch==7 && o.ggtt==0x200000 && o.raw==1);
     CHECK(t.close()==F::Busy && m.holds==1);CHECK(t.observe(7,o)==F::NotBound);m.stopped=true;CHECK(t.close()==F::Ok && m.releases==1);
     CHECK(t.bind(m.slot(),m.ops())==F::Invalid);}
    for(uint64_t corrupt:{2ULL,0x100000001ULL,~0ULL}){Memory m;XeFence::Timeline t;XeFence::Observation o;
        CHECK(t.bind(m.slot(),m.ops())==F::Ok);CHECK(t.published(7,1)==F::Ok);m.word=corrupt;
        CHECK(t.observe(7,o)==F::Corrupt && !o.acquireOrdered);CHECK(t.held());CHECK(t.close()==F::Ok);}
    {Memory m;XeFence::Timeline t;XeFence::Observation o;CHECK(t.bind(m.slot(),m.ops())==F::Ok);
     for(uint32_t seq=1;seq<=65536;++seq){CHECK(t.published(7,seq)==F::Ok);m.word=seq;CHECK(t.observe(7,o)==F::Ok && o.sequence==seq);}
     m.word=65535;CHECK(t.observe(7,o)==F::Corrupt);CHECK(t.close()==F::Ok);}
    {Memory m;XeFence::Timeline t;m.stopped=false;CHECK(t.bind(m.slot(),m.ops())==F::Unavailable);CHECK(m.word==123 && !m.holds);}
    {Memory m;XeFence::Timeline t;XeFence::Observation o;CHECK(t.bind(m.slot(),m.ops())==F::Ok);m.revokeAt=m.validCalls+2;
     CHECK(t.observe(7,o)==F::Unavailable && !o.acquireOrdered);CHECK(t.close()==F::Ok);}
    for(unsigned field=0;field<9;++field){Memory m;XeFence::Timeline t;auto s=m.slot();
        switch(field){case 0:s.cpu=nullptr;break;case 1:s.ggtt=7;break;case 2:s.ggtt=0x100000000ULL;break;
        case 3:s.allocation=0;break;case 4:s.epoch=0;break;case 5:s.context=0;break;case 6:s.owner=0;break;case 7:s.engineClass=4;break;case 8:s.instance=1;break;}
        CHECK(t.bind(s,m.ops())==F::Invalid);CHECK(m.word==123 && !m.holds);}
}
struct GuCPeer {
    XeGuC::Descriptor hd{},gd{};uint32_t hw[1024]{},gw[2048]{};
    XeGuC::Transport transport;unsigned messages=0,fences=0;uint32_t observed=0;
    static bool admit(void *,uint64_t e){return e==7;}
    static bool authorize(void *,uint64_t,const XeGuC::Action &){return true;}
    static bool barrier(void *){return true;}
    static bool config(void *,const XeGuC::Configuration &){return true;}
    static uint64_t now(void *){return 1;}
    static bool message(void *p,uint64_t epoch,const XeGuC::Message &m){auto &g=*static_cast<GuCPeer*>(p);CHECK(epoch==7 && m.count==1 && m.hxg[0]==0x90006000);++g.messages;return true;}
    static bool fence(void *p,const XeFence::Observation &o){auto &g=*static_cast<GuCPeer*>(p);++g.fences;g.observed=o.sequence;return true;}
    void setup(){MellowXe::FirmwareInfo fw{};fw.release={70,53,0};fw.submission={1,26,0};
        CHECK(transport.attach({&hd,hw,1024,0x100000,0x101000},{&gd,gw,2048,0x100040,0x102000},
            {this,admit,authorize,barrier,barrier,barrier,config},7,fw)==XeGuC::Status::Ok);}
};
static void dispatchTests(){
    GuCPeer g;g.setup();Memory m;XeFence::Timeline t;CHECK(t.bind(m.slot(),m.ops())==XeFence::Status::Ok);
    Dispatcher d(g.transport,t,{&g,GuCPeer::now,GuCPeer::message,GuCPeer::fence},7,0);
    Identity guc{0,1,25,4,0,gucToHost},engine{0,0,0,0,0,engineUser};
    for(unsigned i=0;i<65;++i){g.gw[i*2]=1;g.gw[i*2+1]=0x90006000;}g.gd.tail=130;
    CHECK(d.handle(7,guc)==Handling::More && g.messages==64 && g.gd.head==128);
    CHECK(d.handle(7,guc)==Handling::Drained && g.messages==65 && g.gd.head==130);
    CHECK(g.fences==0);CHECK(d.handle(7,engine)==Handling::Drained && g.fences==1 && !g.observed);
    CHECK(t.published(7,1)==XeFence::Status::Ok);CHECK(d.handle(7,engine)==Handling::Drained && !g.observed);
    m.word=1;CHECK(d.handle(7,engine)==Handling::Drained && g.observed==1);
    CHECK(d.handle(6,engine)==Handling::Failed);engine.instance=1;CHECK(d.handle(7,engine)==Handling::Failed);
    guc.instance=16;CHECK(d.handle(7,guc)==Handling::Failed);guc.instance=0;guc.vector|=1;CHECK(d.handle(7,guc)==Handling::Failed);
    CHECK(t.close()==XeFence::Status::Ok);
}
int main(){irqTests();fenceTests();dispatchTests();std::printf("{\"passed\":true,\"assertions\":%u,\"physical_irq_or_fence_tested\":false}\n",checks);}
