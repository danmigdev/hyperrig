; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020282f4..0x020283b4: vendor code (JieLi SDK or library, not reversed), as instructions
L020282f4:
    r1 = r1.b0 (u)
L020282f6:
    r2 = b[r0++=1] (u)
    if (r2 == r1) goto L020282fe
    if (r2 != 0) goto L020282f6
L020282fe:
    r0 += -1
    if (r2 != r1) {
    r0 = 0
    }
    rts
L02028308:
    [--sp] = {rets, r7-r4}
    r4 = r0 & 0x3
    if (r4 == 0) goto L02028326
    r4 = 0x4 - r4
L02028314:
    r2 = b[r0+0] (u)
    if (r2 == 0) goto L0202839a
    r3 = b[r1+0] (u)
    if (r2 != r3) goto L0202839c
    r0 = r0 + 1
    r1 = r1 + 1
    if (--r4 != 0) goto L02028314
L02028326:
    r2 = r1 | r0
    r6 = 4278124287
    if ((r2 & 0x3) != 0) goto L0202835c
    r2 = [r0+0]
    r3 = [r1+0]
    if (r2 != r3) goto L0202838a
    r4 = r1
L02028340:
    r1 = r2 + r6
    r1 = r1 & ~r2
    if ((r1 & 0x80808080) != 0) goto L020283a4
    r2 = [r0+4]
    r5 = [r4+4]
    r1 = r4 + 4
    r0 = r0 + 4
    r4 = r1
    if (r2 == r5) goto L02028340
    goto L0202838a
L0202835c:
    r4 = r1
    r2 = [r0+0]
    r3 = b[r4++=1] (u)
    r5 = b[r4++=1] (u)
    r3 <= insert(r5, p:8, l:8)
    r5 = b[r4++=1] (u)
    r3 <= insert(r5, p:16, l:8)
    r5 = b[r4++=1] (u)
    r3 <= insert(r5, p:24, l:8)
    if (r2 != r3) goto L0202838a
    r5 = r2 + r6
    r5 = r5 & ~r2
    if ((r5 & 0x80808080) != 0) goto L020283a4
    r0 = r0 + 4
    r1 = r1 + 4
    goto L0202835c
L0202838a:
    r2 = b[r0+0] (u)
    if (r2 == 0) goto L0202839a
    r4 = b[r1+0] (u)
    if (r2 != r4) goto L0202839c
    r0 = r0 + 1
    r1 = r1 + 1
    goto L0202838a
L0202839a:
    r2 = 0
L0202839c:
    r3 = r1
    r0 = b[r3+0] (u)
    r0 = r2 - r0
    {pc, r7-r4} = [sp++]
L020283a4:
    r0 = 0
    {pc, r7-r4} = [sp++]
L020283a8:
    r1 = r0
L020283aa:
    r2 = b[r1++=1] (u)
    if (r2 != 0) goto L020283aa
    r1 += -1
    r0 = r1 - r0
    rts
