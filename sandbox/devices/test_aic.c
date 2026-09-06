#include "aic_v1.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
    vf_aic_v1 a;uint32_t value=0;
    assert(!vf_aic_init(&a,896,2));
    assert(!vf_aic_read(&a,1,0x2000,4,&value)&&value==1);
    assert(!vf_aic_set_line(&a,7,1)&&!vf_aic_pending(&a,0));
    assert(!vf_aic_write(&a,0,0x4180,4,1u<<7)&&vf_aic_pending(&a,0));
    assert(!vf_aic_pending(&a,1));
    assert(!vf_aic_read(&a,0,0x2004,4,&value)&&value==0x10007);
    assert(!vf_aic_pending(&a,0));
    /* Level remains high after auto-ack. Unmask must redeliver. */
    assert(!vf_aic_write(&a,0,0x4180,4,1u<<7)&&vf_aic_pending(&a,0));
    assert(!vf_aic_write(&a,0,0x301c,4,2)&&!vf_aic_pending(&a,0)&&vf_aic_pending(&a,1));
    assert(!vf_aic_set_line(&a,7,0)&&!vf_aic_pending(&a,1));
    /* Software pending is independent of the physical level. */
    assert(!vf_aic_write(&a,0,0x4000,4,1u<<7)&&vf_aic_pending(&a,1));
    assert(!vf_aic_write(&a,0,0x4080,4,1u<<7)&&!vf_aic_pending(&a,1));
    assert(!vf_aic_set_line(&a,3,1));assert(!vf_aic_set_line(&a,9,1));
    assert(!vf_aic_write(&a,0,0x4180,4,(1u<<3)|(1u<<9)));
    assert(!vf_aic_read(&a,0,0x2004,4,&value)&&value==0x10003);
    assert(!vf_aic_read(&a,0,0x2004,4,&value)&&value==0x10009);
    assert(!vf_aic_read(&a,0,0x2004,4,&value)&&value==0);
    assert(vf_aic_read(&a,0,0x2004,8,&value)==-1);
    assert(vf_aic_read(&a,2,0x2004,4,&value)==-1);
    assert(vf_aic_write(&a,0,0x2008,4,1)==-1); /* IPI not implemented */
    assert(vf_aic_write(&a,0,0x3000,4,4)==-1);
    assert(vf_aic_set_line(&a,896,1)==-1);
    assert(vf_aic_init(&a,896,33)==-1);
    puts("PASS AIC v1 wired IRQ: auto-mask, level reassert, affinity, priority, software IRQ, bounds");
    return 0;
}
