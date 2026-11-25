; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; biquad_generator: 2 functions, 0x0202870a..0x02028892

; biquad_generator_square_root: 0x0202870a..0x02028734, module biquad-generator (square_root), biquad-pipeline (square_root), dsp-transition-notification (math_square_root), effect-construction (square_root), effect-model-construction (square_root)
.type biquad_generator_square_root,@function
biquad_generator_square_root:
    [--sp] = {rets, r4}
    r1 = 0
    iff (r0 <= r1) goto L02028730
    r1 = r1 + 0x3F800000
    r1 = fmax(r0, r1)
    r2 = 20
    r3 = 0x3F000000
L02028720:
    r4 = r0 / r1 (f)
    r1 = r1 + r4 (f)
    r1 = r1 * r3 (f)
    if (--r2 != 0) goto L02028720
L02028730:
    r0 = r1
    {pc, r4} = [sp++]

; biquad_generator_generate: 0x02028734..0x02028892, module biquad-generator (generate), biquad-pipeline (generate), dsp-transition-notification (math_generate), effect-construction (generate), effect-model-construction (generate)
.type biquad_generator_generate,@function
biquad_generator_generate:
    [--sp] = {rets, r13-r4}
    sp += -20
    r7_r6 = r3_r2
    r4 = r1
    r8 = r0
    r12 = 0x3F000000
    r0 = r7 * r12 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = L01c1f7f0
    r5 = r0  #
    r1 = [r1+8]
    r0 = 1086918619
    r0 = r6 * r0 (f)
    r1 = utof(r1)
    r6 = r0 / r1 (f)
    r0 = r6
    call biquad_generator_cosine
    r9 = r0
    r0 = r6
    call biquad_generator_sine
    if (r4 != 1) goto L020287be
    r1 = [sp+64]
    r2 = 0
    [sp+16] = r2
    r3 = 0
    r2 = 1
    iff (r7 == r3) {
    r2 = 0
    }
    r2 = r3 + 0xC0000000  #
    [sp+12] = r2
    r2 = r9 * r2 (f)
    r1 = r1 + r1 (f)  #
    [sp+4] = r2
    r0 = r0 / r1 (f)
    r1 = r0 / r5 (f)
    r3 = r3 + 0x3F800000
    r4 = r3 - r1 (f)
    r4 = r1 + r3 (f)  #
    [sp+8] = r4
    r0 = r5 * r0 (f)  #
    [sp] = r4
    r1 = r0 + r3 (f)
    r3 = r3 - r0 (f)
    goto L02028888
L020287be:
    r1 = r12 + 0x800000
    r10 = r5 + r1 (f)
    r1 = r1 + 0x80000000
    r13 = r5 + r1 (f)
    r11 = r13 * r9 (f)
    r6 = r0 * r12 (f)
    r0 = r12 + 0x1000000
    call biquad_generator_square_root
    r6 = r6 * r0 (f)
    r0 = r5
    call biquad_generator_square_root
    r0 = r0 + r0 (f)
    r0 = r6 * r0 (f)
    if (r4 != 0) goto L02028836
    r1 = 1
    r2 = 0
    [sp+16] = r1
    iff (r7 == r2) {
    r1 = 0
    }
    r1 = r10 + r11 (f)  #
    [sp+12] = r1
    r2 = r1 - r0 (f)
    r1 = r1 + r0 (f)  #
    [sp+8] = r2
    r2 = r10 * r9 (f)  #
    [sp] = r1
    r1 = r13 + r2 (f)
    r3 = r12 + 0x81000000
    r4 = r1 * r3 (f)
    r3 = r10 - r11 (f)
    r1 = r3 + r0 (f)
    r1 = r5 * r1 (f)
    r2 = r13 - r2 (f)
    r6 = r5 + r5 (f)
    r2 = r6 * r2 (f)
    goto L0202887e
L02028836:
    r1 = 0
    [sp+16] = r1
    r2 = 0
    r1 = 1
    iff (r7 == r2) {
    r1 = 0
    }
    r1 = r10 - r11 (f)  #
    [sp+12] = r1
    r2 = r1 - r0 (f)
    r1 = r1 + r0 (f)  #
    [sp+8] = r2
    r1 = r10 * r9 (f)  #
    [sp] = r1
    r2 = r13 - r1 (f)
    r4 = r2 + r2 (f)
    r2 = r12 + 0x81000000
    r2 = r5 * r2 (f)
    r1 = r13 + r1 (f)
    r2 = r2 * r1 (f)
    r3 = r10 + r11 (f)
    r1 = r3 + r0 (f)
    r1 = r5 * r1 (f)
L0202887e:
    r0 = r3 - r0 (f)  #
    [sp+4] = r4
    r3 = r5 * r0 (f)
L02028888:
    r0 = r8
    call biquad_coefficients_normalize
    sp += 20
    {pc, r13-r4} = [sp++]
