; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02005cb8..0x02005ef2: vendor code (JieLi SDK or library, not reversed), as instructions
L02005cb8:
    [--sp] = rets
    r1 = r0
    r0 = 14
    call L02001ac0
    pc = [sp++]
L02005cc4:
    [--sp] = {rets, r5, r4}
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fc4c
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    if (r1 != 0) goto L02005ce4
    lockset
L02005ce4:
    csync
    r0 = 2
    call L02005cb8
    r0 = 20
    call L02001b94
    r4 = r0
    r0 = 21
    call L02001b94
    csync
    r1 = cnum
    r2 = [r5+r1<<2]
    r2 += -1
    [r5+r1<<2] = r2
    if (r2 != 0) goto L02005d0c
    lockclr
L02005d0c:
    r0 = r0 << 8
    r3 = r0 | r4
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    {pc, r5, r4} = [sp++]
L02005d1c:
    [--sp] = {rets, r5, r4}
    r4 = r2
    r2 = r1
    if (r0 == 0) goto L02005d34
    r0 = r2 << 4
    r1 = 45187
    h[r0+r1<<1] = r4
    csync
    {pc, r5, r4} = [sp++]
L02005d34:
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fc4c
    r0 = cnum
    r1 = [r5+r0<<2]
    r3 = r1 + 1
    [r5+r0<<2] = r3
    if (r1 != 0) goto L02005d52
    lockset
L02005d52:
    csync
    r0 = r2
    call L02005cb8
    r1 = r4.b0 (u)
    r0 = 20
    call L02001ac0
    r1 = r4 >> 8
    r0 = 21
    call L02001ac0
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L02005d7c
    lockclr
L02005d7c:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r5, r4} = [sp++]
L02005d84:
    [--sp] = {rets, r15-r4}
    r8 = L01c25ce8
    r2 = [r8+0]
    r12 = r0
    r9 = L01c1f180
    if (r2 == 0) goto L02005dbc
    r0 = [r2+92]
    r1 = [r9+24]
    r10 = 1  #
    r2 = [r2+60]
    if (r2 != 0) goto L02005dac
    r10 = r2
L02005dac:
    r2 = 64
    r0 = r2 / r0 (u)
    r0 = r0 << 1
    r0 += r1  ; @add.rr
    r11 = r0 + 200
    goto L02005dc6
L02005dbc:
    r0 = [r9+24]
    r11 = r0 + 20
    r10 = 0
L02005dc6:
    r4 = 64
    r13 = L01c1fc4c
    r15 = 0
L02005dd0:
    r0 = [r9+24]
    ifs (r11 < r0) goto L02005ed6
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r13+r0<<2]
    r2 = r1 + 1
    [r13+r0<<2] = r2
    if (r1 != 0) goto L02005df0
    lockset
L02005df0:
    csync
    r0 = 2
    call L02005cb8
    r0 = 20
    call L02001b94
    r6 = 0
    if ((r0 & 1) == 0) goto L02005e16
    r0 = 22
    call L02001b94
    r6 = r0
    r0 = 23
    call L02001b94
    r0 = r0 << 8
    r6 |= r0
L02005e16:
    csync
    r0 = cnum
    r1 = [r13+r0<<2]
    r1 += -1
    [r13+r0<<2] = r1
    if (r1 != 0) goto L02005e2a
    lockclr
L02005e2a:
    call storage_coordination_irq_leave  ; @call.xl
    if (r6 == 0) goto L02005eda
    call L02005cc4
    r1 = [r8+0]
    r14 = r0
    if (r1 == 0) goto L02005e60
    r2 = [r1+60]
    if (r2 == 0) goto L02005e64
    r0 = [r1+44]
    if (r0 != r2) goto L02005e76
    r0 = [r1+92]
    r0 += r2  ; @add.rr
    r2 = r0 + 4
    r0 = 0
    r1 = 2
    call sdk_usb_set_dma_raddr
    r0 = [r8+0]
    r7 = [r0+60]
    goto L02005e8c
L02005e60:
    r7 = 0
    goto L02005e8c
L02005e64:
    r2 = [r1+44]
    r0 = 0
    r1 = 2
    call sdk_usb_set_dma_raddr
    r0 = [r8+0]
    r7 = [r0+44]
    goto L02005e8c
L02005e76:
    r0 = 0
    r1 = 2
    call sdk_usb_set_dma_raddr
    r0 = [r8+0]
    r1 = [r0+92]
    r0 = [r0+60]
    r0 += r1  ; @add.rr
    r7 = r0 + 4
L02005e8c:
    r5 = r14 & 0xFFFFFE9B
    if (r10 != 0) {  ; @if.ne.ri.s12
    r2 = r5 | 0x10
    r0 = 0
    r1 = 2
    call L02005d1c
    }
    r6 = umin(r6, r4)
    if (r12 == 0) goto L02005eba
    ssync
    r0 = r12
    r1 = r7
    r2 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r12 += r6
    goto L02005ebc
L02005eba:
    r12 = 0
L02005ebc:
    if (r10 == 0) {  ; @if.eq.ri.s12
    r2 = r5 | 0x10
    r0 = 0
    r1 = 2
    call L02005d1c
    }
    r4 = r4 - r6
    r15 += r6
    if (r4 != 0) goto L02005dd0  ; @bne.ri
    goto L02005eee
L02005ed6:
    r15 = 0
    goto L02005eee
L02005eda:
    call L02005cc4
    if ((r0 & 16384) == 0) goto L02005eee
    r2 = r0 | 0x10
    r0 = 0
    r1 = 2
    call L02005d1c
L02005eee:
    r0 = r15
    {pc, r15-r4} = [sp++]
