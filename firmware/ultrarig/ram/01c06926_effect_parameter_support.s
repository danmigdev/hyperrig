; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_support: 2 functions, 0x01c06926..0x01c069b0

; effect_parameter_support_ratio: 0x01c06926..0x01c0696a, module effect-parameter-support (ratio)
.type effect_parameter_support_ratio,@function
effect_parameter_support_ratio:
    [--sp] = {rets, r5, r4}
    r5_r4 = r1_r0
    r5_r4 <<= 16
    r3 = -1
    r0 = r4 + -1
    r1 = r5 + r3 + c
    ifs (r2 <= 1) {
    r2 = 1
    }
    r3 = 0
    r4 = 0
    call effect_parameter_support_signed_divide  ; @call.xl
    r2 = 2147483647
    r2 = r0 - r2
    r2 = r1 - r4 - !c
    r2 = psr
    r3 = r2 >> 3
    r2 ^= r3
    if ((r2 & 0x1) == 0) {
    r0 = 2147483647
    r1 = 0
    }
    {pc, r5, r4} = [sp++]

; effect_parameter_support_time_rule: 0x01c0696a..0x01c069b0, module effect-parameter-support (time_rule)
.type effect_parameter_support_time_rule,@function
effect_parameter_support_time_rule:
    [--sp] = {rets, r5, r4}
    r5 = L01c32db0
    r3 = r0  #
    r4 = b[r5+3] (u)
    r0 = 0
    if (r4 == 0) goto L01c0697c
L01c0697a:
    {pc, r5, r4} = [sp++]
L01c0697c:
    r4 = L01c1f7f0
    r4 = b[r4+0] (u)
    if (r3 == 0) goto L01c0697a
    if (r4 == 0) goto L01c0697a
    r5 = [r5+40]
    r2 = r5 & (1 << r2)
    if (r2 == 0) goto L01c0697a
    if (r3 != 100) goto L01c069a2
    if (r4 != 100) goto L01c069a2
    r2 = 1200
    r0 = 2350
    goto L01c069aa
L01c069a2:
    r2 = 2750
    r0 = 3550
L01c069aa:
    if (r1 != 0) goto L01c0697a
    r0 = r2
    {pc, r5, r4} = [sp++]
