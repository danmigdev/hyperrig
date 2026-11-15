/* USB ROM normal-call plugin; never an XIP application or bootloader image. */
ENTRY(hyperrig_reader_entry)
MEMORY { SLOT (rwx) : ORIGIN = READER_ADDRESS, LENGTH = 0x8000 }
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
    ASSERT(hyperrig_reader_entry == __slot_start, "reader entry must be the first uploaded byte")
    ASSERT(__bss_end <= __slot_end, "reader exceeds its own 32 KiB ROM slot")
    /DISCARD/ : { *(.comment .note* .eh_frame* .llvm_addrsig) }
}
