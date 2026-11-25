/* The UltraRig application image, in app.bin order: the flash text, the RAM image (run at 0x01c00000,
 * stored after the flash text) and the trailing table. Every bound follows the sizes of the sections, so the code
 * may grow; the unchanged source gives the original addresses. The MINI image builder links mini/append.ld after
 * this script, with the code it appends; the RAM data and the zeroed data of that code (mini/c) join the RAM image
 * and the bss here. The G target has none. */
SECTIONS {
  .flash 0x02000120 : { flash.o(.flash) }
  ultrarig_flash_text_end = .;
  .ram 0x01c00000 : AT(ALIGN(ultrarig_flash_text_end, 4)) {
    ram.o(.ram)
    *(.ram_text .ram_text.*)
    ultrarig_ram_code_end = .;
    *(.data .data.* .sdata .sdata.*)
  }
  ultrarig_ram_image_load = LOADADDR(.ram);
  ultrarig_ram_image_size = SIZEOF(.ram);
  /* The bss follows the RAM image and keeps the original start modulo 32 (0x01c2030c), and with it the
   * alignment of what it holds. The heap starts at its end aligned to 32 and ends at the fixed 0x01c7fba0. */
  ultrarig_bss_start = ADDR(.ram) + SIZEOF(.ram) + ((0x0c - (ADDR(.ram) + SIZEOF(.ram))) & 31);
  .bss ultrarig_bss_start (NOLOAD) : {
    ram.o(.bss)
    *(.bss .bss.* .sbss .sbss.* COMMON)
  }
  ultrarig_bss_size = SIZEOF(.bss);
  ultrarig_heap_start = ALIGN(ADDR(.bss) + SIZEOF(.bss), 32);
  .tail ALIGN(LOADADDR(.ram) + SIZEOF(.ram), 4) : AT(ALIGN(LOADADDR(.ram) + SIZEOF(.ram), 4)) { tail.o(.tail) }
  ultrarig_app_end = LOADADDR(.tail) + SIZEOF(.tail);
}
/* The end of the heap: fixed, below the boot area at the top of the RAM (the allocator holds it as a number). */
ultrarig_heap_end = 0x01c7fba0;
ASSERT(ultrarig_heap_start < ultrarig_heap_end, "the bss reaches the end of the heap")
/* A call to an undefined weak function, which the original link resolved to 0. */
ultrarig_absolute_00000000 = 0x0;
/* The entries and the end of the code the MINI image appends after app.bin, called by the MINI changes: their MINI
 * v4 addresses, unless the link holds that code (tools/build_hyperrig_mini_image.py with mini/append.ld). These
 * defaults let the MINI target build alone, as tools/build_ultrarig_app.py --target mini does. */
PROVIDE(hyperrig_mini_g_audio_pre_current_clock = 0x02076aac);
PROVIDE(hyperrig_mini_g_audio_post = 0x02076cd6);
PROVIDE(hyperrig_mini_entry_guard_v2 = 0x020773c8);
PROVIDE(hyperrig_mini_append_end = 0x020774f4);
