; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_support: 1 function, 0x02032b2e..0x02032bf0

; effect_parameter_support_memmove: 0x02032b2e..0x02032bf0, module effect-parameter-support (memmove)
.type effect_parameter_support_memmove,@function
effect_parameter_support_memmove:
    [--sp] = {rets, r6-r4}
    if (r1 > r0) goto L02032b3a
    r3 = r1 + r2
    if (r3 > r0) goto L02032b8c
L02032b3a:
    r3 = r0
    if (r2 < 8) goto L02032b68
    r5 = r1 & 0x3
    r4 = r3 & 0x3
    if (r4 == 0) goto L02032b56
    r6 = 0x4 - r4
    r2 = r2 - r6
    rep r6 {
    r6 = b[r1++=1] (u)
    b[r3++=1] = r6
    }
L02032b56:
    r4 ^= r5
    r5 = r2 >> 2
    if (r4 != 0) goto L02032b70
L02032b5c:
    rep r5 {
    r6 = [r1++=4]
    [r3++=4] = r6
    }
    if (r5 != 0) goto L02032b5c
L02032b64:
    r2 = r2 & 0x3
L02032b68:
    rep r2 {
    r2 = b[r1++=1] (u)
    b[r3++=1] = r2
    }
    {pc, r6-r4} = [sp++]
L02032b70:
    rep r5 {
    r6 = b[r1++=1] (u)
    r4 = b[r1++=1] (u)
    r6 <= insert(r4, p:8, l:8)  #
    r4 = b[r1++=1] (u)
    r6 <= insert(r4, p:16, l:8)  #
    r4 = b[r1++=1] (u)
    r6 <= insert(r4, p:24, l:8)
    [r3++=4] = r6
    }
    if (r5 != 0) goto L02032b70
    goto L02032b64
L02032b8c:
    r3 = r0 + r2
    r1 = r1 + r2
    if (r2 < 8) goto L02032bc2
    r5 = r1 & 0x3
    r4 = r3 & 0x3
    if (r4 == 0) goto L02032bac
    r2 = r2 - r4
    r6 = r4
    rep r6 {
    r6 = b[++r1=-1] (u)
    b[++r3=-1] = r6
    }
L02032bac:
    r4 ^= r5
    r5 = r2 >> 2
    if (r4 != 0) goto L02032bce
L02032bb2:
    rep r5 {
    r6 = [++r1=-4]
    [++r3=-4] = r6
    }
    if (r5 != 0) goto L02032bb2
L02032bbe:
    r2 = r2 & 0x3
L02032bc2:
    rep r2 {
    r6 = b[++r1=-1] (u)
    b[++r3=-1] = r6
    }
    {pc, r6-r4} = [sp++]
L02032bce:
    r1 += -1
L02032bd0:
    rep r5 {
    r6 = b[r1++=-1] (u)
    r6 = r6 << 24
    r4 = b[r1++=-1] (u)
    r6 <= insert(r4, p:16, l:8)  #
    r4 = b[r1++=-1] (u)
    r6 <= insert(r4, p:8, l:8)  #
    r4 = b[r1++=-1] (u)
    r6 |= r4
    [++r3=-4] = r6
    }
    if (r5 != 0) goto L02032bd0
    r1 = r1 + 1
    goto L02032bbe
