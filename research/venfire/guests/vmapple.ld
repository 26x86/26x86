ENTRY(_boot)
SECTIONS {
    .boot 0x00100000 : { *(.boot) }
    .text 0x70000000 : AT(0x00100100) { *(.text) }
    __payload_start = ADDR(.text);
    __payload_load = LOADADDR(.text);
    __payload_size = SIZEOF(.text);
    ASSERT(SIZEOF(.boot) <= 0x100, "boot trampoline exceeds reserved size")
    ASSERT(SIZEOF(.text) + 0x100 <= 0x100000, "firmware exceeds 1 MiB")
    /DISCARD/ : { *(.comment) *(.note*) }
}
