// Independently authored EL1 thread-register persistence diagnostic.
.text
.global _start
_start:
    msr tpidr_el0, x1
    mrs x2, tpidr_el0
    msr tpidrro_el0, x1
    mrs x3, tpidrro_el0
    msr tpidr_el1, x1
    mrs x0, tpidr_el1
    hlt #0
