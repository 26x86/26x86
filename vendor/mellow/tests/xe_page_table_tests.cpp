#include "../Mellow/XePageTable.hpp"
#include <array>
#include <vector>
#include <iostream>
#include <cstdlib>
#include <map>
#include <type_traits>

using namespace XeMemory;
static_assert(!std::is_copy_constructible<PageTable>::value, "Page table ownership must not be copied");
static_assert(!std::is_copy_assignable<PageTable>::value, "Page table ownership must not be assigned");
static size_t checks = 0;
#define CHECK(x) do { ++checks; if (!(x)) { std::cerr << "FAIL line " << __LINE__ << ": " << #x << '\n'; std::exit(1); } } while (0)
struct Pool {
    std::vector<std::array<uint64_t,512>> data;
    std::vector<TablePage> descriptors;
    explicit Pool(size_t n) : data(n), descriptors(n) {
        for (size_t i=0;i<n;++i) { data[i].fill(0xDADADADADADADADAULL); descriptors[i]={0x100000+i*4096,data[i].data()}; }
    }
};
static uint64_t independentWalk(const Pool &pool,uint64_t va) {
    size_t slot=0;
    for (unsigned shift : {39U,30U,21U}) {
        const uint64_t pde=pool.data[slot][(va>>shift)&511];
        if (!pde) return 0;
        CHECK((pde & 0xFFF) == 3);
        const uint64_t dma=pde&0x3FFFFFFFF000ULL;
        bool found=false;
        for(size_t i=0;i<pool.descriptors.size();++i) if(pool.descriptors[i].dma==dma) {slot=i;found=true;break;}
        CHECK(found);
    }
    return pool.data[slot][(va>>12)&511];
}
int main() {
    for (size_t count=1;count<=4;++count) {
        Pool pool(count); PageTable tree;
        CHECK(tree.initialize(7,pool.descriptors.data(),count,0)==Status::Ok);
        CHECK(tree.map4K(7,0x4000,0x20000000,0,true)==(count==4?Status::Ok:Status::NoSpace));
        CHECK(tree.usedPages()==(count==4?4U:1U));
        CHECK(tree.mappedPages()==(count==4?1U:0U));
        if(count<4) for(auto word:pool.data[0]) CHECK(word==0);
    }
    {
        Pool pool(32); PageTable tree;
        CHECK(tree.initialize(9,pool.descriptors.data(),32,0)==Status::Ok);
        const uint64_t vas[]={0,0x1FF000,0x200000,0x3FFFF000,0x40000000,0x7FFFFFF000,0x8000000000,VaLimit-4096};
        for(size_t i=0;i<8;++i) {
            const auto dma=0x20000000+i*4096;
            CHECK(tree.map4K(9,vas[i],dma,0,true)==Status::Ok);
            uint64_t out=0;
            CHECK(tree.lookup(9,vas[i],out)==Status::Ok);
            CHECK(out==(dma|3)); CHECK(independentWalk(pool,vas[i])==out);
        }
        CHECK(tree.map4K(9,vas[0],0x30000000,0,false)==Status::Busy);
        CHECK(tree.map4K(8,0x10000,0x30000000,0,false)==Status::WrongOwner);
        CHECK(tree.map4K(9,1,0x30000000,0,false)==Status::Invalid);
        CHECK(tree.map4K(9,VaLimit,0x30000000,0,false)==Status::Invalid);
        CHECK(tree.map4K(9,0x10000,DmaLimit,0,false)==Status::Invalid);
        CHECK(tree.map4K(9,0x10000,0x30000001,0,false)==Status::Invalid);
        CHECK(tree.map4K(9,0x10000,pool.descriptors[31].dma,0,false)==Status::Invalid);
        CHECK(tree.map4K(9,0x10000,0x30000000,16,false)==Status::Invalid);
        for(auto va:vas) CHECK(tree.unmap4K(9,va)==Status::Ok);
        CHECK(tree.usedPages()==1); CHECK(tree.mappedPages()==0);
        uint64_t unchanged=123;
        CHECK(tree.lookup(9,0x4000,unchanged)==Status::NotFound); CHECK(unchanged==123);
        for(unsigned pat=0;pat<16;++pat) {
            const uint64_t va=0x200000+pat*4096;
            CHECK(tree.map4K(9,va,0x20000000,static_cast<uint8_t>(pat),false)==Status::Ok);
            uint64_t value=0; CHECK(tree.lookup(9,va,value)==Status::Ok);
            const uint64_t bits=((pat&1)?8ULL:0)|((pat&2)?16ULL:0)|((pat&4)?128ULL:0)|((pat&8)?(1ULL<<62):0);
            CHECK(value==(0x20000001ULL|bits));
        }
        uint64_t root=0; CHECK(tree.seal(8,root)==Status::WrongOwner); CHECK(root==0);
        CHECK(tree.seal(9,root)==Status::Ok); CHECK(root==pool.descriptors[0].dma);
        CHECK(tree.map4K(9,0x10000,0x30000000,0,false)==Status::Busy);
        CHECK(tree.unmap4K(9,0x200000)==Status::Busy);
    }
    {
        Pool pool(16); PageTable tree; std::map<uint64_t,uint64_t> oracle;
        CHECK(tree.initialize(1,pool.descriptors.data(),16,0)==Status::Ok);
        uint32_t random=0x9e3779b9;
        for(unsigned step=0;step<5000;++step) {
            random=random*1664525U+1013904223U;
            const uint64_t va=((random>>8)%4096ULL)*4096;
            if(random&1) {
                const uint64_t dma=0x30000000+((random>>20)%1024ULL)*4096;
                const bool exists=oracle.count(va)!=0;
                CHECK(tree.map4K(1,va,dma,0,true)==(exists?Status::Busy:Status::Ok));
                if(!exists) oracle[va]=dma|3;
            } else {
                const bool exists=oracle.count(va)!=0;
                CHECK(tree.unmap4K(1,va)==(exists?Status::Ok:Status::NotFound));
                oracle.erase(va);
            }
            CHECK(tree.mappedPages()==oracle.size());
            uint64_t out=0;
            CHECK(tree.lookup(1,va,out)==(oracle.count(va)?Status::Ok:Status::NotFound));
            if(oracle.count(va)) CHECK(out==oracle.at(va));
        }
        for(const auto &pair:oracle) { CHECK(independentWalk(pool,pair.first)==pair.second); CHECK(tree.unmap4K(1,pair.first)==Status::Ok); }
        CHECK(tree.usedPages()==1); CHECK(tree.mappedPages()==0);
    }
    {
        Pool pool(4); PageTable tree;
        pool.descriptors[1].dma=pool.descriptors[0].dma;
        CHECK(tree.initialize(1,pool.descriptors.data(),4,0)==Status::Invalid);
        CHECK(pool.data[0][0]==0xDADADADADADADADAULL);
        pool.descriptors[1].dma=0x101000;
        pool.descriptors[1].words=pool.descriptors[0].words+1;
        CHECK(tree.initialize(1,pool.descriptors.data(),4,0)==Status::Invalid);
        pool.descriptors[1].words=pool.data[1].data();
        CHECK(tree.initialize(1,pool.descriptors.data(),4,4)==Status::Invalid);
        CHECK(tree.initialize(1,pool.descriptors.data(),4,0)==Status::Ok);
        pool.data[0][0]=0xDEAD003;
        uint64_t out=42; CHECK(tree.lookup(1,0,out)==Status::Invalid); CHECK(out==42);
        CHECK(tree.map4K(1,0,0x20000000,0,true)==Status::Invalid);
    }
    std::cout<<"PASS XePageTable: "<<checks<<" assertions; CPU buffers only, no GPU publication or execution\n";
}
