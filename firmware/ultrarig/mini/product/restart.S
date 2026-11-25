/* r0: an 80-byte update request. It is put where the bootloader looks for one after a restart (0x01C7FD88), with the boot status
 * before it cleared, and the chip restarts with the bit that the stock application and the entry guard use. The other core is
 * kept out as before the application's own jump to the ROM (phase3_p7_go_mask_usb_updata). Does not come back. */
.section .text.hyperrig_restart_with,"ax",@progbits
.global hyperrig_restart_with
.type hyperrig_restart_with,@function
hyperrig_restart_with:
    r4 = r0
    r5 = storage_coordination_irq_enter
    call r5
    r0 = L01c1fc4c
    r1 = cnum
    r1 = r1 << 2
    r0 += r1
    r2 = [r0+0]
    r3 = r2 + 1
    [r0+0] = r3
    if (r2 != 0) goto .Lkept_out
    lockset
.Lkept_out:
    csync
    r0 = 0x01c7fd80
    r1 = 0
    [r0+0] = r1
    [r0+4] = r1
    r1 = 20
.Lcopy:
    r2 = [r4+0]
    [r0+8] = r2
    r4 += 4
    r0 += 4
    r1 += -1
    if (r1 != 0) goto .Lcopy
    csync
    r0 = 0x00010000
    r1 = [r0]
    r1 |= 0x10
    [r0] = r1
    csync
.Lrestart:
    goto .Lrestart
.size hyperrig_restart_with, .-hyperrig_restart_with
