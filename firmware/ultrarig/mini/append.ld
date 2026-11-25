/* The code the HyperRig MINI image appends after app.bin, placed by the same link as the application:
 * tools/build_hyperrig_mini_image.py links with app.ld, then with this script. The code runs in place from flash,
 * after the application's trailing table, word aligned:
 * - the audio shim v2 (mini/shims): its code, then its constants, word aligned;
 * - the any-one-footswitch entry guard (mini/shims), word aligned;
 * - the code and the constants of the files in mini/c, word aligned.
 * The data and the zeroed data of mini/c go into the RAM image and the bss (app.ld).
 * The object paths are relative to the link directory: audio/, guard/ and c/. In the original MINI v4 build the
 * shim and the guard were two links of their own (audio_port.ld and append.ld in firmware/mini); this script
 * gives the same bytes at the same addresses. */
SECTIONS {
  .append ALIGN(ultrarig_app_end, 4) : AT(ALIGN(ultrarig_app_end, 4)) {
    hyperrig_mini_audio_start = .;
    audio/*.o(.text .text.*)
    . = ALIGN(4);
    audio/*.o(.rodata .rodata.* .data.rel.ro .data.rel.ro.*)
    hyperrig_mini_audio_end = .;
    . = ALIGN(4);
    hyperrig_mini_guard_start = .;
    KEEP(guard/*.o(.text.hyperrig_mini_entry_guard_v2))
    guard/*.o(.text.hyperrig_mini_entry_recovery_check)
    guard/*.o(.text.hyperrig_mini_entry_recovery_to_rom)
    hyperrig_mini_guard_end = .;
    . = ALIGN(4);
    hyperrig_mini_c_start = .;
    c/*.o(.text .text.* .rodata .rodata.* .data.rel.ro .data.rel.ro.*)
    hyperrig_mini_c_end = .;
  }
  /* The end of the flash code: the protection set-up of the MINI changes bounds the flash execution range with it. */
  hyperrig_mini_append_end = LOADADDR(.append) + SIZEOF(.append);
  /DISCARD/ : { *(.comment) *(.note*) *(.llvm*) *(.debug*) *(.eh_frame) }
}
ASSERT(hyperrig_mini_guard_end - hyperrig_mini_guard_start < 1024, "Unexpected entry guard size")
