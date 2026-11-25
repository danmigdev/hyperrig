; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020222ea..0x02022386: vendor code (JieLi SDK or library, not reversed), as instructions
L020222ea:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = 40
    call L0203d940  ; @call.xl
    if (r0 == 0) goto L020222fa
    [r4+0] = r0
L020222fa:
    {pc, r4} = [sp++]
L020222fc:
    [--sp] = {rets, r7-r4}
    r7 = L01c26354
    r4 = r0  #
    r6 = [r7+16]
    r0 = r4 + 32
    call L020222ea
    r5 = r0
    if (r6 == 0) goto L0202233e
    call L020222ea
    r1 = [r7+16]
    [r5+4] = r1
    r5 += 18  ; @add.ri.u5
    r1 = L02036035  ; "EXT_RESERVED"
    r2 = r5
    rep 16 {
    r3 = b[r1++=1] (u)
    b[r2++=1] = r3
    }
    r6 = r0
    r0 = r5
    call L020283a8  ; @call.xl
    r1 = 0
    b[r5+r0] = r1
    r0 = 3
    r5 = r6
    goto L02022340
L0202233e:
    r0 = 2
L02022340:
    b[r4+165] = r0
    r1 = r4 + 48  #
    r0 = [r7+12]
    [r4+36] = r0
    r0 = 97
    b[r1+2] = r0
    r0 = 112
    b[r1+3] = r0
    b[r1+4] = r0
    r2 = 0
    b[r1+5] = r2
    r0 = [r7+20]
    r1 = r5 + 4
    [r1+0] = r0
    r0 = 114
    b[r1+14] = r0
    r0 = 101
    b[r1+15] = r0
    r0 = 115
    b[r5+20] = r0
    r0 = 0
    b[r5+21] = r2
    {pc, r7-r4} = [sp++]
L02022376:
    r1 = L01c26354
    r2 = [r1+8]
    r0 = r0 - r2  #
    r1 = [r1+0]
    r0 += r1  ; @add.rr
    rts
