.arch armv8.3-a
.text
.global _start
_start:
movz x18,#0
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
mrs x19,CurrentEL
str x19,[x18],#8
mrs x19,ID_AA64ISAR1_EL1
str x19,[x18],#8
mrs x19,S3_0_C0_C6_2
str x19,[x18],#8
movz x19,#48
movk x19,#0,lsl #16
movk x19,#0,lsl #32
movk x19,#0,lsl #48
str x19,[x18],#8
adr x19,vectors
msr VBAR_EL1,x19
isb
movz x10,#4951
movk x10,#9320,lsl #16
movk x10,#13980,lsl #32
movk x10,#18605,lsl #48
movz x11,#60584
movk x11,#56215,lsl #16
movk x11,#51555,lsl #32
movk x11,#46930,lsl #48
msr APIAKeyLo_EL1,x10
msr APIAKeyHi_EL1,x11
movz x10,#4951
movk x10,#9320,lsl #16
movk x10,#13980,lsl #32
movk x10,#18605,lsl #48
movz x11,#60584
movk x11,#56215,lsl #16
movk x11,#51555,lsl #32
movk x11,#46930,lsl #48
msr APIBKeyLo_EL1,x10
msr APIBKeyHi_EL1,x11
movz x10,#4951
movk x10,#9320,lsl #16
movk x10,#13980,lsl #32
movk x10,#18605,lsl #48
movz x11,#60584
movk x11,#56215,lsl #16
movk x11,#51555,lsl #32
movk x11,#46930,lsl #48
msr APDAKeyLo_EL1,x10
msr APDAKeyHi_EL1,x11
movz x10,#4951
movk x10,#9320,lsl #16
movk x10,#13980,lsl #32
movk x10,#18605,lsl #48
movz x11,#60584
movk x11,#56215,lsl #16
movk x11,#51555,lsl #32
movk x11,#46930,lsl #48
msr APDBKeyLo_EL1,x10
msr APDBKeyHi_EL1,x11
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacia x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autia x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autia x4,x2
str x4,[x18],#8
mov x4,x1
autia x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacia x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autia x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autia x4,x2
str x4,[x18],#8
mov x4,x1
autia x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacia x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autia x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autia x4,x2
str x4,[x18],#8
mov x4,x1
autia x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacia x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autia x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autia x4,x2
str x4,[x18],#8
mov x4,x1
autia x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#128,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacia x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autia x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autia x4,x2
str x4,[x18],#8
mov x4,x1
autia x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65407,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacia x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autia x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autia x4,x2
str x4,[x18],#8
mov x4,x1
autia x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacib x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autib x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autib x4,x2
str x4,[x18],#8
mov x4,x1
autib x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacib x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autib x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autib x4,x2
str x4,[x18],#8
mov x4,x1
autib x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacib x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autib x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autib x4,x2
str x4,[x18],#8
mov x4,x1
autib x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacib x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autib x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autib x4,x2
str x4,[x18],#8
mov x4,x1
autib x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#128,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacib x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autib x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autib x4,x2
str x4,[x18],#8
mov x4,x1
autib x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65407,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacib x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autib x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autib x4,x2
str x4,[x18],#8
mov x4,x1
autib x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacda x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autda x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autda x4,x2
str x4,[x18],#8
mov x4,x1
autda x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacda x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autda x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autda x4,x2
str x4,[x18],#8
mov x4,x1
autda x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacda x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autda x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autda x4,x2
str x4,[x18],#8
mov x4,x1
autda x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacda x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autda x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autda x4,x2
str x4,[x18],#8
mov x4,x1
autda x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#128,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacda x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autda x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autda x4,x2
str x4,[x18],#8
mov x4,x1
autda x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65407,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacda x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autda x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autda x4,x2
str x4,[x18],#8
mov x4,x1
autda x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacdb x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autdb x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autdb x4,x2
str x4,[x18],#8
mov x4,x1
autdb x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacdb x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autdb x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autdb x4,x2
str x4,[x18],#8
mov x4,x1
autdb x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacdb x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autdb x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autdb x4,x2
str x4,[x18],#8
mov x4,x1
autdb x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacdb x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autdb x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autdb x4,x2
str x4,[x18],#8
mov x4,x1
autdb x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#128,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacdb x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autdb x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autdb x4,x2
str x4,[x18],#8
mov x4,x1
autdb x4,x2
str x4,[x18],#8
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65407,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacdb x3,x2
movz x10,#32784
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autdb x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autdb x4,x2
str x4,[x18],#8
mov x4,x1
autdb x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacia x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autia x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autia x4,x2
str x4,[x18],#8
mov x4,x1
autia x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacia x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autia x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autia x4,x2
str x4,[x18],#8
mov x4,x1
autia x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacia x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autia x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autia x4,x2
str x4,[x18],#8
mov x4,x1
autia x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacia x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autia x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autia x4,x2
str x4,[x18],#8
mov x4,x1
autia x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#128,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacia x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autia x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autia x4,x2
str x4,[x18],#8
mov x4,x1
autia x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65407,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacia x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIAKeyLo_EL1
str x19,[x18],#8
mrs x19,APIAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autia x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autia x4,x2
str x4,[x18],#8
mov x4,x1
autia x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacib x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autib x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autib x4,x2
str x4,[x18],#8
mov x4,x1
autib x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacib x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autib x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autib x4,x2
str x4,[x18],#8
mov x4,x1
autib x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacib x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autib x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autib x4,x2
str x4,[x18],#8
mov x4,x1
autib x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacib x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autib x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autib x4,x2
str x4,[x18],#8
mov x4,x1
autib x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#128,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacib x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autib x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autib x4,x2
str x4,[x18],#8
mov x4,x1
autib x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65407,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacib x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APIBKeyLo_EL1
str x19,[x18],#8
mrs x19,APIBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autib x4,x2
str x4,[x18],#8
mov x4,x1
xpaci x4
str x4,[x18],#8
mov x4,x3
xpaci x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autib x4,x2
str x4,[x18],#8
mov x4,x1
autib x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacda x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autda x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autda x4,x2
str x4,[x18],#8
mov x4,x1
autda x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacda x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autda x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autda x4,x2
str x4,[x18],#8
mov x4,x1
autda x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacda x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autda x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autda x4,x2
str x4,[x18],#8
mov x4,x1
autda x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacda x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autda x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autda x4,x2
str x4,[x18],#8
mov x4,x1
autda x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#128,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacda x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autda x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autda x4,x2
str x4,[x18],#8
mov x4,x1
autda x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65407,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacda x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDAKeyLo_EL1
str x19,[x18],#8
mrs x19,APDAKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autda x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autda x4,x2
str x4,[x18],#8
mov x4,x1
autda x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacdb x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autdb x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autdb x4,x2
str x4,[x18],#8
mov x4,x1
autdb x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#0,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacdb x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autdb x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autdb x4,x2
str x4,[x18],#8
mov x4,x1
autdb x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacdb x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autdb x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autdb x4,x2
str x4,[x18],#8
mov x4,x1
autdb x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#65535,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacdb x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autdb x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autdb x4,x2
str x4,[x18],#8
mov x4,x1
autdb x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#0,lsl #32
movk x1,#128,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32785
movk x10,#16401,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacdb x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autdb x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autdb x4,x2
str x4,[x18],#8
mov x4,x1
autdb x4,x2
str x4,[x18],#8
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
movz x10,#10240
movk x10,#63696,lsl #16
movk x10,#0,lsl #32
movk x10,#0,lsl #48
msr SCTLR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
movz x1,#304
movk x1,#0,lsl #16
movk x1,#32768,lsl #32
movk x1,#65407,lsl #48
movz x2,#39030
movk x2,#0,lsl #16
movk x2,#0,lsl #32
movk x2,#0,lsl #48
movz x10,#32784
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
mov x3,x1
pacdb x3,x2
movz x10,#32785
movk x10,#16400,lsl #16
movk x10,#5,lsl #32
movk x10,#0,lsl #48
msr TCR_EL1,x10
isb
mrs x19,TCR_EL1
str x19,[x18],#8
mrs x19,SCTLR_EL1
str x19,[x18],#8
str x1,[x18],#8
str x2,[x18],#8
mrs x19,APDBKeyLo_EL1
str x19,[x18],#8
mrs x19,APDBKeyHi_EL1
str x19,[x18],#8
str x3,[x18],#8
mov x4,x3
autdb x4,x2
str x4,[x18],#8
mov x4,x1
xpacd x4
str x4,[x18],#8
mov x4,x3
xpacd x4
str x4,[x18],#8
eor x4,x3,#0x0040000000000000
autdb x4,x2
str x4,[x18],#8
mov x4,x1
autdb x4,x2
str x4,[x18],#8
mov x0,#0x64e
complete:b complete
.balign 2048
vectors:
b trapped
.space 124
b trapped
.space 124
b trapped
.space 124
b trapped
.space 124
b trapped
.space 124
b trapped
.space 124
b trapped
.space 124
b trapped
.space 124
b trapped
.space 124
b trapped
.space 124
b trapped
.space 124
b trapped
.space 124
b trapped
.space 124
b trapped
.space 124
b trapped
.space 124
b trapped
.space 124
trapped:
mrs x20,ESR_EL1
mrs x21,ELR_EL1
mov x0,#0xbad
b trapped
