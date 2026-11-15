/* Return to normal ROM boot without modifying nonvolatile storage.
 * MINI stock writes usb_update_mode at 0x01c7fd80 before reset. Clear its
 * first word so that the marker cannot request download mode again.
 * MINI uboot reset at 0x01c028f4 sets RST_CON(0x10000) bit4.
 * This entry never returns; a lost USB reply is expected after the reset. */
.section .entry,"ax",@progbits
.global hyperrig_rom_reset
.type hyperrig_rom_reset,@function
hyperrig_rom_reset:
    r0 = 0x01c7fd80
    r1 = 0
    [r0] = r1
    csync
    r0 = 0x00010000
    r1 = [r0]
    r1 |= 0x10
    [r0] = r1
    csync
1:
    goto 1b
.size hyperrig_rom_reset, .-hyperrig_rom_reset
