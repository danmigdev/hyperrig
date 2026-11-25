; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; biquad_coefficients: 1 function, 0x01c05182..0x01c051a2

; biquad_coefficients_q28: 0x01c05182..0x01c051a2, module biquad-coefficients (q28), biquad-pipeline (q28), dsp-transition-notification (coefficients_q28), effect-construction (q28), effect-model-construction (q28)
.type biquad_coefficients_q28,@function
biquad_coefficients_q28:
    r1 = 0
    iff (r0 u< r1) {
    r1 = r1 + 0xBF000000
    } else {
    r1 = r1 + 0x3F000000
    }
    r2 = 0x4D800000
    r0 = r0 * r2 (f)
    r0 = r0 + r1 (f)
    r0 = ftoi(r0) (trunc)
    rts
