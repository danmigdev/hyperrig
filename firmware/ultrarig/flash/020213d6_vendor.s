; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020213d6..0x02021410: vendor code (JieLi SDK or library, not reversed), as instructions
L020213d6:
    [--sp] = {rets, r5, r4}
    r3 = r0
    r0 = 0
    if (r3 == 0) goto L020213fe
    r3 = [r3+12]
    if (r3 == 0) goto L020213fe
    r3 += 20  ; @add.ri.u5
    r4 = 0
    goto L020213ea
L020213e8:
    r4 += 1  ; @add.ri.u5
L020213ea:
    ifs (r4 > 15) goto L020213fe
    ifs (r4 >= r2) goto L020213fe
    r5 = b[r3+r4] (u)
    b[r1+r4] = r5
    if (r5 != 0) goto L020213e8
    r0 = r4
L020213fe:
    {pc, r5, r4} = [sp++]
L02021400:
    [--sp] = rets
    if (r0 == 0) goto L0202140c
    r0 = [r0+12]
    call L0203d218  ; @call.xl
L0202140c:
    r0 = 0
    pc = [sp++]
