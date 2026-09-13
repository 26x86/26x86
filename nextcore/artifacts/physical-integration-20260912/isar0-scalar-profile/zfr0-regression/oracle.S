.text
.global _start
_start:
mov x18,#0x40100000
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x0,ID_AA64ZFR0_EL1
mov x4,x0
movz x18,#0
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x1,ID_AA64ZFR0_EL1
mov x4,x1
movz x18,#16
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x2,ID_AA64ZFR0_EL1
mov x4,x2
movz x18,#32
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x3,ID_AA64ZFR0_EL1
mov x4,x3
movz x18,#48
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x4,ID_AA64ZFR0_EL1
mov x4,x4
movz x18,#64
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x5,ID_AA64ZFR0_EL1
mov x4,x5
movz x18,#80
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x6,ID_AA64ZFR0_EL1
mov x4,x6
movz x18,#96
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x7,ID_AA64ZFR0_EL1
mov x4,x7
movz x18,#112
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x8,ID_AA64ZFR0_EL1
mov x4,x8
movz x18,#128
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x9,ID_AA64ZFR0_EL1
mov x4,x9
movz x18,#144
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x10,ID_AA64ZFR0_EL1
mov x4,x10
movz x18,#160
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x11,ID_AA64ZFR0_EL1
mov x4,x11
movz x18,#176
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x12,ID_AA64ZFR0_EL1
mov x4,x12
movz x18,#192
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x13,ID_AA64ZFR0_EL1
mov x4,x13
movz x18,#208
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x14,ID_AA64ZFR0_EL1
mov x4,x14
movz x18,#224
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x15,ID_AA64ZFR0_EL1
mov x4,x15
movz x18,#240
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x16,ID_AA64ZFR0_EL1
mov x4,x16
movz x18,#256
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x17,ID_AA64ZFR0_EL1
mov x4,x17
movz x18,#272
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x18,ID_AA64ZFR0_EL1
mov x4,x18
movz x18,#288
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x19,ID_AA64ZFR0_EL1
mov x4,x19
movz x18,#304
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x20,ID_AA64ZFR0_EL1
mov x4,x20
movz x18,#320
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x21,ID_AA64ZFR0_EL1
mov x4,x21
movz x18,#336
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x22,ID_AA64ZFR0_EL1
mov x4,x22
movz x18,#352
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x23,ID_AA64ZFR0_EL1
mov x4,x23
movz x18,#368
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x24,ID_AA64ZFR0_EL1
mov x4,x24
movz x18,#384
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x25,ID_AA64ZFR0_EL1
mov x4,x25
movz x18,#400
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x26,ID_AA64ZFR0_EL1
mov x4,x26
movz x18,#416
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x27,ID_AA64ZFR0_EL1
mov x4,x27
movz x18,#432
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x28,ID_AA64ZFR0_EL1
mov x4,x28
movz x18,#448
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x29,ID_AA64ZFR0_EL1
mov x4,x29
movz x18,#464
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs x30,ID_AA64ZFR0_EL1
mov x4,x30
movz x18,#480
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
movz x4,#0
movk x4,#61440,lsl #16
movk x4,#0,lsl #32
movk x4,#0,lsl #48
msr nzcv,x4
mrs xzr,ID_AA64ZFR0_EL1
mov x4,xzr
movz x18,#496
movk x18,#16400,lsl #16
movk x18,#0,lsl #32
movk x18,#0,lsl #48
str x4,[x18]
mrs x4,nzcv
str x4,[x18,#8]
mov x0,#0x64e
1:b 1b
