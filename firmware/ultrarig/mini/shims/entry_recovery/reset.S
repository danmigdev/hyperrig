/* Same mailbox and reset bit as the pinned MINI SPL. No guessed ROM call,
 * watchdog, P33 transaction, flash opcode or clock change. For a deliberate
 * future RAM qualification only until its physical behavior is confirmed. */
.section .text.hyperrig_mini_entry_recovery_to_rom,"ax",@progbits
.global hyperrig_mini_entry_recovery_to_rom
.type hyperrig_mini_entry_recovery_to_rom,@function
hyperrig_mini_entry_recovery_to_rom:
    r0 = 0x01c7fd80
    r1 = 0x5f627375
    [r0+0] = r1
    r1 = 0x61647075
    [r0+4] = r1
    r1 = 0x6d5f6574
    [r0+8] = r1
    r1 = 0x0065646f
    [r0+12] = r1
    csync
    r0 = 0x00010000
    r1 = [r0]
    r1 |= 0x10
    [r0] = r1
    csync
.Lreset_wait:
    goto .Lreset_wait
.size hyperrig_mini_entry_recovery_to_rom, .-hyperrig_mini_entry_recovery_to_rom
