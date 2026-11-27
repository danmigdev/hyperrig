; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; storage_control: 7 functions, 0x020026d6..0x02002874

; storage_control_power2: 0x020026d6..0x020026e8, module storage-control (power2)
.type storage_control_power2,@function
storage_control_power2:
    r1 = r0
    r0 = 1
    r2 = 1
    goto L020026e2
L020026de:
    r2 += 1  ; @add.ri.u5
    r0 = r0 << 1
L020026e2:
    ifs (r2 <= r1) goto L020026de
    rts

; storage_control_initialize: 0x020026e8..0x02002772, module storage-control (initialize)
.type storage_control_initialize,@function
storage_control_initialize:
    [--sp] = {rets, r6-r4}
    r5 = L01c3743c
    r0 = b[r5+16] (u)
    if (r0 != 0) goto L0200275a
    r0 = 0x11C00
    [r0+0] &= 0xFFFFFFF7
    [r0+0] &= 0xFFFFF3FF
    [r0+0] |= 0x6000
    r0 = 331804
    [r0+0] &= 0xFFF7FFFF
    r4 = storage_platform_interrupt
    r0 = 125
    r1 = 7
    r3 = 0
    r2 = r4
    call storage_platform_register
    r0 = 124
    r1 = 7
    r3 = 1
    r6 = 1
    r2 = r4
    call storage_platform_register
    r0 = L01c27734
    call L0203fb92  ; @call.xl
    r0 = [r5+24]
    if (r0 != 0) goto L02002752
    call storage_control_identify  ; @call.xl
    r0 = b[r5+28] (u)
    r0 += -16
    call storage_control_power2
    r0 = r0 << 16
    [r5+24] = r0
L02002752:
    h[r5+16] = r6
    call storage_control_status_capture  ; @call.xl
L0200275a:
    r0 = storage_control_bus_enter
    r1 = storage_control_cache_lines
    r1 = r1 - r0
    r0 = 1
    if (r1 <= 4096) {
    r0 = 0
    }
    {pc, r6-r4} = [sp++]

; storage_control_ensure: 0x02002772..0x02002786, module storage-control (ensure)
.type storage_control_ensure,@function
storage_control_ensure:
    [--sp] = {rets, r4}
    r4 = L01c24228
    r0 = b[r4+0] (u)
    if (r0 != 0) goto L02002784
    call storage_control_initialize
    r0 = 1
    b[r4+0] = r0
L02002784:
    {pc, r4} = [sp++]

; storage_control_activity: 0x02002786..0x020027e4, module storage-control (activity)
.type storage_control_activity,@function
storage_control_activity:
    [--sp] = {rets, r5, r4}
    r4 = r0
    call storage_platform_clock  ; @call.xl
    r1 = L01c26890
    r2 = b[r1+22] (u)
    if (r4 == 0) goto L020027ba
    if (r2 > 3) goto L020027e2
    r3 = r2 + r1
    r5 = 392
    b[r3+r5] = r4
    r3 = r1 + 1732
    [r3+r2<<2] = r0
    r0 = r2 + 1
    b[r1+22] = r0
    {pc, r5, r4} = [sp++]
L020027ba:
    if (r2 == 0) goto L020027e2
    r2 += -1
    r3 = r2.b0 (u)
    r4 = r3 + r1
    r5 = 392
    r4 = b[r4+r5] (u)
    b[r1+23] = r4
    r4 = r1 + 1732
    r3 = [r4+r3<<2]
    [r1+396] = r3
    [r1+400] = r0
    b[r1+22] = r2
L020027e2:
    {pc, r5, r4} = [sp++]

; storage_control_poll: 0x020027e4..0x02002806, module storage-control (poll)
.type storage_control_poll,@function
storage_control_poll:
    [--sp] = rets
    r0 = L01c26890
    r1 = [r0+280]
    if (r1 == 0) goto L02002804
    r1 = [r0+380]
    r0 = [r0+384]
    if (r1 != r0) {
    call L0203ea6e  ; @call.xl
    }
L02002804:
    pc = [sp++]

; storage_control_raw_read: 0x02002806..0x02002810, module storage-control (raw_read)
.type storage_control_raw_read,@function
storage_control_raw_read:
    [--sp] = rets
    call storage_control_device_read  ; @call.xl
    pc = [sp++]

; storage_control_read: 0x02002810..0x02002874, module storage-control (read)
.type storage_control_read,@function
storage_control_read:
    [--sp] = {rets, r11-r4}
    r9 = r2
    r8 = r1
    r10 = r0
    r7 = -1
    if (r0 < 782336) goto L02002870
    r0 += r2  ; @add.rr
    if (r0 > 1044480) goto L02002870
    call storage_control_ensure
    r0 = 1
    call storage_control_activity
    call storage_platform_clock  ; @call.xl
    r7 = 0
    r6 = r9
    r5 = 0
    goto L0200286a
L0200283c:
    if (r5 >= r9) goto L0200286c
    r7 = r8 + r5
    r11 = r10 + r5
    r4 = r6
; HyperRig MINI, product option: larger pieces while the sound is paused (mini/product/swap.c).
.if MINI_PRODUCT
    call hyperrig_flash_piece  ; @call.xl
    if (r6 < r0) goto Lhr_piece_kept
    r4 = r0
Lhr_piece_kept:
.else
    if (r6 >= 256) {  ; @if.ge.ri.s12
    r4 = 256
    }
.endif
    call storage_control_poll
    r0 = r7
    r1 = r11
    r2 = r4
    call storage_control_raw_read
    r0 = r0 >>> 31
    r7 = r0 & 0xFFFFFFFE
.if MINI_PRODUCT
    r6 = r6 - r4
    r5 = r5 + r4
.else
    r6 = r6 + -256
    r5 = r5 + 256
.endif
L0200286a:
    if (r7 == 0) goto L0200283c
L0200286c:
    r0 = 0
    call storage_control_activity
L02002870:
    r0 = r7
    {pc, r11-r4} = [sp++]
