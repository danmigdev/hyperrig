; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_integrity: 2 functions, 0x01c06b2c..0x01c06c08

; effect_integrity_integrity_probe: 0x01c06b2c..0x01c06b82, module effect-integrity (integrity_probe)
.type effect_integrity_integrity_probe,@function
effect_integrity_integrity_probe:
    [--sp] = {rets, r9-r4}
    r1 = b[r0+7] (u)
    if (r1 == 0) goto L01c06b7e
    r2 = r0 + 104
    r3 = 0
    r4 = r2 + -12
    r5 = 3235798765
    r6 = r5 + -1
    r9 = r5 + 2
    r8 = r5 + 1
L01c06b4e:
    r7 = h[r2+r3<<1] (u)
    r0 = [r4+r3<<2]
    r7 = r7 << 2
    r7 = [++r0=r7]
    if (r7 != r5) goto L01c06b7c
    r7 = [r0+4]
    if (r7 != r6) goto L01c06b7c
    r7 = [r0+8]
    if (r7 != r9) goto L01c06b7c
    r7 = [r0+12]
    if (r7 != r8) goto L01c06b7c
    r3 = r3 + 1
    if (r3 < r1) goto L01c06b4e
    r0 = 0
    {pc, r9-r4} = [sp++]
L01c06b7c:
    {pc, r9-r4} = [sp++]
L01c06b7e:
    r0 = 0
    {pc, r9-r4} = [sp++]

; effect_integrity_corrupt_slot: 0x01c06b82..0x01c06c08, module effect-integrity (corrupt_slot)
.type effect_integrity_corrupt_slot,@function
effect_integrity_corrupt_slot:
    [--sp] = {rets, r7-r4}
    r4 = r0
    r0 = r4 * 0x1E0
    r1 = L01c2c220
    r5 = r0 + r1
    r0 = [r5+84]
    r1 = [r5+88]
    r1 = r1 << 1
    r1 = r1 + 2
    r1 = r1 & 0xFFFFFFFC
    r1 = [++r0=r1]
    r6 = 3235798765
    if (r1 != r6) goto L01c06bd6
    r2 = r6 + -1  #
    r1 = [r0+4]
    if (r1 != r2) goto L01c06bd6
    r1 = [r0+8]
    r2 = r2 + 3
    if (r1 != r2) goto L01c06bd6
    r1 = [r0+12]
    r2 += -1
    if (r1 != r2) goto L01c06bd6
    r0 = b[r5+7] (u)
    if (r0 == 0) {
    r0 = 0
    } else {
    r0 = r5
    call effect_integrity_integrity_probe
    }
L01c06bd6:
    r2 = 0
    r1 = L01c34464
    r7 = [r1+0]
    b[r5+1] = r2
    h[r5+8] = r2
    b[r5+5] = r2
    r3 = L01c343c4
    r3 = [r3+0]
    r7 = r7 + 1
    [r1+0] = r7
    if (r3 == 0) goto L01c06c06
    r1 = b[r5+0] (u)
    r1 <= insert(r4, p:8, l:24)
    if (r0 == 0) goto L01c06c02
    r0 = [r0+0]
    r2 = r0 ^ r6
L01c06c02:
    r0 = 1
    call r3
L01c06c06:
    {pc, r7-r4} = [sp++]
