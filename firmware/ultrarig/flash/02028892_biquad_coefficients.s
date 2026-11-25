; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; biquad_coefficients: 2 functions, 0x02028892..0x02028920

; biquad_coefficients_setup: 0x02028892..0x020288d6, module biquad-coefficients (setup), biquad-pipeline (setup), dsp-transition-notification (coefficients_setup)
.type biquad_coefficients_setup,@function
biquad_coefficients_setup:
    [--sp] = {rets, r4}
    sp += -4
    r2 = L01c32db0
    r2 = r2 + r0
    r3 = b[r2+169] (s)
    r2 = 1063675494
    [sp] = r2
    r2 = 2
    if (r0 != 4) {
    r2 = 1
    }
    r4 = r0
    if (r0 == 0) goto L020288b8
    r4 = r2
L020288b8:
    r2 = effect_prior_coefficient_selector
    r0 = h[r2+r0<<1] (u)
    r2 = utof(r0)
    r3 = itof(r3)
    r0 = r1
    r1 = r4
    call biquad_generator_generate
    sp += 4
    {pc, r4} = [sp++]

; biquad_coefficients_stage: 0x020288d6..0x02028920, module biquad-coefficients (stage), biquad-pipeline (stage), dsp-transition-notification (coefficients_stage)
.type biquad_coefficients_stage,@function
biquad_coefficients_stage:
    [--sp] = {rets, r4}
    r3_r2 = r1_r0
    call biquad_coefficients_counter  ; @call.xl
    if (r2 <= 4) goto L020288e6
    {pc, r4} = [sp++]
L020288e6:
    r0 = 244
    ifs (r3 < -12) goto L020288f4
    ifs (r3 >= 12) {
    r3 = 12
    }
    r0 = r3
L020288f4:
    r1 = L01c32db0
    r4 = r2 + r1
    r3 = 0
    b[++r4=164] = r3
    r0 = r2 * 0x2C  #
    b[r4+5] = r0
    [r1+24] = r3
    r1 = L01c33190
    r0 = r0 + r1
    r1 = r0 + 176
    r0 = r2
    call biquad_coefficients_setup
    r0 = 1
    b[r4+0] = r0
    {pc, r4} = [sp++]
