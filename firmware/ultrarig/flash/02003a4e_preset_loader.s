; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_loader: 1 function, 0x02003a4e..0x02003aaa

; preset_loader_snapshot: 0x02003a4e..0x02003aaa, module preset-loader (snapshot)
.type preset_loader_snapshot,@function
preset_loader_snapshot:
    [--sp] = {rets, r7-r4}
    r1 = L01c1f26e
    r2 = 0
    r3 = r0
    goto L02003a7e
L02003a5c:
    r4 = 3
    r5 = r3
    r6 = r1
    goto L02003a76
L02003a64:
    r7 = b[r6+-2] (u)
    b[r5+0] = r7
    r7 = b[r6+-1] (u)
    b[r5+1] = r7
    r7 = b[r6++=3] (u)
    b[r5+2] = r7
    r4 += -1
    r5 += 3  ; @add.ri.u5
L02003a76:
    if (r4 != 0) goto L02003a64
    r3 += 9  ; @add.ri.u5
    r1 += 9  ; @add.ri.u5
    r2 += 1  ; @add.ri.u5
L02003a7e:
    if (r2 != 4) goto L02003a5c
    r1 = 0
    goto L02003aa4
L02003a86:
    r2 = b[r0+r1] (u)
    if (r2 != 8) goto L02003aa2
    r3 = r0 + r1
    r2 = r3
    r4 = b[++r2=2] (u)
    if (r4 != 255) {  ; @if.ne.ri.s12
    r5 = b[r3+1] (u)
    r4 |= 128
    b[r3+1] = r4
    b[r2+0] = r5
    }
L02003aa2:
    r1 += 3  ; @add.ri.u5
L02003aa4:
    if (r1 != 36) goto L02003a86
    {pc, r7-r4} = [sp++]
