#include "../Mellow/XeContextExecution.hpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <vector>
static size_t checks;
#define CHECK(x) do{++checks;if(!(x)){std::fprintf(stderr,"FAIL %d: %s\n",__LINE__,#x);std::exit(1);}}while(0)
using namespace XeContext;
struct Fixture {
    XeMemory::VirtualMemory vm;XeMemory::Allocation slots[8];XeMemory::Handle handles[6];
    uint64_t dma[6]={0x100000,0x101000,0x102000,0x103000,0x104000,0x105000};
    XeGuC::Transport transport;XeGuC::Descriptor h {},g {};uint32_t hw[1024] {},gw[2048] {};
    XeFence::Timeline fence;alignas(8) volatile uint64_t completion=0;
    uint32_t ring[1024] {},tail=0;uint8_t heaps[4][4096] {};
    bool admit=true,stopped=true,notifyOk=true,stageOk=true,syncOk=true,retained=false;
    unsigned pins=0,binds=0,retains=0,releases=0,stages=0,fenceRetains=0,fenceReleases=0;
    XeDispatch::Policy policy{112,3,false,false};
    LiveContext context(){return {51,7,19,5,0x200000,0x210000,4096,ring,&tail,0x200119,false};}
    static bool yes(void *){return true;}
    ExecutionBackend backend(){
        ExecutionBackend b;b.opaque=this;
        b.admitted=[](void *p,const LiveContext &c,const XeDispatch::Policy &){return static_cast<Fixture *>(p)->admit && c.epoch==7 && c.owner==51;};
        b.freshStopped=[](void *p,const LiveContext &){auto f=static_cast<Fixture *>(p);return f->stopped && f->tail==0;};
        b.retainContext=[](void *p,const LiveContext &){auto f=static_cast<Fixture *>(p);++f->retains;f->retained=true;return true;};
        b.releaseContext=[](void *p,const LiveContext &){auto f=static_cast<Fixture *>(p);++f->releases;f->retained=false;return true;};
        b.stageHeaps=[](void *p,const LiveContext &,const XeMemory::Handle (&)[6],const XeDispatch::Prepared &s){auto f=static_cast<Fixture *>(p);++f->stages;
            if(!f->stageOk)return false;
            CHECK(f->retained);
            for(unsigned i=0;i<6;++i)CHECK(f->slots[i].activeUses==1);
            std::memcpy(f->heaps[0],s.isa,4096);std::memcpy(f->heaps[1],s.indirect,4096);std::memcpy(f->heaps[2],s.surface,4096);std::memcpy(f->heaps[3],s.batch,4096);return true;};
        b.synchronizeContext=[](void *p,const LiveContext &){auto f=static_cast<Fixture *>(p);CHECK(f->tail==80 && f->fence.lastPublished()==1);return f->syncOk;};
        b.quiesced=[](void *p,const LiveContext &){return static_cast<Fixture *>(p)->stopped;};return b;
    }
    Fixture(){
        using S=XeMemory::Status;XeMemory::Backend b;b.context=this;b.verifiedPatIndices=1U<<3;
        b.pin=[](void *p,uint64_t,uint64_t,XeMemory::Pin &pin){auto f=static_cast<Fixture *>(p);auto page=&f->dma[f->pins++];pin={page,page,1};return S::Ok;};
        b.unpin=[](void *,XeMemory::Pin &){return S::Ok;};
        b.bind=[](void *p,uint64_t,const XeMemory::Pin &,uint8_t,bool){++static_cast<Fixture *>(p)->binds;return S::Ok;};
        b.unbind=[](void *,uint64_t,uint64_t){return S::Ok;};
        CHECK(vm.initialize(slots,8,0x10000,0x100000,b)==S::Ok);
        for(auto &handle:handles){CHECK(vm.reserve(51,4096,4096,handle)==S::Ok);CHECK(vm.pin(51,handle)==S::Ok);CHECK(vm.bind(51,handle,3,true)==S::Ok);}
        XeGuC::Ops op;op.opaque=this;op.acquire=yes;op.release=yes;
        op.admitted=[](void *p,uint64_t e){return e==7 && static_cast<Fixture *>(p)->admit;};
        op.authorizeAction=[](void *p,uint64_t,const XeGuC::Action &a){auto f=static_cast<Fixture *>(p);CHECK(f->retained && f->tail==80);
            if(a.words[0]==0x1001){CHECK(f->fence.lastPublished()==1);f->stopped=false;}return true;};
        op.notify=[](void *p){return static_cast<Fixture *>(p)->notifyOk;};
        MellowXe::FirmwareInfo fw;fw.release={70,53,0};fw.submission={1,26,0};
        CHECK(transport.attach({&h,hw,1024,0x400000,0x410000},{&g,gw,2048,0x400040,0x420000},op,7,fw)==XeGuC::Status::Ok);
        XeFence::Ops fo;fo.opaque=this;
        fo.valid=[](void *p,const XeFence::Slot &s){return static_cast<Fixture *>(p)->admit && s.owner==51 && s.epoch==7;};
        fo.stopped=[](void *p,const XeFence::Slot &){return static_cast<Fixture *>(p)->stopped;};
        fo.retain=[](void *p,const XeFence::Slot &){++static_cast<Fixture *>(p)->fenceRetains;return true;};
        fo.release=[](void *p,const XeFence::Slot &){++static_cast<Fixture *>(p)->fenceReleases;};
        CHECK(fence.bind({&completion,0x220000,8,51,5,7,0,0},fo)==XeFence::Status::Ok);
    }
    void enableAck(uint64_t now=2){gw[0]=3;gw[1]=0x90001002;gw[2]=5;gw[3]=1;g.tail=4;XeGuC::Message m;CHECK(transport.receive(7,now,m)==XeGuC::Status::Ok);}
};
int main(int argc,char **argv){
    const char *path=argc>1?argv[1]:"compiler-evidence/mellow_evidence_mtl.bin";
    std::ifstream file(path,std::ios::binary);CHECK(bool(file));std::vector<uint8_t> data((std::istreambuf_iterator<char>(file)),{});
    XeZebin::Image image;CHECK(image.parse(data.data(),data.size())==XeZebin::Error::None);
    for(unsigned mode=0;mode<6;++mode){
        auto f=new Fixture;auto execution=new EvidenceExecution(f->vm,f->transport,f->fence,f->backend());
        if(mode==1)f->admit=false;
        if(mode==2)f->stageOk=false;
        if(mode==3)f->syncOk=false;
        if(mode==4)f->notifyOk=false;
        auto result=execution->begin(image,f->context(),f->handles,f->policy,1234,32,false,1,10);
        if(mode==0 || mode==5){
            CHECK(result==ExecutionStatus::Pending && execution->state()==ExecutionState::Enabling);
            CHECK(f->hw[1]==0x20004502 && f->hw[3]==5 && f->hw[11]==0x200119);
            CHECK(f->hw[14]==0x20001001 && f->hw[15]==5 && f->hw[16]==1 && f->h.tail==17);
            CHECK(execution->retainedVmUses()==6 && execution->contextHeld());
            CHECK(execution->close()==ExecutionStatus::Busy);
            f->enableAck();CHECK(execution->poll(2)==ExecutionStatus::Pending);
            CHECK(execution->state()==ExecutionState::Running);
            CHECK(execution->poll(10)==ExecutionStatus::Timeout && execution->retainedVmUses()==6);
            CHECK(execution->close()==ExecutionStatus::Busy);
            CHECK(f->vm.retire(51,f->handles[5])==XeMemory::Status::Ok);
            CHECK(f->vm.reclaim(51,f->handles[5])==XeMemory::Status::Busy);
            if(mode==0){
                // Simulated GPU write, never a production completion callback.
                f->completion=1;CHECK(execution->poll(11)==ExecutionStatus::Ok);
                CHECK(execution->state()==ExecutionState::Completed && execution->retainedVmUses()==0);
                CHECK(f->retained && f->fence.held());
            }else {f->completion=1ULL<<32;CHECK(execution->poll(11)==ExecutionStatus::Quarantined);CHECK(execution->retainedVmUses()==6);}
        }else CHECK(result==ExecutionStatus::Unavailable || result==ExecutionStatus::Quarantined);
        if(mode==1)CHECK(f->retains==0 && f->stages==0 && f->tail==0 && f->h.tail==0);
        else CHECK(execution->contextHeld());
        f->admit=true;f->stopped=true;CHECK(execution->close()==ExecutionStatus::Ok);
        CHECK(execution->retainedVmUses()==0 && !execution->contextHeld());
        CHECK(execution->begin(image,f->context(),f->handles,f->policy,1,1,false,12,20)==ExecutionStatus::Busy);
        delete execution;delete f;
    }
    std::printf("XeContextExecution: PASS %zu checks; real VM+GuC+fence code, hardware callbacks simulated\n",checks);
}
