; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; biquad_generator: 3 functions, 0x020285d4..0x020286a0

; biquad_generator_exp: 0x020285d4..0x02028646, module biquad-generator (exp), biquad-pipeline (exp), dsp-transition-notification (math_exp), ir-installation (exp), effect-construction (exp), effect-model-construction (exp)
.type biquad_generator_exp,@function
biquad_generator_exp:
    [--sp] = {rets, r6-r4}
    r3 = 0x3F000000
    r2 = 0
    iff (r0 u<= r3) goto L020285f0
    r1 = 3207688728
L020285e6:
    r0 = r0 + r1 (f)
    r2 = r2 + 1
    iff (r0 > r3) goto L020285e6
L020285f0:
    r1 = r3 + 0x80000000
    iff (r0 u>= r1) goto L02028608
    r4 = 1060205080
L020285fe:
    r0 = r0 + r4 (f)
    r2 += -1
    iff (r0 < r1) goto L020285fe
L02028608:
    r1 = r3 + 0x800000
    r4 = 1
    r5 = r1
L02028610:
    r6 = itof(r4)
    r6 = r0 / r6 (f)
    r5 = r5 * r6 (f)
    r4 = r4 + 1
    r1 = r1 + r5 (f)
    if (r4 != 9) goto L02028610
    ifs (r2 < 1) goto L02028636
L0202862a:
    r2 += -1
    r1 = r1 + r1 (f)
    ifs (r2 > 0) goto L0202862a
    goto L02028642
L02028636:
    ifs (r2 > -1) goto L02028642
L0202863a:
    r2 = r2 + 1
    r1 = r1 * r3 (f)
    if (r2 != 0) goto L0202863a
L02028642:
    r0 = r1
    {pc, r6-r4} = [sp++]

; biquad_generator_cosine: 0x02028646..0x02028676, module biquad-generator (cosine), biquad-pipeline (cosine), dsp-transition-notification (math_cosine), ir-convolution (window_cosine), ir-processing (window_cosine), effect-construction (cosine), effect-model-construction (cosine)
.type biquad_generator_cosine,@function
biquad_generator_cosine:
    [--sp] = {rets, r4}
    r0 = r0 * r0 (f)
    r1 = r0 ^ 0x80000000
    r0 = 0x3F800000
    r2 = 2
    r3 = r0
L02028658:
    r4 = r2 + -1
    r4 *= r2
    r4 = itof(r4)
    r4 = r1 / r4 (f)
    r3 = r3 * r4 (f)
    r2 = r2 + 2
    r0 = r0 + r3 (f)
    if (r2 != 20) goto L02028658
    {pc, r4} = [sp++]

; biquad_generator_sine: 0x02028676..0x020286a0, module biquad-generator (sine), biquad-pipeline (sine), dsp-transition-notification (math_sine), effect-construction (sine), effect-model-construction (sine)
.type biquad_generator_sine,@function
biquad_generator_sine:
    [--sp] = {rets, r4}
    r1 = r0 * r0 (f)
    r1 ^= 2147483648
    r2 = 3
    r3 = r0
L02028682:
    r4 = r2 + -1
    r4 *= r2
    r4 = itof(r4)
    r4 = r1 / r4 (f)
    r3 = r3 * r4 (f)
    r2 = r2 + 2
    r0 = r0 + r3 (f)
    if (r2 != 21) goto L02028682
    {pc, r4} = [sp++]
