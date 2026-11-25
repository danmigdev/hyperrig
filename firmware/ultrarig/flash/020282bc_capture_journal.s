; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_journal: 1 function, 0x020282bc..0x020282f4

; capture_journal_compare: 0x020282bc..0x020282f4, module capture-journal (compare), preset-loader (compare)
.type capture_journal_compare,@function
capture_journal_compare:
    [--sp] = {rets, r4}
    if (r2 < 4) goto L020282cc
    r3 = r1 | r0
    if ((r3 & 0x3) == 0) goto L020282e2
L020282cc:
    if (r2 == 0) goto L020282f0
    r3 = b[r1++=1] (u)
    r4 = b[r0++=1] (u)
    r2 += -1
    if (r4 == r3) goto L020282cc
    r0 = r4 - r3
    {pc, r4} = [sp++]
L020282dc:
    r2 += -4
    r1 += 4  ; @add.ri.u5
    r0 += 4  ; @add.ri.u5
L020282e2:
    if (r2 < 4) goto L020282cc
    r3 = [r1+0]
    r4 = [r0+0]
    if (r4 == r3) goto L020282dc
    goto L020282cc
L020282f0:
    r0 = 0
    {pc, r4} = [sp++]
