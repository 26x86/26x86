/* Original specification-based static ELF loader, no external code imported.
 * ABI references: https://refspecs.linuxfoundation.org/elf/gabi4+/ch4.eheader.html
 * https://refspecs.linuxfoundation.org/elf/gabi4+/ch5.pheader.html
 * SPDX-License-Identifier: BSD-4-Clause
 */
#include "vf_elf.h"
static uint16_t r16(const uint8_t *p) {return (uint16_t)p[0]|(uint16_t)p[1]<<8;}
static uint32_t r32(const uint8_t *p) {return (uint32_t)r16(p)|(uint32_t)r16(p+2)<<16;}
static uint64_t r64(const uint8_t *p) {return (uint64_t)r32(p)|(uint64_t)r32(p+4)<<32;}
static void clear(void *p,size_t n) {volatile uint8_t *b=p;while(n--)*b++=0;}
static int equal(const void *a,const void *b,size_t n) {
    const uint8_t *x=a,*y=b;while(n--)if(*x++!=*y++)return 0;return 1;
}
static int alias(const void *a,size_t an,const void *b,size_t bn) {
    uintptr_t x=(uintptr_t)a,y=(uintptr_t)b;if(!an||!bn)return 0;
    if(an-1>UINTPTR_MAX-x||bn-1>UINTPTR_MAX-y)return 1;
    return x<=y+bn-1 && y<=x+an-1;
}
static int bounded(uint64_t offset,uint64_t bytes,uint64_t total) {
    return offset<=total&&bytes<=total-offset;
}
static int canonical(uint64_t a) {return a<=UINT64_C(0x00007fffffffffff)||a>=UINT64_C(0xffff800000000000);}
static int pow2(uint64_t n) {return !n||!(n&(n-1));}
static int inspect(const uint8_t *f,size_t length,uint64_t budget,struct vf_elf_plan *p) {
    if(!f||length<64)return VF_ELF_EFORMAT;
    if(!budget||budget>VF_ELF_MAX_IMAGE_BYTES||length>VF_ELF_MAX_IMAGE_BYTES)return VF_ELF_ELIMIT;
    if(f[0]!=0x7f||f[1]!='E'||f[2]!='L'||f[3]!='F')return VF_ELF_EFORMAT;
    if(f[4]!=2||f[5]!=1||f[6]!=1||f[7]!=0||f[8]!=0||r16(f+16)!=2||r16(f+18)!=62||r32(f+20)!=1||r32(f+48))return VF_ELF_EUNSUPPORTED;
    for(unsigned i=9;i<16;i++)if(f[i])return VF_ELF_EFORMAT;
    if(r16(f+52)!=64||r16(f+54)!=56)return VF_ELF_EFORMAT;
    uint64_t phoff=r64(f+32),shoff=r64(f+40);uint16_t phnum=r16(f+56),shnum=r16(f+60),shstr=r16(f+62);
    if(!phnum||phnum>64)return VF_ELF_ELIMIT;
    if(phoff<64||(phoff&7)||!bounded(phoff,(uint64_t)phnum*56,length))return VF_ELF_ERANGE;
    if(shoff) {
        if(!shnum||shnum>4096||shstr>=shnum||r16(f+58)!=64)return VF_ELF_EUNSUPPORTED;
        if(shoff<64||(shoff&7)||!bounded(shoff,(uint64_t)shnum*64,length))return VF_ELF_ERANGE;
        if(shoff<phoff+(uint64_t)phnum*56&&phoff<shoff+(uint64_t)shnum*64)return VF_ELF_EOVERLAP;
        for(unsigned i=0;i<shnum;i++) {
            const uint8_t *s=f+shoff+(uint64_t)i*64;uint32_t type=r32(s+4);
            uint64_t flags=r64(s+8),off=r64(s+24),bytes=r64(s+32),align=r64(s+48);
            if(type==4||type==9||type==19||type==6||type==11||(flags&0x400))return VF_ELF_EUNSUPPORTED;
            if(!pow2(align))return VF_ELF_EFORMAT;
            if(!bounded(off,type==8?0:bytes,length))return VF_ELF_ERANGE;
        }
    } else if(shnum||shstr||r16(f+58))return VF_ELF_EFORMAT;
    uint64_t low=UINT64_MAX,high=0;int entry_backed=0;uint64_t entry=r64(f+24);
    if(!entry||!canonical(entry))return VF_ELF_EENTRY;
    for(unsigned i=0;i<phnum;i++) {
        const uint8_t *h=f+phoff+(uint64_t)i*56;uint32_t type=r32(h),flags=r32(h+4);
        if(type==0)continue;
        uint64_t off=r64(h+8),va=r64(h+16),filesz=r64(h+32),memsz=r64(h+40),align=r64(h+48);
        if(type!=1) {
            /* PHDR metadata and a non-executable GNU_STACK declaration are the
             * only other supported headers. Required unknown semantics fail. */
            if(type==0x6474e551) {
                if((flags&~7u)||(flags&1)||filesz||memsz)return VF_ELF_EUNSUPPORTED;
            } else if(type==6) {
                if(flags!=4||off!=phoff||filesz!=(uint64_t)phnum*56||memsz!=filesz)return VF_ELF_EFORMAT;
            } else return VF_ELF_EUNSUPPORTED;
            if(!bounded(off,filesz,length)||!pow2(align))return VF_ELF_ERANGE;
            continue;
        }
        if(p->segment_count==VF_ELF_MAX_SEGMENTS)return VF_ELF_ELIMIT;
        if((flags&~7u)||!(flags&4))return VF_ELF_EUNSUPPORTED;
        if((flags&3)==3)return VF_ELF_EWX;
        if(!memsz||filesz>memsz||!bounded(off,filesz,length)||memsz-1>UINT64_MAX-va)return VF_ELF_ERANGE;
        uint64_t last=va+memsz-1;
        if(!va||!canonical(va)||!canonical(last)||(va>>47)!=(last>>47))return VF_ELF_ERANGE;
        if(!pow2(align)||(align>1&&(va&(align-1))!=(off&(align-1)))||(va&4095)!=(off&4095))return VF_ELF_EFORMAT;
        uint64_t page=va&~UINT64_C(4095);
        if(last>UINT64_MAX-4096)return VF_ELF_ERANGE;
        uint64_t end=(last|UINT64_C(4095))+1;
        for(unsigned j=0;j<p->segment_count;j++) {
            const struct vf_elf_segment *s=&p->segments[j];
            uint64_t sbase=s->virtual_address&~UINT64_C(4095);
            uint64_t send=((s->virtual_address+s->memory_bytes-1)|UINT64_C(4095))+1;
            if(page<send&&sbase<end)return VF_ELF_EOVERLAP;
        }
        if(p->segment_count&&va<p->segments[p->segment_count-1].virtual_address)return VF_ELF_EFORMAT;
        struct vf_elf_segment *s=&p->segments[p->segment_count++];
        s->file_offset=off;s->file_bytes=filesz;s->memory_bytes=memsz;s->virtual_address=va;s->flags=flags;
        if(page<low)low=page;if(end>high)high=end;
        if((flags&1)&&entry>=va&&entry-va<filesz)entry_backed=1;
    }
    if(!p->segment_count||!entry_backed)return VF_ELF_EENTRY;
    if(high<low||high-low>budget)return VF_ELF_ELIMIT;
    p->version=1;p->file_bytes=length;p->image_base=low;p->image_bytes=high-low;
    p->entry_offset=entry-low;p->budget_bytes=budget;
    for(unsigned i=0;i<p->segment_count;i++)p->segments[i].image_offset=p->segments[i].virtual_address-low;
    return VF_ELF_OK;
}
int vf_elf_make_plan(const void *file,size_t bytes,uint64_t budget,struct vf_elf_plan *out) {
    if(!out)return VF_ELF_EARG;
    if(alias(file,bytes,out,sizeof(*out)))return VF_ELF_EARG;
    clear(out,sizeof(*out));int rc=inspect(file,bytes,budget,out);
    if(rc)clear(out,sizeof(*out));return rc;
}
int vf_elf_copy(const void *file,size_t bytes,const struct vf_elf_plan *p,void *destination,size_t capacity) {
    if(!file||!p||!destination)return VF_ELF_EARG;
    if(alias(file,bytes,destination,capacity)||alias(p,sizeof(*p),destination,capacity)||alias(file,bytes,p,sizeof(*p)))return VF_ELF_EARG;
    struct vf_elf_plan actual;int rc=vf_elf_make_plan(file,bytes,p->budget_bytes,&actual);
    if(rc)return rc;
    if(!equal(p,&actual,sizeof(actual)))return VF_ELF_EPLAN;
    if(actual.image_bytes>capacity)return VF_ELF_ERANGE;
    clear(destination,(size_t)actual.image_bytes);
    const uint8_t *src=file;volatile uint8_t *dst=destination;
    for(unsigned i=0;i<actual.segment_count;i++) {
        const struct vf_elf_segment *s=&actual.segments[i];
        for(uint64_t n=0;n<s->file_bytes;n++)dst[s->image_offset+n]=src[s->file_offset+n];
    }
    return VF_ELF_OK;
}
