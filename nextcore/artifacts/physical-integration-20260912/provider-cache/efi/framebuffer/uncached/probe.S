.text
.global _start
_start:
    mov x0, #0
load_base: ldr x4, [x1, #40]
load_stride: ldr x5, [x1, #56]
load_width: ldr x6, [x1, #64]
load_height: ldr x7, [x1, #72]
load_depth: ldr x8, [x1, #80]
load_display: ldr x9, [x1, #48]
load_top: ldr x10, [x1, #32]
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
store_first: str w12, [x4]
    sub x11, x11, #4
    mov w12, #0xff
store_last: str w12, [x11]
    mov x2, x5
    mul x3, x6, x7
    mov x0, #0x600d
done: b done
