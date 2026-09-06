/* 26x86 first-party code; repository LICENSE.txt applies. */
#include "vf_dmar.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static uint8_t table[4096];
static struct vf_dmar_snapshot out;
static unsigned checks;
#define CHECK(c) do { ++checks; assert(c); } while(0)
static void w16(unsigned p,unsigned v) { table[p]=(uint8_t)v; table[p+1]=(uint8_t)(v>>8); }
static void w32(unsigned p,uint32_t v) { w16(p,v); w16(p+2,v>>16); }
static void w64(unsigned p,uint64_t v) { w32(p,(uint32_t)v); w32(p+4,(uint32_t)(v>>32)); }
static void seal(unsigned n) {
    w32(4,n); table[9]=0;
    unsigned sum=0; for(unsigned i=0;i<n;i++) sum+=table[i]; table[9]=(uint8_t)(0-sum);
}
static void fixture(void) {
    memset(table,0,sizeof(table)); memcpy(table,"DMAR",4); table[8]=1; table[36]=47; table[37]=1;
    w16(50,24); w64(56,0xfed90000); /* scoped DRHD */
    table[64]=1; table[65]=8; table[70]=2;
    w16(72,1); w16(74,32); w64(80,0x100000); w64(88,0x101fff);
    table[96]=1; table[97]=8; table[102]=2;
    seal(104);
}
static int run(unsigned n) { return vf_dmar_parse(table,n,NULL,0,&out); }
int main(void) {
    fixture(); CHECK(run(104)==VF_DMAR_OK); CHECK(out.unit_count==1 && out.rmrr_count==1);
    CHECK(out.scope_count==2 && out.scopes[0].path[0][0]==2 && out.interrupt_remap_reported==1);
    CHECK(out.rmrr[0].limit==0x101fff && out.address_bits==48);
    for(unsigned n=0;n<104;n++) CHECK(run(n)!=VF_DMAR_OK);
    CHECK(out.unit_count==0);
    fixture(); table[20]++; CHECK(run(104)==VF_DMAR_CHECKSUM);
    fixture(); w16(50,0); seal(104); CHECK(run(104)==VF_DMAR_FORMAT);
    fixture(); table[65]=7; seal(104); CHECK(run(104)==VF_DMAR_FORMAT);
    fixture(); table[70]=32; seal(104); CHECK(run(104)==VF_DMAR_FORMAT);
    fixture(); table[71]=8; seal(104); CHECK(run(104)==VF_DMAR_FORMAT);
    fixture(); table[64]=5; seal(104); CHECK(run(104)==VF_DMAR_UNSUPPORTED);
    fixture(); w64(56,0xfed90001); seal(104); CHECK(run(104)==VF_DMAR_FORMAT);
    fixture(); w64(56,UINT64_C(1)<<48); seal(104); CHECK(run(104)==VF_DMAR_FORMAT);
    fixture(); table[53]=1; seal(104); CHECK(run(104)==VF_DMAR_UNSUPPORTED);
    fixture(); table[38]=1; seal(104); CHECK(run(104)==VF_DMAR_UNSUPPORTED);
    fixture(); table[37]=0; seal(104); CHECK(run(104)==VF_DMAR_OK && !out.interrupt_remap_reported);
    fixture(); w64(88,0x100fff); seal(104); CHECK(run(104)==VF_DMAR_OK);
    fixture(); w64(88,0xfffff); seal(104); CHECK(run(104)==VF_DMAR_FORMAT);
    fixture(); w64(88,0x101000); seal(104); CHECK(run(104)==VF_DMAR_FORMAT);
    fixture(); struct vf_dmar_range protected={0x100fff,2};
    CHECK(vf_dmar_parse(table,104,&protected,1,&out)==VF_DMAR_CONFLICT);
    CHECK(!out.unit_count && !out.scope_count);
    protected.base=0x102000; CHECK(vf_dmar_parse(table,104,&protected,1,&out)==VF_DMAR_OK);
    protected.base=0xfed90000; CHECK(vf_dmar_parse(table,104,&protected,1,&out)==VF_DMAR_CONFLICT);
    protected.base=UINT64_MAX; CHECK(vf_dmar_parse(table,104,&protected,1,&out)==VF_DMAR_FORMAT);
    fixture(); memcpy(table+104,table+48,24); seal(128); CHECK(run(128)==VF_DMAR_CONFLICT);
    fixture(); w16(104,3); w16(106,20); w64(112,0xfed90000); seal(124);
    CHECK(run(124)==VF_DMAR_OK && out.rhsa_count==1);
    w64(112,0xfed91000); seal(124); CHECK(run(124)==VF_DMAR_CONFLICT);
    fixture(); w16(104,4); w16(106,4); seal(108); CHECK(run(108)==VF_DMAR_UNSUPPORTED);
    /* ATSR device scopes are root ports (type 2) only, VT-d section 8.5. */
    fixture(); w16(104,2); w16(106,16); table[112]=2; table[113]=8; table[118]=3; seal(120);
    CHECK(run(120)==VF_DMAR_OK && out.atsr_count==1 && out.scopes[2].owner_type==2);
    for(unsigned type=1;type<=4;type++) if(type!=2) {
        table[112]=(uint8_t)type; seal(120); CHECK(run(120)==VF_DMAR_FORMAT);
        CHECK(!out.unit_count && !out.atsr_count);
    }
    /* Empty ALL_PORTS entries must not overflow/truncate future owner indexes. */
    fixture();
    for(unsigned i=0;i<VF_DMAR_MAX_ATSR+1;i++) {
        unsigned at=104+i*8;w16(at,2);w16(at+2,8);table[at+4]=1;
    }
    seal(104+VF_DMAR_MAX_ATSR*8);CHECK(run(104+VF_DMAR_MAX_ATSR*8)==VF_DMAR_OK);
    seal(104+(VF_DMAR_MAX_ATSR+1)*8);CHECK(run(104+(VF_DMAR_MAX_ATSR+1)*8)==VF_DMAR_LIMIT);
    CHECK(!out.unit_count && !out.atsr_count);
    /* Bad aliasing cannot let output initialization destroy const input. */
    fixture();memset(&out,0xa5,sizeof(out));memcpy(&out,table,104);
    CHECK(vf_dmar_parse((const uint8_t *)&out,104,NULL,0,&out)==VF_DMAR_FORMAT);
    CHECK(!memcmp(&out,table,104));
    CHECK(((const uint8_t *)&out)[sizeof(out)-1]==0xa5);
    memset(&out,0xa5,sizeof(out));
    CHECK(vf_dmar_parse(table,104,(const struct vf_dmar_range *)(const void *)&out,1,&out)==VF_DMAR_FORMAT);
    CHECK(((const uint8_t *)&out)[0]==0xa5 && ((const uint8_t *)&out)[sizeof(out)-1]==0xa5);
    fixture(); CHECK(vf_dmar_parse(NULL,104,NULL,0,&out)==VF_DMAR_FORMAT);
    CHECK(vf_dmar_parse(table,104,NULL,1,&out)==VF_DMAR_FORMAT);
    /* Bounded malformed-byte corpus under ASan/UBSan, including rechecksummed edits. */
    for(unsigned pos=0;pos<104;pos++) for(unsigned v=0;v<256;v+=17) {
        fixture(); table[pos]=(uint8_t)v; seal(104); int rc=run(104);
        CHECK(rc>=VF_DMAR_OK && rc<=VF_DMAR_CONFLICT);
        if(rc) CHECK(!out.unit_count && !out.rmrr_count && !out.scope_count);
    }
    printf("{\"test\":\"dmar\",\"level\":\"UNIT\",\"passed\":true,\"checks\":%u,\"hardware_verified\":false}\n",checks);
    return 0;
}
