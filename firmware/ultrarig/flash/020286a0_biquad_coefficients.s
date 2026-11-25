; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; biquad_coefficients: 1 function, 0x020286a0..0x0202870a

; biquad_coefficients_normalize: 0x020286a0..0x0202870a, module biquad-coefficients (normalize), biquad-pipeline (normalize), dsp-transition-notification (coefficients_normalize), effect-construction (normalize), effect-model-construction (normalize)
.type biquad_coefficients_normalize,@function
biquad_coefficients_normalize:
    [--sp] = {rets, r6-r4}
    r5 = r2  #
    r6 = [sp+16]
    r1 = r1 / r6 (f)
    r4 = r0
    r0 = r1
    call biquad_coefficients_q28  ; @call.xl
    r1 = r5 / r6 (f)  #
    [r4+0] = r0
    r0 = r1
    call biquad_coefficients_q28  ; @call.xl
    r1 = r3 / r6 (f)  #
    [r4+4] = r0
    r0 = r1
    call biquad_coefficients_q28  ; @call.xl
    r1 = [sp+20]
    r1 ^= 2147483648
    r1 = r1 / r6 (f)  #
    [r4+8] = r0
    r0 = r1
    call biquad_coefficients_q28  ; @call.xl
    r1 = [sp+24]
    r1 ^= 2147483648
    r1 = r1 / r6 (f)  #
    [r4+12] = r0
    r0 = r1
    call biquad_coefficients_q28  ; @call.xl
    r2 = [sp+28]
    r1 = [sp+32]
    [r4+16] = r0
    b[r4+40] = r2
    r0 = 1
    if (r1 != 0) goto L02028704
    r0 = r1
L02028704:
    b[r4+41] = r0
    {pc, r6-r4} = [sp++]
