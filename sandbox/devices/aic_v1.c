/* 26x86 first-party AIC v1 wired IRQ model. See AIC.md for register evidence.
 * No GIC compatibility, guessed IPI/FIQ success, or copied Linux driver code.
 */
#include "aic_v1.h"

int vf_aic_init(vf_aic_v1 *a,unsigned irqs,unsigned cpus) {
    if(!a || !irqs || irqs>VF_AIC_MAX_IRQ || !cpus || cpus>VF_AIC_MAX_CPU)return -1;
    a->irq_count=irqs;a->cpu_count=cpus;
    for(unsigned i=0;i<VF_AIC_MAX_IRQ;i++)a->target[i]=1;
    for(unsigned i=0;i<32;i++){a->level[i]=0;a->software[i]=0;a->masked[i]=UINT32_MAX;}
    return 0;
}
int vf_aic_set_line(vf_aic_v1 *a,unsigned irq,int high) {
    if(!a || irq>=a->irq_count)return -1;
    uint32_t bit=UINT32_C(1)<<(irq&31);
    if(high)a->level[irq>>5]|=bit;else a->level[irq>>5]&=~bit;
    return 0;
}
static int next_irq(const vf_aic_v1 *a,unsigned cpu) {
    if(!a || cpu>=a->cpu_count)return -1;
    for(unsigned word=0;word<32;word++) {
        uint32_t pending=(a->level[word]|a->software[word])&~a->masked[word];
        while(pending) {
            unsigned bit=(unsigned)__builtin_ctz(pending), irq=word*32+bit;
            if(irq<a->irq_count && (a->target[irq]&(UINT32_C(1)<<cpu)))return (int)irq;
            pending&=pending-1;
        }
    }
    return -1;
}
int vf_aic_pending(const vf_aic_v1 *a,unsigned cpu) { return next_irq(a,cpu)>=0; }
int vf_aic_read(vf_aic_v1 *a,unsigned cpu,uint32_t off,unsigned width,uint32_t *value) {
    if(!a || !value || cpu>=a->cpu_count || width!=4 || (off&3))return -1;
    if(off==4){*value=a->irq_count;return 0;}
    if(off==0x2000){*value=cpu;return 0;}
    if(off==0x2004) {
        int irq=next_irq(a,cpu);*value=0;
        if(irq>=0){a->masked[(unsigned)irq>>5]|=UINT32_C(1)<<((unsigned)irq&31);*value=0x10000u|(unsigned)irq;}
        return 0;
    }
    if(off>=0x3000 && off<0x4000) {
        unsigned irq=(off-0x3000)/4;
        if(irq>=a->irq_count)return -1;
        *value=a->target[irq];return 0;
    }
    if(off>=0x4200 && off<0x4280){*value=a->level[(off-0x4200)/4];return 0;}
    return -1;
}
int vf_aic_write(vf_aic_v1 *a,unsigned cpu,uint32_t off,unsigned width,uint32_t value) {
    if(!a || cpu>=a->cpu_count || width!=4 || (off&3))return -1;
    if(off>=0x3000 && off<0x4000) {
        unsigned irq=(off-0x3000)/4;
        if(irq>=a->irq_count || (a->cpu_count<32 && (value>>a->cpu_count)))return -1;
        a->target[irq]=value;return 0;
    }
    if(off>=0x4000 && off<0x4200) {
        unsigned word=(off&0x7f)/4, group=(off-0x4000)/0x80;
        unsigned first=word*32;
        uint32_t valid=first>=a->irq_count?0: a->irq_count-first>=32?UINT32_MAX:
            (UINT32_C(1)<<(a->irq_count-first))-1;
        if(value&~valid)return -1;
        switch(group) {
        case 0:a->software[word]|=value;break;
        case 1:a->software[word]&=~value;break;
        case 2:a->masked[word]|=value;break;
        case 3:a->masked[word]&=~value;break;
        default:return -1;
        }
        return 0;
    }
    return -1;
}
