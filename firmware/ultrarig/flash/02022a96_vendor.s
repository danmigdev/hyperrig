; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02022a96..0x02022abc: vendor code (JieLi SDK or library, not reversed), as instructions
L02022a96:
    r3 = r0
    r0 = -1
    if (r3 == 0) goto L02022aba
    r3 = [r3+12]
    if (r3 == 0) goto L02022aba
    r0 = 0
    if (r2 == 2) goto L02022ab4
    if (r2 == 1) {  ; @if.eq.ri.s12
    [r3+0] += r1
    rts
    }
    if (r2 == 0) goto L02022ab8
    rts
L02022ab4:
    r2 = [r3+12]
    r1 = r2 - r1
L02022ab8:
    [r3+0] = r1
L02022aba:
    rts
