; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02001b40..0x02001cea: vendor code (JieLi SDK or library, not reversed), as instructions
L02001b40:
    [--sp] = {rets, r5, r4}
    r2 = r1
    r3 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r4 = L01c1fc4c
    r0 = cnum
    r1 = [r4+r0<<2]
    r5 = r1 + 1
    [r4+r0<<2] = r5
    if (r1 != 0) goto L02001b64
    lockset
L02001b64:
    csync
    if (r3 == 0) goto L02001b72
    r0 = 90123
    b[r0+0] = r2
    goto L02001b78
L02001b72:
    r0 = 11
    r1 = r2
    call L02001ac0
L02001b78:
    csync
    r0 = cnum
    r1 = [r4+r0<<2]
    r1 += -1
    [r4+r0<<2] = r1
    if (r1 != 0) goto L02001b8c
    lockclr
L02001b8c:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r5, r4} = [sp++]
L02001b94:
    r2 = 0x11800
    r1 = r0  #
    r3 = [r2+0]
    r0 = 0
    if ((r3 & 4) == 0) goto L02001bc8
    r1 = r1 << 8
    r3 = 16760576
    r1 &= r3
    r1 |= 16384
    [r2+4] = r1
    csync
    r1 = -20001
L02001bb6:
    r3 = [r2+4]
    r3 = r3.l (s)
    ifs (r3 < 0) goto L02001bc4
    r1 += 1  ; @add.ri.u5
    if (r1 != 0) goto L02001bb6
    rts
L02001bc4:
    r0 = [r2+4]
    r0 = r0.b0 (u)
L02001bc8:
    rts
L02001bca:
    [--sp] = {rets, r6-r4}
    r4 = r1
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r6 = L01c1fc4c
    r0 = cnum
    r1 = [r6+r0<<2]
    r3 = r1 + 1
    [r6+r0<<2] = r3
    if (r1 != 0) goto L02001bee
    lockset
L02001bee:
    csync
    if (r2 == 0) goto L02001c10
    r0 = 90118
    r1 = h[r0+0] (u)
    if (r4 != -1) {  ; @if.ne.ri.s12
    r2 = 65535
    r2 = r2 ^ (1 << r4)
    r1 &= r2
    } else {
    r1 = 0
    }
    h[r0+0] = r1
    goto L02001c3c
L02001c10:
    r0 = 7
    call L02001b94
    r5 = r0
    r0 = 8
    call L02001b94
    if (r4 != -1) {  ; @if.ne.ri.s12
    r0 = r0 << 8
    r0 |= r5
    r0 = r0 & ~(1 << r4)
    r4 = r0.l (u)
    } else {
    r4 = 0
    }
    r1 = r4 & 0xFFFF00FF
    r0 = 7
    call L02001ac0
    r1 = r4 >> 8
    r0 = 8
    call L02001ac0
L02001c3c:
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L02001c50
    lockclr
L02001c50:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r6-r4} = [sp++]
L02001c58:
    [--sp] = {rets, r6-r4}
    r4 = r1
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r6 = L01c1fc4c
    r0 = cnum
    r1 = [r6+r0<<2]
    r3 = r1 + 1
    [r6+r0<<2] = r3
    if (r1 != 0) goto L02001c7c
    lockset
L02001c7c:
    csync
    if (r2 == 0) goto L02001c9e
    r0 = 90120
    r1 = h[r0+0] (u)
    if (r4 != -1) {  ; @if.ne.ri.s12
    r2 = 65535
    r2 = r2 ^ (1 << r4)
    r1 &= r2
    } else {
    r1 = 0
    }
    h[r0+0] = r1
    goto L02001cce
L02001c9e:
    r0 = 9
    call L02001b94
    r5 = r0
    r0 = 10
    call L02001b94
    if (r4 != -1) {  ; @if.ne.ri.s12
    r0 = r0 << 8
    r0 |= r5
    r0 = r0 & ~(1 << r4)
    r4 = r0.l (u)
    } else {
    r4 = 0
    }
    r1 = r4 & 0xFFFF00FF
    r0 = 9
    call L02001ac0
    r1 = r4 >> 8
    r0 = 10
    call L02001ac0
L02001cce:
    csync
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L02001ce2
    lockclr
L02001ce2:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r6-r4} = [sp++]
