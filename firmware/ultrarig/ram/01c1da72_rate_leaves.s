; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; rate_leaves: 1 function, 0x01c1da72..0x01c1dab2

; rate_leaves_one_pole: 0x01c1da72..0x01c1dab2, module rate-leaves (one_pole)
.type rate_leaves_one_pole,@function
rate_leaves_one_pole:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r0
    r4 = [r0+0]
    r5 = [r0+4]
    r6 = [r0+8]
    r8 = [r0+20]
    r9 = [r0+24]
    r2 = [r0+28]
    r10 = 2147483649
    r1 = [r4++=4]
L01c1da90:
    rep r6 {
    r3_r2 = r2 * r9 (s)
    r3_r2 += r1 * r8 (s)
    r1 = [r4++=4]
    r0 = r3 >>> 31
    r3_r2 += r0 * r10 (s)
    r3_r2 >>>= 31
    [r5++=4] = r2
    }
    if (r6 != 0) goto L01c1da90
    r0 = [sp]
    [r0+28] = r2
    sp += 4
    {pc, r15-r4} = [sp++]
