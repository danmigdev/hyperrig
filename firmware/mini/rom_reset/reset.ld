ENTRY(hyperrig_rom_reset)
MEMORY { SLOT (rwx) : ORIGIN = PROBE_ADDRESS, LENGTH = 0x8000 }
PHDRS { image PT_LOAD FLAGS(5); }
SECTIONS
{
    .text ORIGIN(SLOT) : { KEEP(*(.entry)) } > SLOT :image
    ASSERT(hyperrig_rom_reset == PROBE_ADDRESS, "Reset entry moved")
    ASSERT(SIZEOF(.text) <= 64, "Reset exceeds reviewed instruction bound")
    /DISCARD/ : { *(.comment .note* .eh_frame* .llvm_addrsig) }
}
