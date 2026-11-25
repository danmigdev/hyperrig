; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; biquad_pipeline: 1 function, 0x02028920..0x02028936

; biquad_pipeline_parameter: 0x02028920..0x02028936, module biquad-pipeline (parameter)
.type biquad_pipeline_parameter,@function
biquad_pipeline_parameter:
    r1 = r0
    r0 = 0
    if (r1 <= 4) {
    r0 = L01c32db0
    r0 = r0 + r1
    r0 = b[r0+169] (s)
    }
    rts
