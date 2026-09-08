.text
.global _start
_start:
movz x0,#0
movk x0,#0,lsl #16
movk x0,#22136,lsl #32
movk x0,#4660,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
add x2,sp,#0
mov x3,#0xcc31
ccmp w0,w1,#15,al
probe_success:
hlt #0
