; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201ee98..0x0201ef1c: vendor code (JieLi SDK or library, not reversed), as instructions
L0201ee98:
    [--sp] = {rets, r6-r4}
    sp += -4
    r4 = r2
    r5 = r1
    r6 = r0
    call L0204178c  ; @call.xl
    r1 = 1
    [sp] = r1
    if (r4 <= 3) {  ; @if.le.ri.s12
    r4 = 3
    }
    r1 = r6
    r2 = r5
    r3 = r4
    call L0201c816
    sp += 4
    {pc, r6-r4} = [sp++]
L0201eec0:
    [--sp] = {rets, r6-r4}
    if (r3 == 0) goto L0201eec8
    r3 = r3 >> 2
    r0 ^= r3
L0201eec8:
    r2 += -1
    r3 = -4130
    r4 = r0
    goto L0201eef8
L0201eed2:
    r4 = r0 << 1
    r4 &= r3
    r0 = r0.l (u)
    r5 = r0 >> 15
    r4 |= r5
    r6 = r0 >> 11
    r6 ^= r5
    r6 = r6 << 12
    r6 = r6 & 0x1000
    r4 |= r6
    r0 = r0 >> 4
    r0 ^= r5
    r0 = r0 << 5
    r0 = r0 & 0x20
    r0 |= r4
    r4 = r0.b0 (u)
    r2 += -1
L0201eef8:
    r5 = b[r1+0] (u)
    r4 ^= r5
    b[r1++=1] = r4
    if (r2 != 0) goto L0201eed2
    {pc, r6-r4} = [sp++]
    r0 = 0
    rts
L0201ef06:
    r0 = 1376
    r1 = L01c26890
    r0 = b[r1+r0] (u)
    r1 = 1
    r0 = r1 & ~r0
    rts
