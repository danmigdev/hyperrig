; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201ba8a..0x0201bace: vendor code (JieLi SDK or library, not reversed), as instructions
L0201ba8a:
    [--sp] = {rets, r5, r4}
    if (r3 == 0) goto L0201bac6
    r4 = 1
    b[r0+1] = r4
    r5 = b[r1+7] (u)
    r1 = b[r1+6] (u)
    r1 <= insert(r5, p:8, l:8)  #
    r4 = [r0+4]
    h[r0+2] = r1
    [r0+8] = r4
    r5 = 0
    if (r1 > r3) {
    h[r0+2] = r3
    r1 = r3
    r5 = 1
    }
    b[r0+21] = r5
    if (r4 == r2) goto L0201baca
    r3 = r1.l (u)
    if (r3 == 0) goto L0201baca
    r0 = r4
    r1 = r2
    r2 = r3
    call effect_parameter_support_memmove  ; @call.xl
    goto L0201baca
L0201bac6:
    r4 = 0
    b[r0+1] = r4
L0201baca:
    r0 = r4
    {pc, r5, r4} = [sp++]
