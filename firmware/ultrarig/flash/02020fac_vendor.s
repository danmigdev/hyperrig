; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02020fac..0x02021016: vendor code (JieLi SDK or library, not reversed), as instructions
L02020fac:
    [--sp] = {rets, r10-r4}
    sp += -32
    r9 = r2
    r8 = r1
    r6 = r0
    r5 = sp + 0
    r10 = r5 + 16
    r4 = r5 | 0x2
    r7 = 32
    goto L02020ff2
L02020fc4:
    r0 = sp + 0
    r2 = 32
    r1 = r6
    call phase3_p8_memcpy_flash
    r1 = 30
    r0 = r4
    call L02001776
    r1 = h[sp] (u)
    if (r0 != r1) goto L02020fee
    r0 = r10
    r1 = r9
    call L02020e88
    if (r0 == 0) goto L02020ffc
    r0 = h[r5+14] (u)
    if (r0 == 0) goto L02020ff0
    goto L0202100e
L02020fee:
    r7 += -1
L02020ff0:
    r6 += 32
L02020ff2:
    ifs (r7 >= 1) goto L02020fc4
    r4 = -254
    goto L02021010
L02020ffc:
    r4 = 0
    if (r8 == 0) goto L02021010
    r1 = sp + 0
    r2 = 32
    r0 = r8
    call phase3_p8_memcpy_flash
    goto L02021010
L0202100e:
    r4 = 1
L02021010:
    r0 = r4
    sp += 32
    {pc, r10-r4} = [sp++]
