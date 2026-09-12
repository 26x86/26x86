.text
.global _start
_start:
    mov x0, #0
    ldr x4, [x1, #40]
    ldr x5, [x1, #56]
    ldr x6, [x1, #64]
    ldr x7, [x1, #72]
    ldr x8, [x1, #80]
    ldr x9, [x1, #48]
    ldr x10, [x1, #32]
    cbz x4, done
    cbz x6, done
    cbz x7, done
    cmp x8, #32
    b.ne done
    cmp x9, #1
    b.ne done
    lsl x11, x6, #2
    cmp x5, x11
    b.ne done
    madd x11, x7, x5, x4
    cmp x10, x11
    b.lo done
    mov w12, #0xff0000
    str w12, [x4]
    sub x11, x11, #4
    mov w12, #0xff
    str w12, [x11]
    mov x2, x5
    mul x3, x6, x7
    mov x0, #0x600d
done: b done
