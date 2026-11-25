; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201fdae..0x0201fddc: vendor code (JieLi SDK or library, not reversed), as instructions
L0201fdae:
    [--sp] = {rets, r6-r4}
    r1 = r0
    r0 = 0
    r3 = L02033b40
    r2 = 0
    goto L0201fdce
L0201fdbe:
    r4 = h[++r3=2] (u)
    r6 = h[r1+0] (u)
    if (r5 == r6) goto L0201fdd4
    r2 += r4  ; @add.rr
    r2 += 4  ; @add.ri.u5
    r3 += 2  ; @add.ri.u5
L0201fdce:
    r5 = h[r3+0] (u)
    if (r5 != 0) goto L0201fdbe
    {pc, r6-r4} = [sp++]
L0201fdd4:
    h[r1+2] = r4
    [r1+4] = r2
    r0 = 1
    {pc, r6-r4} = [sp++]
