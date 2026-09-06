ENTRY(vf_fixture_entry)
PHDRS { text PT_LOAD FLAGS(5); data PT_LOAD FLAGS(6); }
SECTIONS {
  . = 0x20000000;
  .text : ALIGN(4096) { *(.text*) } :text
  . = ALIGN(4096);
  .data : { *(.data*) } :data
  .bss : { *(.bss*) *(COMMON) } :data
  /DISCARD/ : { *(.eh_frame*) *(.comment*) *(.note*) }
}
