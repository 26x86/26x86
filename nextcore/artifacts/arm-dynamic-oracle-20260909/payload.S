.section .text.payload,"ax"
.balign 4
.global transition_words, transition_end
transition_words:
    msr sctlr_el1, x0
    isb sy
transition_end:
.global target_words, target_end
target_words:
    mrs x10, sctlr_el1
    adr x11, .
    ldr x12, [x1]
    str x2, [x1, #8]
    dsb sy
    tlbi vmalle1
    dsb sy
    isb sy
    ldr x13, [x1, #8]
    mov x14, #0x34
    hvc #0x34
    b .
target_end:
.global decoy_words, decoy_end
decoy_words:
    mov x14, #0xbad
    hvc #0x34
    b .
decoy_end:
