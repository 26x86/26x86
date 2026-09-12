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
mov x3,x19
strb w2,[x3],#-256
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
mov x3,x19
strb w2,[x3],#-1
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
mov x3,x19
strb w2,[x3],#255
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
strb w2,[x3,#-256]!
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
strb w2,[x3,#-1]!
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
strb w2,[x3,#255]!
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
mov x3,x19
ldrb w2,[x3],#-256
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
mov x3,x19
ldrb w2,[x3],#-1
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
mov x3,x19
ldrb w2,[x3],#255
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
ldrb w2,[x3,#-256]!
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
ldrb w2,[x3,#-1]!
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
ldrb w2,[x3,#255]!
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
mov x3,x19
ldrsb x2,[x3],#-256
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
mov x3,x19
ldrsb x2,[x3],#-1
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
mov x3,x19
ldrsb x2,[x3],#255
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
ldrsb x2,[x3,#-256]!
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
ldrsb x2,[x3,#-1]!
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
ldrsb x2,[x3,#255]!
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
mov x3,x19
ldrsb w2,[x3],#-256
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
mov x3,x19
ldrsb w2,[x3],#-1
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
mov x3,x19
ldrsb w2,[x3],#255
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
ldrsb w2,[x3,#-256]!
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
ldrsb w2,[x3,#-1]!
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
ldrsb w2,[x3,#255]!
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
mov x3,x19
strh w2,[x3],#-256
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
mov x3,x19
strh w2,[x3],#-1
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
mov x3,x19
strh w2,[x3],#255
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
strh w2,[x3,#-256]!
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
strh w2,[x3,#-1]!
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
strh w2,[x3,#255]!
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
mov x3,x19
ldrh w2,[x3],#-256
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
mov x3,x19
ldrh w2,[x3],#-1
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
mov x3,x19
ldrh w2,[x3],#255
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
ldrh w2,[x3,#-256]!
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
ldrh w2,[x3,#-1]!
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
ldrh w2,[x3,#255]!
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
mov x3,x19
ldrsh x2,[x3],#-256
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
mov x3,x19
ldrsh x2,[x3],#-1
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
mov x3,x19
ldrsh x2,[x3],#255
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
ldrsh x2,[x3,#-256]!
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
ldrsh x2,[x3,#-1]!
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
ldrsh x2,[x3,#255]!
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
mov x3,x19
ldrsh w2,[x3],#-256
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
mov x3,x19
ldrsh w2,[x3],#-1
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
mov x3,x19
ldrsh w2,[x3],#255
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
ldrsh w2,[x3,#-256]!
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
ldrsh w2,[x3,#-1]!
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
ldrsh w2,[x3,#255]!
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
mov x3,x19
str w2,[x3],#-256
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
mov x3,x19
str w2,[x3],#-1
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
mov x3,x19
str w2,[x3],#255
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
str w2,[x3,#-256]!
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
str w2,[x3,#-1]!
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
str w2,[x3,#255]!
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
mov x3,x19
ldr w2,[x3],#-256
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
mov x3,x19
ldr w2,[x3],#-1
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
mov x3,x19
ldr w2,[x3],#255
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
ldr w2,[x3,#-256]!
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
ldr w2,[x3,#-1]!
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
ldr w2,[x3,#255]!
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
mov x3,x19
ldrsw x2,[x3],#-256
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
mov x3,x19
ldrsw x2,[x3],#-1
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
mov x3,x19
ldrsw x2,[x3],#255
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
ldrsw x2,[x3,#-256]!
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
ldrsw x2,[x3,#-1]!
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
ldrsw x2,[x3,#255]!
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
mov x3,x19
str x2,[x3],#-256
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
mov x3,x19
str x2,[x3],#-1
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
mov x3,x19
str x2,[x3],#255
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
str x2,[x3,#-256]!
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
str x2,[x3,#-1]!
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
str x2,[x3,#255]!
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
mov x3,x19
ldr x2,[x3],#-256
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
mov x3,x19
ldr x2,[x3],#-1
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
mov x3,x19
ldr x2,[x3],#255
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
ldr x2,[x3,#-256]!
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
ldr x2,[x3,#-1]!
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
ldr x2,[x3,#255]!
str x2,[x18],#8
ldr x4,[x19]
str x4,[x18],#8
sub x4,x3,x19
str x4,[x18],#8
mov x0,#0x64e
1:b 1b
