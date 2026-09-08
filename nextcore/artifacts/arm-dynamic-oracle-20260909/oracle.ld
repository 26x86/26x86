ENTRY(_start)
SECTIONS {
 . = 0x40080000;
 .text : { *(.text.start) *(.text*) }
 .rodata : { *(.rodata*) }
 .data : { *(.data*) }
 .bss (NOLOAD) : { *(.bss*) *(COMMON) }
 _image_end = .;
}
