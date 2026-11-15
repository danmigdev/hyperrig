/* Diagnostic application entry through the stock MINI bootloader only.
 * All instructions stay in the inherited SFC window. No RAM code publication,
 * cache repartition, PLL switch, real IRQ or DMA is part of this experiment.
 * This must not be used for a ROM USB-uploaded RAM program. */
ENTRY(_start)
MEMORY
{
    FLASH (rx) : ORIGIN = 0x02000120, LENGTH = 0x0007DEE0
    RAM (rw)   : ORIGIN = 0x01C00000, LENGTH = 0x0007FD30
}
PHDRS
{
    flash PT_LOAD FLAGS(5);
    ram PT_LOAD FLAGS(6);
    bss PT_LOAD FLAGS(6);
    stacks PT_LOAD FLAGS(6);
}
SECTIONS
{
    .text ORIGIN(FLASH) :
    {
        __xip_text_start = .;
        KEEP(*(.entry))
        *(.text .text.*)
        /* Runtime's RAM annotations are unnecessary for the private-buffer
         * diagnostic. This does NOT make SFC-disabling routines XIP-safe. */
        __xip_ramtext_start = .;
        *(.ramtext .ramtext.*)
        __xip_ramtext_end = .;
        *(.rodata .rodata.*)
        KEEP(*(.capture))
        . = ALIGN(4);
        __xip_text_end = .;
    } > FLASH :flash
    .ram ORIGIN(RAM) : AT(ALIGN(LOADADDR(.text) + SIZEOF(.text), 4))
    {
        __ram_start = .;
        *(.ramdata .ramdata.* .data .data.*)
        . = ALIGN(4);
        __ram_end = .;
    } > RAM :ram
    __ram_load_start = LOADADDR(.ram);
    __ram_load_end = LOADADDR(.ram) + SIZEOF(.ram);
    __flash_image_end = __ram_load_end;
    .bss (NOLOAD) :
    {
        __bss_start = .;
        *(.bss .bss.* COMMON)
        . = ALIGN(32);
        *(.dma .dma.* .dma32 .dma32.*)
        . = ALIGN(4);
        __bss_end = .;
    } > RAM :bss
    .noinit (NOLOAD) :
    {
        __noinit_start = .;
        *(.noinit .noinit.*)
        . = ALIGN(4);
        __noinit_end = .;
    } > RAM :bss
    .stacks 0x01C7CD30 (NOLOAD) :
    {
        __stack_bottom = .;
        . += 0x2000;
        __stack_top = .;
        __ssp_bottom = .;
        . += 0x1000;
        __ssp_top = .;
    } > RAM :stacks
    __ram_region_start = ORIGIN(RAM);
    __ram_region_end = ORIGIN(RAM) + LENGTH(RAM);
    __boot_reserved_start = 0x01C7FD30;
    __boot_reserved_end = 0x01C80000;
    __hyperrig_boot_context = 0x01C7FD50;
    __irq_handler_table = 0x01C7FE00;
    __cpu1_entry_slot = 0x01C7FFF8;
    ASSERT(_start == 0x02000120, "MINI entry moved")
    ASSERT(((__ram_end - __ram_start) & 3) == 0, "RAM copy must be word aligned")
    ASSERT(((__bss_end - __bss_start) & 3) == 0, "BSS must be word aligned")
    ASSERT(__noinit_end <= __stack_bottom, "RAM state overlaps stacks")
    ASSERT(__ssp_top <= __boot_reserved_start, "Stacks overlap boot/IRQ reservation")
    ASSERT(__flash_image_end <= 0x0207E000, "Application exceeds MINI flash area")
    /DISCARD/ : { *(.comment .note* .eh_frame* .llvm_addrsig) }
}
