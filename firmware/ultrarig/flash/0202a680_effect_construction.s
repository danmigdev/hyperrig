; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_construction: 3 functions, 0x0202a680..0x0202a75e

; effect_construction_rate_exp: 0x0202a680..0x0202a6aa, module effect-construction (rate_exp), effect-model-construction (rate_exp)
.type effect_construction_rate_exp,@function
effect_construction_rate_exp:
    [--sp] = rets
    r1 = L01c1f7f0
    r1 = [r1+8]
    r1 = utof(r1)
    r0 = r1 * r0 (f)
    r1 = 3329884160
    r0 = r1 / r0 (f)
    call biquad_generator_exp
    r1 = 0x3F800000
    r0 = r1 - r0 (f)
    pc = [sp++]

; effect_construction_q30: 0x0202a6aa..0x0202a6ca, module effect-construction (q30), effect-model-construction (q30)
.type effect_construction_q30,@function
effect_construction_q30:
    r1 = 0
    iff (r0 u< r1) {
    r1 = r1 + 0xBF000000
    } else {
    r1 = r1 + 0x3F000000
    }
    r2 = 0x4E800000
    r0 = r0 * r2 (f)
    r0 = r0 + r1 (f)
    r0 = ftoi(r0) (trunc)
    rts

; effect_construction_logarithm: 0x0202a6ca..0x0202a75e, module effect-construction (logarithm), effect-model-construction (logarithm)
.type effect_construction_logarithm,@function
effect_construction_logarithm:
    [--sp] = {rets, r5, r4}
    r1 = 8388607
    r1 &= r0
    r1 = r1 | 0x3F800000
    r2 = 1068827891
    r0 = uextra(r0, p:23, l:8)
    iff (r1 > r2) {
    r2 = 0x3F000000
    r1 = r1 * r2 (f)
    r0 += -126
    } else {
    r0 += -127
    }
    r2 = 0x3F800000
    r3 = r1 + r2 (f)
    r4 = r2 + 0x80000000
    r1 = r1 + r4 (f)
    r1 = r1 / r3 (f)
    r3 = r1 * r1 (f)
    r4 = 1038323257
    r4 = r3 * r4 (f)
    r5 = 1041385765
    r4 = r4 + r5 (f)
    r4 = r3 * r4 (f)
    r5 = 1045220557
    r4 = r4 + r5 (f)
    r4 = r3 * r4 (f)
    r5 = 1051372203
    r4 = r4 + r5 (f)
    r3 = r3 * r4 (f)
    r2 = r3 + r2 (f)
    r1 = r1 + r1 (f)
    r1 = r1 * r2 (f)
    r2 = 1069066811
    r1 = r1 * r2 (f)
    r0 = itof(r0)
    r0 = r0 + r1 (f)
    {pc, r5, r4} = [sp++]
