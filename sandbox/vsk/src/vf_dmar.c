/* Original bounded decoder of published DMAR layouts. See SOURCES.md. */
#include "vf_dmar.h"
static uint16_t u16(const uint8_t *p) { return (uint16_t)(p[0] | (uint16_t)p[1]<<8); }
static uint32_t u32(const uint8_t *p) { return u16(p) | (uint32_t)u16(p+2)<<16; }
static uint64_t u64(const uint8_t *p) { return u32(p) | (uint64_t)u32(p+4)<<32; }
static void clear(void *p, size_t n) { uint8_t *b=p; while(n--) *b++=0; }
static int zero(const uint8_t *p, size_t n) { while(n--) if(*p++) return 0; return 1; }
static int fits(uint64_t address, unsigned bits) { return bits==64 || address < (UINT64_C(1)<<bits); }
static int aliases(const void *a,size_t an,const void *b,size_t bn) {
    if(!an||!bn)return 0;
    uintptr_t first=(uintptr_t)a,second=(uintptr_t)b;
    /* Invalid spans are rejected without dereferencing or clearing them. */
    if(an-1>UINTPTR_MAX-first||bn-1>UINTPTR_MAX-second)return 1;
    return first<=second+bn-1 && second<=first+an-1;
}
static int conflict(uint64_t first, uint64_t last,
                    const struct vf_dmar_range *r, size_t n) {
    for(size_t i=0;i<n;i++)
        if(first<=r[i].base+r[i].bytes-1 && r[i].base<=last) return 1;
    return 0;
}
static int scopes(const uint8_t *p, size_t n, uint16_t segment,
                  unsigned kind, unsigned index, struct vf_dmar_snapshot *s) {
    while(n) {
        if(n<8 || p[1]<8 || p[1]>n || (p[1]-6)%2 || !zero(p+2,2)) return VF_DMAR_FORMAT;
        if(p[0]<1 || p[0]>4 || (kind==1 && p[0]>2)) return VF_DMAR_UNSUPPORTED;
        /* Intel VT-d architecture spec section 8.5: ATSR scopes identify PCIe
         * root ports and must use type 02h, not endpoint/IOAPIC/HPET scopes. */
        if(kind==2 && p[0]!=2) return VF_DMAR_FORMAT;
        unsigned paths=(p[1]-6)/2;
        if(paths>VF_DMAR_MAX_PATH || s->scope_count==VF_DMAR_MAX_SCOPES) return VF_DMAR_LIMIT;
        struct vf_dmar_scope *v=&s->scopes[s->scope_count++];
        v->segment=segment; v->owner_type=(uint8_t)kind; v->owner_index=(uint16_t)index;
        v->type=p[0]; v->enumeration_id=p[4]; v->start_bus=p[5]; v->path_count=(uint8_t)paths;
        for(unsigned j=0;j<paths;j++) {
            if(p[6+j*2]>31 || p[7+j*2]>7) return VF_DMAR_FORMAT;
            v->path[j][0]=p[6+j*2]; v->path[j][1]=p[7+j*2];
        }
        size_t consumed=p[1]; p+=consumed; n-=consumed;
    }
    return VF_DMAR_OK;
}
static int parse(const uint8_t *p, size_t n, const struct vf_dmar_range *r,
                 size_t nr, struct vf_dmar_snapshot *s) {
    if(!p || n<48 || n>1048576 || u32(p)!=UINT32_C(0x52414d44) || u32(p+4)!=n)
        return VF_DMAR_FORMAT;
    uint8_t sum=0; for(size_t i=0;i<n;i++) sum=(uint8_t)(sum+p[i]);
    if(sum) return VF_DMAR_CHECKSUM;
    if(p[8]!=1 || p[36]<31 || p[36]>63 || (p[37]&~7u) || !zero(p+38,10)) return VF_DMAR_UNSUPPORTED;
    s->address_bits=(uint8_t)(p[36]+1); s->interrupt_remap_reported=p[37]&1;
    for(size_t off=48;off<n;) {
        if(n-off<4) return VF_DMAR_FORMAT;
        const uint8_t *v=p+off; unsigned type=u16(v), len=u16(v+2); int rc;
        if(len<4 || len>n-off) return VF_DMAR_FORMAT;
        if(type==0) {
            if(len<16 || (v[4]&~1u)) return VF_DMAR_FORMAT;
            if(v[5]) return VF_DMAR_UNSUPPORTED; /* extended register size not supported */
            if(s->unit_count==VF_DMAR_MAX_UNITS) return VF_DMAR_LIMIT;
            uint64_t base=u64(v+8); uint16_t seg=u16(v+6);
            if(!base || (base&4095) || !fits(base+4095,s->address_bits)) return VF_DMAR_FORMAT;
            if(conflict(base,base+4095,r,nr)) return VF_DMAR_CONFLICT;
            for(unsigned i=0;i<s->unit_count;i++)
                if(s->units[i].registers==base || (s->units[i].segment==seg && s->units[i].include_all && v[4]))
                    return VF_DMAR_CONFLICT;
            struct vf_dmar_unit *u=&s->units[s->unit_count];
            u->registers=base; u->segment=seg; u->include_all=v[4];
            if(len==16 && !v[4]) return VF_DMAR_FORMAT;
            rc=scopes(v+16,len-16,seg,0,s->unit_count++,s); if(rc) return rc;
        } else if(type==1) {
            if(len<32 || !zero(v+4,2)) return VF_DMAR_FORMAT;
            if(s->rmrr_count==VF_DMAR_MAX_RMRR) return VF_DMAR_LIMIT;
            uint64_t base=u64(v+8), limit=u64(v+16);
            if((base&4095) || (limit&4095)!=4095 || base>limit || !fits(limit,s->address_bits)) return VF_DMAR_FORMAT;
            if(conflict(base,limit,r,nr)) return VF_DMAR_CONFLICT;
            struct vf_dmar_rmrr *m=&s->rmrr[s->rmrr_count];
            m->base=base; m->limit=limit; m->segment=u16(v+6);
            rc=scopes(v+24,len-24,m->segment,1,s->rmrr_count++,s); if(rc) return rc;
        } else if(type==2) {
            if(len<8 || (v[4]&~1u) || v[5] || (len==8 && !v[4])) return VF_DMAR_FORMAT;
            /* Even empty ALL_PORTS ATSRs consume an index; bound them before
             * incrementing, preserving the fixed uint16 scope owner_index. */
            if(s->atsr_count==VF_DMAR_MAX_ATSR)return VF_DMAR_LIMIT;
            rc=scopes(v+8,len-8,u16(v+6),2,s->atsr_count++,s); if(rc) return rc;
        } else if(type==3) {
            if(len!=20 || !zero(v+4,4) || !u64(v+8) || (u64(v+8)&4095)) return VF_DMAR_FORMAT;
            s->rhsa_count++;
        } else return VF_DMAR_UNSUPPORTED;
        off+=len;
    }
    if(!s->unit_count) return VF_DMAR_FORMAT;
    /* RHSA references must resolve, including when the DRHD occurs later. */
    for(size_t off=48;off<n;off+=u16(p+off+2)) if(u16(p+off)==3) {
        unsigned matches=0; for(unsigned i=0;i<s->unit_count;i++) matches+=s->units[i].registers==u64(p+off+8);
        if(matches!=1) return VF_DMAR_CONFLICT;
    }
    return VF_DMAR_OK;
}
int vf_dmar_parse(const uint8_t *p, size_t n, const struct vf_dmar_range *r,
                  size_t nr, struct vf_dmar_snapshot *out) {
    if(!out) return VF_DMAR_FORMAT;
    if(aliases(p,n,out,sizeof(*out)) || (r && nr &&
       (nr>SIZE_MAX/sizeof(*r)||aliases(r,nr*sizeof(*r),out,sizeof(*out)))))return VF_DMAR_FORMAT;
    clear(out,sizeof(*out));
    if(nr>4096 || (nr && !r)) return VF_DMAR_FORMAT;
    for(size_t i=0;i<nr;i++) if(!r[i].bytes || r[i].base>UINT64_MAX-(r[i].bytes-1)) return VF_DMAR_FORMAT;
    int rc=parse(p,n,r,nr,out);
    if(rc) clear(out,sizeof(*out));
    return rc;
}
