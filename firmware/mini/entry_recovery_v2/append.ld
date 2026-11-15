/* Position is mandatory and supplied by the append allocator. This is one
 * XIP component only, not an application/firmware installation image. */
ENTRY(hyperrig_mini_entry_guard_v2)
PHDRS { code PT_LOAD FLAGS(5); }
hyperrig_mini_g_startup_resume = 0x02000196;
SECTIONS {
    . = HYPERRIG_ENTRY_GUARD_ADDRESS;
    .text : {
        KEEP(*(.text.hyperrig_mini_entry_guard_v2))
        *(.text.hyperrig_mini_entry_recovery_check)
        *(.text.hyperrig_mini_entry_recovery_to_rom)
    } :code
    /DISCARD/ : { *(.comment) *(.note*) *(.llvm*) *(.debug*) }
}
ASSERT(DEFINED(HYPERRIG_ENTRY_GUARD_ADDRESS), "Explicit append address required")
ASSERT(HYPERRIG_ENTRY_GUARD_ADDRESS >= 0x02076aac, "Overlaps original G application")
ASSERT((HYPERRIG_ENTRY_GUARD_ADDRESS & 3) == 0, "Append entry must be word aligned")
ASSERT(SIZEOF(.text) < 1024, "Unexpected entry guard size")
ASSERT(HYPERRIG_ENTRY_GUARD_ADDRESS + SIZEOF(.text) <= 0x0207de81,
       "No space left for the unchanged cfg_tool.bin")
