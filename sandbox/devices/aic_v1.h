/* 26x86 first-party code; repository LICENSE.txt applies. */
#ifndef VENFIRE_AIC_V1_H
#define VENFIRE_AIC_V1_H
#include <stdint.h>
#define VF_AIC_MAX_IRQ 1024u
#define VF_AIC_MAX_CPU 32u
typedef struct {
    uint32_t irq_count, cpu_count;
    uint32_t target[VF_AIC_MAX_IRQ];
    uint32_t level[32], software[32], masked[32];
} vf_aic_v1;
/* Single scheduler owner: serialize all MMIO and device line changes. */
int vf_aic_init(vf_aic_v1 *, unsigned irq_count, unsigned cpu_count);
int vf_aic_set_line(vf_aic_v1 *, unsigned irq, int high);
int vf_aic_pending(const vf_aic_v1 *, unsigned cpu);
/* Accesses are exactly aligned little-endian u32. Unknown registers fail. */
int vf_aic_read(vf_aic_v1 *, unsigned cpu, uint32_t offset, unsigned width, uint32_t *value);
int vf_aic_write(vf_aic_v1 *, unsigned cpu, uint32_t offset, unsigned width, uint32_t value);
#endif
