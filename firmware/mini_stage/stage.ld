/* The loader where the bootloader decompresses M-VAVE's: 0x01c0a800, no larger than that one (0x5b1c bytes). */
ENTRY(stage_entry)
MEMORY { ram (rwx) : ORIGIN = 0x1c0a800, LENGTH = 0xc000 }
SECTIONS {
    .text ORIGIN(ram) : {
        KEEP(*(.entry))
        *(.text .text.*) *(.rodata .rodata.*) *(.data .data.*)
        . = ALIGN(4);
    } > ram
    __payload_end = .;
    .bss (NOLOAD) : {
        . = ALIGN(16); __bss_start = .;
        *(.bss .bss.*) *(COMMON)
        . = ALIGN(16); __bss_end = .;
    } > ram
    .stacks (NOLOAD) : {
        __exception_stack_bottom = .; . += 1024; __exception_stack_top = .;
        __main_stack_bottom = .; . += 4096; __main_stack_top = .;
    } > ram
    __ram_end = .;
    /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) *(.llvm*) *(.debug*) }
}
ASSERT(__payload_end - ORIGIN(ram) <= 0x5b1c, "the loader exceeds the stock loader's size")
