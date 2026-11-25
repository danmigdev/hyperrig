; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_loader: 1 function, 0x0200c7ce..0x0200c806

; preset_loader_binding: 0x0200c7ce..0x0200c806, module preset-loader (binding)
.type preset_loader_binding,@function
preset_loader_binding:
    [--sp] = {rets, r8-r4}
    r4 = 0
    b[r2+0] = r4
    b[r3+0] = r4
    ifs (r1 < 0) goto L0200c804
    r4 = b[r0++=1] (u)
    ifs (r4 <= r1) goto L0200c804
    r8 = r0 + r1
    r4 = 0
    goto L0200c7fa
L0200c7e8:
    r7 = b[r8+0] (u)
    r5 = b[r0++=1] (u)
    r6 = 1
    if (r5 != r7) {
    r6 = 0
    }
    r4 += r6  ; @add.rr
    r1 += -1
L0200c7fa:
    if (r1 != 0) goto L0200c7e8
    r0 = b[r8+0] (u)
    b[r2+0] = r0
    b[r3+0] = r4
L0200c804:
    {pc, r8-r4} = [sp++]
