ENTRY(hyperrig_mini_g_audio_pre_current_clock)
PHDRS { code PT_LOAD FLAGS(5); }
SECTIONS {
    . = AUDIO_PORT_ADDRESS;
    __audio_port_start = .;
    .text : { *(.text .text.*) } :code
    .rodata : ALIGN(4) { *(.rodata .rodata.* .data.rel.ro .data.rel.ro.*) } :code
    .data : { *(.data .data.* .sdata .sdata.*) } :code
    .bss (NOLOAD) : { *(.bss .bss.* .sbss .sbss.* COMMON) } :code
    __audio_port_end = .;
    /DISCARD/ : { *(.comment .note.* .eh_frame .llvm_addrsig) }
}
ASSERT(SIZEOF(.data) == 0, "audio port needs a RAM data copy")
ASSERT(SIZEOF(.bss) == 0, "audio port needs a RAM BSS reservation")
ASSERT(__audio_port_end <= AUDIO_PORT_LIMIT, "audio append exceeds MINI cfg limit")
