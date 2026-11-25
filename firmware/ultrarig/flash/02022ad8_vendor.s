; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02022ad8..0x02022b12: vendor code (JieLi SDK or library, not reversed), as instructions
L02022ad8:
    [--sp] = {rets, r5, r4}
    r3 = r0
    r0 = 0
    if (r3 == 0) goto L02022b00
    r3 = [r3+12]
    if (r3 == 0) goto L02022b00
    r3 += 20  ; @add.ri.u5
    r4 = 0
    goto L02022aec
L02022aea:
    r4 += 1  ; @add.ri.u5
L02022aec:
    ifs (r4 > 15) goto L02022b00
    ifs (r4 >= r2) goto L02022b00
    r5 = b[r3+r4] (u)
    b[r1+r4] = r5
    if (r5 != 0) goto L02022aea
    r0 = r4
L02022b00:
    {pc, r5, r4} = [sp++]
L02022b02:
    [--sp] = rets
    if (r0 == 0) goto L02022b0e
    r0 = [r0+12]
    call L0203d218  ; @call.xl
L02022b0e:
    r0 = 0
    pc = [sp++]
