// Independently authored tests of the explicit software IRQ compatibility profile.
// Encoding/fields: public m1n1 cpu_regs.h and XNU apple_arm64_regs.h.
// No original firmware instructions or hardware reset values are included.
.text
.global _start
_start:
    mov x3, #0x31
#if defined(PROBE_INVALID_WRITE)
    mov x0, #1
    msr S3_5_C15_C5_0, x0
#elif defined(PROBE_PENDING)
    msr daifclr, #3
    mrs x2, S3_5_C15_C5_0
#ifdef PROBE_UNMASK
    msr S3_5_C15_C5_0, xzr
#endif
#elif defined(PROBE_DAIF_IRQ)
    msr daifclr, #2
#elif defined(PROBE_DAIF_FIQ)
    msr daifclr, #1
#else
    mrs x2, S3_5_C15_C5_0
    mov x0, #0xa00000
    msr S3_5_C15_C5_0, x0
    mrs x1, S3_5_C15_C5_0
#endif
    hlt #0
