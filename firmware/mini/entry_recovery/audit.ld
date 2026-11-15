/* Standalone XIP link for byte-level auditing, never a bootable app image.
 * The integrator must allocate actual append space before using this code. */
ENTRY(hyperrig_mini_entry_guard)
PHDRS { code PT_LOAD FLAGS(5); }
hyperrig_mini_g_startup_resume = 0x02000196;
SECTIONS {
    . = DEFINED(HYPERRIG_ENTRY_GUARD_ADDRESS) ? HYPERRIG_ENTRY_GUARD_ADDRESS : 0x02078000;
    .text : {
        KEEP(*(.text.hyperrig_mini_entry_guard))
        *(.text.hyperrig_mini_entry_recovery_check)
        *(.text.hyperrig_mini_entry_recovery_to_rom)
    } :code
    /DISCARD/ : { *(.comment) *(.note*) *(.llvm*) *(.debug*) }
}
ASSERT(SIZEOF(.text) < 1024, "Unexpected entry guard size")
