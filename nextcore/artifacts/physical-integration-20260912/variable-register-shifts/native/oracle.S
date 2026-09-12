.text
.global _start
_start:
mov x18,#0x40100000
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w0,w0,w1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w1,w0,w1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w0,w0,w0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,wzr,w1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv w2,w0,wzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv wzr,w0,w1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv wzr,wzr,wzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lslv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
lsrv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
asrv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#1
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#2
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#3
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#4
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#5
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#6
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#7
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#8
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#9
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#10
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#11
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#12
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#13
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#14
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#15
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#16
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#17
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#18
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#19
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#20
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#21
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#22
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#23
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#24
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#25
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#26
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#27
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#28
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#29
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#30
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#31
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#32
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#33
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#34
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#35
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#36
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#37
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#38
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#39
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#40
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#41
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#42
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#43
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#44
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#45
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#46
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#47
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#48
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#49
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#50
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#51
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#52
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#53
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#54
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#55
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#56
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#57
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#58
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#59
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#60
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#61
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#62
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#63
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#127
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#32768,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#0
movk x0,#0,lsl #16
movk x0,#0,lsl #32
movk x0,#0,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#65535
movk x0,#65535,lsl #16
movk x0,#65535,lsl #32
movk x0,#65535,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#1
movk x0,#32768,lsl #16
movk x0,#0,lsl #32
movk x0,#32768,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x0,x0,x1
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x1,x0,x1
mov x4,x1
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x0,x0,x0
mov x4,x0
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,xzr,x1
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv x2,x0,xzr
mov x4,x2
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv xzr,x0,x1
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#0
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#64
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#65535
movk x1,#65535,lsl #16
movk x1,#65535,lsl #32
movk x1,#65535,lsl #48
movz x2,#64206
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
rorv xzr,xzr,xzr
mov x4,xzr
str x4,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
mov x0,#0x64e
1:b 1b
