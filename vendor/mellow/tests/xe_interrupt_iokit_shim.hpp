// Explicit host-only OS boundary emulator; never part of the Darwin target.
#pragma once
#include "XeMmioAccess.hpp"
#include <map>
#include <stdint.h>
using IOReturn=int;
constexpr int kIOReturnSuccess=0,kIODirectionInOut=3,kIOPCIConfigVendorID=0,kIOPCIConfigDeviceID=2;
class OSObject {
public:
    unsigned refs=1;
    virtual ~OSObject()=default;
    virtual void free(){delete this;}
    void retain(){++refs;}
    void release(){if(!--refs)free();}
};
#define OSDeclareDefaultStructors(cls) public: cls()=default; ~cls() override=default;
#define OSDefineMetaClassAndStructors(cls,parent)
class IOInterruptEventSource:public OSObject {
public:
    using Action=void(*)(OSObject*,IOInterruptEventSource*,int);
    bool enabled=false;
    void enable(){enabled=true;}
    void disable(){enabled=false;}
};
class IOPCIDevice:public OSObject {
public:
    int getInterruptType(int index,int *type){*type=0;return index==0?0:-1;}
    int getBusNumber(){return 0;}int getDeviceNumber(){return 2;}int getFunctionNumber(){return 0;}
    uint16_t configRead16(int r){return r==kIOPCIConfigVendorID?0x8086:0x7d41;}
};
class IOFilterInterruptEventSource:public IOInterruptEventSource {
public:
    using Filter=bool(*)(OSObject*,IOFilterInterruptEventSource*);
    inline static bool failFactory=false;
    inline static unsigned alive=0;
    OSObject *owner=nullptr;Action action=nullptr;Filter filter=nullptr;
    unsigned signals=0;
    ~IOFilterInterruptEventSource() override{--alive;}
    static IOFilterInterruptEventSource *filterInterruptEventSource(OSObject *o,Action a,Filter f,IOPCIDevice *,int){
        if(failFactory)return nullptr;
        auto *s=new IOFilterInterruptEventSource;++alive;s->owner=o;s->action=a;s->filter=f;return s;
    }
    void signalInterrupt(){++signals;}
};
class IOWorkLoop:public OSObject {
public:
    bool gate=true,failAdd=false;unsigned adds=0,removes=0;
    bool inGate(){return gate;}
    IOReturn addEventSource(IOInterruptEventSource *){if(failAdd)return -1;++adds;return 0;}
    void removeEventSource(IOInterruptEventSource *){++removes;}
};
namespace MellowXe {
class MockWake {
public: bool awake=true;GraphicsIp g{12,70,0,0};
    bool held(WakeDomain)const{return awake;}const GraphicsIp &ip()const{return g;}
};
class IOKitMmio {
public:
    std::map<uint32_t,uint32_t> registers;
    bool failStop=false,ignoreStop=false;unsigned accesses=0;MockWake wake;
    MockWake &forceWake(){return wake;}
    static bool read(void *p,uint32_t r,uint32_t &v){auto &s=*static_cast<IOKitMmio*>(p);++s.accesses;v=s.registers[r];return true;}
    static bool write(void *p,uint32_t r,uint32_t v){auto &s=*static_cast<IOKitMmio*>(p);++s.accesses;if(s.failStop && r==0x190008 && !v)return false;if(s.ignoreStop && r==0x190008 && !v)return true;s.registers[r]=v;return true;}
    static uint64_t now(void *){return 0;}
    MmioAccess access(){return {this,read,write,now,nullptr};}
};
}
class IOMemoryMap:public OSObject {
public:
    uintptr_t address;uint64_t bytes;
    IOMemoryMap(uintptr_t a,uint64_t b):address(a),bytes(b){}
    uintptr_t getVirtualAddress(){return address;}uint64_t getLength(){return bytes;}
};
class IOMemoryDescriptor:public OSObject {
public:
    alignas(8) uint64_t words[8]{};unsigned prepares=0,completes=0;
    bool failPrepare=false,failMap=false,failComplete=false;
    uint64_t getLength(){return sizeof(words);}
    int prepare(int){if(failPrepare)return -1;++prepares;return 0;}
    int complete(int){if(failComplete)return -1;++completes;return 0;}
    IOMemoryMap *map(){return failMap?nullptr:new IOMemoryMap(reinterpret_cast<uintptr_t>(words),sizeof(words));}
};
