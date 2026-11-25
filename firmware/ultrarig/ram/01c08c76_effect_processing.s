; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_processing: 1 function, 0x01c08c76..0x01c08c98

; effect_processing_exp: 0x01c08c76..0x01c08c98, module effect-processing (exp)
.type effect_processing_exp,@function
effect_processing_exp:
    r1 = 5130
    r1 *= r0
    r1 = r1 >> 16
    r2 = 14831
    r1 = r1 + r2
    r1 *= r0
    r1 = r1 >> 16
    r2 = 45575
    r1 = r1 + r2
    r0 *= r1
    r0 = r0 >> 16
    r0 |= 65536
    rts
