; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02006a9e..0x02006c9c: vendor code (JieLi SDK or library, not reversed), as instructions
L02006a9e:
    [--sp] = {rets, r5, r4}
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fc4c
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    if (r1 != 0) goto L02006abe
    lockset
L02006abe:
    csync
    r0 = 2
    call L02005cb8
    r0 = 17
    call L02001b94
    r4 = r0
    r0 = 18
    call L02001b94
    csync
    r1 = cnum
    r2 = [r5+r1<<2]
    r2 += -1
    [r5+r1<<2] = r2
    if (r2 != 0) goto L02006ae8
    lockclr
L02006ae8:
    r0 = r0 << 8
    r3 = r0 | r4
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    {pc, r5, r4} = [sp++]
L02006af8:
    [--sp] = {rets, r5, r4}
    r4 = r2
    r2 = r1
    if (r0 == 0) goto L02006b10
    r0 = r2 << 4
    r1 = 45185
    h[r0+r1<<1] = r4
    csync
    {pc, r5, r4} = [sp++]
L02006b10:
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fc4c
    r0 = cnum
    r1 = [r5+r0<<2]
    r3 = r1 + 1
    [r5+r0<<2] = r3
    if (r1 != 0) goto L02006b2e
    lockset
L02006b2e:
    csync
    r0 = r2
    call L02005cb8
    r1 = r4.b0 (u)
    r0 = 17
    call L02001ac0
    r1 = r4 >> 8
    r0 = 18
    call L02001ac0
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L02006b5a
    lockclr
L02006b5a:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r5, r4} = [sp++]
sdk_usb_set_dma_taddr:
    [--sp] = {rets, r5, r4}
    r3 = L01c25ce8
    r4 = [r3+r0<<2]
    if (r4 == 0) goto L02006bc8
    if (r0 == 0) goto L02006b84
    if (r1 == 0) goto L02006ba0
    r1 += -1
    r4 = r1 << 3
    r5 = 23048
    [r4+r5<<2] = r2
    csync
    goto L02006bbe
L02006b84:
    r4 = L02035cb0
    if (r1 == 0) goto L02006ba4
    r4 = [r4+r0<<2]
    if (r1 != 4) goto L02006bb4
    [r4+56] = r2
    csync
    r0 = [r3+r0<<2]
    [r0+20] = r2
    {pc, r5, r4} = [sp++]
L02006ba0:
    [r4+0] = r2
    {pc, r5, r4} = [sp++]
L02006ba4:
    r1 = [r4+r0<<2]
    [r1+24] = r2
    csync
    r0 = [r3+r0<<2]
    [r0+0] = r2
    {pc, r5, r4} = [sp++]
L02006bb4:
    r1 += -1
    r5 = r1 << 3
    r4 += r5  ; @add.rr
    [r4+28] = r2
    csync
L02006bbe:
    r0 = [r3+r0<<2]
    r0 += 8  ; @add.ri.u5
    [r0+r1<<2] = r2
L02006bc8:
    {pc, r5, r4} = [sp++]
L02006bca:
    [--sp] = {rets, r14-r4}
    r2 = L01c25ce8
    r11 = r1  #
    r2 = [r2+0]
    r9 = r0
    r13 = L01c1f180
    if (r2 == 0) goto L02006bfa
    r10 = [r2+76]
    r8 = [r2+12]
    r0 = [r13+24]
    r1 = r1 / r10 (u)
    r1 = r1 << 1
    r0 += r1  ; @add.rr
    r4 = r0 + 200
    goto L02006c04
L02006bfa:
    r0 = [r13+24]
    r4 = r0 + 20
    r10 = 0
    r8 = 0
L02006c04:
    r12 = 71696
    r5 = 16386
    r14 = r11
L02006c10:
    r0 = [r13+24]
    r7 = 0
    ifs (r4 < r0) goto L02006c98
    call L02006a9e
    r6 = r0
    if ((r6 & 1) == 0) goto L02006c44
    r0 = r6 & r5
    if (r0 == r5) goto L02006c98
    if ((r6 & 128) == 0) goto L02006c10
    r7 = r6 & 0xFFFFFF7F
    r0 = 0
    r1 = 2
    r2 = r7
    call L02006af8
    if ((r6 & 16384) == 0) goto L02006c10
    goto L02006c8a
L02006c44:
    r7 = umin(r10, r14)
    if (r9 == 0) goto L02006c5c
    r1_r0 = r9_r8
    r2 = r7
    call effect_parameter_support_memmove  ; @call.xl
    r9 += r7
    csync
    goto L02006c5e
L02006c5c:
    r9 = 0
L02006c5e:
    r0 = 0
    r1 = 2
    r2 = r8
    call sdk_usb_set_dma_taddr
    [r12+0] = r7
    csync
    call L02006a9e
    r2 = r0 | 0x1
    r0 = 0
    r1 = 2
    call L02006af8
    r14 = r14 - r7
    if (r14 != 0) goto L02006c10
    r7 = r11
    goto L02006c98
L02006c8a:
    r2 = r7 | 0x1
    r0 = 0
    r1 = 2
    r7 = 0
    call L02006af8
L02006c98:
    r0 = r7
    {pc, r14-r4} = [sp++]
