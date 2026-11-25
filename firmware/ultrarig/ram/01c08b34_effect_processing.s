; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_processing: 1 function, 0x01c08b34..0x01c08b3e

; effect_processing_q16: 0x01c08b34..0x01c08b3e, module effect-processing (q16)
.type effect_processing_q16,@function
effect_processing_q16:
    r1_r0 = r1 * r0 (s)
    r1_r0 >>= 16
    rts
