.text
.global _start
_start:
mov x18,#0x40100000
mov x19,#0x40110000
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#256
sturb w2,[x3,#-256]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#1
sturb w2,[x3,#-1]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
sub x3,x19,#255
sturb w2,[x3,#255]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#256
ldurb w2,[x3,#-256]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#1
ldurb w2,[x3,#-1]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
sub x3,x19,#255
ldurb w2,[x3,#255]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#256
ldursb x2,[x3,#-256]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#1
ldursb x2,[x3,#-1]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
sub x3,x19,#255
ldursb x2,[x3,#255]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#256
ldursb w2,[x3,#-256]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#1
ldursb w2,[x3,#-1]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
sub x3,x19,#255
ldursb w2,[x3,#255]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#256
sturh w2,[x3,#-256]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#1
sturh w2,[x3,#-1]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
sub x3,x19,#255
sturh w2,[x3,#255]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#256
ldurh w2,[x3,#-256]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#1
ldurh w2,[x3,#-1]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
sub x3,x19,#255
ldurh w2,[x3,#255]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#256
ldursh x2,[x3,#-256]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#1
ldursh x2,[x3,#-1]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
sub x3,x19,#255
ldursh x2,[x3,#255]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#256
ldursh w2,[x3,#-256]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#1
ldursh w2,[x3,#-1]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
sub x3,x19,#255
ldursh w2,[x3,#255]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#256
stur w2,[x3,#-256]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#1
stur w2,[x3,#-1]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
sub x3,x19,#255
stur w2,[x3,#255]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#256
ldur w2,[x3,#-256]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#1
ldur w2,[x3,#-1]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
sub x3,x19,#255
ldur w2,[x3,#255]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#256
ldursw x2,[x3,#-256]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#1
ldursw x2,[x3,#-1]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
sub x3,x19,#255
ldursw x2,[x3,#255]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#256
stur x2,[x3,#-256]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#1
stur x2,[x3,#-1]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
sub x3,x19,#255
stur x2,[x3,#255]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#256
ldur x2,[x3,#-256]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
add x3,x19,#1
ldur x2,[x3,#-1]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x2,#0x7788
movk x2,#0x5566,lsl #16
movk x2,#0x3344,lsl #32
movk x2,#0x1122,lsl #48
mov x4,#0x8081
movk x4,#0x8283,lsl #16
movk x4,#0x8485,lsl #32
movk x4,#0x8687,lsl #48
str x4,[x19]
sub x3,x19,#255
ldur x2,[x3,#255]
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x0,#0x64e
1:b 1b
