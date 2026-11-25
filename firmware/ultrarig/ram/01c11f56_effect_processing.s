; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_processing: 1 function, 0x01c11f56..0x01c11f66

; effect_processing_ir_active: 0x01c11f56..0x01c11f66, module effect-processing (ir_active)
.type effect_processing_ir_active,@function
effect_processing_ir_active:
    if (r0 == 0) goto L01c11f62
    r1 = [r0+0]
    r0 = 1
    if (r1 != 0) goto L01c11f60
    r0 = r1
L01c11f60:
    rts
L01c11f62:
    r0 = 0
    rts
