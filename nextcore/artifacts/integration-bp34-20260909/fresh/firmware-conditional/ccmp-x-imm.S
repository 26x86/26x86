.text
.global _start
_start:
movz x0,#31
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
add x2,sp,#0
mov x3,#0xcc31
ccmp x0,#31,#15,al
probe_success:
hlt #0
