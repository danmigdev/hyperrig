; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_initialization: 1 function, 0x01c0539c..0x01c053bc

; dsp_initialization_q16: 0x01c0539c..0x01c053bc, module dsp-initialization (q16), dsp-transition-notification (initialization_q16), effect-construction (q16), effect-model-construction (q16)
.type dsp_initialization_q16,@function
dsp_initialization_q16:
    r1 = 0
    iff (r0 u< r1) {
    r1 = r1 + 0xBF000000
    } else {
    r1 = r1 + 0x3F000000
    }
    r2 = 0x47800000
    r0 = r0 * r2 (f)
    r0 = r0 + r1 (f)
    r0 = ftoi(r0) (trunc)
    rts
