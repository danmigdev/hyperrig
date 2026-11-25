; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201b60a..0x0201b9a2: vendor code (JieLi SDK or library, not reversed), as instructions
L0201b60a:
    [--sp] = {rets, r7-r4}
    r4 = r3
    r5 = r2
    r6 = r1
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r7 = L01c1fc4c
    r0 = cnum
    r1 = [r7+r0<<2]
    r3 = r1 + 1
    [r7+r0<<2] = r3
    if (r1 != 0) goto L0201b632
    lockset
L0201b632:
    csync
    if (r2 == 0) goto L0201b656
    r0 = 0x16800
    [r0+0] &= 0xFFFFEFFF
    csync
    r1 = r0 + -2046
    r2 = b[r1+8] (u)
    [r6+0] = r2
    r2 = h[r1+0] (u)
    [r5+0] = r2
    r1 = h[r1+2] (u)
    [r4+0] = r1
    [r0+0] |= 0x1000
    goto L0201b686
L0201b656:
    r0 = 6
    call L02001b94
    [r6+0] = r0
    r0 = 2
    call L02001b94
    r6 = r0
    r0 = 3
    call L02001b94
    r0 = r0 << 8
    r0 |= r6
    [r5+0] = r0
    r0 = 4
    call L02001b94
    r5 = r0
    r0 = 5
    call L02001b94
    r0 = r0 << 8
    r0 |= r5
    [r4+0] = r0
L0201b686:
    csync
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L0201b69a
    lockclr
L0201b69a:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r7-r4} = [sp++]
L0201b6a2:
    [--sp] = {rets, r7-r4}
    r4 = r3
    r5 = r2
    r6 = r1
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r7 = L01c1fc4c
    r0 = cnum
    r1 = [r7+r0<<2]
    r3 = r1 + 1
    [r7+r0<<2] = r3
    if (r1 != 0) goto L0201b6ca
    lockset
L0201b6ca:
    csync
    if (r2 == 0) goto L0201b6e0
    r0 = 90118
    r1 = b[r0+5] (u)
    [r6+0] = r1
    r1 = h[r0+0] (u)
    [r5+0] = r1
    r0 = h[r0+2] (u)
    goto L0201b70e
L0201b6e0:
    r0 = 11
    call L02001b94
    [r6+0] = r0
    r0 = 7
    call L02001b94
    r6 = r0
    r0 = 8
    call L02001b94
    r0 = r0 << 8
    r0 |= r6
    [r5+0] = r0
    r0 = 9
    call L02001b94
    r5 = r0
    r0 = 10
    call L02001b94
    r0 = r0 << 8
    r0 |= r5
L0201b70e:
    [r4+0] = r0
    csync
    r0 = cnum
    r1 = [r7+r0<<2]
    r1 += -1
    [r7+r0<<2] = r1
    if (r1 != 0) goto L0201b724
    lockclr
L0201b724:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r7-r4} = [sp++]
L0201b72c:
    [--sp] = {rets, r4}
    r2 = r1
    if (r0 == 0) goto L0201b73a
    r0 = 0x16000
    b[r0+0] = r2
    {pc, r4} = [sp++]
L0201b73a:
    call storage_coordination_irq_enter  ; @call.xl
    r4 = L01c1fc4c
    r0 = cnum
    r1 = [r4+r0<<2]
    r3 = r1 + 1
    [r4+r0<<2] = r3
    if (r1 != 0) goto L0201b758
    lockset
L0201b758:
    csync
    r0 = 0
    r1 = r2
    call L02001ac0
    csync
    r0 = cnum
    r1 = [r4+r0<<2]
    r1 += -1
    [r4+r0<<2] = r1
    if (r1 != 0) goto L0201b776
    lockclr
L0201b776:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r4} = [sp++]
L0201b77e:
    [--sp] = {rets, r9-r4}
    r4 = r0
    r8 = r4 + 23
    r0 = b[r8+2] (u)
    r5 = r0 & 0xFFFFFF01
    r0 = r5 << 2
    r7 = L01c26890
    r6 = r0 + r7
    r9 = 414
    r0 = [r6+r9<<2]
    r1 = 2
    b[r0+20] = r1
    r0 = b[r8+0] (u)
    r0 &= 4294967293
    b[r8+0] = r0
    r1_r0 = 0
    r0 = r5  #
    b[r4+0] = r0
    call L0201b72c
    r0 = [r6+r9<<2]
    if (r0 == 0) goto L0201b7dc
    r6 = 17
    goto L0201b7d8
L0201b7c2:
    r0 = r7 + 1656
    r0 = [r0+r5<<2]
    r2 = [r0+r6<<2]
    if (r2 == 0) goto L0201b7d6
    r1 = -1
    r0 = r4
    call r2
L0201b7d6:
    r6 += 1  ; @add.ri.u5
L0201b7d8:
    if (r6 != 25) goto L0201b7c2
L0201b7dc:
    if (r5 != 0) goto L0201b824
    call storage_coordination_irq_enter  ; @call.xl
    r4 = L01c1fc4c
    r0 = cnum
    r1 = [r4+r0<<2]
    r2 = r1 + 1
    [r4+r0<<2] = r2
    if (r1 != 0) goto L0201b7fc
    lockset
L0201b7fc:
    csync
    r0 = 1
    call L02001b94
    csync
    r1 = cnum
    r2 = [r4+r1<<2]
    r3 = r0
    r0 = r2 + -1
    [r4+r1<<2] = r0
    if (r0 != 0) goto L0201b81c
    lockclr
L0201b81c:
    call storage_coordination_irq_leave  ; @call.xl
    goto L0201b82c
L0201b824:
    r0 = 90113
    r3 = b[r0+0] (u)
L0201b82c:
    r0 = uextra(r3, p:4, l:1)
    r0 |= 2
    b[r8+1] = r0
    {pc, r9-r4} = [sp++]
L0201b838:
    [--sp] = {rets, r4}
    if (r0 == 0) goto L0201b848
    ssync
    r0 = 90370
    r3 = h[r0+0] (u)
    goto L0201b892
L0201b848:
    call storage_coordination_irq_enter  ; @call.xl
    r4 = L01c1fc4c
    r0 = cnum
    r1 = [r4+r0<<2]
    r2 = r1 + 1
    [r4+r0<<2] = r2
    if (r1 != 0) goto L0201b866
    lockset
L0201b866:
    csync
    r0 = 0
    call L02005cb8
    r0 = 17
    call L02001b94
    csync
    r1 = cnum
    r2 = [r4+r1<<2]
    r3 = r0
    r0 = r2 + -1
    [r4+r1<<2] = r0
    if (r0 != 0) goto L0201b88c
    lockclr
L0201b88c:
    call storage_coordination_irq_leave  ; @call.xl
L0201b892:
    r0 = r3
    {pc, r4} = [sp++]
L0201b896:
    [--sp] = {rets, r5, r4}
    r4 = r1
    if (r0 == 0) goto L0201b8a8
    r0 = 90370
    h[r0+0] = r4
    csync
    {pc, r5, r4} = [sp++]
L0201b8a8:
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fc4c
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    if (r1 != 0) goto L0201b8c6
    lockset
L0201b8c6:
    csync
    r0 = 0
    call L02005cb8
    r0 = 17
    r1 = r4
    call L02001ac0
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L0201b8ea
    lockclr
L0201b8ea:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r5, r4} = [sp++]
L0201b8f2:
    [--sp] = {rets, r5, r4}
    r3 = r1
    if (r0 == 0) goto L0201b950
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fc4c
    r1 = cnum
    r4 = [r0+r1<<2]
    r5 = r4 + 1
    [r0+r1<<2] = r5
    if (r4 != 0) goto L0201b916
    lockset
L0201b916:
    csync
    r1 = 0x16800
    [r1+0] &= 0xFFFFF7FF
    csync
    r4 = r1 + -2016
    goto L0201b92e
L0201b928:
    r5 = b[r4+0] (u)
    b[r3++=1] = r5
    r2 += -1
L0201b92e:
    if (r2 != 0) goto L0201b928
    [r1+0] |= 0x800
    csync
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L0201b948
    lockclr
L0201b948:
    call storage_coordination_irq_leave  ; @call.xl
L0201b94e:
    {pc, r5, r4} = [sp++]
L0201b950:
    r0 = L01c25ce8
    r0 = [r0+0]
    if (r0 == 0) goto L0201b94e
    r0 = r3  #
    r1 = [r0+0]
    call effect_parameter_support_memmove  ; @call.xl
    {pc, r5, r4} = [sp++]
L0201b966:
    [--sp] = {rets, r5, r4}
    r4 = r2
    r5 = r0
    if (r5 == 0) goto L0201b980
    r0 = 90144
    goto L0201b97c
L0201b976:
    r2 = b[r1++=1] (u)
    b[r0+0] = r2
    r4 += -1
L0201b97c:
    if (r4 != 0) goto L0201b976
    {pc, r5, r4} = [sp++]
L0201b980:
    r0 = L01c25ce8
    r0 = [r0+r5<<2]
    if (r0 == 0) goto L0201b9a0
    r0 = [r0+0]
    call effect_parameter_support_memmove  ; @call.xl
    r0 = L02035cb0
    r0 = [r0+r5<<2]
    [r0+8] = r4
L0201b9a0:
    {pc, r5, r4} = [sp++]
