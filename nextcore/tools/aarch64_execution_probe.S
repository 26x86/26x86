// Authored AArch64 program for execution evidence. No vendor firmware input.
.text
.global _start
_start:
    mov x0, #42
1:
    wfi
    b 1b
