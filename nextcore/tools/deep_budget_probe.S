// Independently authored BP35 budget observation; no vendor bytes.
.text
.global probe_start
probe_start:
    movz x3, #0x35
loop:
    add x0, x0, #1
    b loop
