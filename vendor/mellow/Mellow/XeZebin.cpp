// Local 7D41 research implementation, 2026. See LICENSE and NOTICE.
#include "XeZebin.hpp"

namespace XeZebin {
namespace {
uint16_t u16(const uint8_t *p) { return uint16_t(p[0]) | uint16_t(p[1])<<8; }
uint32_t u32(const uint8_t *p) { return uint32_t(u16(p)) | uint32_t(u16(p+2))<<16; }
uint64_t u64(const uint8_t *p) { return uint64_t(u32(p)) | uint64_t(u32(p+4))<<32; }
void put(uint8_t *p,uint64_t v,unsigned bytes) { for(unsigned i=0;i<bytes;++i) p[i]=uint8_t(v>>(i*8)); }
bool range(uint64_t start,uint64_t length,uint64_t limit) { return start<=limit && length<=limit-start; }
bool power2(uint64_t n) { return n && !(n&(n-1)); }
bool equal(const char *a,const char *b) { if(!a || !b)return false;while(*a && *a==*b){++a;++b;}return *a==*b; }
bool prefix(const char *a,const char *b) { if(!a)return false;while(*b)if(*a++!=*b++)return false;return true; }
bool overlap(uint64_t a,uint64_t an,uint64_t b,uint64_t bn) { return an && bn && a<b+bn && b<a+an; }
struct Slice {const char *p;size_t n;};
bool eq(Slice a,const char *b) {size_t i=0;while(i<a.n && b[i] && a.p[i]==b[i])++i;return i==a.n && !b[i];}
Slice trim(Slice a) {while(a.n && a.p[0]==' '){++a.p;--a.n;}while(a.n && (a.p[a.n-1]==' ' || a.p[a.n-1]=='\r'))--a.n;return a;}
bool number(Slice a,uint32_t &out) {if(!a.n)return false;uint32_t n=0;for(size_t i=0;i<a.n;++i){if(a.p[i]<'0'||a.p[i]>'9')return false;uint32_t digit=a.p[i]-'0';if(n>(UINT32_MAX-digit)/10)return false;n=n*10+digit;}out=n;return true;}
bool boolean(Slice a,bool &out) {if(eq(a,"true")){out=true;return true;}if(eq(a,"false")){out=false;return true;}return false;}
bool ptrRange(const void *p,size_t n) {return p && n && reinterpret_cast<uintptr_t>(p)<=UINTPTR_MAX-(n-1);}
}
const char *Image::string(size_t section,uint64_t offset) const {
    if(section>=sectionCount_)return nullptr;
    const auto &s=sections_[section];
    if(s.type!=3 || offset>=s.bytes)return nullptr;
    const char *p=reinterpret_cast<const char *>(data_+s.offset+offset);
    for(uint64_t i=offset;i<s.bytes;++i)if(data_[s.offset+i]==0)return p;
    return nullptr;
}
bool Image::name(size_t section,const char *wanted) const {return section<sectionCount_ && equal(string(stringSection_,sections_[section].name),wanted);}
size_t Image::segmentForSection(uint32_t section) const {for(size_t i=0;i<segmentCount_;++i)if(segments_[i].section==section)return i;return MaxSegments;}

Error Image::readMetadata(size_t section) {
    const auto &s=sections_[section];if(s.bytes>16384)return Error::Capacity;
    enum class Area {Root,Kernel,User,Environment,Payload,PerThread,Misc};Area area=Area::Root;
    Metadata m {};Argument arg {};uint32_t fields=0,environment=0,perThread=0,root=0;bool haveArg=false,haveKernel=false,walk=false;
    auto finishArg=[&]() {
        if(!haveArg)return true;
        const uint32_t expected=arg.type==ArgType::Pointer?127U:arg.type==ArgType::Value?15U:7U;
        if(fields!=expected || m.argumentCount>=8)return false;
        m.args[m.argumentCount++]=arg;haveArg=false;return true;
    };
    size_t at=0;
    while(at<s.bytes) {
        size_t end=at;while(end<s.bytes && data_[s.offset+end]!='\n')++end;
        const char *line=reinterpret_cast<const char *>(data_+s.offset+at);size_t length=end-at;at=end+(end<s.bytes);
        for(size_t i=0;i<length;++i)if((uint8_t(line[i])<32 && line[i]!='\r') || uint8_t(line[i])>126)return Error::Metadata;
        size_t indent=0;while(indent<length && line[indent]==' ')++indent;
        Slice body=trim({line+indent,length-indent});if(!body.n)continue;
        if(!indent && (eq(body,"---") || eq(body,"...")))continue;
        bool list=body.n>=2 && body.p[0]=='-' && body.p[1]==' ';
        if(list)body=trim({body.p+2,body.n-2});
        size_t colon=0;while(colon<body.n && body.p[colon]!=':')++colon;
        if(colon==body.n)return Error::Metadata;
        Slice key=trim({body.p,colon}),value=trim({body.p+colon+1,body.n-colon-1});
        if(!indent) {
            if(list || !finishArg())return Error::Metadata;
            if(eq(key,"version")) {
                if(root&1 || !eq(value,"'1.73'"))return Error::Metadata;
                root|=1;m.versionMajor=1;m.versionMinor=73;
            } else if(eq(key,"kernels") && !value.n) {if(root&2)return Error::Duplicate;root|=2;area=Area::Kernel;}
            else if(eq(key,"kernels_misc_info") && !value.n) {if(root&4)return Error::Duplicate;root|=4;area=Area::Misc;}
            else return Error::Unsupported;
            continue;
        }
        if(area==Area::Misc)continue; // Names/types for reflection do not control dispatch.
        if(indent==2 && list && eq(key,"name")) {
            if(haveKernel || !eq(value,"mellow_evidence"))return Error::Unsupported;
            haveKernel=true;for(size_t i=0;i<value.n;++i)m.name[i]=value.p[i];area=Area::Kernel;continue;
        }
        if(!haveKernel)return Error::Metadata;
        if(indent==4 && !list && !value.n) {
            if(!finishArg())return Error::Metadata;
            if(eq(key,"user_attributes"))area=Area::User;
            else if(eq(key,"execution_env"))area=Area::Environment;
            else if(eq(key,"payload_arguments"))area=Area::Payload;
            else if(eq(key,"per_thread_payload_arguments"))area=Area::PerThread;
            else return Error::Unsupported;
            continue;
        }
        if(area==Area::User && indent==6 && !list && eq(key,"intel_reqd_workgroup_walk_order")) {
            if(walk)return Error::Duplicate;
            char compact[16] {};size_t n=0;
            for(size_t i=0;i<value.n;++i)if(value.p[i]!=' '){if(n==15)return Error::Metadata;compact[n++]=value.p[i];}
            if(!equal(compact,"[0,1,2]"))return Error::Unsupported;
            walk=true;continue;
        }
        if(area==Area::Environment && indent==6 && !list) {
            uint32_t bit=0;bool valid=false;
            if(eq(key,"disable_mid_thread_preemption")){bit=1;valid=boolean(value,m.disableMidThreadPreemption);}
            else if(eq(key,"grf_count")){bit=2;valid=number(value,m.grf);}
            else if(eq(key,"has_no_stateless_write")){bit=4;valid=boolean(value,m.noStatelessWrites);}
            else if(eq(key,"inline_data_payload_size")){bit=8;valid=number(value,m.inlineBytes);}
            else if(eq(key,"offset_to_skip_per_thread_data_load")){bit=16;valid=number(value,m.skipPerThreadLoad);}
            else if(eq(key,"simd_size")){bit=32;valid=number(value,m.simd);}
            else if(eq(key,"subgroup_independent_forward_progress")){bit=64;valid=boolean(value,m.independentProgress);}
            else if(eq(key,"eu_thread_count")){bit=128;valid=number(value,m.euThreads);}
            else return Error::Unsupported;
            if(!valid || (environment&bit))return Error::Metadata;
            environment|=bit;continue;
        }
        if(area==Area::Payload) {
            if(indent==6 && list && eq(key,"arg_type")) {
                if(!finishArg())return Error::Metadata;
                arg={};fields=1;haveArg=true;
                if(eq(value,"global_id_offset"))arg.type=ArgType::GlobalOffset;
                else if(eq(value,"enqueued_local_size"))arg.type=ArgType::LocalSize;
                else if(eq(value,"arg_bypointer"))arg.type=ArgType::Pointer;
                else if(eq(value,"arg_byvalue"))arg.type=ArgType::Value;
                else return Error::Unsupported;
                continue;
            }
            if(indent!=8 || list || !haveArg)return Error::Metadata;
            uint32_t bit=0;bool valid=false;
            if(eq(key,"offset")){bit=2;valid=number(value,arg.offset);}
            else if(eq(key,"size")){bit=4;valid=number(value,arg.size);}
            else if(eq(key,"arg_index")){bit=8;valid=number(value,arg.index);}
            else if(eq(key,"addrmode")){bit=16;valid=eq(value,"stateless")||eq(value,"bindless");arg.mode=eq(value,"stateless")?AddressMode::Stateless:AddressMode::Bindless;}
            else if(eq(key,"addrspace")){bit=32;valid=eq(value,"global");}
            else if(eq(key,"access_type")){bit=64;valid=eq(value,"readonly")||eq(value,"readwrite");arg.writable=eq(value,"readwrite");}
            else return Error::Unsupported;
            if(!valid || (fields&bit))return Error::Metadata;
            fields|=bit;continue;
        }
        if(area==Area::PerThread) {
            if(indent==6 && list && eq(key,"arg_type") && eq(value,"local_id") && !perThread){perThread=1;continue;}
            if(indent!=8 || list || !(perThread&1))return Error::Metadata;
            uint32_t n=0;if(!number(value,n))return Error::Metadata;
            if(eq(key,"offset") && !(perThread&2) && !n)perThread|=2;
            else if(eq(key,"size") && !(perThread&4)){perThread|=4;m.perThreadBytes=n;}
            else return Error::Metadata;
            continue;
        }
        return Error::Metadata;
    }
    if(!finishArg() || (root&3)!=3 || !haveKernel || !walk || environment!=255 || perThread!=7 || m.argumentCount!=8)return Error::Metadata;
    // Explicitly bounded execution profile; a new compiler schema needs review.
    if(m.simd!=32 || m.grf!=128 || m.inlineBytes!=32 || m.perThreadBytes!=192 || m.euThreads!=8 ||
       !m.disableMidThreadPreemption || !m.noStatelessWrites || !m.independentProgress)return Error::Unsupported;
    uint32_t seen=0,largest=0;
    for(size_t i=0;i<m.argumentCount;++i) {
        const auto &a=m.args[i];uint32_t bit=0;
        if(!a.size || !range(a.offset,a.size,MaxPayload))return Error::Metadata;
        if(a.type==ArgType::GlobalOffset || a.type==ArgType::LocalSize){if(a.size!=12)return Error::Metadata;bit=a.type==ArgType::GlobalOffset?1:2;}
        else if(a.type==ArgType::Value){if(a.size!=4 || a.index<2 || a.index>3)return Error::Metadata;bit=1U<<(a.index+2);}
        else {if(a.index>1 || a.writable!=(a.index==1))return Error::Metadata;
            if(a.mode==AddressMode::Stateless && a.size==8)bit=1U<<(a.index+2);
            else if(a.mode==AddressMode::Bindless && a.size==4)bit=1U<<(a.index+6);else return Error::Metadata;}
        if(seen&bit)return Error::Duplicate;
        seen|=bit;
        for(size_t j=0;j<i;++j)if(overlap(a.offset,a.size,m.args[j].offset,m.args[j].size))return Error::Metadata;
        if(a.offset+a.size>largest)largest=a.offset+a.size;
    }
    if(seen!=255)return Error::Metadata;
    m.crossThreadBytes=(largest+31)&~31U;if(m.crossThreadBytes>MaxPayload || m.inlineBytes>m.crossThreadBytes)return Error::Metadata;
    metadata_=m;return Error::None;
}
Error Image::readCompatibility(size_t section) {
    const auto &s=sections_[section];uint64_t at=0;uint32_t seen=0;
    while(at<s.bytes) {
        if(!range(at,12,s.bytes))return Error::Bounds;
        const uint8_t *p=data_+s.offset+at;
        const uint64_t names=u32(p),desc=u32(p+4);uint32_t type=u32(p+8);
        const uint64_t namePadded=(names+3)&~3ULL,descPadded=(desc+3)&~3ULL;
        if(names!=8 || !range(at+12,namePadded+descPadded,s.bytes))return Error::Bounds;
        if(!equal(reinterpret_cast<const char *>(p+12),"IntelGT") || p[19])return Error::Metadata;
        const uint8_t *value=p+12+namePadded;
        if(type==0 || type>8 || (seen&(1U<<type)))return Error::Unsupported;
        seen|=1U<<type;
        if(type==4){if(desc!=5 || value[0]!='1'||value[1]!='.'||value[2]!='7'||value[3]!='3'||value[4])return Error::Metadata;}
        else {if(desc!=4)return Error::Metadata;const uint32_t v=u32(value);
            if(type==1)compatibility_.productFamily=v;
            if(type==2)compatibility_.gfxCore=v;
            if(type==3)compatibility_.targetFlags=v;
            if(type==6)compatibility_.productConfig=v;}
        at+=12+namePadded+descPadded;
    }
    return (seen&94U)==94U && compatibility_.productFamily && compatibility_.gfxCore && compatibility_.productConfig ? Error::None:Error::Metadata;
}
Error Image::parse(const uint8_t *data,size_t bytes) {
    valid_=false;data_=nullptr;segmentCount_=0;metadata_={};compatibility_={};
    if(!ptrRange(data,bytes) || bytes<64)return Error::InvalidElf;
    if(data[0]!=127 || data[1]!='E'||data[2]!='L'||data[3]!='F'||data[4]!=2||data[5]!=1||data[6]!=1 ||
       u16(data+16)!=1 || u16(data+18)!=205 || u32(data+20)!=1 || u16(data+52)!=64 || u16(data+58)!=64 ||
       u64(data+24) || u64(data+32) || u16(data+56))return Error::Unsupported;
    const uint64_t table=u64(data+40);sectionCount_=u16(data+60);stringSection_=u16(data+62);
    if(!sectionCount_ || sectionCount_>MaxSections)return Error::Capacity;
    if(stringSection_>=sectionCount_ || table<64 || !range(table,sectionCount_*64,bytes))return Error::Bounds;
    data_=data;bytes_=bytes;symbolSection_=MaxSections;
    for(size_t i=0;i<sectionCount_;++i) {
        const uint8_t *p=data+table+i*64;
        sections_[i]={u32(p),u32(p+4),u32(p+40),u32(p+44),u64(p+8),u64(p+24),u64(p+32),u64(p+48),u64(p+56)};
        const auto &s=sections_[i];
        if(s.align && !power2(s.align))return Error::InvalidElf;
        if(s.type!=8 && (!range(s.offset,s.bytes,bytes) || overlap(s.offset,s.bytes,0,64) || overlap(s.offset,s.bytes,table,sectionCount_*64)))return Error::Bounds;
        for(size_t j=0;j<i;++j)if(s.type!=8 && sections_[j].type!=8 && overlap(s.offset,s.bytes,sections_[j].offset,sections_[j].bytes))return Error::InvalidElf;
    }
    if(sections_[0].type || sections_[0].bytes || sections_[stringSection_].type!=3)return Error::InvalidElf;
    size_t meta=MaxSections,compat=MaxSections;bool haveText=false;
    for(size_t i=1;i<sectionCount_;++i) {
        const auto &s=sections_[i];const char *n=string(stringSection_,s.name);if(!n)return Error::Bounds;
        for(size_t j=1;j<i;++j)if(equal(n,string(stringSection_,sections_[j].name)))return Error::Duplicate;
        bool text=prefix(n,".text."),bss=name(i,".bss.global")||name(i,".bss.const");
        bool load=text||bss||name(i,".data.global")||name(i,".data.const")||name(i,".data.global_const")||name(i,".data.const.string");
        if(load) {
            if((bss?s.type!=8:s.type!=1) || !s.bytes || s.bytes>64*1024*1024 || s.align>65536)return Error::Unsupported;
            if(segmentCount_==MaxSegments)return Error::Capacity;
            if(text){if(haveText || !name(i,".text.mellow_evidence") || !(s.flags&4))return Error::Unsupported;haveText=true;textSegment_=segmentCount_;}
            segments_[segmentCount_++]={static_cast<uint16_t>(i),s.offset,s.bytes,s.align?s.align:1,text,bss};
        } else if(s.flags&2)return Error::Unsupported;
        if(name(i,".ze_info")){if(s.type!=0xff000011)return Error::InvalidElf;meta=i;}
        if(name(i,".note.intelgt.compat")){if(s.type!=7)return Error::InvalidElf;compat=i;}
        if(s.type==2){if(symbolSection_!=MaxSections || !name(i,".symtab") || s.entry!=24 || !s.bytes || s.bytes%24 || s.bytes/24>256 || s.link>=sectionCount_ || sections_[s.link].type!=3)return Error::InvalidElf;symbolSection_=i;}
        if(s.type==4 || s.type==9){const uint64_t expected=s.type==4?24:16;if(s.entry!=expected || s.bytes%expected || s.link>=sectionCount_ || s.info>=sectionCount_)return Error::InvalidElf;}
    }
    if(!haveText || meta==MaxSections || compat==MaxSections || symbolSection_==MaxSections)return Error::InvalidElf;
    const auto &sym=sections_[symbolSection_];
    for(uint64_t at=0;at<sym.bytes;at+=24){const uint8_t *p=data_+sym.offset+at;if(!string(sym.link,u32(p)) || (u16(p+6)>=sectionCount_ && u16(p+6)!=0xfff1))return Error::InvalidElf;}
    Error error=readMetadata(meta);if(error!=Error::None)return error;
    error=readCompatibility(compat);if(error!=Error::None)return error;
    if(metadata_.skipPerThreadLoad>=segments_[textSegment_].bytes || (metadata_.skipPerThreadLoad&15))return Error::Metadata;
    bool kernelSymbol=false;
    for(uint64_t at=0;at<sym.bytes;at+=24) {
        const uint8_t *p=data_+sym.offset+at;
        if(!equal(string(sym.link,u32(p)),metadata_.name))continue;
        if(kernelSymbol || (p[4]&15)!=2 || u16(p+6)!=segments_[textSegment_].section || u64(p+8) ||
           !u64(p+16) || u64(p+16)>segments_[textSegment_].bytes)return Error::Unsupported;
        kernelSymbol=true;
    }
    if(!kernelSymbol)return Error::InvalidElf;
    valid_=true;return Error::None;
}

Error Image::stage(const Destination *dest,size_t count,StagedImage &out) const {
    if(!valid_ || !dest || count!=segmentCount_)return Error::InvalidBinding;
    struct Patch {size_t segment;uint64_t offset,value;unsigned width;};Patch patches[MaxRelocations] {};size_t patchCount=0;
    for(size_t i=0;i<count;++i) {
        const auto &s=segments_[i];const auto &d=dest[i];
        if(d.capacity<s.bytes || !ptrRange(d.cpu,d.capacity) || !d.gpuAddress || (d.gpuAddress&(XeMemory::PageSize-1)) ||
           d.gpuAddress%s.alignment || !range(d.gpuAddress,s.bytes,XeMemory::VaLimit))return Error::InvalidBinding;
        if(overlap(reinterpret_cast<uintptr_t>(d.cpu),s.bytes,reinterpret_cast<uintptr_t>(data_),bytes_))return Error::InvalidBinding;
        for(size_t j=0;j<i;++j)if(overlap(d.gpuAddress,s.bytes,dest[j].gpuAddress,segments_[j].bytes) ||
            overlap(reinterpret_cast<uintptr_t>(d.cpu),s.bytes,reinterpret_cast<uintptr_t>(dest[j].cpu),segments_[j].bytes))return Error::InvalidBinding;
    }
    const auto &sym=sections_[symbolSection_];
    for(size_t i=1;i<sectionCount_;++i) {
        const auto &r=sections_[i];if(r.type!=4 && r.type!=9)continue;
        const size_t target=segmentForSection(r.info);
        if(target==MaxSegments || r.link!=symbolSection_)return Error::Unsupported;
        for(uint64_t at=0;at<r.bytes;at+=r.entry) {
            const uint8_t *p=data_+r.offset+at;uint64_t offset=u64(p),info=u64(p+8);uint32_t type=uint32_t(info),symbol=uint32_t(info>>32);
            if(type==0)continue;
            if(type>4 || symbol>=sym.bytes/24)return Error::Relocation;
            const unsigned width=type==1?8:4;
            if(!range(offset,width,segments_[target].bytes) || patchCount==MaxRelocations)return Error::Relocation;
            uint64_t value=0;bool special=false;const uint8_t *entry=data_+sym.offset+uint64_t(symbol)*24;uint16_t source=u16(entry+6);
            const char *symbolName=string(sym.link,u32(entry));
            if(source==0 && equal(symbolName,"__INTEL_PATCH_CROSS_THREAD_OFFSET_OFF_R0")) {
                // Intel linker.h identifies this as the implicit-argument prefix,
                // NOT the per-thread offset. This profile excludes stack calls,
                // debugger mode and require_implicit_arg_buffer, so prefix=0.
                if(!segments_[target].executable || type!=2 || u32(data_+segments_[target].fileOffset+offset)!=0)return Error::Relocation;
                value=0;special=true;
            } else if(type==4 || (source==0 && equal(symbolName,"__INTEL_PER_THREAD_OFF"))) {
                if(!segments_[target].executable || type==1 || type==3)return Error::Relocation;
                value=metadata_.crossThreadBytes-metadata_.inlineBytes;special=true;
            } else if(source==0xfff1)value=u64(entry+8);
            else {
                const size_t sourceSegment=segmentForSection(source);
                if(sourceSegment==MaxSegments)return Error::UnresolvedSymbol;
                const uint64_t within=u64(entry+8),symbolBytes=u64(entry+16);
                if(!range(within,symbolBytes,segments_[sourceSegment].bytes))return Error::Relocation;
                value=dest[sourceSegment].gpuAddress+within;
            }
            // Intel ELF REL has zero explicit addend. RELA carries signed addend.
            if(r.type==4) {const uint64_t raw=u64(p+16);
                if(special && raw)return Error::Unsupported;
                if(raw>>63){const uint64_t magnitude=(~raw)+1;if(magnitude>value)return Error::Relocation;value-=magnitude;}
                else {if(raw>UINT64_MAX-value)return Error::Relocation;value+=raw;}}
            if(type==2)value&=0xffffffffULL;else if(type==3)value>>=32;
            // Intel's data relocations increment existing data; ISA relocations
            // replace the immediate. BSS starts at zero.
            if(!segments_[target].executable && !segments_[target].zeroInit) {
                const uint8_t *initial=data_+segments_[target].fileOffset+offset;
                value+=width==8?u64(initial):u32(initial);
            }
            for(size_t j=0;j<patchCount;++j)if(patches[j].segment==target && overlap(offset,width,patches[j].offset,patches[j].width))return Error::Relocation;
            patches[patchCount++]={target,offset,value,width};
        }
    }
    // Commit only after every address, relocation and capacity is valid.
    for(size_t i=0;i<count;++i)for(uint64_t b=0;b<segments_[i].bytes;++b)dest[i].cpu[b]=segments_[i].zeroInit?0:data_[segments_[i].fileOffset+b];
    for(size_t i=0;i<patchCount;++i){const auto &p=patches[i];put(dest[p.segment].cpu+p.offset,p.value,p.width);}
    StagedImage staged {};staged.kernelGpuAddress=dest[textSegment_].gpuAddress;
    staged.skipLocalIdLoadGpuAddress=staged.kernelGpuAddress+metadata_.skipPerThreadLoad;
    staged.textBytes=segments_[textSegment_].bytes;staged.relocationCount=patchCount;out=staged;return Error::None;
}
Error Image::payload(const EvidenceValues &v,Payload &out) const {
    if(!valid_)return Error::Metadata;
    const uint64_t required=uint64_t(v.count)*4;
    if(!v.count || !v.inputAddress || !v.outputAddress || (v.inputAddress&3) || (v.outputAddress&3) ||
       v.inputBytes<required || v.outputBytes<required || !range(v.inputAddress,v.inputBytes,XeMemory::VaLimit) || !range(v.outputAddress,v.outputBytes,XeMemory::VaLimit))return Error::InvalidBinding;
    uint64_t workgroup=1;
    for(unsigned i=0;i<3;++i){if(!v.localSize[i] || v.localSize[i]>1024 || workgroup>1024/v.localSize[i] ||
        v.globalOffset[i]>UINT32_MAX-v.localSize[i])return Error::InvalidBinding;
        workgroup*=v.localSize[i];}
    Payload payload {};payload.size=metadata_.crossThreadBytes;payload.inlineBytes=metadata_.inlineBytes;
    payload.indirectCrossThreadBytes=payload.size-payload.inlineBytes;payload.perThreadBytes=metadata_.perThreadBytes;
    for(size_t i=0;i<metadata_.argumentCount;++i) {
        const auto &a=metadata_.args[i];uint8_t *p=payload.bytes+a.offset;
        if(a.type==ArgType::GlobalOffset || a.type==ArgType::LocalSize){const auto *values=a.type==ArgType::GlobalOffset?v.globalOffset:v.localSize;for(unsigned d=0;d<3;++d)put(p+d*4,values[d],4);}
        else if(a.type==ArgType::Value)put(p,a.index==2?v.nonce:v.count,4);
        else if(a.mode==AddressMode::Stateless)put(p,a.index?v.outputAddress:v.inputAddress,8);
        else put(p,a.index?v.outputSurface:v.inputSurface,4);
    }
    out=payload;return Error::None;
}
Error resolveEvidencePointers(const XeMemory::VirtualMemory &vm,uint64_t owner,XeMemory::Handle input,
    XeMemory::Handle output,SurfaceBackend surfaces,EvidenceValues &values) {
    const auto *a=vm.inspect(owner,input),*b=vm.inspect(owner,output);
    auto mapped=[](const XeMemory::Allocation *p){return p && (p->state==XeMemory::State::Pinned || p->state==XeMemory::State::Bound) && p->pin.cookie && p->pin.dmaPages && p->pin.pageCount==p->bytes/XeMemory::PageSize;};
    if(!mapped(a) || !mapped(b))return Error::InvalidBinding;
    if(!surfaces.resolve)return Error::Unavailable;
    EvidenceValues resolved=values;
    if(!surfaces.resolve(surfaces.context,owner,input,*a,false,resolved.inputSurface) ||
       !surfaces.resolve(surfaces.context,owner,output,*b,true,resolved.outputSurface))return Error::Unavailable;
    resolved.inputAddress=a->address;resolved.outputAddress=b->address;resolved.inputBytes=a->bytes;resolved.outputBytes=b->bytes;
    values=resolved;return Error::None;
}
}
