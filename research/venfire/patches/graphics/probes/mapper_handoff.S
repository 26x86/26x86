/* SPDX-License-Identifier: MIT
 * Self-authored MMIO handoff experiment. No Apple firmware or kernel code.
 * Only publish a synthetic ring entry; its fake internal address is rejected.
 */
.arch armv8.3-a
.section .text, "ax"
.global _start
_start:
    msr daifset, #15
    /* A 16-byte synthetic MAP request at the start of VMApple RAM. */
    ldr x0, =0x71000000
    mov w1, #1
    str w1, [x0]
    mov w1, #0x1234
    str w1, [x0, #4]
    str xzr, [x0, #8]
    dsb sy
    /* IOSFC ring base, capacity, and producer from the pinned Reims contract. */
    ldr x1, =0x30211000
    str x0, [x1]
    mov w2, #1
    str w2, [x1, #8]
    ldr x19, =0xfffffe0011223344
    mov x21, #1
    ldr x22, =0x5566778899aabbcc
    str w2, [x1, #0x18]
    dsb sy
    /* Always emit that the guest returned from the real MMIO call. Host trace
     * must separately prove which values the Rust mapper actually received. */
    adr x2, done
    ldr x3, =0x20010000
1:  ldrb w4, [x2], #1
    cbz w4, 2f
    str w4, [x3]
    b 1b
2:  ldr x1, =0x71000100
    ldr x0, =0x20026
    stp x0, xzr, [x1]
    mov x0, #0x20
    hlt #0xf000
3:  wfe
    b 3b
.ltorg
done:
    .asciz "VENFIRE_GPU|MAPPER_MMIO_RETURNED\n"
