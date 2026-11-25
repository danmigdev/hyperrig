; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201e09a..0x0201e1f8: vendor code (JieLi SDK or library, not reversed), as instructions
L0201e09a:
    [--sp] = {rets, r5, r4}
    r2 = r1
    r3 = r0
    if (r3 < 148) goto L0201e0a8
    call phase3_p6_usb_set_die
    {pc, r5, r4} = [sp++]
L0201e0a8:
    if (r3 > 143) goto L0201e0f2
    call sdk_gpio2reg
    r4 = r0
    if (r4 == -1) goto L0201e0f2
    r0 = r3 >> 4
    r1 = L01c25ce0
    r5 = r0 + r1
    call storage_coordination_irq_enter  ; @call.xl
    csync
L0201e0c8:
    testset b[r5]
    ifeq goto L0201e0c8
    r0 = r3 & 0xF
    r1 = 1
    r0 = r1 << r0
    csync
    if (r2 == 0) {  ; @if.eq.ri.s12
    [r4+32] &= ~r0
    } else {
    [r4+32] |= r0
    }
    csync
    r0 = 0
    b[r5+0] = r0
    call storage_coordination_irq_leave  ; @call.xl
L0201e0f2:
    {pc, r5, r4} = [sp++]
L0201e0f4:
    [--sp] = {rets, r7-r4}
    r4 = r1
    r5 = r0
    if (r5 == 0) goto L0201e120
    r0 = 92684
    [r0+0] |= 0x7
    [r0+0] |= 0x18
    if ((r4 & 0x2) != 0) {
    [r0+0] |= 0x30000000
    }
    [r0+0] |= 0x20
    [r0+0] |= 0x100
    if ((r4 & 8) == 0) goto L0201e1a6
    {pc, r7-r4} = [sp++]
L0201e120:
    r0 = 0
    call L0201e03e
    r7 = r5 << 1
    r6 = r7 + 148
    r0 = r6
    call L02004ad6
    r1 = 1
    r0 = r6
    call phase3_p5_gpio_set_die
    r1 = 1
    r0 = r6
    call L0201e09a
    r1 = 0
    r0 = r6
    call phase3_p5_gpio_set_pull_up
    r1 = 1
    r0 = r6
    call phase3_p5_gpio_set_pull_down
    r6 = r7 + 149
    r0 = r6
    call L02004ad6
    if ((r4 & 8) != 0) goto L0201e176
    r1 = 1
    r0 = r6
    call phase3_p5_gpio_set_die
    r1 = 1
    r0 = r6
    call L0201e09a
    r1 = 0
    r0 = r6
    call phase3_p5_gpio_set_pull_up
    r1 = 1
    goto L0201e18e
L0201e176:
    r1 = 0
    r0 = r6
    call phase3_p5_gpio_set_die
    r1 = 0
    r0 = r6
    call L0201e09a
    r1 = 0
    r0 = r6
    call phase3_p5_gpio_set_pull_up
    r1 = 0
L0201e18e:
    r0 = r6
    call phase3_p5_gpio_set_pull_down
    r0 = L02035cb0
    r0 = [r0+r5<<2]
    [r0+0] |= 0x1
    if ((r4 & 2) == 0) goto L0201e1aa
L0201e1a6:
    [r0+0] |= 0x200
L0201e1aa:
    {pc, r7-r4} = [sp++]
sdk_usb_check_dpo:
    if (r0 == 0) {  ; @if.eq.ri.s12
    r0 = 0x11800
    r0 = [r0+0]
    r0 = r0 >> 15
    } else {
    r0 = 92688
    r0 = [r0+0]
    r0 = r0 >> 17
    }
    r0 = r0 & 0x1
    rts
sdk_usb_read_dp_se:
    if (r0 == 0) {  ; @if.eq.ri.s12
    r0 = 0x11800
    r0 = [r0+0]
    r0 = r0 >> 17
    } else {
    r0 = 92688
    r0 = [r0+0]
    r0 = r0 >> 15
    }
    r0 = r0 & 0x1
    rts
sdk_usb_read_dm_se:
    r1 = 0x11800
    if (r0 == 0) goto L0201e1f0
    r1 = 92688
L0201e1f0:
    r0 = [r1+0]
    r0 = uextra(r0, p:16, l:1)
    rts
