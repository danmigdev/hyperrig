; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_construction: 1 function, 0x0202beb2..0x0202bffc

; effect_construction_type26: 0x0202beb2..0x0202bffc, module effect-construction (type26), effect-model-construction (type26)
.type effect_construction_type26,@function
effect_construction_type26:
    [--sp] = {rets, r15-r4}
    sp += -8
    r4 = r0
    r0 = h[r4+72] (s)
    r0 = itof(r0)
    r1 = 1036831949
    r5 = h[r4+70] (s)
    r6 = h[r4+74] (s)
    r0 = r0 + r1 (f)
    r1 = 0xBF000000
    r0 = r0 * r1 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = L01c1f7f0
    r9 = r0  #
    r1 = [r1+8]
    r1 = utof(r1)
    r0 = 1055286886
    r12 = r1 * r0 (f)
    r0 = itof(r6)
    r13 = itof(r5)
    r0 = r13 / r0 (f)
    r0 = r0 + r0 (f)
    [sp] = r0
    [sp+4] = r1
    r5 = 0
    r7 = 1
    r14 = 328
    goto L0202bfce
L0202bf16:
    r0 = 1086918619
    r0 = r1 * r0 (f)  #
    r1 = [sp+4]
    r6 = r0 / r1 (f)
    r0 = 0x3F000000
    r0 = r6 * r0 (f)
    call biquad_generator_sine
    r10 = r0
    r0 = r6
    call biquad_generator_sine
    r1 = [sp]
    r3 = r0 / r1 (f)
    r0 = r9 * r3 (f)
    r8 = r9 * r0 (f)
    r0 = r8 - r3 (f)
    r1 = 0x3F800000
    r15 = r3 + r1 (f)
    r0 = r0 / r15 (f)
    call biquad_coefficients_q28  ; @call.xl
    r0 = r0 + 0x10000000
    r6 = r4 + r5
    r11 = r6 + 288
    [r11+0] = r0
    r0 = r3 + r8 (f)
    r0 = r0 / r15 (f)
    call biquad_coefficients_q28  ; @call.xl
    r0 = 0x10000000 - r0
    [r11+8] = r0
    r0 = r10 + r10 (f)
    r0 = r10 * r0 (f)
    r0 = r0 + r3 (f)
    r0 = r0 + r0 (f)
    r0 = r0 / r15 (f)
    call biquad_coefficients_q28  ; @call.xl
    r0 = 0x20000000 - r0
    [r11+12] = r0
    r0 = 0x0 - r0
    [r11+4] = r0
    r0 = r3 + r3 (f)
    r0 = r0 / r15 (f)
    call biquad_coefficients_q28  ; @call.xl
    r0 = r0 + 0xF0000000
    [r11+16] = r0
    r0 = 1
    r1 = 329
    b[r6+r1] = r0
    goto L0202bfea
L0202bfce:
    r1 = h[r4+76] (s)
    r2 = r7 + -1
    r0 = 0
    ifs (r2 >= r1) goto L0202bfea
    r0 = itof(r7)
    r1 = r13 * r0 (f)
    r0 = 0
    iff (r1 u< r12) goto L0202bf16
L0202bfea:
    r1 = r4 + r5
    b[r1+r14] = r0
    r5 += 44
    r7 = r7 + 1
    if (r5 != 176) goto L0202bfce
    sp += 8
    {pc, r15-r4} = [sp++]
