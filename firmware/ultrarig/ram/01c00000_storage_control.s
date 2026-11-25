; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; storage_control: 30 functions, 0x01c00000..0x01c008b4

; storage_control_bus_enter: 0x01c00000..0x01c00072, module storage-control (bus_enter)
.type storage_control_bus_enter,@function
storage_control_bus_enter:
    [--sp] = {rets, r5, r4}
    r5 = L01c26890
    r0 = r5 + 3748
    call L02040614  ; @call.xl
    r0 = b[r5+67] (u)
    r4 = L01c3743c
    r1 = b[r4+17] (u)
    r0 += 1  ; @add.ri.u5
    b[r5+67] = r0
    if (r1 != 0) goto L01c00030
    r1_r0 = 0
    call storage_platform_enter  ; @call.xl
L01c00030:
    r0 = 1
    b[r5+66] = r0
    r1 = 262656
    r0 = [r1+0]
    r0 = 0x11C00  #
    [r4+56] = r0
    r2 = [r0+0]
    [r4+60] = r2
    r2 = [r1+0]
    csync
L01c0004c:
    r2 = [r1+0]
    ifs (r2 < 0) goto L01c0004c
    r2 = 0
    [r1+0] = r2
    r1 = 331804
    [r1+0] &= 0xFFFFFFDF
    [r0+0] = r2
    r1 = [r4+64]
    if (r1 != 0) goto L01c0006c
    r1 = 4137
L01c0006c:
    [r0+0] = r1
    csync
    {pc, r5, r4} = [sp++]

; storage_control_delay: 0x01c00072..0x01c00088, module storage-control (delay)
.type storage_control_delay,@function
storage_control_delay:
    sp += -4
    [sp] = r0
    goto L01c0007a
L01c00078:
    nop
L01c0007a:
    r0 = [sp]
    r1 = r0 + -1
    [sp] = r1
    if (r0 != 0) goto L01c00078
    sp += 4
    rts

; storage_control_chip_select: 0x01c00088..0x01c000a8, module storage-control (chip_select)
.type storage_control_chip_select,@function
storage_control_chip_select:
    [--sp] = rets
    r1 = 327872
    [r1+8] &= 0xFFFFFFFE
    r2 = [r1+0]
    r3 = r2 | 0x1
    r2 &= 4294967294
    if (r0 == 0) goto L01c000a0
    r2 = r3
L01c000a0:
    [r1+0] = r2
    r0 = 10
    call storage_control_delay
    pc = [sp++]

; storage_control_transfer_wait: 0x01c000a8..0x01c000d8, module storage-control (transfer_wait)
.type storage_control_transfer_wait,@function
storage_control_transfer_wait:
    sp += -4
    r0 = 50000000
    [sp] = r0
    csync
    r0 = 0x11C00
L01c000b8:
    r1 = [r0+0]
    r1 = r1.l (s)
    ifs (r1 < 0) goto L01c000c8
    r1 = [sp]
    r1 += -1
    [sp] = r1
    if (r1 != 0) goto L01c000b8
L01c000c8:
    [r0+0] |= 0x4000
    r1 = [sp]
    r0 = -1
    if (r1 == 0) goto L01c000d4
    r0 = 0
L01c000d4:
    sp += 4
    rts

; storage_control_send_byte: 0x01c000d8..0x01c000f0, module storage-control (send_byte)
.type storage_control_send_byte,@function
storage_control_send_byte:
    [--sp] = rets
    r2 = 0x11C00
    [r2+0] |= 0x8
    [r2+0] &= 0xFFFFEFFF
    [r2+8] = r0
    call storage_control_transfer_wait
    [r2+0] &= 0xFFFFFFF7
    pc = [sp++]

; storage_control_leave_continuous: 0x01c000f0..0x01c0012e, module storage-control (leave_continuous)
.type storage_control_leave_continuous,@function
storage_control_leave_continuous:
    [--sp] = {rets, r4}
    r0 = L01c3743c
    r0 = [r0+56]
    if (r0 != 0) goto L01c00104
    r0 = 262656
    r0 = [r0+0]
L01c00104:
    r0 = uextra(r0, p:8, l:4)
    if (r0 == 6) goto L01c00118
    r4 = 0
    if (r0 != 7) goto L01c0012a
    r0 = 0
    call storage_control_chip_select
    goto L01c00120
L01c00118:
    r0 = 0
    call storage_control_chip_select
    r0 = 255
    call storage_control_send_byte
L01c00120:
    r0 = 255
    call storage_control_send_byte
    r0 = 1
    r4 = 1
    call storage_control_chip_select
L01c0012a:
    r0 = r4
    {pc, r4} = [sp++]

; storage_control_receive_byte: 0x01c0012e..0x01c0014c, module storage-control (receive_byte)
.type storage_control_receive_byte,@function
storage_control_receive_byte:
    [--sp] = rets
    r2 = 0x11C00
    [r2+0] |= 0x8
    [r2+0] |= 0x1000
    [r2+8] = 0xFF
    call storage_control_transfer_wait
    r0 = [r2+8]
    [r2+0] &= 0xFFFFFFF7
    r0 = r0.b0 (u)
    pc = [sp++]

; storage_control_send_address: 0x01c0014c..0x01c00170, module storage-control (send_address)
.type storage_control_send_address,@function
storage_control_send_address:
    [--sp] = rets
    r1 = L01c3748c
    r3 = r0  #
    r1 = b[r1+0] (u)
    if (r1 == 0) goto L01c0015e
    r0 = r3 >> 24
    call storage_control_send_byte
L01c0015e:
    r0 = uextra(r3, p:16, l:8)
    call storage_control_send_byte
    r0 = uextra(r3, p:8, l:8)
    call storage_control_send_byte
    r0 = r3.b0 (u)
    call storage_control_send_byte
    pc = [sp++]

; storage_control_receive_fast: 0x01c00170..0x01c00184, module storage-control (receive_fast)
.type storage_control_receive_fast,@function
storage_control_receive_fast:
    [--sp] = rets
    r2 = 72712
    [r2+0] = 0xFF
    call storage_control_transfer_wait
    r0 = [r2+0]
    r0 = r0.b0 (u)
    pc = [sp++]

; storage_control_receive_buffer: 0x01c00184..0x01c00204, module storage-control (receive_buffer)
.type storage_control_receive_buffer,@function
storage_control_receive_buffer:
    [--sp] = {rets, r6-r4}
    r2 = L01c3743c
    r3 = r1  #
    r2 = [r2+56]
    r4 = r0
    if (r2 != 0) goto L01c0019c
    r0 = 262656
    r2 = [r0+0]
L01c0019c:
    r5 = 0x11C00
    [r5+0] |= 0x1000
    r0 = uextra(r2, p:8, l:4)
    if (r0 > 9) goto L01c001f6
    r1 = 340
    r1 = r1 & (1 << r0)
    if (r1 != 0) goto L01c001cc
    r1 = 680
    r0 = r1 & (1 << r0)
    if (r0 == 0) goto L01c001f6
    [r5+0] &= 0xFFFFF9F7
    r0 = [r5+0]
    r0 = r0 | 0x900
    goto L01c001d8
L01c001cc:
    r0 = -2825
    [r5+0] &= r0
    r0 = [r5+0]
    r0 |= 1024
L01c001d8:
    r6 = 4
L01c001da:
    [r5+0] = r0
    goto L01c001e4
L01c001de:
    call storage_control_receive_fast
    b[r4++=1] = r0
    r3 += -1
L01c001e4:
    r0 = r3.l (u)
    if (r0 != 0) goto L01c001de
    if (r6 == 0) goto L01c001f2
    [r5+0] &= 0xFFFFF0FF
    [r5+0] |= 0x8
L01c001f2:
    r0 = 0
    {pc, r6-r4} = [sp++]
L01c001f6:
    [r5+0] |= 0x8
    r0 = [r5+0]
    r0 = r0 & 0xFFFFF0FF
    r6 = 0
    goto L01c001da

; storage_control_send_fast: 0x01c00204..0x01c00214, module storage-control (send_fast)
.type storage_control_send_fast,@function
storage_control_send_fast:
    [--sp] = rets
    r1 = 72712
    [r1+0] = r0
    call storage_control_transfer_wait
    pc = [sp++]

; storage_control_send_buffer: 0x01c00214..0x01c00290, module storage-control (send_buffer)
.type storage_control_send_buffer,@function
storage_control_send_buffer:
    [--sp] = {rets, r5, r4}
    r2 = L01c3743c
    r2 = r1  #
    r5 = [r2+56]
    r3 = r0
    if (r5 != 0) goto L01c0022c
    r0 = 262656
    r5 = [r0+0]
L01c0022c:
    r4 = 0x11C00
    [r4+0] &= 0xFFFFEFFF
    r0 = uextra(r5, p:8, l:4)
    if (r0 > 9) goto L01c00282
    r1 = 340
    r1 = r1 & (1 << r0)
    if (r1 != 0) goto L01c0025c
    r1 = 680
    r0 = r1 & (1 << r0)
    if (r0 == 0) goto L01c00282
    [r4+0] &= 0xFFFFF9F7
    r0 = [r4+0]
    r0 = r0 | 0x900
    goto L01c00268
L01c0025c:
    r0 = -2825
    [r4+0] &= r0
    r0 = [r4+0]
    r0 |= 1024
L01c00268:
    r5 = 4
L01c0026a:
    [r4+0] = r0
    goto L01c00274
L01c0026e:
    r0 = b[r3++=1] (u)
    call storage_control_send_fast
    r2 += -1
L01c00274:
    r0 = r2.l (u)
    if (r0 != 0) goto L01c0026e
    if (r5 == 0) goto L01c0027e
    [r4+0] &= 0xFFFFF0FF
L01c0027e:
    r0 = 0
    {pc, r5, r4} = [sp++]
L01c00282:
    [r4+0] |= 0x8
    r0 = [r4+0]
    r0 = r0 & 0xFFFFF0FF
    r5 = 0
    goto L01c0026a

; storage_control_transfer_read: 0x01c00290..0x01c003d4, module storage-control (transfer_read)
.type storage_control_transfer_read,@function
storage_control_transfer_read:
    [--sp] = {rets, r8-r4}
    sp += -4
    r4 = L01c3743c
    r7 = r3  #
    r5 = [r4+56]
    r4 = r2
    r6 = r1
    r8 = r0
    if (r5 != 0) goto L01c002ae
    r0 = 262656
    r5 = [r0+0]
L01c002ae:
    r0 = sextra(r5, p:8, l:4)
    ifs (r0 < 0) goto L01c002d8
    r0 = uextra(r5, p:8, l:4)
    tbb [r0]
storage_read_modes:
    .byte (L01c002c4 - storage_read_modes) / 2, (L01c002dc - storage_read_modes) / 2, (L01c002f4 - storage_read_modes) / 2, (L01c0030c - storage_read_modes) / 2, (L01c00324 - storage_read_modes) / 2, (L01c00340 - storage_read_modes) / 2, (L01c0035c - storage_read_modes) / 2, (L01c0038a - storage_read_modes) / 2
L01c002c4:
    r0 = 0
    call storage_control_chip_select
    r0 = 3
    call storage_control_send_byte
    r0 = r6
    call storage_control_send_address
    goto L01c003c0
L01c002d8:
    r4 = -1
    goto L01c003ce
L01c002dc:
    r0 = 0
    call storage_control_chip_select
    r0 = 11
    call storage_control_send_byte
    r0 = r6
    call storage_control_send_address
    call storage_control_receive_byte
    goto L01c003c0
L01c002f4:
    r0 = 0
    call storage_control_chip_select
    r0 = 59
    call storage_control_send_byte
    r0 = r6
    call storage_control_send_address
    r0 = sp + 0
    r1 = 2
    goto L01c003bc
L01c0030c:
    r0 = 0
    call storage_control_chip_select
    r0 = 107
    call storage_control_send_byte
    r0 = r6
    call storage_control_send_address
    r0 = sp + 0
    r1 = 4
    goto L01c003bc
L01c00324:
    r0 = r6 >> 16
    b[sp] = r0
    r0 = r6 >> 8
    b[sp+1] = r0
    b[sp+2] = r6
    r0 = 0
    b[sp+3] = r0
    call storage_control_chip_select
    goto L01c0037a
L01c00340:
    r0 = r6 >> 16
    b[sp] = r0
    r0 = r6 >> 8
    b[sp+1] = r0
    b[sp+2] = r6
    r0 = 0
    b[sp+3] = r0
    call storage_control_chip_select
    goto L01c003a8
L01c0035c:
    r0 = r6 >> 16
    b[sp] = r0
    r0 = r6 >> 8
    b[sp+1] = r0
    b[sp+2] = r6
    r0 = 160
    b[sp+3] = r0
    r0 = 0
    call storage_control_chip_select
    if (r7 == 0) goto L01c00380
L01c0037a:
    r0 = 187
    call storage_control_send_byte
L01c00380:
    r0 = sp + 0
    r1 = 4
    call storage_control_send_buffer
    goto L01c003c0
L01c0038a:
    r0 = r6 >> 16
    b[sp] = r0
    r0 = r6 >> 8
    b[sp+1] = r0
    b[sp+2] = r6
    r0 = 160
    b[sp+3] = r0
    r0 = 0
    call storage_control_chip_select
    if (r7 == 0) goto L01c003ae
L01c003a8:
    r0 = 235
    call storage_control_send_byte
L01c003ae:
    r6 = sp + 0
    r1 = 4
    r0 = r6
    call storage_control_send_buffer
    r1 = 2
    r0 = r6
L01c003bc:
    call storage_control_receive_buffer
L01c003c0:
    r0 = r8
    r1 = r4
    call storage_control_receive_buffer
    r0 = 1
    call storage_control_chip_select
L01c003ce:
    r0 = r4
    sp += 4
    {pc, r8-r4} = [sp++]

; storage_control_restore_read: 0x01c003d4..0x01c003e8, module storage-control (restore_read)
.type storage_control_restore_read,@function
storage_control_restore_read:
    [--sp] = rets
    sp += -4
    r0 = sp + 0
    r1 = 0
    r2 = 1
    r3 = 1
    call storage_control_transfer_read
    sp += 4
    pc = [sp++]

; storage_control_bus_leave: 0x01c003e8..0x01c0044c, module storage-control (bus_leave)
.type storage_control_bus_leave,@function
storage_control_bus_leave:
    [--sp] = {rets, r4}
    r4 = L01c26890
    b[r4+66] = r0
    r0 = L01c3743c
    r2 = [r0+56]
    r1 = 262656
    if (r2 != 0) goto L01c00406
    r2 = [r1+0]
L01c00406:
    r3 = 0x11C00  #
    r2 = [r0+60]
    [r3+0] = r2
    r2 = 331804
    [r2+0] |= 0x20
    csync
L01c0041a:
    r2 = [r1+0]
    ifs (r2 < 0) goto L01c0041a
    r2 = [r0+56]
    [r1+0] = r2
    [r0+56] = 0x0
    csync
    r0 = b[r0+17] (u)
    if (r0 != 0) goto L01c00436
    call storage_platform_leave  ; @call.xl
L01c00436:
    r0 = b[r4+67] (u)
    r0 += -1
    b[r4+67] = r0
    r0 = r4 + 3748
    call L0204074c  ; @call.xl
    {pc, r4} = [sp++]

; storage_control_identify: 0x01c0044c..0x01c004d0, module storage-control (identify)
.type storage_control_identify,@function
storage_control_identify:
    [--sp] = {rets, r6-r4}
    call storage_control_bus_enter
    call storage_control_leave_continuous
    r4 = r0
    r0 = 0
    r6 = 0
    call storage_control_chip_select
    r0 = 159
    call storage_control_send_byte
    r5 = L01c3743c
    [r5+28] = r6
    r3 = 3
    goto L01c00480
L01c00472:
    call storage_control_receive_byte
    r1 = [r5+28]
    r0 |= r1
    r0 = r0 << 8
    [r5+28] = r0
    r3 += -1
L01c00480:
    if (r3 != 0) goto L01c00472
    r0 = 1
    call storage_control_chip_select
    r0 = 0
    call storage_control_chip_select
    r0 = 75
    call storage_control_send_byte
    r0 = 0
    call storage_control_send_byte
    r0 = 0
    call storage_control_send_byte
    r0 = 0
    call storage_control_send_byte
    r0 = 0
    call storage_control_send_byte
    goto L01c004b8
L01c004ae:
    call storage_control_receive_byte
    b[r6+r5] = r0
    r6 += 1  ; @add.ri.u5
L01c004b8:
    if (r6 != 16) goto L01c004ae
    r0 = 1
    call storage_control_chip_select
    if (r4 == 0) goto L01c004c6
    call storage_control_restore_read
L01c004c6:
    [r5+28] >>= 8
    r0 = 0
    call storage_control_bus_leave
    {pc, r6-r4} = [sp++]

; storage_control_status_read: 0x01c004d0..0x01c0050a, module storage-control (status_read)
.type storage_control_status_read,@function
storage_control_status_read:
    [--sp] = {rets, r5, r4}
    r0 = 0
    call storage_control_chip_select
    r0 = 5
    call storage_control_send_byte
    call storage_control_receive_byte
    r4 = r0
    r0 = 1
    call storage_control_chip_select
    r0 = 0
    call storage_control_chip_select
    r0 = 53
    call storage_control_send_byte
    call storage_control_receive_byte
    r5 = r0
    r0 = 1
    call storage_control_chip_select
    r4 <= insert(r5, p:8, l:8)
    r0 = r4
    {pc, r5, r4} = [sp++]

; storage_control_status_capture: 0x01c0050a..0x01c00536, module storage-control (status_capture)
.type storage_control_status_capture,@function
storage_control_status_capture:
    [--sp] = {rets, r4}
    call storage_control_bus_enter
    call storage_control_leave_continuous
    r4 = r0
    call storage_control_status_read
    r1 = 16892
    r0 &= r1
    r1 = L01c3743c
    [r1+68] = r0
    if (r4 == 0) goto L01c0052e
    call storage_control_restore_read
L01c0052e:
    r0 = 0
    call storage_control_bus_leave
    {pc, r4} = [sp++]

; storage_control_bank_enter: 0x01c00536..0x01c0056e, module storage-control (bank_enter)
.type storage_control_bank_enter,@function
storage_control_bank_enter:
    [--sp] = rets
    r1 = L01c3743c
    r1 = [r1+24]
    if (r1 <= 16777216) goto L01c0056c
    r1 = L01c3748c
    r2 = b[r1+0] (u)
    if (r0 < 16777216) goto L01c0056c
    if (r2 != 0) goto L01c0056c
    r0 = 1
    b[r1+0] = r0
    r0 = 0
    call storage_control_chip_select
    r0 = 183
    call storage_control_send_byte
    r0 = 1
    call storage_control_chip_select
L01c0056c:
    pc = [sp++]

; storage_control_bank_leave: 0x01c0056e..0x01c005a4, module storage-control (bank_leave)
.type storage_control_bank_leave,@function
storage_control_bank_leave:
    [--sp] = rets
    r1 = L01c3743c
    r1 = [r1+24]
    if (r1 <= 16777216) goto L01c005a2
    r1 = L01c3748c
    r2 = b[r1+0] (u)
    if (r0 < 16777216) goto L01c005a2
    if (r2 == 0) goto L01c005a2
    r0 = 0
    b[r1+0] = r0
    call storage_control_chip_select
    r0 = 233
    call storage_control_send_byte
    r0 = 1
    call storage_control_chip_select
L01c005a2:
    pc = [sp++]

; storage_control_device_read: 0x01c005a4..0x01c005d0, module storage-control (device_read)
.type storage_control_device_read,@function
storage_control_device_read:
    [--sp] = {rets, r7-r4}
    r4 = r2
    r5 = r1
    r6 = r0
    call storage_control_bus_enter
    r7 = r4 + r5
    r0 = r7
    call storage_control_bank_enter
    r2 = r4.l (u)
    r3 = 0
    r0 = r6
    r1 = r5
    call storage_control_transfer_read
    r0 = r7
    call storage_control_bank_leave
    r0 = 0
    call storage_control_bus_leave
    r0 = r4
    {pc, r7-r4} = [sp++]

; storage_control_write_enable: 0x01c005d0..0x01c005e6, module storage-control (write_enable)
.type storage_control_write_enable,@function
storage_control_write_enable:
    [--sp] = rets
    r0 = 0
    call storage_control_chip_select
    r0 = 6
    call storage_control_send_byte
    r0 = 1
    call storage_control_chip_select
    pc = [sp++]

; storage_control_translate: 0x01c005e6..0x01c005f6, module storage-control (translate)
.type storage_control_translate,@function
storage_control_translate:
    r1 = L01c3743c
    r2 = [r1+48]
    r0 = r0 - r2  #
    r1 = [r1+52]
    r0 += r1  ; @add.rr
    rts

; storage_control_cache_forward: 0x01c005f6..0x01c00600, module storage-control (cache_forward)
.type storage_control_cache_forward,@function
storage_control_cache_forward:
    [--sp] = rets
    call storage_control_cache_lines  ; @call.xl
    pc = [sp++]

; storage_control_busy_wait: 0x01c00600..0x01c00640, module storage-control (busy_wait)
.type storage_control_busy_wait,@function
storage_control_busy_wait:
    [--sp] = {rets, r4}
    sp += -4
    r0 = 5000000
    [sp] = r0
    goto L01c00630
L01c0060e:
    r0 = 0
    call storage_control_chip_select
    r0 = 5
    call storage_control_send_byte
    call storage_control_receive_byte
    r4 = r0
    r0 = 1
    call storage_control_chip_select
    if ((r4 & 1) == 0) goto L01c00634
    r0 = sp + 0
    [r0+0] += -1  ; @rmw.add.s12
L01c00630:
    r0 = [sp]
    if (r0 != 0) goto L01c0060e
L01c00634:
    r1 = [sp]
    r0 = -1
    if (r1 == 0) goto L01c0063c
    r0 = 0
L01c0063c:
    sp += 4
    {pc, r4} = [sp++]

; storage_control_device_erase: 0x01c00640..0x01c006d2, module storage-control (device_erase)
.type storage_control_device_erase,@function
storage_control_device_erase:
    [--sp] = {rets, r8-r4}
    r2 = r0 + -200
    r4 = -1
    if (r2 > 4) goto L01c006ce
    r7 = 32
    r5 = 4096
    r0 = L01c3743c
    tbb [r2]
storage_erase200:
    .byte (L01c00674 - storage_erase200) / 2, (L01c00660 - storage_erase200) / 2, (L01c00668 - storage_erase200) / 2, (L01c006ce - storage_erase200) / 2, (L01c0066e - storage_erase200) / 2
    .byte 0x00  ; alignment
L01c00660:
    r7 = 216
    r5 = 0x10000
    goto L01c00674
L01c00668:
    r5 = [r0+24]
    r7 = 199
    goto L01c00674
L01c0066e:
    r7 = 129
    r5 = 256
L01c00674:
    r2 = 0x0 - r5  #
    r0 = [r0+24]
    r6 = r2 & r1
    r0 &= r2
    if (r6 == r0) goto L01c006ce
    call storage_control_bus_enter
    r0 = r6
    call storage_control_bank_enter
    call storage_control_leave_continuous
    r8 = r0
    call storage_control_write_enable
    r0 = 0
    r4 = 0
    call storage_control_chip_select
    r0 = r7
    call storage_control_send_byte
    r0 = r6
    call storage_control_send_address
    r0 = 1
    call storage_control_chip_select
    r0 = r6
    call storage_control_translate
    r1 = r5
    call storage_control_cache_forward
    call storage_control_busy_wait
    if (r8 != 0) {  ; @if.ne.ri.s12
    call storage_control_restore_read
    }
    r0 = r6
    call storage_control_bank_leave
    r0 = 0
    call storage_control_bus_leave
L01c006ce:
    r0 = r4
    {pc, r8-r4} = [sp++]

; storage_control_status_write: 0x01c006d2..0x01c0079e, module storage-control (status_write)
.type storage_control_status_write,@function
storage_control_status_write:
    [--sp] = {rets, r8-r4}
    r4 = r0
    r0 = 0
    call storage_control_chip_select
    r8 = r4 >> 8
    r7 = r4 & 0x10000
    r6 = r4 & 0x20000
    if ((r4 & 262144) != 0) goto L01c0072a
    if (r6 == 0) {  ; @if.eq.ri.s12
    r0 = 6
    } else {
    r0 = 80
    }
    call storage_control_send_byte
    r0 = 1
    call storage_control_chip_select
    r0 = 0
    call storage_control_chip_select
    r0 = 1
    call storage_control_send_byte
    r0 = r4.b0 (u)
    call storage_control_send_byte
    if (r7 == 0) goto L01c0071a
    r0 = uextra(r8, p:0, l:8)
    call storage_control_send_byte
L01c0071a:
    r0 = 1
    call storage_control_chip_select
    call storage_control_busy_wait
    r5 = 3
    if (r0 != 0) goto L01c0079a
    goto L01c00798
L01c0072a:
    if (r6 == 0) {  ; @if.eq.ri.s12
    r0 = 6
    } else {
    r0 = 80
    }
    call storage_control_send_byte
    r0 = 1
    call storage_control_chip_select
    r0 = 0
    call storage_control_chip_select
    r0 = 1
    r5 = 1
    call storage_control_send_byte
    r0 = r4.b0 (u)
    call storage_control_send_byte
    r0 = 1
    call storage_control_chip_select
    call storage_control_busy_wait
    if (r0 != 0) goto L01c0079a
    if (r7 == 0) goto L01c00798
    r0 = 0
    call storage_control_chip_select
    if (r6 == 0) {  ; @if.eq.ri.s12
    r0 = 6
    } else {
    r0 = 80
    }
    call storage_control_send_byte
    r0 = 1
    call storage_control_chip_select
    r0 = 0
    call storage_control_chip_select
    r0 = 49
    call storage_control_send_byte
    r0 = uextra(r8, p:0, l:8)
    call storage_control_send_byte
    r0 = 1
    call storage_control_chip_select
    call storage_control_busy_wait
    r5 = 2
    if (r0 != 0) goto L01c0079a
L01c00798:
    r5 = 0
L01c0079a:
    r0 = r5
    {pc, r8-r4} = [sp++]

; storage_control_status_apply: 0x01c0079e..0x01c00822, module storage-control (status_apply)
.type storage_control_status_apply,@function
storage_control_status_apply:
    [--sp] = {rets, r10-r4}
    r5 = r0
    call storage_control_bus_enter
    r0 = L01c3743c
    [r0+68] = r5
    r7 = 0
    call storage_control_leave_continuous
    r8 = r0
    r10 = 16892
    r9 = r10 + 0x70000
    r4 = r5
    goto L01c007ee
L01c007c4:
    r1 = r7.l (u)
    if (r1 >= 3) goto L01c0080c
    r1 = r4 | 0x40000
    r4 &= 4294705151
    if ((r7 & 0x1) != 0) {
    r4 = r1
    }
    if ((r5 & 0x40000) != 0) {
    r4 = r1
    }
    r1 = r4 & r9
    r0 = r0 & 0xBE00
    r0 |= r1
    call storage_control_status_write
    r6 = r0
    r7 += 1  ; @add.ri.u5
L01c007ee:
    call storage_control_status_read
    if ((r5 & 0x10000) == 0) {
    r1 = r4 & 0xFF00
    r0 = r0 & 0xFFFF00FF
    r0 |= r1
    }
    r1 = r0 ^ r4
    if ((r1 & r10) != 0) goto L01c007c4
    r6 = 0
    goto L01c00810
L01c0080c:
    if (r6 != 0) goto L01c00810
    r6 = -1
L01c00810:
    if (r8 != 0) {  ; @if.ne.ri.s12
    call storage_control_restore_read
    }
    r0 = 0
    call storage_control_bus_leave
    r0 = r6
    {pc, r10-r4} = [sp++]

; storage_control_cache_region: 0x01c00822..0x01c00840, module storage-control (cache_region)
.type storage_control_cache_region,@function
storage_control_cache_region:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r5 = r0
    call storage_control_bus_enter
    r0 = r5
    call storage_control_translate
    r1 = r4
    call storage_control_cache_forward
    r0 = 0
    call storage_control_bus_leave
    {pc, r5, r4} = [sp++]

; storage_control_device_program: 0x01c00840..0x01c008b4, module storage-control (device_program)
.type storage_control_device_program,@function
storage_control_device_program:
    [--sp] = {rets, r9-r4}
    r5 = r2
    r6 = r1
    r7 = r0
    if (r5 == 0) goto L01c008b0
    call storage_control_bus_enter
    r9 = r5 + r6
    r0 = r9
    call storage_control_bank_enter
    call storage_control_leave_continuous
    r8 = r0
    call storage_control_write_enable
    r0 = 0
    r4 = 0
    call storage_control_chip_select
    r0 = 2
    call storage_control_send_byte
    r0 = r6
    call storage_control_send_address
    goto L01c00882
L01c00878:
    r0 = b[r7+r4] (u)
    call storage_control_send_byte
    r4 += 1  ; @add.ri.u5
L01c00882:
    if (r5 != r4) goto L01c00878
    r0 = 1
    call storage_control_chip_select
    r0 = r6
    call storage_control_translate
    r1 = r5
    call storage_control_cache_forward
    call storage_control_busy_wait
    if (r8 != 0) {  ; @if.ne.ri.s12
    call storage_control_restore_read
    }
    r0 = r9
    call storage_control_bank_leave
    r0 = 0
    call storage_control_bus_leave
L01c008b0:
    r0 = 0
    {pc, r9-r4} = [sp++]
