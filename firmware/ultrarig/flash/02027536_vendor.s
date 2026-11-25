; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02027536..0x02027590: vendor code (JieLi SDK or library, not reversed), as instructions
L02027536:
    [--sp] = {rets, r8-r4}
    sp += -20
    r4 = r1
    r5 = r0
    r8 = L01c21c58
    r1 = r8 + 32
    r0 = sp + 8
    call L0204cc32  ; @call.xl
    r7 = 0
    goto L0202756e
L02027554:
    r0 = sp + 8
    call L0204cbb4  ; @call.xl
    r6 = [r0+12]
    if (r6 == 0) goto L0202756e
    r2 = r4  #
    r0 = h[r5+0] (u)
    [sp+4] = r7
    r1 = 0
    r3 = 0
    [sp] = r7
    call r6
L0202756e:
    r0 = sp + 8
    call L0204cb98  ; @call.xl
    if (r0 != 0) goto L02027554
    r6 = [r8+24]
    if (r6 == 0) goto L0202758c
    r3_r2 = 0  #
    r0 = h[r5+0] (u)
    [sp+4] = r2
    r1 = 0
    r2 = r4  #
    [sp] = r2
    call r6
L0202758c:
    sp += 20
    {pc, r8-r4} = [sp++]
