// Independently authored finite-budget loop; no original OS instructions.
.text
.global probe_start
probe_start:
    mov x3, #0x29
loop:
    add x0, x0, #1
    b loop
