// Authored MMFR0/control readback and lower-to-upper alias memory transaction.
.text
.global _start
_start:
    str x2, [x0]
    ldr x3, [x1]
    cmp x3, x2
    b.ne failure
    mrs x0, ID_AA64MMFR0_EL1
    mrs x1, TCR_EL1
    mrs x2, TTBR0_EL1
    mrs x3, TTBR1_EL1
    hlt #0
failure:
    b failure
