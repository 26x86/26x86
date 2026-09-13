.text
.global _start
_start:
movz x0,#31
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
add x2,sp,#0
mov x3,#0xcc31
ccmp x0,x1,#0,al
ccmn w0,w1,#15,ne
ccmp x0,#31,#0,nv
b.eq probe_success
mov x3,#0xbad
hlt #0
probe_success:
hlt #0
