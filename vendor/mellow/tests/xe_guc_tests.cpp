#include "XeGuCTransport.hpp"
#include <cstdio>
#include <cstdlib>
#include <vector>
using namespace XeGuC;
static unsigned checks;
#define CHECK(c) do { ++checks; if (!(c)) { std::fprintf(stderr,"line %d: %s\n",__LINE__,#c); std::exit(1); } } while (0)
struct Fixture {
    Descriptor hd {}, gd {};
    uint32_t hw[1024] {}, gw[2048] {};
    bool admitted {true}, authorized {true}, barriers {true}, notified {true}, stopped {true};
    unsigned releaseCount {}, notifyCount {}, acquireCount {};
    Transport transport;
    static bool admit(void *v, uint64_t epoch) { return static_cast<Fixture*>(v)->admitted && epoch == 7; }
    static bool authorize(void *v, uint64_t, const Action &) { return static_cast<Fixture*>(v)->authorized; }
    static bool acquire(void *v) { auto &f=*static_cast<Fixture*>(v); ++f.acquireCount; return f.barriers; }
    static bool release(void *v) { auto &f=*static_cast<Fixture*>(v); ++f.releaseCount; return f.barriers; }
    static bool notify(void *v) { auto &f=*static_cast<Fixture*>(v); ++f.notifyCount; return f.notified; }
    static bool config(void *v, const Configuration &) { return static_cast<Fixture*>(v)->stopped; }
    Ops ops() { return Ops{this, admit, authorize, acquire, release, notify, config}; }
    Ring h() { return Ring{&hd,hw,1024,0x100000,0x101000}; }
    Ring g() { return Ring{&gd,gw,2048,0x100040,0x102000}; }
    static MellowXe::FirmwareInfo firmware() {
        MellowXe::FirmwareInfo f {}; f.release={70,53,0}; f.submission={1,26,0}; return f;
    }
    Status attach() { return transport.attach(h(),g(),ops(),7,firmware()); }
    Cookie send(const Action &a, uint64_t deadline=100) {
        Cookie c; CHECK(transport.send(a,0,deadline,c)==Status::Ok); return c;
    }
    void peerRead() { hd.head=hd.tail; }
    void peerMessage(uint16_t fence, const std::vector<uint32_t> &hxg) {
        uint32_t tail=gd.tail; gw[tail]=(uint32_t(fence)<<16)|uint32_t(hxg.size());
        for (size_t i=0;i<hxg.size();++i) gw[(tail+1+uint32_t(i))&2047]=hxg[i];
        gd.tail=(tail+1+uint32_t(hxg.size()))&2047;
    }
    void receive(uint64_t now=1) { Message m; CHECK(transport.receive(7,now,m)==Status::Ok); }
};
static Action mode(uint32_t id=2,bool enable=true) { Action a; CHECK(encodeMode(id,enable,a)==Status::Ok); return a; }
static Action schedule(uint32_t id=2) { Action a; CHECK(encodeSchedule(id,a)==Status::Ok); return a; }
static Action request() { Action a; CHECK(encodeAuthenticateHuC(0x100000,a)==Status::Ok); return a; }
static void encoders() {
    CHECK(statusAuthenticatedAndReady(0x8000f0ec));
    for (uint32_t s : {0U,0xffffffffU,0x4000f0ecU,0x800050ecU,0x8000f0a0U,0x8000f0edU,0x8002f0ecU})
        CHECK(!statusAuthenticatedAndReady(s));
    Action a;
    CHECK(encodeRegister(5,4,3,0x123456789abcdef1ULL,a)==Status::Ok);
    const uint32_t expected[]={0x4502,1,5,4,3,0,0,0,0,0,0x9abcdef1,0x12345678};
    CHECK(a.count==12); for(unsigned i=0;i<12;++i) CHECK(a.words[i]==expected[i]);
    CHECK(validateAction(a)==Status::Ok);
    a.words[5]=1; CHECK(validateAction(a)==Status::Invalid);
    CHECK(encodeRegister(65535,0,1,1,a)==Status::Invalid);
    CHECK(encodeRegister(3,5,1,1,a)==Status::Invalid);
    CHECK(encodeRegister(3,0,0,1,a)==Status::Invalid);
    CHECK(encodeRegister(3,0,1,0,a)==Status::Invalid);
    CHECK(encodeAuthenticateHuC(3,a)==Status::Invalid);
    a=mode(); a.words[2]=2; CHECK(validateAction(a)==Status::Invalid);
    a=schedule(); a.words[0]=0x7f454c46; CHECK(validateAction(a)==Status::Invalid);
}
static void requests() {
    Fixture f; CHECK(f.attach()==Status::Ok);
    Cookie c=f.send(request());
    CHECK(c.epoch==7 && c.fence==0 && f.hw[0]==2 && f.hw[1]==0x4000 && f.hw[2]==0x100000);
    CHECK(f.hd.tail==3 && f.transport.responseCredits()==767 && f.releaseCount==2 && f.notifyCount==1);
    Reply reply;
    f.peerMessage(c.fence,{0xb0000005}); f.receive(1);
    CHECK(f.transport.query(c,reply)==Status::Ok && reply.state==ReplyState::Busy && reply.creditsHeld);
    CHECK(f.transport.retire(c)==Status::Busy);
    f.peerMessage(c.fence,{0xf0000000}); f.receive(2);
    CHECK(f.transport.query(c,reply)==Status::Ok && reply.state==ReplyState::Success && !reply.creditsHeld);
    CHECK(f.transport.responseCredits()==1023 && f.transport.retire(c)==Status::Ok);
    CHECK(f.transport.query(c,reply)==Status::UnknownCookie);
    Fixture failure; CHECK(failure.attach()==Status::Ok); auto a=request(); Cookie fc=failure.send(a);
    failure.peerMessage(fc.fence,{0xe0120034}); failure.receive();
    CHECK(failure.transport.query(fc,reply)==Status::Ok && reply.state==ReplyState::Failure && reply.hxg[0]==0xe0120034);
    Fixture retry; CHECK(retry.attach()==Status::Ok); Cookie rc=retry.send(a);
    retry.peerMessage(rc.fence,{0xd0000002}); retry.receive();
    CHECK(retry.transport.query(rc,reply)==Status::Ok && reply.state==ReplyState::Retry && !reply.creditsHeld);
}
static void eventAndTimeout() {
    Fixture f; CHECK(f.attach()==Status::Ok); Cookie c=f.send(mode());
    CHECK(c.fence==0x8000 && f.hw[0]==0x80000003 && f.hw[1]==0x20001001);
    Cookie extra; CHECK(f.transport.send(mode(),0,100,extra)==Status::Busy);
    CHECK(f.transport.expire(100)==Status::Ok);
    Reply reply; CHECK(f.transport.query(c,reply)==Status::Ok && reply.state==ReplyState::TimedOut && reply.creditsHeld);
    CHECK(f.transport.retire(c)==Status::Busy);
    f.peerMessage(0,{0x90001002,2,1}); f.receive(101);
    CHECK(f.transport.query(c,reply)==Status::Ok && reply.state==ReplyState::TimedOut && reply.late && !reply.creditsHeld);
    CHECK(f.transport.responseCredits()==1023);
    CHECK(f.transport.retire(c)==Status::Ok);
    Fixture padding; CHECK(padding.attach()==Status::Ok); const Action a=schedule();
    for(unsigned i=0;i<341;++i) { auto pc=padding.send(a); CHECK(padding.transport.retire(pc)==Status::Ok); if(!i)padding.peerRead(); }
    CHECK(padding.hd.head==3); // exactly 3 free words: padding consumes one, packet must wait
    CHECK(padding.transport.send(a,0,100,c)==Status::Busy && !c.epoch && padding.hd.tail==0 && padding.hw[1023]==0);
    padding.peerRead(); CHECK(padding.transport.send(a,0,100,c)==Status::Ok && padding.hd.tail==3);
    Fixture d; CHECK(d.attach()==Status::Ok); Action dereg; CHECK(encodeDeregister(9,dereg)==Status::Ok);
    Cookie dc=d.send(dereg); d.peerMessage(0,{0x90004600,9}); d.receive();
    CHECK(d.transport.query(dc,reply)==Status::Ok && reply.state==ReplyState::Success);
    Fixture wrong; CHECK(wrong.attach()==Status::Ok); wrong.send(mode());
    wrong.peerMessage(0,{0x90001002,2,0}); Message message;
    CHECK(wrong.transport.receive(7,1,message)==Status::Corrupt && wrong.transport.responseCredits()==1019);
}
static void ringWrapAndCredits() {
    Fixture f; CHECK(f.attach()==Status::Ok); Action a=schedule();
    for(unsigned i=0;i<341;++i) { Cookie c=f.send(a); CHECK(f.transport.retire(c)==Status::Ok); f.peerRead(); }
    CHECK(f.hd.tail==1023); f.hw[1023]=0xdeadbeef;
    Cookie c=f.send(a); CHECK(f.hw[1023]==0 && f.hd.tail==3 && f.hw[1]==0x20001000);
    CHECK(f.transport.retire(c)==Status::Ok);
    // Advance G2H to 2046 using real incoming unsolicited events, then split response.
    for(unsigned i=0;i<1023;++i) { f.peerMessage(0,{0x90006000}); f.receive(1); }
    CHECK(f.gd.head==2046);
    // send requires monotonic time; use explicit now rather than fixture helper.
    CHECK(f.transport.send(request(),1,100,c)==Status::Ok);
    f.peerMessage(c.fence,{0xf0000000,0x12345678}); f.receive(2);
    Reply reply; CHECK(f.transport.query(c,reply)==Status::Ok && reply.count==2 && reply.hxg[1]==0x12345678 && f.gd.head==1);
    Fixture credits; CHECK(credits.attach()==Status::Ok);
    auto req=request(); credits.send(req); credits.send(req); credits.send(req);
    CHECK(credits.transport.responseCredits()==255);
    CHECK(credits.transport.send(req,0,100,c)==Status::Busy);
    CHECK(credits.transport.expire(100)==Status::Ok && credits.transport.responseCredits()==255);
    Fixture full; CHECK(full.attach()==Status::Ok);
    for(unsigned i=0;i<32;++i) full.send(a);
    CHECK(full.transport.send(a,0,100,c)==Status::Busy);
}
static void invalidPaths() {
    Fixture initialEvent; initialEvent.peerMessage(0,{0x90006000});
    CHECK(initialEvent.attach()==Status::Ok); initialEvent.receive();
    Fixture f; f.admitted=false; CHECK(f.attach()==Status::Unavailable && f.hd.tail==0);
    f.admitted=true; CHECK(f.attach()==Status::Ok);
    f.authorized=false; Cookie c; CHECK(f.transport.send(schedule(),0,100,c)==Status::Unavailable && !c.epoch && f.hd.tail==0);
    f.authorized=true; f.hd.head=1024;
    CHECK(f.transport.send(schedule(),0,100,c)==Status::Corrupt && f.transport.broken());
    Fixture stale; CHECK(stale.attach()==Status::Ok); Message m;
    CHECK(stale.transport.receive(8,1,m)==Status::StaleEpoch && !stale.transport.broken());
    Fixture truncated; CHECK(truncated.attach()==Status::Ok); truncated.gw[0]=10; truncated.gd.tail=2;
    CHECK(truncated.transport.receive(7,1,m)==Status::Corrupt && truncated.gd.head==0);
    Fixture reserved; CHECK(reserved.attach()==Status::Ok); reserved.gw[0]=0x101; reserved.gw[1]=0xf0000000; reserved.gd.tail=2;
    CHECK(reserved.transport.receive(7,1,m)==Status::Corrupt);
    Fixture origin; CHECK(origin.attach()==Status::Ok); origin.peerMessage(0,{0x70000000});
    CHECK(origin.transport.receive(7,1,m)==Status::Corrupt);
    Fixture unknown; CHECK(unknown.attach()==Status::Ok); unknown.peerMessage(8,{0xf0000000});
    CHECK(unknown.transport.receive(7,1,m)==Status::UnknownCookie && unknown.transport.responseCredits()==1023);
    Fixture duplicate; CHECK(duplicate.attach()==Status::Ok); auto dc=duplicate.send(request());
    duplicate.peerMessage(dc.fence,{0xf0000000}); duplicate.receive(); duplicate.peerMessage(dc.fence,{0xf0000000});
    CHECK(duplicate.transport.receive(7,2,m)==Status::Corrupt && duplicate.transport.responseCredits()==1023);
    Fixture notify; CHECK(notify.attach()==Status::Ok); notify.notified=false;
    CHECK(notify.transport.send(request(),0,100,c)==Status::PublishedUnknown && c.epoch==7 && notify.hd.tail==3);
    CHECK(notify.transport.responseCredits()==767 && notify.transport.retire(c)==Status::Busy);
    Fixture abi; auto fw=Fixture::firmware(); fw.submission.minor=25;
    CHECK(abi.transport.attach(abi.h(),abi.g(),abi.ops(),7,fw)==Status::Invalid);
}
struct MmioFixture {
    bool allowed {true}, failRead {}, failWrite {}, stuckClock {}, regress {}, autoReply {true};
    uint64_t now {};
    uint32_t reply {0xf0000000}, reads {}, notify {}, request[4] {};
    std::vector<std::vector<uint32_t>> commands;
    std::vector<uint32_t> scripted;
    static bool admit(void *v,uint64_t e) { return static_cast<MmioFixture*>(v)->allowed && e==7; }
    static bool read(void *v,uint32_t offset,uint32_t &out) {
        auto &f=*static_cast<MmioFixture*>(v); if(f.failRead)return false;
        if(offset==mainMailboxRegister+12) {out=f.request[3];return true;}
        CHECK(offset==mainMailboxRegister);
        if(!f.scripted.empty()) {out=f.scripted[f.reads<f.scripted.size()?f.reads:f.scripted.size()-1];++f.reads;}
        else out=f.reply;
        return true;
    }
    static bool write(void *v,uint32_t offset,uint32_t value) {
        auto &f=*static_cast<MmioFixture*>(v); if(f.failWrite)return false;
        if(offset==mainNotifyRegister) {
            CHECK(value==0); ++f.notify;
            f.commands.push_back({f.request[0],f.request[1],f.request[2],f.request[3]});
            if(f.autoReply) f.reply=f.request[0]==0x508?0xf0000001:0xf0000000;
        } else {CHECK(offset>=mainMailboxRegister && offset<mainMailboxRegister+16 && !(offset&3)); f.request[(offset-mainMailboxRegister)/4]=value;}
        return true;
    }
    static uint64_t time(void *v) {return static_cast<MmioFixture*>(v)->now;}
    static void delay(void *v,uint32_t us) {auto &f=*static_cast<MmioFixture*>(v);if(f.regress)f.now=0;else if(!f.stuckClock)f.now+=us;}
    MmioOps ops() {return MmioOps{this,admit,read,write,time,delay};}
};
static void mailbox() {
    const uint32_t enable[]={0x4509,1}; uint32_t response;
    MmioFixture m; Mailbox box(m.ops(),7);
    const uint32_t invalidKey[]={0x508,0x99990002,0,0};
    CHECK(box.exchange(invalidKey,4,response)==Status::Invalid && !m.notify);
    const uint32_t wrongLength[]={0x508,0x9040002,4096,0};
    CHECK(box.exchange(wrongLength,4,response)==Status::Invalid && !m.notify);
    CHECK(box.exchange(enable,2,response)==Status::Ok && response==0 && m.notify==1);
    MmioFixture busy; busy.scripted={0xb0000001,0xb0000002,0xf0000000}; Mailbox b(busy.ops(),7);
    CHECK(b.exchange(enable,2,response)==Status::Ok && busy.now==2000);
    MmioFixture timeout; timeout.autoReply=false; timeout.reply=0; Mailbox t(timeout.ops(),7);
    CHECK(t.exchange(enable,2,response)==Status::Timeout && timeout.now==50000 && t.poisoned());
    CHECK(t.exchange(enable,2,response)==Status::Corrupt && timeout.notify==1);
    MmioFixture busyTimeout; busyTimeout.autoReply=false; busyTimeout.reply=0xb0000001; Mailbox bt(busyTimeout.ops(),7);
    CHECK(bt.exchange(enable,2,response)==Status::Timeout && busyTimeout.now==2000000);
    MmioFixture retry; retry.autoReply=false; retry.reply=0xd0000011; Mailbox r(retry.ops(),7);
    CHECK(r.exchange(enable,2,response)==Status::Retry && !r.poisoned() && retry.notify==1);
    MmioFixture failure; failure.autoReply=false; failure.reply=0xe0000011; Mailbox f(failure.ops(),7);
    CHECK(f.exchange(enable,2,response)==Status::Rejected && response==0xe0000011 && !f.poisoned());
    MmioFixture allones; allones.autoReply=false; allones.reply=0xffffffff; Mailbox a(allones.ops(),7);
    CHECK(a.exchange(enable,2,response)==Status::IoFailure && a.poisoned());
    MmioFixture no; no.allowed=false; Mailbox n(no.ops(),7);
    CHECK(n.exchange(enable,2,response)==Status::Unavailable && no.notify==0);
    MmioFixture stuck; stuck.stuckClock=true; stuck.autoReply=false; stuck.reply=0; Mailbox sc(stuck.ops(),7);
    CHECK(sc.exchange(enable,2,response)==Status::Timeout);
    MmioFixture reg; reg.now=100; reg.regress=true; reg.autoReply=false; reg.reply=0; Mailbox cr(reg.ops(),7);
    CHECK(cr.exchange(enable,2,response)==Status::IoFailure);
}
static void configure() {
    Fixture f; Configuration c{f.h(),f.g(),7,0x100000,0xf0000000,Fixture::firmware()};
    MmioFixture m; Mailbox box(m.ops(),7);
    CHECK(configureAndEnable(box,c,f.ops())==Status::Ok && m.commands.size()==7);
    const uint32_t keys[]={0x9030002,0x9020002,0x9040001,0x9060002,0x9050002,0x9070001};
    const uint32_t values[]={0x100000,0x101000,4096,0x100040,0x102000,8192};
    for(unsigned i=0;i<6;++i) {CHECK(m.commands[i][0]==0x508 && m.commands[i][1]==keys[i]);CHECK(m.commands[i][2]==values[i] && m.commands[i][3]==0);}
    CHECK(m.commands[6][0]==0x4509 && m.commands[6][1]==1);
    f.stopped=false; f.hw[0]=123; size_t before=m.commands.size();
    CHECK(configureAndEnable(box,c,f.ops())==Status::Unavailable && f.hw[0]==123 && m.commands.size()==before);
    f.stopped=true; c.g2h.bufferGgtt=c.h2g.bufferGgtt;
    CHECK(configureAndEnable(box,c,f.ops())==Status::Invalid);
    c.g2h=f.g(); c.epoch=8; CHECK(configureAndEnable(box,c,f.ops())==Status::Invalid);
    c.epoch=7; MmioFixture rejected; rejected.autoReply=false; rejected.reply=0xf0000000; Mailbox rb(rejected.ops(),7);
    CHECK(configureAndEnable(rb,c,f.ops())==Status::Rejected && rejected.commands.size()==1);
}
static void exhaustCookies() {
    Fixture f; CHECK(f.attach()==Status::Ok); const Action a=schedule();
    // Real public API exercise: no internal mutation to reach the wire-cookie boundary.
    for(unsigned i=0;i<0x8000;++i) { Cookie c=f.send(a); CHECK(c.fence==(i|0x8000)); CHECK(f.transport.retire(c)==Status::Ok);f.peerRead(); }
    Cookie c; CHECK(f.transport.send(a,0,100,c)==Status::Exhausted && !c.epoch);
}
int main() {
    encoders(); requests(); eventAndTimeout(); ringWrapAndCredits(); invalidPaths(); mailbox(); configure(); exhaustCookies();
    std::printf("{\"assertions\":%u,\"status\":\"passed\",\"gpu_execution\":false}\n",checks);
}
