; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; biquad_generator: 1 function, 0x01c0516e..0x01c05182

; biquad_generator_scaled_exp: 0x01c0516e..0x01c05182, module biquad-generator (scaled_exp), biquad-pipeline (scaled_exp), dsp-transition-notification (math_scaled_exp), ir-installation (scaled_exp), effect-construction (scaled_exp), effect-model-construction (scaled_exp)
.type biquad_generator_scaled_exp,@function
biquad_generator_scaled_exp:
    [--sp] = rets
    r1 = 1038862563
    r0 = r0 * r1 (f)
    call biquad_generator_exp  ; @call.xl
    pc = [sp++]
