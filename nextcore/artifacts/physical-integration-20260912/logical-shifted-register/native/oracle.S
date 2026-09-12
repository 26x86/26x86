.text
.global _start
_start:
mov x18,#0x40100000
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsl #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsl #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,lsr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,asr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,asr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,ror #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and w2,w0,w1,ror #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsl #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsl #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,lsr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,asr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,asr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,ror #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic w2,w0,w1,ror #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsl #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsl #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,lsr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,asr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,asr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,ror #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr w2,w0,w1,ror #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsl #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsl #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,lsr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,asr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,asr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,ror #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn w2,w0,w1,ror #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsl #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsl #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,lsr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,asr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,asr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,ror #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor w2,w0,w1,ror #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsl #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsl #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,lsr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,asr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,asr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,ror #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon w2,w0,w1,ror #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsl #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsl #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,lsr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,asr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,asr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,ror #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands w2,w0,w1,ror #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsl #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsl #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsl #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsl #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,lsr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,asr #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,asr #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,asr #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,asr #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,ror #16
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,ror #16
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,ror #31
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics w2,w0,w1,ror #31
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsl #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsl #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,lsr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,asr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,asr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,ror #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
and x2,x0,x1,ror #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsl #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsl #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,lsr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,asr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,asr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,ror #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bic x2,x0,x1,ror #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsl #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsl #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,lsr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,asr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,asr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,ror #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orr x2,x0,x1,ror #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsl #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsl #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,lsr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,asr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,asr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,ror #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
orn x2,x0,x1,ror #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsl #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsl #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,lsr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,asr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,asr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,ror #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eor x2,x0,x1,ror #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsl #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsl #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,lsr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,asr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,asr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,ror #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
eon x2,x0,x1,ror #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsl #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsl #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,lsr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,asr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,asr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,ror #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
ands x2,x0,x1,ror #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsl #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsl #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsl #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsl #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsl #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsl #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsl #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsl #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,lsr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,asr #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,asr #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,asr #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,asr #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,asr #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,asr #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,asr #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,asr #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,ror #0
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,ror #0
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,ror #1
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,ror #1
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,ror #32
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,ror #32
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
movz x0,#63360
movk x0,#54758,lsl #16
movk x0,#46020,lsl #32
movk x0,#37282,lsl #48
movz x1,#52719
movk x1,#35243,lsl #16
movk x1,#17767,lsl #32
movk x1,#33059,lsl #48
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,ror #63
str x2,[x18],#8
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
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
bics x2,x0,x1,ror #63
str x2,[x18],#8
mrs x4,nzcv
str x4,[x18],#8
mov x0,#0x64e
1:b 1b
