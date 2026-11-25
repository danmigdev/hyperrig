; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02025eaa..0x02025ed8: vendor code (JieLi SDK or library, not reversed), as instructions
L02025eaa:
    [--sp] = {rets, r4}
    r1 = 15
    r2 = 65535
    r3 = 15
    goto L02025ec6
L02025eb8:
    r4 += -1
    r4 = r2 & (1 << r4)
    if (r0 > r4) goto L02025ed4
    r1 += -1
    r3 += -1
L02025ec6:
    r4 = r3.l (u)
    if (r4 >= 2) goto L02025eb8
    r1 = 1
    if (r0 <= 1) {  ; @if.le.ri.s12
    r1 = 0
    }
L02025ed4:
    r0 = r1.b0 (u)
    {pc, r4} = [sp++]
