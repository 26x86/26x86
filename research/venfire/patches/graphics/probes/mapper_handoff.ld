ENTRY(_start)
SECTIONS {
    .text 0x00100000 : { *(.text) }
    /DISCARD/ : { *(.comment) *(.note*) }
}
