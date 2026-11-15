/* Slots exercised by the AC791N ROM hwtest reference, not application RAM. */
ENTRY(hyperrig_rom_entry)
MEMORY { SLOT (rwx) : ORIGIN = PROBE_ADDRESS, LENGTH = 0x8000 }
PHDRS { image PT_LOAD FLAGS(7); }
SECTIONS
{
    __slot_start = ORIGIN(SLOT);
    __slot_end = ORIGIN(SLOT) + LENGTH(SLOT);
    .text ORIGIN(SLOT) : {
        KEEP(*(.entry))
        *(.text .text.* .rodata .rodata.*)
        . = ALIGN(4);
    } > SLOT :image
    .data : { *(.data .data.*) . = ALIGN(4); } > SLOT :image
    __image_file_end = .;
    .bss (NOLOAD) : {
        __bss_start = .;
        *(.bss .bss.* COMMON)
        . = ALIGN(4);
        __bss_end = .;
    } > SLOT :image
    ASSERT(hyperrig_rom_entry == __slot_start, "ROM entry must be the first payload byte")
    ASSERT(__bss_end <= __slot_end, "ROM probe exceeds its own upload slot")
    /DISCARD/ : { *(.comment .note* .eh_frame* .llvm_addrsig) }
}
