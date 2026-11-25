; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02001d0a..0x02001e7e: vendor code (JieLi SDK or library, not reversed), as instructions
sdk_usb_set_dma_raddr:
    [--sp] = {rets, r5, r4}
    r3 = L01c25ce8
    if (r0 == 0) goto L02001d2c
    r4 = [r3+r0<<2]
    if (r4 == 0) goto L02001d78
    if (r1 == 0) goto L02001d4e
    r1 += -1
    r4 = r1 << 3
    r5 = 23049
    [r4+r5<<2] = r2
    csync
    goto L02001d6e
L02001d2c:
    r4 = L02035cb0
    if (r1 == 0) goto L02001d52
    r5 = [r3+r0<<2]
    if (r5 == 0) goto L02001d78
    r4 = [r4+r0<<2]
    if (r1 != 4) goto L02001d64
    [r4+60] = r2
    csync
    r0 = [r3+r0<<2]
    [r0+52] = r2
    {pc, r5, r4} = [sp++]
L02001d4e:
    [r4+0] = r2
    {pc, r5, r4} = [sp++]
L02001d52:
    r1 = [r4+r0<<2]
    [r1+24] = r2
    csync
    r0 = [r3+r0<<2]
    if (r0 == 0) goto L02001d78
    [r0+0] = r2
    {pc, r5, r4} = [sp++]
L02001d64:
    r1 += -1
    r5 = r1 << 3
    r4 += r5  ; @add.rr
    [r4+32] = r2
    csync
L02001d6e:
    r0 = [r3+r0<<2]
    r0 += 40
    [r0+r1<<2] = r2
L02001d78:
    {pc, r5, r4} = [sp++]
L02001d7a:
    [--sp] = {rets, r6-r4}
    r4 = r1
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fc4c
    r0 = cnum
    r1 = [r5+r0<<2]
    r3 = r1 + 1
    [r5+r0<<2] = r3
    if (r1 != 0) goto L02001d9e
    lockset
L02001d9e:
    csync
    if (r2 == 0) goto L02001db2
    r0 = 90118
    r1 = h[r0+0] (u)
    r1 = r1 | (1 << r4)
    h[r0+0] = r1
    goto L02001dda
L02001db2:
    r0 = 7
    call L02001b94
    r6 = r0 | (1 << r4)
    r0 = 8
    call L02001b94
    r4 = r0
    r1 = r6.b0 (u)
    r0 = 7
    call L02001ac0
    r0 = r4 << 8
    r0 |= r6
    r1 = uextra(r0, p:8, l:8)
    r0 = 8
    call L02001ac0
L02001dda:
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L02001dee
    lockclr
L02001dee:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r6-r4} = [sp++]
L02001df6:
    [--sp] = {rets, r6-r4}
    r4 = r1
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fc4c
    r0 = cnum
    r1 = [r5+r0<<2]
    r3 = r1 + 1
    [r5+r0<<2] = r3
    if (r1 != 0) goto L02001e1a
    lockset
L02001e1a:
    csync
    if (r2 == 0) goto L02001e2e
    r0 = 90120
    r1 = h[r0+0] (u)
    r1 = r1 | (1 << r4)
    h[r0+0] = r1
    goto L02001e56
L02001e2e:
    r0 = 9
    call L02001b94
    r6 = r0 | (1 << r4)
    r0 = 10
    call L02001b94
    r4 = r0
    r1 = r6.b0 (u)
    r0 = 9
    call L02001ac0
    r0 = r4 << 8
    r0 |= r6
    r1 = uextra(r0, p:8, l:8)
    r0 = 10
    call L02001ac0
L02001e56:
    csync
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L02001e6a
    lockclr
L02001e6a:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r6-r4} = [sp++]
L02001e72:
    r1 = L01c26f08
    r0 = [r1+r0<<2]
    rts
