.text
.global _start
_start:
movz x0,#11
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
add x2,sp,#0
mov x3,#0xcc31
ccmn xzr,xzr,#15,nv
probe_success:
hlt #0
