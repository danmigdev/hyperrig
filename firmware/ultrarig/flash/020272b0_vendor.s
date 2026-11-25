; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020272b0..0x02027312: vendor code (JieLi SDK or library, not reversed), as instructions
L020272b0:
    [--sp] = {rets, r7-r4}
    r2 = r0
    r3 = [r2+0]
    r1 = 0
    r5 = 0
    r0 = r3
    call L0204cb74  ; @call.xl
    r4 = r0
    h[r2+4] = r4
    if (r4 == 0) goto L020272fe
    r1 = 2
    r0 = r3
    call L0204cb74  ; @call.xl
    r5 = r0
    r0 = r3  #
    h[r2+6] = r5
    r1 = 4
    call L0204cb74  ; @call.xl
    if ((r5 & 0x200) != 0) {
    r6 = 22
    r7 = 65514
    } else {
    r6 = 8
    r7 = 65528
    }
    r5 = r3 + 6
    r1 = r3 + r4
    r3 += r6  ; @add.rr
    r4 += r7  ; @add.rr
    goto L02027306
L020272fe:
    r1_r0 = 0  #
    h[r2+6] = r5
    r4 = 0
    r3 = 0
L02027306:
    h[r2+8] = r0
    [r2+12] = r5
    h[r2+16] = r4
    [r2+20] = r3
    [r2+0] = r1
    {pc, r7-r4} = [sp++]
