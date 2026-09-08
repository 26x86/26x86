.arch armv8.3-a
.text
.global _start
_start:
movz x10, #0
movk x10, #0, lsl #16
movk x10, #0, lsl #32
movk x10, #0, lsl #48
movz x11, #0
movk x11, #0, lsl #16
movk x11, #0, lsl #32
movk x11, #0, lsl #48
msr APGAKeyLo_EL1,x10
msr APGAKeyHi_EL1,x11
isb
movz x4, #0
movk x4, #0, lsl #16
movk x4, #0, lsl #32
movk x4, #0, lsl #48
movz x3, #0
movk x3, #0, lsl #16
movk x3, #0, lsl #32
movk x3, #0, lsl #48
pacga x4,x4,x3
mov x20,x4
movz x10, #65535
movk x10, #65535, lsl #16
movk x10, #65535, lsl #32
movk x10, #65535, lsl #48
movz x11, #65535
movk x11, #65535, lsl #16
movk x11, #65535, lsl #32
movk x11, #65535, lsl #48
msr APGAKeyLo_EL1,x10
msr APGAKeyHi_EL1,x11
isb
movz x4, #65535
movk x4, #65535, lsl #16
movk x4, #65535, lsl #32
movk x4, #65535, lsl #48
movz x3, #65535
movk x3, #65535, lsl #16
movk x3, #65535, lsl #32
movk x3, #65535, lsl #48
pacga x4,x4,x3
mov x21,x4
movz x10, #35049
movk x10, #57508, lsl #16
movk x10, #724, lsl #32
movk x10, #60456, lsl #48
movz x11, #59723
movk x11, #38916, lsl #16
movk x11, #34254, lsl #32
movk x11, #33982, lsl #48
msr APGAKeyLo_EL1,x10
msr APGAKeyHi_EL1,x11
isb
movz x4, #33063
movk x4, #55918, lsl #16
movk x4, #13721, lsl #32
movk x4, #64354, lsl #48
movz x3, #34658
movk x3, #60427, lsl #16
movk x3, #18077, lsl #32
movk x3, #18301, lsl #48
pacga x4,x4,x3
mov x22,x4
movz x10, #4951
movk x10, #9320, lsl #16
movk x10, #13980, lsl #32
movk x10, #18605, lsl #48
movz x11, #60584
movk x11, #56215, lsl #16
movk x11, #51555, lsl #32
movk x11, #46930, lsl #48
msr APGAKeyLo_EL1,x10
msr APGAKeyHi_EL1,x11
isb
movz x4, #304
movk x4, #0, lsl #16
movk x4, #0, lsl #32
movk x4, #0, lsl #48
movz x3, #39030
movk x3, #0, lsl #16
movk x3, #0, lsl #32
movk x3, #0, lsl #48
pacga x4,x4,x3
mov x23,x4
movz x10, #4369
movk x10, #4369, lsl #16
movk x10, #4369, lsl #32
movk x10, #4369, lsl #48
movz x11, #34952
movk x11, #34952, lsl #16
movk x11, #34952, lsl #32
movk x11, #34952, lsl #48
msr APGAKeyLo_EL1,x10
msr APGAKeyHi_EL1,x11
isb
movz x4, #52719
movk x4, #35243, lsl #16
movk x4, #17767, lsl #32
movk x4, #291, lsl #48
movz x3, #12816
movk x3, #30292, lsl #16
movk x3, #47768, lsl #32
movk x3, #65244, lsl #48
pacga x4,x4,x3
mov x24,x4
movz x10, #2
movk x10, #0, lsl #16
movk x10, #0, lsl #32
movk x10, #0, lsl #48
movz x11, #4
movk x11, #0, lsl #16
movk x11, #0, lsl #32
movk x11, #0, lsl #48
msr APGAKeyLo_EL1,x10
msr APGAKeyHi_EL1,x11
isb
movz x4, #0
movk x4, #0, lsl #16
movk x4, #0, lsl #32
movk x4, #32768, lsl #48
movz x3, #1
movk x3, #0, lsl #16
movk x3, #0, lsl #32
movk x3, #0, lsl #48
pacga x4,x4,x3
mov x25,x4
movz x10, #30600
movk x10, #21862, lsl #16
movk x10, #13124, lsl #32
movk x10, #4386, lsl #48
movz x11, #8721
movk x11, #17459, lsl #16
movk x11, #26197, lsl #32
movk x11, #34935, lsl #48
msr APGAKeyLo_EL1,x10
msr APGAKeyHi_EL1,x11
isb
movz x4, #52719
movk x4, #35243, lsl #16
movk x4, #17767, lsl #32
movk x4, #291, lsl #48
movz x3, #28800
movk x3, #20576, lsl #16
movk x3, #12352, lsl #32
movk x3, #4128, lsl #48
pacga x4,x4,x3
mov x26,x4
movz x10, #0
movk x10, #0, lsl #16
movk x10, #0, lsl #32
movk x10, #0, lsl #48
movz x11, #65535
movk x11, #65535, lsl #16
movk x11, #65535, lsl #32
movk x11, #65535, lsl #48
msr APGAKeyLo_EL1,x10
msr APGAKeyHi_EL1,x11
isb
movz x4, #43690
movk x4, #43690, lsl #16
movk x4, #43690, lsl #32
movk x4, #43690, lsl #48
movz x3, #21845
movk x3, #21845, lsl #16
movk x3, #21845, lsl #32
movk x3, #21845, lsl #48
pacga x4,x4,x3
mov x27,x4
mov x0,#0x64e
1: b 1b
