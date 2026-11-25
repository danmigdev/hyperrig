; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; biquad_coefficients: 1 function, 0x01c05160..0x01c0516e

; biquad_coefficients_counter: 0x01c05160..0x01c0516e, module biquad-coefficients (counter), biquad-pipeline (counter), dsp-transition-notification (coefficients_counter), effect-enable (counter)
.type biquad_coefficients_counter,@function
biquad_coefficients_counter:
    r0 = L01c34468
    r1 = [r0+0]
    r1 = r1 + 1
    [r0+0] = r1
    rts
