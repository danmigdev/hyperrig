; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_support: 2 functions, 0x01c06554..0x01c065a4

; effect_parameter_support_clear_halfwords: 0x01c06554..0x01c06582, module effect-parameter-support (clear_halfwords)
.type effect_parameter_support_clear_halfwords,@function
effect_parameter_support_clear_halfwords:
    [--sp] = rets
    if (r1 < 1024) goto L01c06572
    r2 = L01c34194
    r2 = [r2+0]
    if (r2 == 0) goto L01c06572
    r1 = r1 << 1
    r1 = r1 + 2
    r1 = r1 & 0xFFFFFFFC
    call r2
    pc = [sp++]
L01c06572:
    r1 = r1 + 1
    r1 = r1 >> 1
    if (r1 == 0) goto L01c06580
    r2 = 0
L01c0657a:
    [r0++=4] = r2
    if (--r1 != 0) goto L01c0657a
L01c06580:
    pc = [sp++]

; effect_parameter_support_extra: 0x01c06582..0x01c065a4, module effect-parameter-support (extra)
.type effect_parameter_support_extra,@function
effect_parameter_support_extra:
    r1 = r0
    r3 = r1 + 84
    r2 = [r3+0]
    r0 = 0
    if (r2 == 0) goto L01c065a2
    r1 = b[r1+7] (u)
    if (r1 == 0) goto L01c06596
    r0 = [r3+8]
    rts
L01c06596:
    r1 = [r3+4]
    r1 = r1 >> 4
    if (r1 >= 2021) {
    r0 = r2 + 0x2000
    }
L01c065a2:
    rts
