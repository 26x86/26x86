// The actual forcewake implementation against a register/time simulator.
#include "XeMmioAccess.hpp"
#include <cstdio>
#include <cstdlib>
#include <type_traits>
using namespace MellowXe;
static unsigned checks=0;
#define CHECK(x) do { ++checks; if (!(x)) { std::fprintf(stderr,"line %d: %s\n",__LINE__,#x); std::exit(1); } } while (0)
struct Device {
    uint32_t gmd=(12U<<22)|(70U<<14)|(2U<<6)|3U, ack[2]={0,0};
    uint64_t time=0;
    unsigned writes=0,reads=0,delays=0;
    bool failRead=false,failWrite=false,allOnes=false,noAckOn=false,noAckOff=false,stalledClock=false,reverseClock=false;
    static bool read(void *p,uint32_t reg,uint32_t &out) {
        auto &d=*static_cast<Device *>(p); ++d.reads;
        if (d.failRead) return false;
        if (d.allOnes) { out=UINT32_MAX; return true; }
        if (reg==0xD8C) out=d.gmd;
        else if (reg==0xDFC) out=d.ack[0];
        else if (reg==0xD84) out=d.ack[1];
        else return false;
        return true;
    }
    static bool write(void *p,uint32_t reg,uint32_t value) {
        auto &d=*static_cast<Device *>(p); ++d.writes;
        if (d.failWrite) return false;
        CHECK(reg==0xA188 || reg==0xA278);
        CHECK(value==0x10000 || value==0x10001);
        auto &ack=d.ack[reg==0xA278];
        if (value&1) { if (!d.noAckOn) ack|=1; }
        else if (!d.noAckOff) ack&=~1U;
        return true;
    }
    static uint64_t now(void *p) { return static_cast<Device *>(p)->time; }
    static void delay(void *p,uint32_t micros) {
        auto &d=*static_cast<Device *>(p); ++d.delays;
        CHECK(micros==50);
        if (d.reverseClock) --d.time;
        else if (!d.stalledClock) d.time+=micros;
    }
    MmioAccess access() { return {this,read,write,now,delay}; }
};
int main() {
    static_assert(!std::is_copy_constructible<ForceWake>::value,"hardware ownership must not copy");
    { ForceWake f; Device d;
      CHECK(f.acquire(WakeDomain::Gt)==MmioStatus::Unavailable);
      CHECK(f.initialize({})==MmioStatus::Unavailable);
      CHECK(f.initialize(d.access())==MmioStatus::Ok);
      CHECK(f.ip().architecture==12 && f.ip().release==70 && f.ip().subIp==2 && f.ip().revision==3);
      CHECK(f.initialize(d.access())==MmioStatus::Busy);
      CHECK(f.acquire(static_cast<WakeDomain>(2))==MmioStatus::Invalid);
      CHECK(f.release(static_cast<WakeDomain>(2))==MmioStatus::Invalid);
      CHECK(f.acquire(WakeDomain::Render)==MmioStatus::Busy);
      CHECK(f.release(WakeDomain::Gt)==MmioStatus::Busy);
      d.ack[0]=2; // Another hardware requester bit must remain untouched.
      CHECK(f.acquire(WakeDomain::Gt)==MmioStatus::Ok);
      CHECK(d.ack[0]==3 && d.writes==1);
      CHECK(f.acquire(WakeDomain::Gt)==MmioStatus::Ok && d.writes==1);
      CHECK(f.acquire(WakeDomain::Render)==MmioStatus::Ok);
      CHECK(f.release(WakeDomain::Gt)==MmioStatus::Ok);
      CHECK(f.release(WakeDomain::Gt)==MmioStatus::Busy);
      CHECK(f.shutdown()==MmioStatus::Busy && !f.canDetach());
      CHECK(f.acquire(WakeDomain::Render)==MmioStatus::Ok);
      CHECK(f.release(WakeDomain::Render)==MmioStatus::Ok);
      CHECK(f.held(WakeDomain::Render));
      CHECK(f.release(WakeDomain::Render)==MmioStatus::Ok);
      CHECK(f.release(WakeDomain::Gt)==MmioStatus::Ok && d.ack[0]==2);
      CHECK(f.canDetach() && !f.held(WakeDomain::Gt));
      CHECK(f.shutdown()==MmioStatus::Ok);
      CHECK(f.acquire(WakeDomain::Gt)==MmioStatus::Unavailable);
      CHECK(f.initialize(d.access())==MmioStatus::Ok); // Attach/detach/re-attach lifecycle.
      CHECK(f.shutdown()==MmioStatus::Ok);
    }
    for (unsigned mode=0;mode<5;++mode) {
      ForceWake f; Device d;
      if (mode==0) d.gmd=0;
      if (mode==1) d.gmd=(12U<<22)|(71U<<14);
      if (mode==2) d.gmd=(20U<<22)|(70U<<14);
      if (mode==3) d.allOnes=true;
      if (mode==4) d.failRead=true;
      CHECK(f.initialize(d.access())==(mode<3?MmioStatus::UnsupportedIp:MmioStatus::IoFailure));
      CHECK(d.writes==0 && f.canDetach());
    }
    { ForceWake f; Device d; CHECK(f.initialize(d.access())==MmioStatus::Ok);
      d.ack[0]=1;
      CHECK(f.acquire(WakeDomain::Gt)==MmioStatus::Busy && d.writes==0);
      CHECK(f.canDetach());
    }
    for (unsigned stalled=0;stalled<2;++stalled) {
      ForceWake f; Device d; CHECK(f.initialize(d.access())==MmioStatus::Ok);
      d.noAckOn=true; d.stalledClock=stalled!=0;
      CHECK(f.acquire(WakeDomain::Gt)==MmioStatus::Timeout);
      CHECK(d.delays==1000 && d.writes==2 && f.canDetach());
      d.noAckOn=false;
      CHECK(f.acquire(WakeDomain::Gt)==MmioStatus::Ok);
      CHECK(f.release(WakeDomain::Gt)==MmioStatus::Ok);
    }
    { ForceWake f; Device d; CHECK(f.initialize(d.access())==MmioStatus::Ok);
      d.noAckOn=true; d.time=500; d.reverseClock=true;
      CHECK(f.acquire(WakeDomain::Gt)==MmioStatus::ClockRegression);
      CHECK(d.delays==1 && f.canDetach());
    }
    { ForceWake f; Device d; CHECK(f.initialize(d.access())==MmioStatus::Ok);
      d.failWrite=true;
      CHECK(f.acquire(WakeDomain::Gt)==MmioStatus::IoFailure);
      CHECK(!f.canDetach() && f.shutdown()==MmioStatus::Busy);
      CHECK(f.acquire(WakeDomain::Gt)==MmioStatus::Faulted);
    }
    for (unsigned mode=0;mode<3;++mode) {
      ForceWake f; Device d; CHECK(f.initialize(d.access())==MmioStatus::Ok);
      CHECK(f.acquire(WakeDomain::Gt)==MmioStatus::Ok);
      if (mode==0) d.noAckOff=true;
      if (mode==1) d.failWrite=true;
      if (mode==2) d.allOnes=true;
      CHECK(f.release(WakeDomain::Gt)==(mode==0?MmioStatus::Timeout:MmioStatus::IoFailure));
      CHECK(!f.canDetach() && !f.held(WakeDomain::Gt));
      CHECK(f.release(WakeDomain::Gt)==MmioStatus::Faulted);
    }
    std::printf("PASS %u assertions; actual ForceWake code, simulated registers/time, hardware not executed\n",checks);
}
