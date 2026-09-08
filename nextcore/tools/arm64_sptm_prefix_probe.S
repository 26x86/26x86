// Independently authored cold-register diagnostic, not an SPTM implementation.
.text
.global _start
_start:
    mov x3, #0x31
    cmp x0, #0
    b.ne failed
    add x2, x1, #0
    ldr x3, [x1]
    hlt #0
failed:
    hlt #1
