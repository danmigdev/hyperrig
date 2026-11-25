; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_ownership: 2 functions, 0x0202de50..0x0202def2

; effect_ownership_lookup: 0x0202de50..0x0202de8c, module effect-ownership (lookup), effect-resource-ownership (ownership_lookup)
.type effect_ownership_lookup,@function
effect_ownership_lookup:
    [--sp] = {rets, r8-r4}
    r2 = r0
    r8 = L01c32db0
    r4 = r8 + 348
    r0 = 0
L0202de60:
    r5 = r0 + r8
    r5 = b[r5+14] (u)
    if (r5 == 0) goto L0202de78
    r6 = 0
    r7 = r4
L0202de6c:
    r3 = b[r7++=1] (u)
    if (r3 == r2) goto L0202de84
    r6 = r6 + 1
    ifs (r6 < r5) goto L0202de6c
L0202de78:
    r0 = r0 + 1
    r4 = r4 + 10
    ifs (r0 < 2) goto L0202de60
    r0 = -1
    {pc, r8-r4} = [sp++]
L0202de84:
    if (r1 == 0) goto L0202de8a
    [r1+0] = r6
    {pc, r8-r4} = [sp++]
L0202de8a:
    {pc, r8-r4} = [sp++]

; effect_ownership_neighbors: 0x0202de8c..0x0202def2, module effect-ownership (neighbors)
.type effect_ownership_neighbors,@function
effect_ownership_neighbors:
    [--sp] = {rets, r5, r4}
    sp += -4
    r4 = r1
    r5 = r0
    r1 = sp + 0
    r0 = r4
    call effect_ownership_lookup
    ifs (r0 < 0) goto L0202deee
    r0 = [sp]
    ifs (r0 < 1) goto L0202deee
    r1 = L01c32db0
    r2 = r5 + r1
    r2 = b[r2+14] (u)
    r2 += -1
    ifs (r0 >= r2) goto L0202deee
    r2 = r5 * 0xA
    r0 = r0 + r2
    r2 = r0 + r1
    r0 = 347
    r0 = b[r2+r0] (u)
    r1 = r0 * 0x1E0
    r0 = L01c2c220
    r1 = r1 + r0
    r1 = b[r1+4] (u)
    if (r1 == 0) goto L0202deee
    r3 = 349
    r2 = b[r2+r3] (u)
    r2 = r2 * 0x1E0
    r2 = r2 + r0
    r2 = b[r2+4] (u)
    if (r2 == 0) goto L0202deee
    r2 = r4 * 0x1E0
    r0 = r0 + r2
    b[r0+4] = r1
L0202deee:
    sp += 4
    {pc, r5, r4} = [sp++]
