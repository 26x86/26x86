#pragma once
#include "XeInterrupt.hpp"
#include "XeGuCTransport.hpp"
#include "XeFence.hpp"

namespace XeInterrupt {
// Serialized workloop callbacks. A transport event is delivered from a real
// decoded G2H message. A fence event comes only from coherent slot observation.
struct DispatchOps {
    void *opaque {};
    uint64_t (*nowMicros)(void *) {};
    bool (*message)(void *,uint64_t,const XeGuC::Message &) {};
    bool (*fence)(void *,const XeFence::Observation &) {};
};
class Dispatcher {
public:
    Dispatcher(XeGuC::Transport &transport,XeFence::Timeline &fence,
               DispatchOps ops,uint64_t epoch,uint8_t engineClass,uint8_t instance=0)
        : transport_(transport),fence_(fence),ops_(ops),epoch_(epoch),class_(engineClass),instance_(instance) {}
    Handling handle(uint64_t epoch,const Identity &id) {
        if (epoch!=epoch_ || !ops_.nowMicros || !ops_.message || !ops_.fence) return Handling::Failed;
        if (id.engineClass==4 && id.instance==0) {
            if (!id.vector || (id.vector & ~gucToHost)) return Handling::Failed;
            for (unsigned count=0;count<64;++count) {
                XeGuC::Message message {};
                const auto status=transport_.receive(epoch,ops_.nowMicros(ops_.opaque),message);
                if (status==XeGuC::Status::Empty) return Handling::Drained;
                if (status!=XeGuC::Status::Ok || !ops_.message(ops_.opaque,epoch,message)) return Handling::Failed;
            }
            return Handling::More; // source remains masked; next workloop drains again
        }
        if (id.engineClass!=class_ || id.instance!=instance_ || !id.vector ||
            (id.vector & ~(engineUser|engineFlush))) return Handling::Failed;
        XeFence::Observation observation {};
        if (fence_.observe(epoch,observation)!=XeFence::Status::Ok ||
            observation.engineClass!=class_ || observation.instance!=instance_) return Handling::Failed;
        return ops_.fence(ops_.opaque,observation) ? Handling::Drained : Handling::Failed;
    }
private:
    XeGuC::Transport &transport_;
    XeFence::Timeline &fence_;
    DispatchOps ops_ {};
    uint64_t epoch_ {}; uint8_t class_ {}, instance_ {};
};
}
