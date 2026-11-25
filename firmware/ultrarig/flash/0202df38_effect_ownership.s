; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_ownership: 1 function, 0x0202df38..0x0202df9a

; effect_ownership_release: 0x0202df38..0x0202df9a, module effect-ownership (release), effect-resource-ownership (ownership_release)
.type effect_ownership_release,@function
effect_ownership_release:
    [--sp] = {rets, r9-r4}
    sp += -12
    r9 = r0  #
    r4 = b[r0+7] (u)
    r3 = r0 + 104
    r8 = r0 + 84
    r0 = [r8+0]
    r5 = r9 + 92
    r7_r6 = 0
L0202df52:
    r2 = [r5+0]
    r1 = sp + 0
    [r1+r7<<2] = r2
    [r5++=4] = r6
    h[r3+r7<<1] = r6
    r7 = r7 + 1
    if (r7 != 3) goto L0202df52
    r3 = 0
    b[r9+5] = r3
    [r8+0] = r3
    [r8+4] = r3
    b[r9+7] = r3
    r5 = L01c32db0
    r1 = [r5+56]
    if (r1 == 0) goto L0202df96
    if (r0 == 0) goto L0202df86
    call r1
L0202df86:
    if (r4 == 0) goto L0202df96
    r6 = sp + 0
L0202df8a:
    r0 = [r6++=4]
    if (r0 == 0) goto L0202df92
    r1 = [r5+56]
    call r1
L0202df92:
    if (--r4 != 0) goto L0202df8a
L0202df96:
    sp += 12
    {pc, r9-r4} = [sp++]
