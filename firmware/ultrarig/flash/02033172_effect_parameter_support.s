; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_parameter_support: 1 function, 0x02033172..0x020331ce

; effect_parameter_support_signed_divide: 0x02033172..0x020331ce, module effect-parameter-support (signed_divide)
.type effect_parameter_support_signed_divide,@function
effect_parameter_support_signed_divide:
    [--sp] = {rets, r13-r4}
    sp += -4
    r13_r12 = r3_r2
    r7_r6 = r1_r0
    r3_r2 = r7_r6
    r3_r2 >>>= 63
    r9 = r3 ^ r7
    r8 = r2 ^ r6
    r0 = r8 - r2
    r1 = r9 - r3 - !c
    r9_r8 = r13_r12
    r9_r8 >>>= 63
    r11 = r9 ^ r13
    r10 = r8 ^ r12
    r2 = r10 - r8
    r4 = 0
    r3 = r11 - r9 - !c  #
    [sp] = r4
    call effect_parameter_support_unsigned_divide  ; @call.xl
    r3 = r13 ^ r7
    r2 = r12 ^ r6
    r3_r2 >>>= 63
    r5 = r1 ^ r3
    r4 = r0 ^ r2
    r0 = r4 - r2
    r1 = r5 - r3 - !c
    sp += 4
    {pc, r13-r4} = [sp++]
