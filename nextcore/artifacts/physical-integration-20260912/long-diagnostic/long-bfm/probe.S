.text
.global _start
_start:
    mov x0, #0xffff
    mov x4, #0x1234
    cmp x4, x4
    bfi x0, x4, #8, #8
    bfxil x0, x4, #8, #8
    mov x2, #0xffff
    bfc x2, #4, #8
    bfi w2, w4, #16, #8
    mov x3, #0xabcd
    bfi x3, x3, #8, #8
    bfxil w3, wzr, #0, #8
    b.ne failure
done: b done
failure:
    mov x0, #0
    b done
