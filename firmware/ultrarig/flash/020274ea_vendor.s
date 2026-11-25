; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x020274ea..0x0202752c: vendor code (JieLi SDK or library, not reversed), as instructions
L020274ea:
    [--sp] = {rets, r6-r4}
    r5 = r1
    r6 = r0
    r4 = 0
    if (r5 == 0) goto L02027514
    r0 = L01c21c58
    r0 = [r0+12]
    [r6+0] = r0
    goto L0202750e
L02027500:
    r0 = r6
    call L020272b0
    r0 = h[r6+8] (u)
    if (r0 == r5) goto L02027512
    r0 = [r6+0]
L0202750e:
    if (r0 != 0) goto L02027500
    goto L02027514
L02027512:
    r4 = 1
L02027514:
    r0 = r4
    {pc, r6-r4} = [sp++]
L02027518:
    [--sp] = rets
    call L0202741c
    r2 = r0 + 12
    r1 = L01c21c70
    if (r0 == 0) goto L02027528
    r1 = r2
L02027528:
    r0 = [r1+0]
    pc = [sp++]
